const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

test('reconnect recovers the same pending result without resolving or confirming an attack', async () => {
  const slots = [], effects = [], listeners = new Map();
  let cursor = 0, tree, reads = 0, opened, cleanup, interval;
  const record = { resolution_id: 'unchanged-preview', actor_name: 'Morthak', target_name: 'Aranha', attack_name: 'Mísseis Mágicos' };
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], value => { slots[i] = value; }]; },
    useEffect(fn) { const i = cursor++; if (!slots[i]) { slots[i] = true; effects.push(fn); } },
  };
  const window = {
    setInterval: fn => { interval = fn; return 1; }, clearInterval: () => { interval = null; },
    addEventListener: (name, fn) => listeners.set(name, fn), removeEventListener: name => listeners.delete(name),
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync('src/components/PendingAttacks.tsx', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, window, require: name => name === 'react' ? react : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : { listPendingAttacks: async () => { reads++; return [record]; } } });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  const render = () => { cursor = 0; tree = module.exports.default({ onOpen: item => { opened = item; } }); while (effects.length) cleanup = effects.shift()(); };
  render(); await new Promise(setImmediate); render();
  assert.equal(tree.type, 'details');
  assert.equal(tree.props.open, undefined, 'technical recovery is collapsed');
  assert.equal(reads, 1);
  walk(tree).find(n => n.type === 'button').props.onClick();
  assert.equal(opened.resolution_id, 'unchanged-preview');
  await listeners.get('online')(); render();
  assert.equal(reads, 2);
  assert.equal(walk(tree).filter(n => n.type === 'button').length, 1);
  cleanup();
  assert.equal(listeners.size, 0);
  assert.equal(interval, null);
});
