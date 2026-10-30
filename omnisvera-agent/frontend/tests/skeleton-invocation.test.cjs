const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const mod={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/skeletonInvocation.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:mod,exports:mod.exports});
const {invokeSkeleton}=mod.exports;
function options(changes={}) { let id=0;return {actor:'morthak',ability:'levantar-um-esqueleto',mapId:'new-map',pending:{current:null},newId:()=>`request-${++id}`,confirmReplacement:()=>true,...changes}; }
test('one Use inspects hidden summon then confirms an explicit replacement command',async()=>{
 const calls=[];const opts=options({invoke:async payload=>{calls.push(payload);return payload.mode==='reuse'?{existing:true,existing_token_id:'old',needs_replacement:true}:{token:{id:'new'}};}});
 assert.equal((await invokeSkeleton(opts)).token.id,'new');assert.equal(calls.length,2);
 assert.equal(calls[1].mode,'replace');assert.equal(calls[1].target_id,'old');assert.notEqual(calls[0].request_id,calls[1].request_id);
 assert.equal(opts.pending.current,null);
});
test('cancel spends no replacement and does not open a hidden pin',async()=>{
 const calls=[];const opts=options({confirmReplacement:()=>false,invoke:async payload=>{calls.push(payload);return {existing:true,existing_token_id:'old',needs_replacement:true};}});
 assert.equal(await invokeSkeleton(opts),null);assert.equal(calls.length,1);assert.equal(opts.pending.current,null);
});
test('a lost replacement reply retries the same explicit command without a second summon',async()=>{
 const calls=[];let lose=true;const opts=options({invoke:async payload=>{calls.push(payload);if(payload.mode==='reuse')return {existing:true,existing_token_id:'old',needs_replacement:true};if(lose){lose=false;throw Error('timeout');}return {token:{id:'new'}};}});
 await assert.rejects(()=>invokeSkeleton(opts),/timeout/);assert.equal(opts.pending.current.id,calls[1].request_id);
 assert.equal((await invokeSkeleton(opts)).token.id,'new');assert.equal(calls.length,3);
 assert.equal(calls[1].request_id,calls[2].request_id);assert.equal(calls[2].mode,'replace');
});
test('a current-map visible summon opens normally without dismissal',async()=>{
 let confirms=0;const result={existing:true,token:{id:'old',map_id:'new-map',visible_to_players:true}};
 assert.equal(await invokeSkeleton(options({confirmReplacement:()=>{confirms++;return true;},invoke:async()=>result})),result);assert.equal(confirms,0);
});
test('a definitive rejection clears the obsolete intent so the next click reinspects',async()=>{
 const opts=options({invoke:async payload=>{if(payload.mode==='reuse')return {existing:true,existing_token_id:'old',needs_replacement:true};throw Object.assign(Error('A invocação mudou'),{status:400});}});
 await assert.rejects(()=>invokeSkeleton(opts),/mudou/);assert.equal(opts.pending.current,null);
 let mode;opts.invoke=async payload=>{mode=payload.mode;return {existing:true,token:{id:'new',map_id:'new-map'}};};
 await invokeSkeleton(opts);assert.equal(mode,'reuse');
});
test('a replacement pending for another character never executes for this one',async()=>{
 const calls=[];const opts=options({actor:'raziel',pending:{current:{key:JSON.stringify(['skeleton','morthak','levantar-um-esqueleto','replace','old']),id:'old-command'}},invoke:async payload=>{calls.push(payload);return {token:{id:'own'}};}});
 await invokeSkeleton(opts);assert.equal(calls[0].mode,'reuse');assert.notEqual(calls[0].request_id,'old-command');
});
