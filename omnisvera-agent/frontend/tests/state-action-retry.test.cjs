const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
function setup(api,refresh=async()=>{}){
 let id=0;const context={selectedId:'raziel',busy:'',mutationLock:{current:false},itemRequestRef:{current:null},battleState:{},character:{state:{current_hp:10}},
  consumableActionBlock:()=>'',newDiceRequestId:()=> 'state-'+ ++id,setBusy(){},setError(){},refresh,applyCharacterStateAction:api};
 const start=source.indexOf('  async function stateAction('),end=source.indexOf('  async function restAllCharacters(',start);
 const run=vm.runInNewContext(ts.transpileModule(source.slice(start,end)+'\nstateAction',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,context);
 return {run,context};
}
test('night form failed response retries a stable explicit receipt',async()=>{
 const calls=[];let fail=true;const {run}=setup(async(...args)=>{calls.push(args);if(fail)throw new Error('connection lost');return {};});
 const payload={resource_key:'forma_da_noite',amount:1,animal:'corvo'};
 await run('consume_resource',payload,'Forma da Noite: corvo');fail=false;await run('consume_resource',payload,'Forma da Noite: corvo');
 assert.ok(calls[0][4]);assert.equal(calls[0][4],calls[1][4]);
 await run('consume_resource',{...payload,animal:'morcego'},'Forma da Noite: morcego');assert.notEqual(calls[1][4],calls[2][4]);
});
test('accepted state mutation keeps its receipt if following read fails',async()=>{
 const calls=[];let fail=true;const {run}=setup(async(...args)=>{calls.push(args);return {};},async()=>{if(fail)throw new Error('read lost');});
 await run('end_night_form',{},'Voltar');fail=false;await run('end_night_form',{},'Voltar');
 assert.ok(calls[0][4]);assert.equal(calls[0][4],calls[1][4]);
});
test('generic state double click before render sends one command',async()=>{
 const calls=[];let done;const {run}=setup((...args)=>{calls.push(args);return new Promise(resolve=>done=resolve);});
 const first=run('consume_resource',{resource_key:'forma_da_noite',amount:1,animal:'corvo'},'Corvo');
 await run('consume_resource',{resource_key:'forma_da_noite',amount:1,animal:'corvo'},'Corvo');
 assert.equal(calls.length,1);done({});await first;
});
