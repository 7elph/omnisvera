const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function harness(status = 'ready', overrides = {}, props = {}, planOverrides = {}) {
  const slots = [], calls = [];
  let cursor = 0, tree;
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
  };
  const plan = { status, fingerprint: 'a'.repeat(64), source: 'Reviewed source', changes: [], warnings: [], blockers: status === 'blocked' ? ['Needs approval'] : [], ...planOverrides };
  const api = {
    previewLevel: async (...args) => { calls.push(['preview', ...args]); return plan; },
    confirmLevel: async (...args) => { calls.push(['confirm', ...args]); return { applied: true, character: {} }; }, ...overrides,
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync('src/components/LevelAdvancement.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  const render = () => { cursor = 0; tree = module.exports.default({ id: 'vezemir', level: 2, onApplied: async () => {}, ...props }); };
  const button = label => walk(tree).find(n => n.type === 'button' && n.props.children === label);
  const flush = async () => { await new Promise(setImmediate); render(); };
  render(); return { calls, button, flush, input: () => walk(tree).find(n => n.type === 'input') };
}

test('preview never commits and blocked rules have no confirmation', async () => {
  const h = harness('blocked');
  h.button('Conferir nível 2').props.onClick(); await h.flush();
  assert.equal(h.calls.length, 1);
  assert.equal(h.calls[0][0], 'preview');
  assert.equal(h.button('Confirmar avanço preservando ferimentos'), undefined);
});

test('double confirmation uses one fingerprint and applied state removes action', async () => {
  const h = harness();
  h.button('Conferir nível 2').props.onClick(); await h.flush();
  const click = h.button('Confirmar avanço preservando ferimentos').props.onClick;
  click(); click(); await h.flush();
  const commits = h.calls.filter(c => c[0] === 'confirm');
  assert.equal(commits.length, 1);
  assert.equal(commits[0][2], 'a'.repeat(64));
  assert.equal(commits[0][3], undefined); // Existing level 2 never gets another HP roll.
  assert.equal(h.button('Confirmar avanço preservando ferimentos'), undefined);
});

test('lost response retains the same confirmation fingerprint for safe retry', async () => {
  const fingerprints = [];
  const h = harness('ready', { confirmLevel: async (id, fingerprint) => {
    fingerprints.push(fingerprint); if (fingerprints.length === 1) throw Error('offline');
    return { applied: false, character: {} };
  } });
  h.button('Conferir nível 2').props.onClick(); await h.flush();
  h.button('Confirmar avanço preservando ferimentos').props.onClick(); await h.flush();
  h.button('Confirmar avanço preservando ferimentos').props.onClick(); await h.flush();
  assert.deepEqual(fingerprints, ['a'.repeat(64), 'a'.repeat(64)]);
});

test('advancement is exposed only behind the Master guard', () => {
  const source = fs.readFileSync('src/components/CharacterLevel.tsx', 'utf8');
  assert.match(source, /canEdit && characterId && onApplied && typeof level === "number" && <LevelAdvancement/);
});

test('confirmed level offers next level with explicit target instead of editing the label', async () => {
  const h = harness('blocked', {}, { confirmedLevel: 2 });
  h.button('Subir para nível 3').props.onClick(); await h.flush();
  assert.equal(h.calls[0][3], 3);
});

test('Morthak already showing level 2 can supply the missing HP roll without stale confirmation', async () => {
  const h = harness('ready', {}, { id: 'morthak' }, { requires_hp_roll: true, hit_die: 4 });
  h.button('Conferir nível 2').props.onClick(); await h.flush();
  assert.equal(h.input().props.max, 4);
  h.input().props.onChange({ target: { value: '3' } }); await h.flush();
  assert.equal(h.button('Confirmar avanço preservando ferimentos'), undefined);
  h.button('Atualizar prévia').props.onClick(); await h.flush();
  assert.deepEqual(h.calls.at(-1), ['preview', 'morthak', 3, 2, 'preserve_wounds']);
});
