const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function apiWith(fetch) {
  const timers = new Map();
  let id = 0;
  function load(filename) {
    const module = { exports: {} };
    const source = fs.readFileSync(filename, 'utf8').replaceAll('import.meta.env.VITE_API_BASE_URL', '""');
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
    vm.runInNewContext(code, {
      module, exports: module.exports, fetch, AbortController,
      localStorage: { getItem: () => '' },
      setTimeout: fn => { timers.set(++id, fn); return id; },
      clearTimeout: timer => timers.delete(timer),
      require: name => load(path.resolve(path.dirname(filename), name + '.ts')),
    });
    return module.exports;
  }
  return { api: load(path.join(__dirname, '../src/api.ts')), timers,
    expire: () => [...timers.values()].forEach(fn => fn()) };
}
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };

test('a pending workspace fetch releases the polling lock and allows a subsequent refresh', async () => {
  let calls = 0;
  const signals = [];
  const h = apiWith((url, options) => {
    calls++;
    signals.push(options.signal);
    return calls === 1 ? new Promise(() => {}) : Promise.resolve({ ok: true, json: async () => ({ version: 2 }) });
  });
  let locked = false, version;
  const poll = () => {
    if (locked) return;
    locked = true;
    void h.api.getSessionWorkspace().then(value => { version = value.version; }).catch(() => {}).finally(() => { locked = false; });
  };
  poll(); poll();
  assert.equal(calls, 1);
  h.expire(); await flush();
  assert.equal(locked, false, 'pending network request must not permanently lock refresh');
  assert.equal(signals[0].aborted, true);
  poll(); await flush();
  assert.equal(version, 2);
  assert.equal(locked, false);
  assert.equal(h.timers.size, 0);
});

test('timeout includes a response body that never completes', async () => {
  const h = apiWith(async () => ({ ok: true, json: () => new Promise(() => {}) }));
  let settled = false;
  void h.api.getSessionWorkspace().catch(() => { settled = true; });
  await flush(); h.expire(); await flush();
  assert.equal(settled, true);
});

test('every read involved in the overview/character refresh has a deadline', async () => {
  for (const [method, args] of [
    ['listPlayableCharacters', []], ['getSessionWorkspace', []], ['listSessionLedger', []],
    ['listSessionItems', []], ['listWorkspaceMaps', []], ['listWorkspaceIcons', []],
    ['listWorkspaceLoot', []], ['getCompanionRoster', []], ['getPlayableCharacter', ['raziel']],
    ['listGameSessions', []], ['listScenes', []], ['getScene', [1]], ['getActiveScene', []],
  ]) {
    const h = apiWith(() => new Promise(() => {}));
    let settled = false;
    void h.api[method](...args).catch(() => { settled = true; });
    h.expire(); await flush();
    assert.equal(settled, true, method);
  }
});

function overviewHarness(overrides = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  const start = source.indexOf('  async function loadOverview(');
  const end = source.indexOf('  async function loadCharacter(', start);
  assert.ok(start >= 0 && end > start);
  const state = { catalogs: ['confirmed'], updates: 0 };
  const context = {
    mode: 'gm', Promise, DEFAULT_FOG: {},
    overviewRequestRef: { current: 0 }, currentModeRef: { current: 'gm' },
    fogMutationVersionRef: { current: 0 }, fogSavePendingRef: { current: false },
    paintingFogRef: { current: false }, workspaceAuxLoadedRef: { current: false },
    playerMapIdRef: { current: '' }, activeMapIdRef: { current: '' },
    selectedIdRef: { current: '' }, charactersRef: { current: [] }, ledgerLoadedRef: { current: false },
    listPlayableCharacters: async () => [], getSessionWorkspace: async () => ({}),
    getCompanionRoster: async () => ({ allies: [], archived_character_ids: ['varkh'] }),
    setAllies() {}, setArchivedIds() {},
    listSessionItems: async () => [], listSessionLedger: async () => [],
    listWorkspaceMaps: async () => [], listWorkspaceIcons: async () => [], listWorkspaceLoot: async () => [],
    setCharacters() {}, setWorkspace() { state.updates++; }, setWorkspaceMaps() {},
    setSessionItems(items) { state.catalogs = items; }, setGrantDraft() {},
    setUploadedIcons() {}, setLootResolutions() {}, setLedger() {},
    ...overrides,
  };
  const code = ts.transpileModule(source.slice(start, end), {}).outputText;
  vm.createContext(context);
  vm.runInContext(code, context);
  return { context, state, load: () => context.loadOverview() };
}

test('a failed auxiliary read preserves its confirmed catalog and retries on the next refresh', async () => {
  let attempts = 0;
  const h = overviewHarness({ listSessionItems: async () => {
    if (++attempts === 1) throw new Error('offline');
    return ['recovered'];
  } });
  await h.load();
  assert.deepEqual(h.state.catalogs, ['confirmed']);
  assert.equal(h.context.workspaceAuxLoadedRef.current, false);
  await h.load();
  assert.deepEqual(h.state.catalogs, ['recovered']);
  assert.equal(h.context.workspaceAuxLoadedRef.current, true);
});

test('ally roster failure preserves prior allies and player refresh never requests private roster', async () => {
  let calls = 0, writes = 0;
  const h = overviewHarness({ getCompanionRoster: async () => { calls++; throw new Error('offline'); }, setAllies: () => writes++ });
  await h.load();
  assert.equal(calls, 1); assert.equal(writes, 0);
  h.context.mode = 'player'; h.context.currentModeRef.current = 'player';
  await h.load();
  assert.equal(calls, 1);
});

test('a superseded overview cannot overwrite a newer confirmed workspace', async () => {
  let resolveFirst;
  let calls = 0;
  const h = overviewHarness({ getSessionWorkspace: () => ++calls === 1
    ? new Promise(resolve => { resolveFirst = resolve; }) : Promise.resolve({}) });
  const old = h.load();
  await h.load();
  assert.equal(h.state.updates, 1);
  resolveFirst({}); await old;
  assert.equal(h.state.updates, 1);
});

test('cleanup invalidation prevents a pending overview from applying state', async () => {
  let resolve;
  const h = overviewHarness({ getSessionWorkspace: () => new Promise(done => { resolve = done; }) });
  const pending = h.load();
  h.context.overviewRequestRef.current++;
  resolve({}); await pending;
  assert.equal(h.state.updates, 0);
});
