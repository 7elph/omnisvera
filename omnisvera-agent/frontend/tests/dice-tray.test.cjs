// Component-level regression tests, no network/DOM/dependencies beyond TypeScript.
// Run: node --test tests/dice-tray.test.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');

const request = { id: 7, request_id: 'gm-cf01-request', character_id: 'varkh', label: 'Carisma CF01', formula: '1d20+3' };
const roll = { id: 9, label: request.label, character_id: 'varkh', total: 18, dice: '1d20', individual_results: [15], modifier: 3 };
const tick = () => new Promise(resolve => setImmediate(resolve));

function harness(mode = 'player', overrides = {}) {
  const slots = [], effects = [], intervals = new Map(), listeners = new Map();
  let cursor = 0, tree, sequence = 0, historyCalls = 0;
  const api = {
    listRollHistory: async () => { historyCalls++; return []; },
    listPendingRollRequests: async () => [request],
    listPlayableCharacters: async () => [{ id: 'varkh', name: 'Varkh', access_level: 'owner' }],
    completeRollRequest: async () => roll,
    createRollRequest: async () => request,
    newDiceRequestId: prefix => `${prefix}-${++sequence}`,
    mediaUrlFromVaultPath: () => '', ...overrides,
  };
  const depsChanged = (a, b) => !a || !b || a.length !== b.length || a.some((v, i) => v !== b[i]);
  const react = {
    useState(initial) {
      const i = cursor++; if (!(i in slots)) slots[i] = typeof initial === 'function' ? initial() : initial;
      return [slots[i], value => { slots[i] = typeof value === 'function' ? value(slots[i]) : value; }];
    },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useMemo(fn) { cursor++; return fn(); },
    useEffect(fn, deps) {
      const i = cursor++;
      if (depsChanged(slots[i]?.deps, deps)) effects.push(() => { slots[i]?.cleanup?.(); slots[i] = { deps, cleanup: fn() }; });
    },
  };
  const window = {
    addEventListener(name, fn) { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name).add(fn); },
    removeEventListener(name, fn) { listeners.get(name)?.delete(fn); },
    dispatchEvent(event) { for (const fn of listeners.get(event.type) || []) fn(event); },
    setInterval(fn, ms) { intervals.set(fn, ms); return fn; }, clearInterval(fn) { intervals.delete(fn); },
    setTimeout: () => 0, clearTimeout: () => {},
  };
  const jsx = (type, props) => ({ type, props: props || {} });
  const document = { visibilityState: 'visible', addEventListener: window.addEventListener, removeEventListener: window.removeEventListener };
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src/components/DiceTray.tsx'), 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(compiled, {
    module, exports: module.exports, require: name => name === 'react' ? react : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api,
    window, document,
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options?.detail; } },
    console,
  });
  function render() { cursor = 0; tree = module.exports.default({ mode }); while (effects.length) effects.shift()(); }
  function walk(node) {
    if (!node || typeof node !== 'object') return [];
    if (Array.isArray(node)) return node.flatMap(walk);
    return [node, ...walk(node.props?.children)];
  }
  const nodes = () => walk(tree);
  const text = node => Array.isArray(node) ? node.map(text).join('') : typeof node === 'object' && node ? text(node.props?.children) : String(node ?? '');
  async function flush() { await tick(); render(); await tick(); render(); }
  function button(label) { const found = nodes().find(n => n.type === 'button' && (text(n) === label || n.props['aria-label'] === label)); assert.ok(found, `Button not found: ${label}`); return found.props.onClick; }
  async function open() { render(); await flush(); button('Abrir bandeja de dados')(); await flush(); }
  return { open, flush, button, nodes, api, window, document, intervals, get historyCalls() { return historyCalls; } };
}

test('GM shortcut opens the request form before free dice with selected character', async () => {
  const h = harness('gm');
  await h.flush();
  h.window.dispatchEvent({type:'omnisvera-open-dice-tray',detail:{panel:'request',characterId:'varkh'}});
  await h.flush();
  const nodes = h.nodes();
  const panel = nodes.find(n => n.props.className === 'roll-request-panel');
  assert.equal(panel.props.open, true);
  assert.ok(nodes.indexOf(panel) < nodes.findIndex(n => n.props.className === 'free-roll-panel'));
  assert.ok(nodes.some(n => n.type === 'select' && n.props.value === 'varkh'));
});

test('player cannot open the GM request form through the shortcut event', async () => {
  const h = harness('player'); await h.flush();
  h.window.dispatchEvent({type:'omnisvera-open-dice-tray',detail:{panel:'request',characterId:'raziel'}});
  await h.flush();
  assert.equal(h.nodes().some(n => n.props.className === 'roll-request-panel'), false);
});

test('polling refreshes completed history as well as pending requests, without a Mesa event', async () => {
  const h = harness('gm'); await h.open();
  const before = h.historyCalls;
  h.api.listRollHistory = async () => [roll];
  for (const fn of h.intervals.keys()) fn();
  await h.flush();
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
  assert.ok(before > 0);
});

test('retry after a lost completion response reuses the same key', async () => {
  const keys = [];
  const h = harness('player', { completeRollRequest: async (_, key) => { keys.push(key); if (keys.length === 1) throw Error('connection lost'); return roll; } });
  await h.open(); h.button('Confirmar e rolar')(); await h.flush();
  h.button('Confirmar e rolar')(); await h.flush();
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
});

test('completion key survives remount/reload of the same persisted request', async () => {
  const keys = [];
  for (let i = 0; i < 2; i++) {
    const h = harness('player', { newDiceRequestId: () => `random-${i}`, completeRollRequest: async (_, key) => { keys.push(key); throw Error('lost'); } });
    await h.open(); h.button('Confirmar e rolar')(); await h.flush();
  }
  assert.equal(keys[0], keys[1]);
});

test('two clicks in the same render send one completion', async () => {
  let calls = 0, finish;
  const h = harness('player', { completeRollRequest: () => { calls++; return new Promise(resolve => { finish = resolve; }); } });
  await h.open(); const click = h.button('Confirmar e rolar'); click(); click();
  assert.equal(calls, 1); finish(roll); await h.flush();
});

test('successful completion is announced even when the following refresh fails', async () => {
  const h = harness(); await h.open(); let announced = 0;
  h.window.addEventListener('omnisvera-roll-created', () => announced++);
  h.api.listRollHistory = async () => { throw Error('refresh offline'); };
  h.button('Confirmar e rolar')(); await h.flush();
  assert.equal(announced, 1);
});

test('GM retry after lost create response keeps the same request key', async () => {
  const keys = [];
  const h = harness('gm', { createRollRequest: async payload => { keys.push(payload.request_id); throw Error('lost response'); } });
  await h.open(); h.button('Enviar solicitação')(); await h.flush();
  h.button('Enviar solicitação')(); await h.flush();
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
});

test('GM pending card clearly distinguishes player response from an override', async () => {
  const h = harness('gm'); await h.open();
  assert.ok(h.button('Rolar pelo jogador'));
});

test('online event recovers pending requests and history after failed polling', async () => {
  const h = harness(); await h.open();
  h.api.listRollHistory = async () => { throw Error('offline'); };
  for (const fn of h.intervals.keys()) fn();
  await h.flush();
  assert.ok(h.nodes().some(n => n.props.role === 'status'));
  h.api.listRollHistory = async () => [roll];
  h.api.listPendingRollRequests = async () => [];
  h.window.dispatchEvent({ type: 'online' }); await h.flush();
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
  assert.ok(!h.nodes().some(n => n.props.role === 'status'));
});

test('an older in-flight snapshot cannot restore a completed request', async () => {
  const h = harness(); await h.open();
  let finishOld;
  h.api.listPendingRollRequests = () => new Promise(resolve => { finishOld = resolve; });
  for (const fn of h.intervals.keys()) fn();
  const old = () => finishOld([request]);
  h.api.listPendingRollRequests = async () => [];
  h.api.listRollHistory = async () => [roll];
  h.button('Confirmar e rolar')(); await h.flush();
  old(); await h.flush();
  assert.ok(!h.nodes().some(n => n.type === 'button' && n.props.children === 'Confirmar e rolar'));
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
});

test('slow polling does not supersede itself forever', async () => {
  const h = harness(); await h.open();
  let calls = 0, finish;
  h.api.listRollHistory = () => { calls++; return new Promise(resolve => { finish = resolve; }); };
  for (const fn of h.intervals.keys()) { fn(); fn(); fn(); }
  assert.equal(calls, 1);
  finish([roll]); await h.flush();
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
});

test('failed roster loading does not block pending/history and retries when opened', async () => {
  let attempts = 0;
  const h = harness('gm', { listPlayableCharacters: async () => {
    if (++attempts === 1) throw Error('temporary roster failure');
    return [{ id: 'varkh', name: 'Varkh', access_level: 'gm' }];
  } });
  await h.open();
  assert.ok(attempts >= 2);
  assert.ok(h.nodes().some(n => n.type === 'option' && n.props.value === 'varkh'));
});

test('return from background refreshes pending requests and completed history', async () => {
  const h = harness(); await h.open();
  const before = h.historyCalls;
  h.document.visibilityState = 'hidden';
  h.window.dispatchEvent({ type: 'visibilitychange' }); await h.flush();
  assert.equal(h.historyCalls, before);
  h.api.listRollHistory = async () => [roll];
  h.api.listPendingRollRequests = async () => [];
  h.document.visibilityState = 'visible';
  h.window.dispatchEvent({ type: 'visibilitychange' }); await h.flush();
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
  assert.ok(!h.nodes().some(n => n.type === 'button' && n.props.children === 'Confirmar e rolar'));
});

test('focus resumes a failed connection without a manual refresh', async () => {
  const h = harness('gm'); await h.open();
  h.api.listRollHistory = async () => { throw Error('offline'); };
  for (const fn of h.intervals.keys()) fn();
  await h.flush();
  h.api.listRollHistory = async () => [roll];
  h.window.dispatchEvent({ type: 'focus' }); await h.flush();
  assert.ok(h.nodes().some(n => n.props.roll?.id === roll.id));
  assert.ok(!h.nodes().some(n => n.props.role === 'status'));
});
