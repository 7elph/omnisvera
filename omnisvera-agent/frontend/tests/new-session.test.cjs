const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const ts = require('typescript');

function harness(overrides = {}) {
  const slots = [], calls = [], selected = [];
  let cursor = 0, tree;
  const api = {
    newSceneRequestId: () => 'fixed-request',
    createGameSession: async payload => { calls.push(['create', payload]); return { id: 9 }; },
    updateGameSessionStatus: async (...args) => { calls.push(['activate', ...args]); },
    ...overrides,
  };
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = typeof v === 'function' ? v(slots[i]) : v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
  };
  const jsx = (type, props) => ({ type, props: props || {} });
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/components/NewSessionForm.tsx'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports,
    require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  const render = () => { cursor = 0; tree = module.exports.default({ onCreated: async id => selected.push(id) }); };
  const node = type => walk(tree).find(n => n.type === type);
  const flush = async () => { await new Promise(setImmediate); render(); };
  render();
  return { calls, selected, node, flush, render, edit(value) { node('input').props.onChange({ target: { value } }); render(); } };
}

test('new session requires only a title and locks double submission before render', async () => {
  const h = harness();
  assert.equal(h.node('button').props.disabled, true);
  h.edit('  Sessão de ensaio  ');
  const click = h.node('button').props.onClick;
  click(); click(); await h.flush();
  assert.equal(h.calls.filter(c => c[0] === 'create').length, 1);
  assert.equal(h.calls[0][1].title, 'Sessão de ensaio');
  assert.deepEqual(h.selected, [9]);
  assert.equal(h.node('input').props.value, '');
});

test('failed activation retries the saved session without creating another', async () => {
  let tries = 0;
  const h = harness({ updateGameSessionStatus: async id => { assert.equal(id, 9); if (++tries === 1) throw Error('offline'); } });
  h.edit('Sessão'); h.node('button').props.onClick(); await h.flush();
  assert.equal(h.node('input').props.disabled, true);
  h.node('button').props.onClick(); await h.flush();
  assert.equal(tries, 2);
  assert.equal(h.calls.filter(c => c[0] === 'create').length, 1);
  assert.deepEqual(h.selected, [9]);
});

test('lost creation response retries identical request ID and payload', async () => {
  const requests = [];
  const h = harness({ createGameSession: async payload => { requests.push(payload); if (requests.length === 1) throw Error('lost response'); return { id: 9 }; } });
  h.edit('Sessão'); h.node('button').props.onClick(); await h.flush();
  h.node('button').props.onClick(); await h.flush();
  assert.equal(requests.length, 2);
  assert.deepEqual(requests[0], requests[1]);
  assert.deepEqual(h.selected, [9]);
});

test('session creation is available without a scene and restricted to GM', () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/ScenePanel.tsx'), 'utf8');
  const empty = source.slice(source.indexOf('if (!scene) return <section'), source.indexOf('return <section className={`panel'));
  assert.match(empty, /mode === "gm" && <><NewSessionForm/);
  assert.match(empty, /renderSceneCreateForm\(true\)/);
  assert.match(source, /setCreateDraft\(\(current\) => \(\{ \.\.\.current, session_id: String\(id\) \}\)\)/);
});

test('new scene refresh explicitly uses its returned ID instead of stale React selection', async () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/ScenePanel.tsx'), 'utf8');
  const start = source.indexOf('  async function run(');
  const end = source.indexOf('  async function declare()', start);
  const refreshed = [];
  const context = {
    busy: false, createDraft: { title: 'Nova cena', session_id: '9', checklist: {} },
    newSceneRequestId: () => 'scene-request', createScene: async () => ({ id: 42 }),
    setBusy() {}, setError() {}, setNotice() {}, setCreateDraft() {}, setSelectedId() {},
    EMPTY_CHECKLIST: {}, refresh: async id => refreshed.push(id),
  };
  vm.createContext(context);
  vm.runInContext(ts.transpileModule(source.slice(start, end), {}).outputText, context);
  await context.submitScene();
  assert.deepEqual(refreshed, [42]);
});
