const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const labels = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/specializationLabel.ts','utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText, {module:labels,exports:labels.exports});

function harness(options, { failFirst = false } = {}) {
  const slots = [], calls = [];
  let cursor = 0, tree;
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useEffect(fn, deps) { const i = cursor++; if (!slots[i] || deps.some((d,j)=>d!==slots[i].deps[j])) { slots[i]?.cleanup?.(); slots[i]={deps,cleanup:fn()}; } },
  };
  const api = {
    listSpecializations: async () => { calls.push(['list']); if(failFirst&&calls.filter(c=>c[0]==='list').length===1)throw new Error('Falha transitória'); return { current: null, options }; },
    chooseSpecialization: async (...args) => { calls.push(['choose', ...args]); return { applied: true, specialization: args[1] }; },
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync('src/components/SpecializationSection.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, Error, exports: module.exports, require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : n.includes('specializationLabel') ? labels.exports : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children), ...walk(n.props.description)];
  const character = { definition: { id: 'vezemir', specialization: null }, inventory: [{ item_path: 'w1', item_title: 'Espada', quantity: 1, equipped: true }] };
  const render = () => { cursor = 0; tree = module.exports.default({ character, canOperate: true, onApplied: async () => {} }); };
  const flush = async () => { await new Promise(setImmediate); render(); };
  render(); return { calls, flush, render, find: pred => walk(tree).find(pred), all: pred => walk(tree).filter(pred) };
}

const OPTIONS = [
  { id: 'guerreiro-arma', name: 'Guerreiro de Arma', eligible: true, reasons: [], benefits: ['+1'], restrictions: [], requires: { weapon_choice: true }, upcoming: [], current: false },
  { id: 'paladino', name: 'Paladino', eligible: false, reasons: ['exige alinhamento ordeiro'], benefits: [], restrictions: [], requires: {}, upcoming: [], current: false },
];

test('lista elegíveis e bloqueia inelegível sem arma', async () => {
  const h = harness(OPTIONS);
  await h.flush();
  const buttons = [];
  const walk2 = n => { if (!n || typeof n !== 'object') return; if (Array.isArray(n)) return n.forEach(walk2); if (n.type === 'button' && n.props.children === 'Escolher') buttons.push(n); walk2(n.props.children); };
  walk2(h.find(n=>n.props?.className==='workspace-specialization-options'));
  assert.equal(buttons.length, 2);
  assert.equal(buttons[0].props.disabled, true);
  assert.equal(buttons[1].props.disabled, true);
});

test('escolha exige arma e chama a API', async () => {
  const h = harness(OPTIONS);
  await h.flush();
  assert.deepEqual(h.calls[0], ['list']);
  h.find(n=>n.type==='select').props.onChange({target:{value:'w1'}});h.render();
  const choose=h.all(n=>n.type==='button'&&n.props.children==='Escolher')[0];
  assert.equal(choose.props.disabled,false);await choose.props.onClick();await h.flush();
  assert.deepEqual(h.calls.find(c=>c[0]==='choose').slice(1,4),['vezemir','guerreiro-arma','w1']);
});

test('GM specialization management shows benefits directly, without nested floating menus',async()=>{
 const h=harness(OPTIONS);await h.flush();
 assert.ok(h.find(n=>n.props?.className==='workspace-specialization-options'));
 assert.ok(h.find(n=>n.props.className==='workspace-specialization-benefits'));
 assert.ok(h.find(n=>n.type==='li'&&n.props.children==='+1'));
});

test('a failed catalogue remains visible and can retry without changing specialization',async()=>{
 const h=harness(OPTIONS,{failFirst:true});await h.flush();
 assert.equal(h.find(n=>n.props.role==='alert').props.children,'Falha transitória');
 h.find(n=>n.type==='button'&&n.props.children==='Tentar novamente').props.onClick();h.render();await h.flush();
 assert.ok(h.find(n=>n.props.className==='workspace-specialization-benefits'));
 assert.equal(h.calls.filter(c=>c[0]==='choose').length,0);
});
