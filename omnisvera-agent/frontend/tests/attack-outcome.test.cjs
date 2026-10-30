const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(file,require=()=>({})){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,require});return m.exports;}
const result={confirmed:true,actor_name:'Vezemir',target_name:'Lobo',attack_name:'Grisalma',result:'hit',damage_total:12,damage_formula:'1d10+2',damage_rolls:[10],damage_modifier:2,d20:15,attack_bonus:10,attack_total:25,target_ac:14,hp_before:5,hp_after:0,breakdown:{}};
test('breath ledger keeps shared dice, each JP and actual damage without implementation data',()=>{
 const {monsterBreathOutcomeText}=load('src/attackOutcome.ts');
 const text=monsterBreathOutcomeText({roll:{formula:'2d6',individual_results:[6,6],total:12},private:'hidden',results:[
  {target:'Troll',target_id:'private-token-id',damage_dealt:6,save:{total:15,target:10},resisted:true,hp:{before:20,after:14}},
  {target:'Dragão imune',damage_dealt:0,save:{total:3,target:10},resisted:false,hp:{before:80,after:80}}
 ]});
 assert.match(text.summary,/2 alvos.*6 PV/);assert.match(text.details,/6 \+ 6 = 12/);
 assert.match(text.details,/Troll: JP 15\/10.*resistiu.*dano 6.*20 → 14/);
 assert.match(text.details,/Dragão imune:.*dano 0/);assert.doesNotMatch(text.details,/private-token-id|hidden|target_id|JSON/);
});
function automaticController(confirm,seen){
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8'),start=source.indexOf('    async function showResolution('),end=source.indexOf('\n    }',start)+6;
 const m={exports:{}};
 vm.runInNewContext(ts.transpileModule(source.slice(start,end)+'\nexports.run=showResolution;',{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:m.exports,automatic:true,confirmCharacterAttack:confirm,setAttackResolution:value=>seen.push(value)});
 return m.exports.run;
}
test('automatic confirmation never opens a transient preview while waiting',async()=>{
 const seen=[];let done;const confirm=new Promise(resolve=>{done=resolve;});
 const run=automaticController(()=>confirm,seen),pending={...result,confirmed:false,resolution_id:'same-id'};
 const inFlight=run(pending);assert.equal(seen.length,0);
 done(result);await inFlight;assert.equal(seen.length,1);assert.equal(seen[0].confirmed,true);
});
test('failed automatic confirmation retains the same pending receipt for recovery',async()=>{
 const seen=[],pending={...result,confirmed:false,resolution_id:'same-id'};
 await assert.rejects(automaticController(async()=>{throw new Error('offline');},seen)(pending),/offline/);
 assert.equal(seen.length,1);assert.equal(seen[0].resolution_id,'same-id');assert.equal(seen[0].confirmed,false);
});
test('summary distinguishes actual HP removed from rolled damage and preserves roll details',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts'),text=attackOutcomeText(result);
 assert.match(text.summary,/5 PV/);assert.match(text.details,/12/);assert.match(text.details,/15 \+ 10 = 25/);assert.match(text.details,/5 → 0/);
});
test('miss never reports rolled damage as damage dealt; automatic hit never invents a d20',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts');
 assert.match(attackOutcomeText({...result,result:'miss',hp_after:5}).summary,/0 PV/);
 const automatic=attackOutcomeText({...result,breakdown:{automatic_hit:true,resource_cost:{amount:1}}});
 assert.match(automatic.details,/Acerto automático/);assert.doesNotMatch(automatic.details,/d20|15 \+ 10/);assert.match(automatic.details,/1/);
});
test('confirmed outcome is inline, read-only, and details open only through Ver resultado',()=>{
 const jsx=(type,props)=>({type,props});
 const Outcome=load('src/components/AttackOutcome.tsx',id=>id.includes('attackOutcome')?load('src/attackOutcome.ts'):id.includes('SheetDetail')?{default:'SheetDetail'}:{jsx,jsxs:jsx}).default;
 const node=Outcome({resolution:result});assert.equal(node.props.role,'status');
 const serialized=JSON.stringify(node);assert.match(serialized,/Ver resultado/);assert.doesNotMatch(serialized,/Concluído|Confirmar|role.*dialog/);
 assert.equal(Outcome({resolution:{...result,confirmed:false}}),null);
 const workspace=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.match(workspace,/attackResolution && !attackResolution.confirmed && !attackResolution.breakdown.automatic_hit/);
 assert.match(workspace,/!attackResolution.confirmed && attackResolution.breakdown.automatic_hit/);
});
