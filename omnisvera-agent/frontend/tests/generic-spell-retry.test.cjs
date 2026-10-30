const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function moduleFile(file){
 const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports});
 return m.exports;
}
const factory=()=>{let id=0;return moduleFile('src/commandRetry.ts').createCommandRetry(()=> 'test-receipt-'+(++id));};
test('ambiguous failure keeps command ID; concurrent click sends no second mutation; success permits a new command',async()=>{
 const retry=factory(),ids=[];let fail=true,finish;
 const send=id=>{ids.push(id);if(fail)return Promise.reject(Error('lost response'));return new Promise(r=>finish=r);};
 await assert.rejects(retry.run({target:'a'},send),/lost response/);
 fail=false;const pending=retry.run({target:'a'},send);
 assert.equal(await retry.run({target:'a'},send),undefined);assert.equal(ids.length,2);assert.equal(ids[0],ids[1]);
 finish({ok:true});await pending;assert.equal(retry.pending,false);
 await retry.run({target:'a'},async id=>ids.push(id));assert.notEqual(ids[1],ids[2]);
});
test('new target, caster or turn is a new intent without retrying the failed request automatically',async()=>{
 const retry=factory(),ids=[];for(const intent of [{target:'a',turn:1},{target:'b',turn:1},{target:'b',turn:2}]){
  await assert.rejects(retry.run(intent,async id=>{ids.push(id);throw Error('network');}));
 }
 assert.equal(new Set(ids).size,3);
});
function actualHandler(file,name,endMarker,context){
 const source=fs.readFileSync(file,'utf8'),start=source.indexOf('  async function '+name+'('),end=source.indexOf(endMarker,start);
 assert.ok(start>=0&&end>start);const code=source.slice(start,end)+'\n'+name;
 return vm.runInNewContext(ts.transpileModule(code,{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,context);
}
function monster(name,refresh){
 const requests=[],applied=new Set(),state={hp:30};let lost=true;
 const send=async(id,payload)=>{requests.push(payload.request_id);if(!applied.has(payload.request_id)){applied.add(payload.request_id);state.hp-=4;}
  if(lost){lost=false;throw Error('confirmation lost');}return {results:[],manual_note:null};};
 const context={lock:{current:false},blocked:false,done:false,token:{id:'caster'},physical:false,target:'victim',die:'1',
  combat:{encounter:{started_at:'combat',turn_sequence:1}},genericCommands:{current:factory()},setBusy(){},setError(){},setExecResult(){},
  splitTarget:id=>({type:'token',id}),castCompendiumSpell:send,executeTokenAction:send,onChange:refresh|| (async()=>{})};
 const handler=actualHandler('src/components/MonsterAttackPanel.tsx',name,name==='conjureNamed'?'  async function executeUsable(':'  async function executeContact(',context);
 return {context,requests,state,handler};
}
test('actual monster spell and usable handlers recover a committed-but-lost response with one damage application',async()=>{
 for(const name of ['conjureNamed','executeUsable']){
  const h=monster(name),args=name==='conjureNamed'?['Magic','spell','Spell']:['Usable'];
  await h.handler(...args);await h.handler(...args);
  assert.equal(h.state.hp,26);assert.equal(h.requests.length,2);assert.equal(h.requests[0],h.requests[1]);
 }
});
test('actual monster handler retains receipt when the following refresh fails',async()=>{
 let refreshes=0;const h=monster('conjureNamed',async()=>{if(++refreshes===1)throw Error('read lost');});
 await h.handler('Magic','spell','Spell');await h.handler('Magic','spell','Spell');await h.handler('Magic','spell','Spell');
 assert.equal(h.state.hp,26);assert.ok(h.requests.every(id=>id===h.requests[0]));
});
test('actual CompendiumPanel handler blocks double click before React renders and recovers the same ID',async()=>{
 const ids=[];let resolve,fail=true;
 const context={spell:{id:'spell'},caster:'caster',castTarget:'victim',castDie:'',
  commands:{current:factory()},setError(){},setCasting(){},setCastResult(){},parseTarget:id=>({type:'character',id}),
  castCompendiumSpell:async(id,payload)=>{ids.push(payload.request_id);if(fail)throw Error('network');return new Promise(r=>resolve=r);}};
 const run=actualHandler('src/components/CompendiumPanel.tsx','conjureSpell','  const abilitySpecs',context);
 await run();fail=false;const pending=run();await run();assert.equal(ids.length,2);assert.equal(ids[0],ids[1]);
 resolve({results:[]});await pending;
});
test('actual non-grid grimoire picker retains its ID through refresh failure; grid arming does not cast',async()=>{
 const ids=[];let fail=true,armed=0;
 const context={chosen:{id:'spell',name:'Spell'},disabled:false,gridded:false,tokenId:'caster',target:'victim',physical:false,die:'',
  commands:{current:factory()},setError(){},setCasting(){},onArm(){armed++;},
  castCompendiumSpell:async(id,payload)=>{ids.push(payload.request_id);return {results:[]};},onDone:async()=>{if(fail)throw Error('read lost');}};
 const run=actualHandler('src/components/MonsterAttackPanel.tsx','castSelected','  return <div>',context);
 await run();fail=false;await run();assert.equal(ids[0],ids[1]);
 context.gridded=true;await run();assert.equal(armed,1);assert.equal(ids.length,2);
});
test('both real API wrappers use bounded writes and preserve the caller command ID',async()=>{
 const source=fs.readFileSync('src/api.ts','utf8'),calls=[];
 for(const name of ['castCompendiumSpell','executeTokenAction']){
  const start=source.indexOf('export async function '+name+'('),end=source.indexOf('\n}',start)+2;
  const m={exports:{}},context={module:m,exports:m.exports,API_BASE:'',authHeaders:x=>x,newDiceRequestId:()=> 'fallback-id',
   writeJson:async(...args)=>{calls.push(args);return {ok:true};}};
  vm.runInNewContext(ts.transpileModule(source.slice(start,end),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,context);
  await m.exports[name]('source',{request_id:'stable-receipt',targets:[]});
  assert.equal(calls.at(-1)[2],'POST');assert.equal(calls.at(-1)[3].request_id,'stable-receipt');
 }
 assert.equal(calls.length,2);
});
