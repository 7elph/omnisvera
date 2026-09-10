const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const ts = require('typescript');

function harness(overrides = {}) {
  const slots = [], effects = [], listeners = new Map();
  let cursor = 0, tree;
  const saved = { character_id: 'varkh', content: 'Nota salva', version: 2, updated_at: '2026-08-28T00:00:00Z' };
  const calls = [];
  const api = {
    getCharacterNotes: async () => saved,
    saveCharacterNotes: async (id, content, version) => { calls.push({ id, content, version }); return { ...saved, content, version: version + 1 }; },
    ...overrides,
  };
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], value => { slots[i] = typeof value === 'function' ? value(slots[i]) : value; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useEffect(fn, deps) {
      const i = cursor++;
      if (!slots[i] || deps.some((d, n) => d !== slots[i].deps[n])) effects.push(() => { slots[i]?.cleanup?.(); slots[i] = { deps, cleanup: fn() }; });
    },
  };
  const window = { confirm: () => true, addEventListener: (name, fn) => listeners.set(name, fn), removeEventListener: name => listeners.delete(name) };
  const jsx = (type, props) => ({ type, props: props || {} });
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src/components/CharacterNotes.tsx'), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, window, console,
    require: name => name === 'react' ? react : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : name.endsWith('.css') ? {} : api });
  const walk = node => !node || typeof node !== 'object' ? [] : Array.isArray(node) ? node.flatMap(walk) : [node, ...walk(node.props.children)];
  const text = node => Array.isArray(node) ? node.map(text).join('') : node && typeof node === 'object' ? text(node.props.children) : String(node ?? '');
  function render() { cursor = 0; tree = module.exports.default({ characterId: 'varkh' }); while (effects.length) effects.shift()(); }
  async function flush() { await new Promise(setImmediate); render(); await new Promise(setImmediate); render(); }
  const nodes = () => walk(tree);
  const textarea = () => nodes().find(n => n.type === 'textarea');
  const button = label => nodes().find(n => n.type === 'button' && text(n) === label);
  const edit = value => { textarea().props.onChange({ target: { value } }); render(); };
  render();
  return { api, calls, flush, edit, textarea, button, nodes, listeners, render };
}

test('loads persisted notes into a collapsed section', async () => {
  const h = harness(); await h.flush();
  assert.equal(h.textarea().props.value, 'Nota salva');
  assert.equal(h.button('Salvar alterações').props.disabled, true);
  assert.equal(h.nodes()[0].type, 'details');
  assert.equal(h.nodes()[0].props.open, undefined);
  assert.equal(h.nodes().filter(n => n.type === 'button').length, 1);
  assert.equal(h.nodes().some(n => n.type === 'summary'), true);
});

test('save uses server version and double click is locked', async () => {
  const h = harness(); await h.flush(); h.edit('Nova pista');
  const click = h.button('Salvar alterações').props.onClick; click(); click(); await h.flush();
  assert.equal(h.calls.length, 1);
  assert.deepEqual(h.calls[0], { id: 'varkh', content: 'Nova pista', version: 2 });
  assert.equal(h.button('Salvar alterações').props.disabled, true);
});

test('offline or conflict preserves the draft and retry version', async () => {
  const h = harness({ saveCharacterNotes: async () => { throw Error('Conflito de versão'); } });
  await h.flush(); h.edit('Não perder'); h.button('Salvar alterações').props.onClick(); await h.flush();
  assert.equal(h.textarea().props.value, 'Não perder');
  assert.ok(h.nodes().some(n => n.props.role === 'alert'));
  assert.ok(h.listeners.has('beforeunload'));
});

test('failed initial read cannot overwrite stored content', async () => {
  const h = harness({ getCharacterNotes: async () => { throw Error('offline'); } }); await h.flush();
  assert.equal(h.textarea().props.disabled, true);
  assert.equal(h.button('Salvar alterações').props.disabled, true);
  assert.equal(h.button('Recarregar notas salvas').props.disabled, false);
});

test('typing during save is retained as an unsaved newer draft', async () => {
  let finish;
  const h = harness({ saveCharacterNotes: () => new Promise(resolve => { finish = resolve; }) });
  await h.flush(); h.edit('Primeira'); h.button('Salvar alterações').props.onClick();
  h.edit('Segunda'); finish({ character_id: 'varkh', content: 'Primeira', version: 3 }); await h.flush();
  assert.equal(h.textarea().props.value, 'Segunda');
  assert.equal(h.button('Salvar alterações').props.disabled, false);
});
