const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ts=require('typescript'),{createHash,webcrypto}=require('node:crypto');
function factory(){
 const m={exports:{}};const source=fs.readFileSync(process.env.COMMAND_RETRY_SOURCE||'src/commandRetry.ts','utf8');
 vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports});
 return m.exports.createCommandRetry;
}
function setup(){
 const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
 let identity='master',counter=0;
 const digest=async v=>createHash('sha256').update(v).digest('hex');
 const options={storage:()=>storage,scope:()=>digest(identity),digest};
 return {values,storage,options,identity:v=>identity=v,make:()=>factory()(()=>`command-${++counter}`,options)};
}
test('reload recovers the same receipt after committed but lost response, without automatic send',async()=>{
 const h=setup(),ids=[],applied=new Set();let hp=30;
 const cast=async id=>{ids.push(id);if(!applied.has(id)){hp-=4;applied.add(id);}throw Error('lost confirmation');};
 await assert.rejects(h.make().run({spell:'fire',target:'victim'},cast));
 const reloaded=h.make();assert.equal(ids.length,1);
 await reloaded.run({spell:'fire',target:'victim'},async id=>{ids.push(id);assert.ok(applied.has(id));return {hp};});
 assert.equal(ids[0],ids[1]);assert.equal(hp,26);assert.equal(h.values.size,0);
});
test('journal stores only opaque hashes and ID; no token, target or dice payload',async()=>{
 const h=setup();await assert.rejects(h.make().run({token:'DO-NOT-STORE',private_target:'secret',d20:17},async()=>{throw Error('network');}));
 const data=[...h.values].flat().join('');assert.ok(data.length>0);assert.doesNotMatch(data,/DO-NOT-STORE|private_target|secret|d20/);
});
test('switching access cannot reuse another identity receipt',async()=>{
 const h=setup(),ids=[];const controller=h.make();const send=async id=>{ids.push(id);throw Error('network');};
 await assert.rejects(controller.run({action:'a'},send));h.identity('player');
 await assert.rejects(controller.run({action:'a'},send));assert.notEqual(ids[0],ids[1]);
 h.identity('master');await assert.rejects(h.make().run({action:'a'},send));assert.equal(ids[0],ids[2]);
});
test('another browser tab has independent storage and command IDs',async()=>{
 const a=setup(),b=setup(),ids=[];let counter=0;
 for(const h of [a,b])await assert.rejects(factory()(()=>`tab-command-${++counter}`,h.options).run({action:'same'},async id=>{ids.push(id);throw Error('network');}));
 assert.notEqual(ids[0],ids[1]);assert.equal(a.values.size,1);assert.equal(b.values.size,1);
});
test('blocked or full storage prevents the write from being sent',async()=>{
 for(const failure of ['getter','quota','ignored','corrupt']){
  const h=setup();let sends=0;
  if(failure==='getter')h.options.storage=()=>{throw Error('blocked');};
  if(failure==='quota')h.storage.setItem=()=>{throw Error('quota');};
  if(failure==='ignored')h.storage.setItem=()=>{};
  if(failure==='corrupt')h.storage.getItem=()=>'{invalid';
  await assert.rejects(h.make().run({a:1},async()=>sends++));assert.equal(sends,0,failure);
 }
});
test('pending guard starts before asynchronous identity hashing',async()=>{
 const h=setup();let release,sends=0;const scope=()=>new Promise(r=>release=r);
 h.options.scope=scope;const run=h.make();const first=run.run({a:1},async()=>sends++);
 assert.equal(await run.run({a:1},async()=>sends++),undefined);release('a'.repeat(64));
 await new Promise(setImmediate);release('a'.repeat(64));await new Promise(setImmediate);
 release('a'.repeat(64));await first;assert.equal(sends,1);
});
test('successful acknowledgement allows a fresh command after reload',async()=>{
 const h=setup(),ids=[];await h.make().run({a:1},async id=>ids.push(id));
 await h.make().run({a:1},async id=>ids.push(id));assert.notEqual(ids[0],ids[1]);assert.equal(h.values.size,0);
});
test('confirming one action never erases another pending action',async()=>{
 const h=setup(),a=h.make(),b=h.make();let resolve;
 const first=a.run({action:'a'},()=>new Promise(r=>resolve=r));await new Promise(setImmediate);
 await assert.rejects(b.run({action:'b'},async()=>{throw Error('network');}));
 resolve('ok');await first;assert.equal(h.values.size,1);
 assert.equal(Object.keys(JSON.parse([...h.values.values()][0]).pending).length,1);
});
test('cleanup failure retains the same server receipt on the next reload',async()=>{
 const h=setup(),ids=[];h.storage.removeItem=()=>{throw Error('blocked cleanup');};
 await assert.rejects(h.make().run({action:'a'},async id=>ids.push(id)));
 h.storage.removeItem=k=>h.values.delete(k);
 await h.make().run({action:'a'},async id=>ids.push(id));assert.equal(ids[0],ids[1]);
});
test('pending capacity is bounded without silently deleting unresolved receipts',async()=>{
 const h=setup();for(let i=0;i<32;i++)await assert.rejects(h.make().run({i},async()=>{throw Error('network');}));
 let sends=0;await assert.rejects(h.make().run({i:32},async()=>sends++),/32/);assert.equal(sends,0);
 assert.equal(Object.keys(JSON.parse([...h.values.values()][0]).pending).length,32);
});
test('real API recovery scope binds access, mode and channel without persisting credentials',async()=>{
 const source=fs.readFileSync('src/api.ts','utf8'),start=source.indexOf('export function commandRecoveryOptions('),end=source.indexOf('\nexport function consumeAccessBootstrapFromUrl',start);
 let token='secret-master',mode='gm';const context={crypto:webcrypto,TextEncoder,Uint8Array,API_BASE:'',getAccessToken:()=>token,getAccessMode:()=>mode};
 const code=ts.transpileModule(source.slice(start,end).replace('export function','function')+'\ncommandRecoveryOptions',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText;
 const options=vm.runInNewContext(code,context);const a=await options('compendium').scope();
 assert.match(a,/^[a-f0-9]{64}$/);mode='player';assert.notEqual(a,await options('compendium').scope());
 mode='gm';assert.notEqual(a,await options('monster').scope());token='new-token';assert.notEqual(a,await options('compendium').scope());
 token='';await assert.rejects(options('compendium').scope(),/acesso/);
});
