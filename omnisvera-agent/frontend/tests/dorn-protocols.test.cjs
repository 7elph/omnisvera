const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const walk = v => Array.isArray(v) ? v.flatMap(walk) : v && typeof v === 'object' ? [v, ...walk(v.props?.children)] : [];
const text = v => Array.isArray(v) ? v.map(text).join('') : v && typeof v === 'object' ? text(v.props?.children) : String(v ?? '');
function render(combat, values = []) {
  const calls = [];
  let index = 0;
  const mod = { exports: {} };
  const jsx = (type,props) => ({type,props:props||{}});
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/DornProtocolControls.tsx','utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText, {module:mod,exports:mod.exports,require: id => id==='react' ? {useState: initial => [values[index++] ?? initial,()=>{}],useRef:initial=>({current:initial})} : id.includes('api') ? {newDiceRequestId:()=> 'fixture-id',sendCombatEffectCommand:async payload=>{calls.push(payload);return { ...combat, protocol_result: {total:14,difficulty:12,outcome:'success'} };}} : {jsx,jsxs:jsx}});
  return {tree:mod.exports.default({combat,onChange:async state=>calls.push(state)}),calls};
}
const state = (extra={}) => ({version:3,effects:[],encounter:{active:true,participants:[{target_type:'character',target_id:'dorn7',name:'Dorn'},{target_type:'character',target_id:'ally',name:'Aliado'}],turn_index:0},...extra});
test('guard requires ally and position; vanguard is disabled in combat', () => {
  const buttons=walk(render(state()).tree).filter(n=>n.type==='button');
  assert.ok(buttons[0].props.disabled); assert.ok(buttons[1].props.disabled); assert.ok(buttons[2].props.disabled);
});
test('approved action sends guard to existing effect command with explicit position', async () => {
  const {tree,calls}=render(state(),['ally','', '12',true]);
  const button=walk(tree).find(n=>n.type==='button' && text(n).includes('Ativar Guarda'));
  assert.equal(button.props.disabled,false);
  await button.props.onClick(); await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls[0].action,'dorn_guard'); assert.equal(calls[0].expected_version,3);
  assert.equal(calls[0].payload.ally_id,'ally'); assert.equal(calls[0].payload.position_confirmed,true);
});
test('used action and other actor disable guard and diagnostic', () => {
  for (const encounter of [{...state().encounter,action_committed:true},{...state().encounter,turn_index:1},{...state().encounter,attacks_used:1}]) {
    const buttons=walk(render(state({encounter}),['ally','Máquina','12',true]).tree).filter(n=>n.type==='button');
    assert.ok(buttons[0].props.disabled); assert.ok(buttons[2].props.disabled);
  }
});
test('active flags show actual protocol state and vanguard can turn off', () => {
  const {tree}=render(state({encounter:{active:false},effects:[{protocol:'guard',target_id:'dorn7',ally_id:'ally'},{protocol:'vanguard',target_id:'dorn7'}]}));
  assert.ok(text(tree).includes('Protocolo de Guarda · ATIVO'));
  assert.ok(text(tree).includes('Desativar Vanguarda'));
});
test('diagnostic sends subject and GM difficulty, no lore field', async () => {
  const {tree,calls}=render(state({encounter:{active:false}}),['','Núcleo','15',false]);
  const button=walk(tree).find(n=>n.type==='button' && text(n).includes('Diagnosticar'));
  assert.equal(button.props.disabled,false); await button.props.onClick(); await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls[0].action,'dorn_diagnose'); assert.equal(calls[0].payload.difficulty,15);
  assert.deepEqual(Object.keys(calls[0].payload).sort(),['difficulty','subject']);
});
test('monster UI confirms interposition before resolving and identifies actual target', () => {
  const source=fs.readFileSync('src/components/MonsterAttackPanel.tsx','utf8');
  assert.ok(source.includes('guard_effect_id: guard.id')); assert.ok(source.includes('confirmar antes de rolar'));
  assert.ok(source.includes('Alvo resolvido: {result.target_name}'));
});
