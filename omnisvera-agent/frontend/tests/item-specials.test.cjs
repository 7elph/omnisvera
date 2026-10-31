const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const moduleUnderTest={exports:{}};
const jsx=(type,props)=>({type,props});
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/components/WeaponDamageChoice.tsx'),'utf8'),
 {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
 {module:moduleUnderTest,exports:moduleUnderTest.exports,require:name=>name==='react/jsx-runtime'?{jsx,jsxs:jsx}:{}});
const {weaponDamageChoices,default:Choice}=moduleUnderTest.exports;
test('only types actually offered by the weapon are selectable, without a silent default',()=>{
 const choices=weaponDamageChoices({mechanics:{damage_types:['slashing','fire','bludgeoning']}});
 assert.deepEqual(Array.from(choices),['slashing','bludgeoning']);
 let chosen='unexpected';const tree=Choice({choices,onChange:value=>chosen=value});
 const select=tree.props.children[1];assert.equal(select.props.value,'');
 select.props.onChange({target:{value:'bludgeoning'}});assert.equal(chosen,'bludgeoning');
 select.props.onChange({target:{value:'fire'}});assert.equal(chosen,undefined);
});
test('ordinary weapons and absent inventory do not add controls',()=>{
 assert.equal(Choice({choices:weaponDamageChoices(),onChange:()=>assert.fail()}),null);
 assert.equal(Choice({choices:weaponDamageChoices({mechanics:{}}),onChange:()=>assert.fail()}),null);
});

function load(relative){
 const output={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,relative),'utf8'),
  {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
  {module:output,exports:output.exports,require:name=>name==='react/jsx-runtime'?{jsx,jsxs:jsx}:{}});
 return output.exports;
}
test('tower direction has no silent default and preserves explicit false',()=>{
 const Choice=load('../src/components/AttackDirectionChoice.tsx').default;
 assert.equal(Choice({required:false,onChange:()=>assert.fail()}),null);
 let value='unexpected';const select=Choice({required:true,onChange:v=>value=v}).props.children[1];
 assert.equal(select.props.value,'');
 select.props.onChange({target:{value:'open'}});assert.equal(value,false);
 select.props.onChange({target:{value:'protected'}});assert.equal(value,true);
 select.props.onChange({target:{value:''}});assert.equal(value,undefined);
});
test('shield followup cannot enable other weapons, turns, conditions or pending previews',()=>{
 const {combatActionBlock}=load('../src/components/combatActionAvailability.ts');
 const state={effects:[],encounter:{active:true,battle_mode:true,started_at:'fixture',turn_sequence:2,turn_index:0,
  participants:[{target_type:'character',target_id:'vezemir'}],action_committed:true,attacks_used:1,attack_limit:1,
  item_followups:{vezemir:{turn:['fixture',2,'character','vezemir'],item_path:'shield'}}}};
 assert.equal(combatActionBlock(state,'vezemir',20,'shield'),'');
 assert.ok(combatActionBlock(state,'vezemir',20,'sword'));
 assert.ok(combatActionBlock(state,'vezemir',20));
 assert.ok(combatActionBlock(state,'vezemir',0,'shield'));
 state.encounter.turn_sequence=3;assert.ok(combatActionBlock(state,'vezemir',20,'shield'));
 state.encounter.turn_sequence=2;state.encounter.pending_attack='pending';assert.ok(combatActionBlock(state,'vezemir',20,'shield'));
});
