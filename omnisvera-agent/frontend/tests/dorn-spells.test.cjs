const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const helper={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/nativeSpellRevision.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:helper,exports:helper.exports});
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props?.children)]:[];
const text=v=>Array.isArray(v)?v.map(text).join(''):v&&typeof v==='object'?text(v.props?.children):String(v??'');
function render(name,props,values=[]){
  let index=0;const calls=[];const mod={exports:{}};const jsx=(type,props)=>({type,props:props||{}});
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(`src/components/${name}.tsx`,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:id=>id==='react'?{useState:initial=>[values[index++]??initial,()=>{}],useRef:initial=>({current:initial})}:id==='./nativeSpellRevision'?helper.exports:id.includes('api')?{newDiceRequestId:()=> 'fixture-spell',sendCombatEffectCommand:async request=>{calls.push(request);return {protocol_result:{spell:'Relâmpago',results:[]}}}}:{jsx,jsxs:jsx}});
  return {tree:mod.exports.default(props),calls};
}
const props={spell:'relampago',tokens:[{id:'wolf',name:'Lobo',token_type:'monster',current_hp:10}],combat:{version:7,effects:[],encounter:{active:false}},onChange:async()=>{},onClose:()=>{}};
test('spell requires targets and explicit geometry confirmation',()=>{
  const {tree}=render('DornSpellControls',props);
  assert.ok(walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar')).props.disabled);
});
test('spell routes real command, contact count and prevents double submit',async()=>{
  const {tree,calls}=render('DornSpellControls',props,[['wolf'],'10','',false,'line',{wolf:2},true]);
  const button=walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar'));
  assert.equal(button.props.disabled,false);button.props.onClick();button.props.onClick();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls.length,1);assert.equal(calls[0].action,'dorn_spell_cast');assert.equal(calls[0].expected_version,7);
  assert.equal(calls[0].payload.targets[0].contacts,2);assert.equal(calls[0].payload.position_confirmed,true);
});
test('levitation requires exactly one recipient and weight',()=>{
  for(const values of [[['wolf'],'0','',false,'line',{},true],[['wolf','other'],'0','100',false,'line',{},true]]){
    const {tree}=render('DornSpellControls',{...props,spell:'levitacao'},values);
    assert.ok(walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar')).props.disabled);
  }
});
test('active effects stay compact and expose fictional time and vertical controls',()=>{
  const {tree}=render('DornSpellEffects',{combat:{...props.combat,effects:[{id:'lev',spell:'levitacao',label:'Levitação',target_id:'dorn7',remaining_seconds:1800,altitude_meters:2}]},onChange:async()=>{}});
  assert.equal(tree.type,'details');assert.ok(text(tree).includes('30 min restantes'));
  for(const label of ['Subir 2 m','Descer 2 m','Estabilizar','Encerrar efeito','Avançar uma rodada'])assert.ok(text(tree).includes(label));
});
test('Reflexos casts on self without a manual geometry checkbox or target',async()=>{
  const {tree,calls}=render('DornSpellControls',{...props,spell:'reflexos'});
  const button=walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar'));
  assert.equal(button.props.disabled,false);button.props.onClick();button.props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls.length,1);assert.equal(calls[0].payload.spell_id,'reflexos');assert.equal(calls[0].payload.position_confirmed,undefined);
});
test('new grid spells require one recipient and Dispel selects a persisted effect',async()=>{
  const {tree,calls}=render('DornSpellControls',{...props,spell:'dissipar-magia',combat:{...props.combat,effects:[{id:'magic-fixture',label:'Reflexos',target_id:'dorn7',magic_type:'arcane',spell_circle:2,caster_level:5}]}},[['magic-fixture']]);
  assert.ok(walk(tree).find(n=>n.props?.['aria-label']==='Efeito a dissipar'));
  walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar')).props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls[0].payload.effect_id,'magic-fixture');assert.equal(calls[0].payload.targets,undefined);
});

test('approved native spell sends its revision; invalid contract cannot submit',async()=>{
 const c={schema_version:1,ref:'technique:dorn7:reflexos',revision:'dorn-reflexos-campaign-v1',executor:{binding:'dorn_reflexos'}};
 for(const [contract,expected] of [[c,1],[{...c,executor:{binding:'arbitrary'}},0]]) {
  const {tree,calls}=render('DornSpellControls',{...props,spell:'reflexos',ability:{action_contract:contract}});
  walk(tree).find(n=>n.type==='button'&&text(n).includes('Conjurar')).props.onClick();
  await new Promise(r=>setImmediate(r));
  assert.equal(calls.length,expected);
  if(expected)assert.equal(calls[0].payload.definition_revision,c.revision);
 }
});
