const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync('src/components/CombatEncounterPanel.tsx', 'utf8');
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };

test('combat adopts the parent confirmed action snapshot without rewinding a newer local turn', () => {
  const start = source.indexOf('  useEffect(() => {\n    if (!confirmedState) return;');
  assert.ok(start >= 0, 'The sheet snapshot must reach the combat card without waiting for polling');
  const end = source.indexOf('  }, [confirmedState]);', start) + '  }, [confirmedState]);'.length;
  const context = { state: { version: 1 }, confirmedState: { version: 2, effects: ['shield'] },
    useEffect: fn => fn(), setState: update => { context.state = update(context.state); } };
  const code = ts.transpileModule(source.slice(start, end), {}).outputText;
  vm.runInNewContext(code, context);
  assert.equal(context.state.version, 2); assert.equal(context.state.effects[0], 'shield');
  context.state = { version: 5, turn: 'monster' };
  context.confirmedState = { version: 3, turn: 'raziel' };
  vm.runInNewContext(code, context);
  assert.equal(context.state.version, 5); assert.equal(context.state.turn, 'monster');
  context.confirmedState = undefined;
  vm.runInNewContext(code, context); assert.equal(context.state.version, 5);
});

test('both native combat views receive the confirmed sheet snapshot', () => {
  const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  const views = workspace.split('\n').filter(line => line.includes('<CombatEncounterPanel '));
  assert.equal(views.length, 2);
  for (const view of views) assert.ok(view.includes('confirmedState={battleState || undefined}'));
});

test('monster grid targets retain participant character pins without exposing outsiders', () => {
  const start = source.indexOf('  const battleTokens =');
  const end = source.indexOf(';', start) + 1;
  assert.ok(start >= 0 && end > start);
  const tokens = [{ id: 'enemy' }, { id: 'pc-pin', character_id: 'raziel' },
    { id: 'outside-pc', character_id: 'morthak' }, { id: 'outside-npc' }];
  const context = { tokens, state: { encounter: { battle_mode: true } }, members: [
    { target_type: 'token', target_id: 'enemy' }, { target_type: 'character', target_id: 'raziel' }], selected: null };
  const code = source.slice(start, end) + '\nselected = battleTokens;';
  vm.runInNewContext(code, context);
  assert.deepEqual(Array.from(context.selected, token => token.id), ['enemy', 'pc-pin']);
  context.state.encounter.battle_mode = false;
  const legacy = { ...context, selected: null };
  vm.runInNewContext(code, legacy);
  assert.deepEqual(Array.from(legacy.selected, token => token.id), tokens.map(token => token.id));
});

function pollHarness(getCombatEffects) {
  const start = source.indexOf('  useEffect(() => {\n    let alive = true, pending = false;');
  const end = source.indexOf('  }, []);', start) + '  }, []);'.length;
  assert.ok(start >= 0 && end > start);
  let state = { version: 1 }, cleanup, poll, error = '';
  const events = new Map(), visibility = new Map();
  const document = { visibilityState: 'visible', addEventListener: (key, fn) => visibility.set(key, fn), removeEventListener: key => visibility.delete(key) };
  const context = {
    getCombatEffects, lock: { current: false }, document,
    setState: update => { state = typeof update === 'function' ? update(state) : update; },
    setSyncError: value => { error = value; }, Error,
    useEffect: fn => { cleanup = fn(); },
    window: { addEventListener: (key, fn) => events.set(key, fn), removeEventListener: key => events.delete(key), setInterval: fn => { poll = fn; return 1; } },
    setInterval: fn => { poll = fn; return 1; }, clearInterval() {},
  };
  vm.runInNewContext(ts.transpileModule(source.slice(start, end), {}).outputText, context);
  return { context, events, visibility, poll: () => poll(), cleanup: () => cleanup(), state: () => state, error: () => error };
}

test('combat polling never overlaps, recovers after failure and clears only the sync error', async () => {
  let calls = 0, resolve, reject;
  const h = pollHarness(() => { calls++; return new Promise((yes, no) => { resolve = yes; reject = no; }); });
  h.poll(); h.events.get('omnisvera-session-changed')();
  assert.equal(calls, 1);
  reject(new Error('offline')); await flush();
  assert.equal(h.state().version, 1);
  assert.equal(h.error(), 'offline');
  h.events.get('online')();
  assert.equal(calls, 2);
  resolve({ version: 2 }); await flush();
  assert.equal(h.state().version, 2); assert.equal(h.error(), '');
});

test('late polling cannot undo a newer confirmed turn, and cleanup stops updates', async () => {
  let resolve;
  const h = pollHarness(() => new Promise(done => { resolve = done; }));
  h.context.setState({ version: 5 });
  resolve({ version: 2 }); await flush();
  assert.equal(h.state().version, 5);
  h.poll(); h.cleanup(); resolve({ version: 6 }); await flush();
  assert.equal(h.state().version, 5);
  assert.equal(h.events.size, 0); assert.equal(h.visibility.size, 0);
});

test('returning from background triggers recovery without a page reload', async () => {
  let calls = 0;
  const h = pollHarness(async () => ({ version: ++calls }));
  await flush();
  h.context.document.visibilityState = 'hidden'; h.visibility.get('visibilitychange')();
  await flush(); assert.equal(calls, 1);
  h.context.document.visibilityState = 'visible'; h.visibility.get('visibilitychange')();
  await flush(); assert.equal(calls, 2);
});

function saveHarness(overrides = {}) {
  const start = source.indexOf('  async function save('), end = source.indexOf('  if ((mode === "player"', start);
  const context = {
    lock: { current: false }, retry: { current: null }, state: { version: 1 },
    participants: [], drafts: {}, orderCount: 0, title: 'Test', mapId: 'map', encounterMapId: '', arena: '', mode: 'gm', tableMode: 'digital',
    HttpError: class extends Error { constructor(status) { super('conflict'); this.status = status; } },
    setBusy() {}, setError: value => { context.error = value; }, setState: value => { context.state = typeof value === 'function' ? value(context.state) : value; },
    newDiceRequestId: () => 'explicit-id', onChange: async () => {}, getCombatEffects: async () => ({ version: 2 }),
    ...overrides,
  };
  vm.createContext(context);
  vm.runInContext(ts.transpileModule(source.slice(start, end), {}).outputText, context);
  return context;
}

test('a combat version conflict refreshes state but never automatically repeats the action', async () => {
  let writes = 0, reads = 0;
  const h = saveHarness();
  h.sendCombatEffectCommand = async () => { writes++; throw new h.HttpError(409); };
  h.getCombatEffects = async () => { reads++; return { version: 2 }; };
  await h.save('next_turn');
  assert.equal(writes, 1); assert.equal(reads, 1); assert.equal(h.state.version, 2);
  assert.match(h.error, /confira o turno/); assert.equal(h.lock.current, false);
});

test('a successful action followed by failed refresh is reported as applied, not failed', async () => {
  let writes = 0;
  const h = saveHarness({ sendCombatEffectCommand: async () => { writes++; return { version: 2 }; }, onChange: async () => { throw new Error('offline'); } });
  await h.save('next_turn');
  assert.equal(writes, 1); assert.equal(h.state.version, 2);
  assert.match(h.error, /Ação aplicada/); assert.match(h.error, /Não repita/);
  assert.equal(h.retry.current, null);
});

function childRefreshHarness(getCombatEffects, summon = true) {
  let cursor = 0, changes = 0;
  const token = { id: 'skeleton', map_id: 'arena', current_hp: 10, sheet: summon ? { summon: { caster: 'morthak' } } : {} };
  const slots = [{ version: 4, round: 1, effects: [], encounter: { active: true, participants: [{ target_type: 'token', target_id: token.id }], turn_index: 0 } }];
  const react = {
    useEffect() {},
    useRef: initial => ({ current: initial }),
    useState(initial) { const slot = cursor++; if (!(slot in slots)) slots[slot] = initial; return [slots[slot], value => { slots[slot] = typeof value === 'function' ? value(slots[slot]) : value; }]; },
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText, {
    module, exports: module.exports, require: name => name === 'react' ? react : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : name.includes('api') ? { getCombatEffects } : { default: name },
  });
  const tree = module.exports.default({ mode: 'gm', mapId: 'arena', characters: [], tokens: [token], onChange: async () => { changes++; } });
  const walk = node => !node || typeof node !== 'object' ? [] : Array.isArray(node) ? node.flatMap(walk) : [node, ...walk(node.props.children)];
  return { nodes: walk(tree), state: () => slots[0], update: state => { slots[0] = state; }, changes: () => changes };
}

for (const child of ['./SummonControls', './CombatEffectsPanel', './MonsterAttackPanel']) {
  test(`${child} refresh cannot rewind a newer combat version`, async () => {
    let resolve;
    const h = childRefreshHarness(() => new Promise(done => { resolve = done; }), child !== './MonsterAttackPanel');
    const refresh = h.nodes.find(node => node.type === child).props.onChange;
    const pending = refresh();
    h.update({ version: 9, effects: [], encounter: { active: true, turn_sequence: 7 } });
    resolve({ version: 5, effects: [], encounter: { active: true, turn_sequence: 3 } });
    await pending;
    assert.equal(h.state().version, 9);
    assert.equal(h.state().encounter.turn_sequence, 7);
    assert.equal(h.changes(), 1, 'parent overview still refreshes');
    const next = refresh(); resolve({ version: 10, effects: [] }); await next;
    assert.equal(h.state().version, 10, 'newer snapshots continue to synchronize');
  });
}

test('conflict recovery cannot rewind a newer state received while its read was pending', async () => {
  let resolve;
  const h = saveHarness();
  h.sendCombatEffectCommand = async () => { throw new h.HttpError(409); };
  h.getCombatEffects = () => new Promise(done => { resolve = done; });
  const pending = h.save('next_turn'); await flush();
  h.setState({ version: 9 }); resolve({ version: 2 }); await pending;
  assert.equal(h.state.version, 9);
});
