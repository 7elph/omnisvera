const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const walk = v => Array.isArray(v) ? v.flatMap(walk) : v && typeof v === 'object' ? [v, ...walk(v.props?.children)] : [];
const text = v => Array.isArray(v) ? v.map(text).join('') : v && typeof v === 'object' ? text(v.props?.children) : String(v ?? '');
function render(combat, gridded = false) {
  const calls = [],events=[],listeners={};
  let index = 0;
  const mod = { exports: {} };
  const jsx = (type,props) => ({type,props:props||{}});
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/DornProtocolControls.tsx','utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText, {module:mod,exports:mod.exports,crypto:{randomUUID:()=> 'arm-fixture'},CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},window:{addEventListener:(name,fn)=>listeners[name]=fn,removeEventListener:()=>{},dispatchEvent:event=>events.push(event)},require: id => id==='react' ? {useState: initial => [initial,()=>{}],useEffect:fn=>fn(),useRef:initial=>({current:initial})} : id.includes('api') ? {mediaUrlFromVaultPath:path=>path,newDiceRequestId:()=> 'fixture-id',sendCombatEffectCommand:async payload=>{calls.push(payload);return { ...combat, protocol_result: {total:14,difficulty:12,outcome:'success'} };}} : {jsx,jsxs:jsx}});
  return {tree:mod.exports.default({combat,gridded,tokens:[{id:'pin-ally',character_id:'ally'}],onChange:async state=>calls.push(state)}),calls,events,listeners};
}
const state = (extra={}) => ({version:3,effects:[],encounter:{active:true,participants:[{target_type:'character',target_id:'dorn7',name:'Dorn'},{target_type:'character',target_id:'ally',name:'Aliado'}],turn_index:0},...extra});
test('guard requires ally; vanguard is disabled in combat', () => {
  const buttons=walk(render(state()).tree).filter(n=>n.type==='button');
  assert.equal(buttons.length,2); assert.ok(buttons[0].props.disabled); assert.ok(buttons[1].props.disabled);
});
test('party guard activates once directly, without an ally selector or aiming step', async () => {
  const {tree,calls,events,listeners}=render(state(),true);
  const button=walk(tree).find(n=>n.type==='button' && text(n)==='Usar');
  assert.equal(button.props.disabled,false);
  button.props.onClick();button.props.onClick();await new Promise(setImmediate);
  assert.equal(events.length,0);
  assert.equal(calls[0].action,'dorn_guard'); assert.equal(calls[0].expected_version,3);
  assert.equal(JSON.stringify(calls[0].payload),'{}');assert.equal(calls.filter(c=>c.action==='dorn_guard').length,1);
});

test('guard counter is not offered as a second raw consume-resource card', () => {
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const filter=source.match(/const standaloneResources = ([^\n]+);/)[1];
  const evaluate=new Function('state','definition','catalogResourceKeys','return '+filter);
  const resources=[{key:'dorn_guard',label:'Protocolo de Guarda',current:1,maximum:1},
    {key:'other',label:'Outro recurso',current:2,maximum:2}];
  assert.deepEqual(evaluate({resources},{id:'dorn7'},new Set()).map(r=>r.key),['other']);
  assert.equal(evaluate({resources},{id:'other'},new Set()).length,2);
});
test('used action and other actor disable guard', () => {
  for (const encounter of [{...state().encounter,action_committed:true},{...state().encounter,turn_index:1},{...state().encounter,attacks_used:1}]) {
    const buttons=walk(render(state({encounter}),true).tree).filter(n=>n.type==='button');
    assert.ok(buttons[0].props.disabled);
  }
});
test('active flags show actual protocol state and vanguard can turn off', () => {
  const {tree}=render(state({encounter:{active:false},effects:[{protocol:'guard',target_id:'dorn7',ally_id:'ally'},{protocol:'vanguard',target_id:'dorn7'}]}));
  assert.ok(walk(tree).some(node => text(node.props?.heading).includes('Protocolo de Guarda · ATIVO')));
  assert.ok(text(tree).includes('Desativar Vanguarda'));
});
test('Dorn only exposes two inventory-style protocols without diagnostic or removed text', () => {
  const source=fs.readFileSync('src/components/DornProtocolControls.tsx','utf8');
  assert.equal((source.match(/<SpellCard /g)||[]).length,2);
  for(const removed of ['Diagnóstico da Unidade','dorn_diagnose','Protocolo atualizado','Uma interposição, antes da rolagem. Dorn recebe o ataque sem bônus.','Dorn assume a frente; exposição ao perigo decidida pelo Mestre. Sem detecção ou proteção automática.','<label>Aliado'])assert.ok(!source.includes(removed),removed);
  assert.ok(!fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8').includes('Base 10 · DES -1 · Escritas Rúnicas +2'));
});
test('monster UI does not offer an interposition opt-out and identifies actual resolved target', () => {
  const source=fs.readFileSync('src/components/MonsterAttackPanel.tsx','utf8');
  assert.ok(!source.includes('Interpor Dorn'));assert.ok(!source.includes('setInterpose'));
  assert.ok(source.includes('Alvo resolvido: {result.target_name}'));
});
test('Dorn approved art is present and requested protocol labels are removed', () => {
 const protocols=fs.readFileSync('src/components/DornProtocolControls.tsx','utf8');
 const traits=fs.readFileSync('src/components/DornConstructDetails.tsx','utf8');
 for(const path of ['protocolo_guarda_e51a549b42.jpg','protocolo_vanguarda_2c8a61c1c8.jpg'])assert.ok(protocols.includes(path));
 for(const path of ['forma_imutavel_8ca8772cb2.jpg','corpo_artificial_a3e38666fb.jpg'])assert.ok(traits.includes(path));
 for(const label of ['Posição permite interposição','Ativar Guarda · gastar ação','Exploração · até desativar ou encerrar cena'])assert.ok(!protocols.includes(label));
 assert.ok(!protocols.includes('type="checkbox"'));
 assert.ok(protocols.includes("use('dorn_guard',{})"));
});
