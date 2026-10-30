const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
function controller(overrides={}){
 const start=source.indexOf('  async function useAbility('),end=source.indexOf('  async function submitMessage(',start),calls=[],armed=[],confirmed=[];
 const ctx={combatActionBlock:()=>'',consumableActionBlock:()=>'',battleState:{effects:[]},selectedId:'raziel',character:{definition:{hemomancy:{revision:'approved-v1'}},state:{current_hp:10}},busy:'',
  abilityLock:{current:false},mutationLock:{current:false},techniqueRequestRef:{current:null},defaultAttackRollMode:'digital',attackPhysicalD20ById:{},
  newDiceRequestId:()=> 'hemomancy-stable-01',setError(){},setBusy(){},setAttackResolution(){},refresh:async()=>{},
  armPcAction:detail=>armed.push(detail),useCharacterTechnique:async(...args)=>{calls.push(args);return {resolution_id:'native-preview'};},
  confirmCharacterAttack:async id=>{confirmed.push(id);return {resolution_id:id,confirmed:true};},...overrides};
 const run=vm.runInNewContext(ts.transpileModule(source.slice(start,end)+'\nuseAbility',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,ctx);
 return {ctx,run,calls,armed,confirmed};
}
test('weapon card arms the existing grid without spending before a target is confirmed',async()=>{
 const c=controller();await c.run({id:'hemomancia-arco',name:'Arco',active:true,requires_target:true});
 assert.equal(c.calls.length,0);assert.equal(c.armed[0].actionRef,'technique:raziel:hemomancia-arco');
});
test('confirmed grid target calls the native attack and confirmation once despite double click',async()=>{
 let finish;const c=controller({useCharacterTechnique:async(...args)=>{c.calls.push(args);await new Promise(r=>finish=r);return {resolution_id:'native-preview'};}});
 const action={id:'hemomancia-lanca-habilidade',active:true,requires_target:true};
 const running=c.run(action,{id:'enemy'},true);await c.run(action,{id:'enemy'},true);
 assert.equal(c.calls.length,1);assert.equal(c.calls[0][2].target_id,'enemy');assert.equal(c.calls[0][2].roll_mode,'digital');
 assert.equal(c.calls[0][2].definition_revision,'approved-v1');finish();await running;
 assert.deepEqual(c.confirmed,['native-preview']);
});
test('lost read after acceptance retains the same native command identity',async()=>{
 let fail=true;const c=controller({refresh:async()=>{if(fail)throw new Error('read failed');}});
 const action={id:'hemomancia-escudo',active:true,requires_target:false};
 await c.run(action);fail=false;await c.run(action);
 assert.equal(c.calls[0][2].request_id,c.calls[1][2].request_id);assert.equal(c.confirmed.length,0);
});
test('blood weapon selection comes only from server metadata; no animal forms or equipment-item conflation',()=>{
 const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/hemomancySelection.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});
 const pack={weapons:['arco','foice','marreta','escudo','lanca'].map(weapon=>({weapon,name:weapon,damage:'1d8',range_m:3,invocation_cost:1,skill:{name:'skill',cost:1,description:'effect'},passive:{name:'passive',description:'automatic'}}))};
 for(const weapon of pack.weapons){const value=m.exports.hemomancySelection(pack,weapon.weapon,true);assert.equal(value.requires_target,weapon.weapon!=='escudo');assert.equal(value.id,`hemomancia-${weapon.weapon}${weapon.weapon==='escudo'?'':'-habilidade'}`);}
 assert.equal(m.exports.hemomancySelection(pack,'morcego',false),null);
 const card=fs.readFileSync('src/components/HemomancyCard.tsx','utf8');assert.match(card,/Arma da Hemomancia/);assert.doesNotMatch(card,/Armas e formas|Arma ou forma/);
 assert.match(source,/<BloodReinforcement/);assert.doesNotMatch(source,/const hemomancyWeapons=/);
 assert.doesNotMatch(source,/className="workspace-weapon-blood-boost"/);
});

test('weapon picker has one basic command; skill and passive cards belong to their own sections',()=>{
 const controls=source.slice(source.indexOf('const hemomancyCard='),source.indexOf('const timeline ='));
 assert.doesNotMatch(controls,/Ação da arma de sangue|HemomancyWeaponDetails/);
 assert.match(source,/hemomancySelection\(definition\?\.hemomancy,hemomancyChoice,false\)/);
 assert.equal((controls.match(/data-card-command/g)||[]).length,1);
});
