const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function harness(targets, rangeResult) {
  const slots = [];
  let cursor = 0, tree;
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useEffect(fn) { fn(); },
  };
  const api = {
    attackTargets: async () => rangeResult,
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync('src/components/TargetSelect.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  const render = () => { cursor = 0; tree = module.exports.default({ targets, value: '', onChange: () => {}, label: 'Alvo', rangeQuery: { profileId: 'vezemir', attackId: 'melee', slot: 'melee' } }); };
  const flush = async () => { await new Promise(setImmediate); render(); };
  render(); return { flush, options: () => walk(tree).filter(n => n.type === 'option' && n.props.value) };
}

const TARGETS = [{ id: 'a', name: 'Perto' }, { id: 'b', name: 'Longe' }];

test('sem grid mantém todas as opções', async () => {
  const h = harness(TARGETS, { gridded: false, targets: [] });
  await h.flush();
  assert.deepEqual(h.options().map(o => o.props.disabled || false), [false, false]);
});

test('fora de alcance desabilita com motivo', async () => {
  const h = harness(TARGETS, { gridded: true, targets: [
    { id: 'a', valid: true, reason: '' },
    { id: 'b', valid: false, reason: '4 células (adjacência exigida)' },
  ] });
  await h.flush();
  const opts = h.options();
  assert.equal(opts[0].props.disabled, undefined);
  assert.equal(opts[1].props.disabled, true);
  assert.ok(opts[1].props.children.includes('adjacência'));
});

test('falha de rede mantém comportamento atual', async () => {
  const slots = [];
  let cursor = 0;
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useEffect(fn) { fn(); },
  };
  const api = { attackTargets: async () => { throw new Error('offline'); } };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync('src/components/TargetSelect.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  cursor = 0;
  const tree = module.exports.default({ targets: TARGETS, value: '', onChange: () => {}, label: 'Alvo', rangeQuery: { profileId: 'v', attackId: 'melee' } });
  await new Promise(setImmediate);
  cursor = 0;
  const tree2 = module.exports.default({ targets: TARGETS, value: '', onChange: () => {}, label: 'Alvo', rangeQuery: { profileId: 'v', attackId: 'melee' } });
  const opts = walk(tree2).filter(n => n.type === 'option' && n.props.value);
  assert.deepEqual(opts.map(o => o.props.disabled || false), [false, false]);
});
