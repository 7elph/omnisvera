const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function apiWith(fetch) {
  const timers = new Map();
  const modules = new Map(), storage = new Map();
  let id = 0;
  function load(filename) {
    if (modules.has(filename)) return modules.get(filename).exports;
    const module = { exports: {} };
    modules.set(filename, module);
    const source = fs.readFileSync(filename, 'utf8').replaceAll('import.meta.env.VITE_API_BASE_URL', '""');
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
    vm.runInNewContext(code, {
      module, exports: module.exports, fetch, AbortController,
      localStorage: { getItem: key => storage.get(key) || '', setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) },
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
    ['health', []], ['getCombatEffects', []], ['getCombatTestViews', []], ['listWorldMaps', []],
  ]) {
    const h = apiWith(() => new Promise(() => {}));
    let settled = false;
    void h.api[method](...args).catch(() => { settled = true; });
    h.expire(); await flush();
    assert.equal(settled, true, method);
  }
});

test('panels share a pending combat read but do not cache completed state', async () => {
  let calls = 0, resolve;
  const h = apiWith(() => { calls++; return new Promise(done => { resolve = done; }); });
  const one = h.api.getCombatEffects(), two = h.api.getCombatEffects();
  assert.equal(calls, 1);
  resolve({ ok: true, json: async () => ({ version: 1, effects: [{ label: 'Original' }] }) });
  const [first, second] = await Promise.all([one, two]);
  first.effects[0].label = 'Changed';
  assert.equal(second.effects[0].label, 'Original');
  const fresh = h.api.getCombatEffects();
  assert.equal(calls, 2);
  resolve({ ok: true, json: async () => ({ version: 2 }) });
  assert.equal((await fresh).version, 2);
});

test('stalled combat mutations release their timeout without retrying any write', async () => {
  for (const [method, args] of [
    ['resolveCharacterAttack', ['vezemir', { request_id:'stable-attack' }]],
    ['useCharacterTechnique', ['morthak', 'levantar-esqueleto', { request_id:'stable-summon' }]],
    ['confirmCharacterAttack', ['attack:stored']],
    ['applyCharacterStateAction', ['vezemir', 'use_item', { item_path:'potion' }, 'Poção', 'stable-potion']],
    ['resolveMonsterAttack', ['skeleton', { request_id:'stable-skeleton-attack' }]],
    ['sendCombatEffectCommand', [{ request_id:'stable-turn', action:'next_turn' }]],
  ]) {
    let calls = 0;
    const h = apiWith(() => { calls++; return new Promise(() => {}); });
    let settled = false;
    void h.api[method](...args).catch(() => { settled = true; });
    h.expire(); await flush();
    assert.equal(settled, true, method);
    assert.equal(calls, 1, method + ' must never retry automatically');
  }
});

test('pending combat reads never cross token identities', async () => {
  const calls = [], resolves = [];
  const h = apiWith((url, options) => { calls.push(options.headers['X-Omnisvera-Token']); return new Promise(done => resolves.push(done)); });
  h.api.setAccessToken('test-raziel');
  const first = h.api.getCombatEffects();
  h.api.setAccessToken('test-morthak');
  const second = h.api.getCombatEffects();
  assert.deepEqual(calls, ['test-raziel', 'test-morthak']);
  resolves.forEach((done, index) => done({ ok: true, json: async () => ({ version: index + 1 }) }));
  assert.equal((await first).version, 1);
  assert.equal((await second).version, 2);
});

test('a shared combat timeout releases all readers and the next request can recover', async () => {
  let calls = 0;
  const h = apiWith(() => ++calls === 1 ? new Promise(() => {}) : Promise.resolve({ ok: true, json: async () => ({ version: 9 }) }));
  const first = h.api.getCombatEffects(), second = h.api.getCombatEffects();
  const outcomes = Promise.allSettled([first, second]);
  h.expire();
  assert.equal((await outcomes).every(value => value.status === 'rejected'), true);
  assert.equal((await h.api.getCombatEffects()).version, 9);
  assert.equal(calls, 2);
});

test('combat mutations keep their explicit request ids and are never merged or retried', async () => {
  const calls = [];
  const h = apiWith(async (url, options) => { calls.push(JSON.parse(options.body).request_id); return { ok: false, status: 409, json: async () => ({ detail: 'Outdated' }) }; });
  const payload = { request_id: 'explicit-1', expected_version: 1, action: 'next_turn', payload: {} };
  const results = await Promise.allSettled([h.api.sendCombatEffectCommand(payload), h.api.sendCombatEffectCommand({ ...payload, request_id: 'explicit-2' })]);
  assert.deepEqual(calls, ['explicit-1', 'explicit-2']);
  assert.equal(results.every(value => value.status === 'rejected' && value.reason.status === 409), true);
});

function overviewHarness(overrides = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  const start = source.indexOf('  async function loadOverview(');
  const end = source.indexOf('  async function loadCharacter(', start);
  assert.ok(start >= 0 && end > start);
  const state = { catalogs: ['confirmed'], updates: 0, error: '' };
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
    setError(update) { state.error = typeof update === 'function' ? update(state.error) : update; },
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

test('a stalled session log does not block the workspace or character overview', async () => {
  const h = overviewHarness({ listSessionLedger: () => new Promise(() => {}) });
  await h.load();
  assert.equal(h.state.updates, 1);
  assert.equal(h.context.ledgerLoadedRef.current, false);
});

test('session log failure preserves the previous log and retries independently', async () => {
  let attempts = 0, writes = 0;
  const h = overviewHarness({ listSessionLedger: async () => {
    if (++attempts === 1) throw new Error('offline');
    return ['recovered'];
  }, setLedger: () => writes++ });
  await h.load();
  assert.equal(h.state.updates, 1); assert.equal(writes, 0);
  await h.load();
  assert.equal(writes, 1);
});

test('confirmed overview recovery clears the previous character-list timeout', async () => {
  const h = overviewHarness();
  h.state.error = 'Falha ao carregar personagens: conexão demorou demais. Tentaremos atualizar novamente.';
  await h.load();
  assert.equal(h.state.error, '');
});

test('overview recovery preserves action errors and failed reads keep the prior banner', async () => {
  const h = overviewHarness();
  h.state.error = 'Ação rejeitada: sangue insuficiente';
  await h.load();
  assert.equal(h.state.error, 'Ação rejeitada: sangue insuficiente');
  h.context.listPlayableCharacters = async () => { throw new Error('offline'); };
  h.state.error = 'Falha ao carregar personagens: conexão demorou demais.';
  await assert.rejects(h.load(), /offline/);
  assert.equal(h.state.error, 'Falha ao carregar personagens: conexão demorou demais.');
});
