const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
function controller(api,overrides={}){
 const start=source.indexOf('  async function useAbility('),end=source.indexOf('  async function submitMessage(',start);
 const ctx={combatActionBlock:()=>'',consumableActionBlock:()=>'',battleState:{},selectedId:'raziel',character:{definition:{id:'raziel'},state:{current_hp:10,resources:[]}},busy:'',mode:'gm',
  abilityLock:{current:false},mutationLock:{current:false},vampireLock:{current:false},techniqueRequestRef:{current:null},
  abilityResource:()=>({key:'reserva_de_sangue',current:10,maximum:10}),requiredItemForAbility:()=>null,
  defaultAttackRollMode:'physical',attackPhysicalD20ById:{'lamina-de-sangue':'15'},techniqueModeById:{'lamina-de-sangue':'3:ranged'},
  newDiceRequestId:()=> 'blood-stable-fixture-id',setError(){},setBusy(){},setVampireOutcome(){},setAttackResolution(){},setTargetPickerAbilityId(){},refresh:async()=>{},useCharacterTechnique:api,...overrides};
 return {ctx,run:vm.runInNewContext(ts.transpileModule(source.slice(start,end)+'\nuseAbility',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,ctx)};
}

test('Dorn dispels the single eligible magic on the grid target through the existing command once',async()=>{
 const calls=[];let finish;
 const c=controller(async()=>{}, {selectedId:'dorn7',character:{definition:{id:'dorn7'},state:{current_hp:24}},
  battleState:{version:7,effects:[{id:'magic-one',magic_type:'arcane',spell_circle:2,caster_level:5,target_type:'token',target_id:'enemy'}]},
  sendCombatEffectCommand:body=>{calls.push(body);return new Promise(resolve=>finish=resolve);},setDornSpell(){}});
 const action={id:'dissipar-magia',active:true};const pending=c.run(action,{id:'enemy'},true);
 await c.run(action,{id:'enemy'},true);assert.equal(calls.length,1);
 assert.equal(calls[0].action,'dorn_spell_cast');assert.equal(calls[0].payload.effect_id,'magic-one');
 assert.equal(calls[0].expected_version,7);finish({});await pending;
});
test('blood blades respect Physical mode, send declared d20, and lock double clicks',async()=>{
 let done;const calls=[];const c=controller((...args)=>{calls.push(args);return new Promise(resolve=>done=resolve);});
 const running=c.run({id:'lamina-de-sangue',active:true},{id:'foe'});await c.run({id:'lamina-de-sangue',active:true},{id:'foe'});
 assert.equal(calls.length,1);assert.equal(calls[0][2].roll_mode,'physical');assert.equal(calls[0][2].d20,15);assert.equal(calls[0][2].charges,3);
 done({resolution_id:'blood-preview'});await running;
});
test('failed blood mark retries the same request id, not an unkeyed mutation',async()=>{
 const calls=[];let fail=true;const c=controller(async(...args)=>{calls.push(args);if(fail)throw new Error('lost response');return {};});
 await c.run({id:'marca-rubra',active:true},{id:'foe'});fail=false;await c.run({id:'marca-rubra',active:true},{id:'foe'});
 assert.ok(calls[0][2].request_id);assert.equal(calls[0][2].request_id,calls[1][2].request_id);
});
test('blood blades expose the same physical d20 input as other targeted attacks',()=>{
 assert.match(source,/\['adaga-de-osso', 'mordida', 'lamina-de-sangue'\]\.includes\(ability.id\)/);
});

test('invalid Physical d20 never sends a blood blade command',async()=>{
 for(const value of ['', '0', '21', '1.5']){
  const calls=[];const c=controller(async(...args)=>calls.push(args),{attackPhysicalD20ById:{'lamina-de-sangue':value}});
  await c.run({id:'lamina-de-sangue',active:true},{id:'foe'});assert.equal(calls.length,0,value);
 }
});

test('accepted blood mark with failed refresh preserves receipt for recovery',async()=>{
 const calls=[];let fail=true;const c=controller(async(...args)=>{calls.push(args);return {};},{refresh:async()=>{if(fail)throw new Error('read interrupted');}});
 await c.run({id:'marca-rubra',active:true},{id:'foe'});fail=false;await c.run({id:'marca-rubra',active:true},{id:'foe'});
 assert.equal(calls[0][2].request_id,calls[1][2].request_id);
});

test('approved blood weapons send native Physical commands instead of narrative messages',async()=>{
 for(const id of ['arma-de-sangue','garras-predatorias','investida-predatoria']){
  const calls=[];const c=controller(async(...args)=>{calls.push(args);return {resolution_id:id};},{attackPhysicalD20ById:{[id]:'15'}});
  await c.run({id,active:true,uses:{cost:2}},{id:'foe'});
  assert.equal(calls.length,1,id);assert.equal(calls[0][1],id);assert.equal(calls[0][2].target_id,'foe');assert.equal(calls[0][2].roll_mode,'physical');assert.equal(calls[0][2].d20,15);
 }
});
test('approved defensive blood uses the effect endpoint once and keeps receipt through read failure',async()=>{
 const calls=[];let fail=true;const c=controller(async(...args)=>{calls.push(args);return {};},{refresh:async()=>{if(fail)throw new Error('read interrupted');}});
 await c.run({id:'sangue-defensivo',active:true,uses:{cost:2}});fail=false;await c.run({id:'sangue-defensivo',active:true,uses:{cost:2}});
 assert.equal(calls.length,2);assert.equal(calls[0][2].request_id,calls[1][2].request_id);assert.equal(calls[0][1],'sangue-defensivo');assert.equal(calls[0][2].target_id,undefined);
});
test('coffin uses one atomic personal rest, never rest_at_inn plus separate consumption',async()=>{
 const calls=[];const c=controller(async()=>{}, {stateAction:async(...args)=>calls.push(args)});
 await c.run({id:'caixao',active:true});assert.equal(calls.length,1);assert.equal(calls[0][0],'rest_in_coffin');
});
