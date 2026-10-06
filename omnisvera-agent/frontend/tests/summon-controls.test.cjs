const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const token = { id: 'skeleton', name: 'Esqueleto', map_id: 'arena', current_hp: 10, sheet: { summon: { caster: 'morthak' } } };
const characters = [{ id: 'morthak', access_level: 'owner' }, { id: 'raziel', access_level: 'public' }];
function render(overrides = {}, api = {}) {
  const module = { exports: {} };
  const jsx = (type, props, key) => ({ type, props: props || {}, key });
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/components/SummonControls.tsx'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: name => name === 'react' ? { useRef: value => ({ current: value }), useState: value => [value, () => {}] } : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : name === '../api' ? { newDiceRequestId: () => 'fixture-request', ...api } : { default: 'AttackPanel' } });
  return module.exports.default({ token, mode: 'player', characters, tokens: [token], state: { round: 1, version: 4, effects: [], encounter: { active: true, turn_index: 0, turn_sequence: 2, participants: [{ target_type: 'token', target_id: token.id }] } }, physical: false, onChange: async () => {}, ...overrides });
}
const walk = node => !node || typeof node !== 'object' ? [] : Array.isArray(node) ? node.flatMap(walk) : [node, ...walk(node.props.children)];
const text = node => Array.isArray(node) ? node.map(text).join('') : node && typeof node === 'object' ? text(node.props.children) : String(node ?? '');

test('owner sees attacks and explicit pass-turn inside summon controls', () => {
  const tree = render();
  assert.ok(text(tree).includes('É o turno de Esqueleto'));
  assert.equal(walk(tree).filter(n => n.type === 'AttackPanel').length, 1);
  assert.equal(walk(tree).filter(n => n.type === 'button').length, 1);
});
test('another player and ordinary enemy never receive summon controls', () => {
  assert.equal(render({ characters: [{ id: 'raziel', access_level: 'owner' }] }), null);
  assert.equal(render({ token: { ...token, sheet: {} } }), null);
  assert.ok(render({ mode: 'gm', characters: [] }));
});
test('off-turn controls explain why attacking is unavailable', () => {
  const tree = render({ state: { version: 4, encounter: { active: true, turn_index: 0, participants: [{ target_type: 'character', target_id: 'morthak', name: 'Morthak' }, { target_type: 'token', target_id: 'skeleton' }] } } });
  assert.ok(text(tree).includes('Aguarde seu turno. Agora: Morthak'));
  const panel = walk(tree).find(n => n.type === 'AttackPanel');
  assert.ok(panel, 'attacks remain visible immediately after summoning');
  assert.equal(panel.props.blocked, true);
  assert.equal(walk(tree).filter(n => n.type === 'button').length, 0);
  assert.equal(tree.type, 'details');
  assert.equal(tree.props.open, false, 'off-turn controls are collapsed');
  const active = render();
  assert.equal(active.props.open, true);
  assert.notEqual(tree.key, active.key, 'turn changes remount disclosure so it closes again');
});
test('dead summons cannot attack; outside combat live summons can', () => {
  assert.equal(walk(render({ token: { ...token, current_hp: 0 } })).find(n => n.type === 'AttackPanel').props.blocked, true);
  assert.equal(walk(render({ state: { version: 1, effects: [] } })).filter(n => n.type === 'AttackPanel').length, 1);
});

test('reanimated wolf has the same visible controlled attacks as skeleton', () => {
  const wolf = { ...token, id: 'wolf-reanimated', name: 'Lobo reanimado', sheet: { summon: { caster: 'morthak', technique: 'animar-mortos' } } };
  const tree = render({ token: wolf, state: { version: 4, encounter: { active: true, turn_index: 0, participants: [{ target_type: 'character', target_id: 'morthak', name: 'Morthak' }, { target_type: 'token', target_id: wolf.id }] } } });
  assert.ok(text(tree).includes('Lobo reanimado · Ações da invocação'));
  assert.equal(walk(tree).find(n => n.type === 'AttackPanel').props.blocked, true);
});

test('combat mounts controlled summons before their turn without duplicate current attack panel', () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/components/CombatEncounterPanel.tsx'), 'utf8');
  assert.ok(source.includes('controlledSummons.map(token => <SummonControls'));
  assert.ok(source.includes("token.sheet.summon.caster === ownerId"));
  assert.ok(source.includes('!currentToken?.sheet?.summon'));
  const workspace = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  assert.ok(workspace.includes('!token.sheet?.reanimated_by'));
  assert.ok(workspace.includes('Aguarda autorização do Mestre em Combate'));
});

function renderEncounter(mode, state, tokens, characters) {
  const module = { exports: {} };
  let slot = 0;
  const jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/components/CombatEncounterPanel.tsx'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: name => name === 'react' ? { useRef: value => ({ current: value }), useEffect() {}, useState: value => [slot++ === 0 ? state : value, () => {}] } : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : name.includes('api') ? {} : { default: name } });
  return module.exports.default({ mode, tableMode: 'digital', mapId: 'arena', characters, tokens, onChange: async () => {} });
}

test('combat renders skeleton and reanimated wolf immediately for owner, not another player', () => {
  const wolf = { ...token, id: 'wolf', name: 'Lobo reanimado' };
  const state = { version: 4, round: 1, effects: [], encounter: { active: true, turn_index: 0, participants: [
    { target_type: 'character', target_id: 'morthak', name: 'Morthak' },
    { target_type: 'token', target_id: 'skeleton' }, { target_type: 'token', target_id: 'wolf' },
  ] } };
  const cards = tree => walk(tree).filter(n => n.type === './SummonControls');
  assert.deepEqual(cards(renderEncounter('player', state, [token, wolf], characters)).map(n => n.props.token.id), ['skeleton', 'wolf']);
  assert.equal(cards(renderEncounter('player', state, [token, wolf], [{ id: 'raziel', access_level: 'owner' }])).length, 0);
  assert.equal(cards(renderEncounter('gm', state, [token, wolf], characters)).length, 2);
  const current = { ...state, encounter: { ...state.encounter, turn_index: 1 } };
  const tree = renderEncounter('player', current, [token, wolf], characters);
  assert.equal(cards(tree).length, 2);
  assert.equal(walk(tree).filter(n => n.type === './MonsterAttackPanel').length, 0, 'summon actions are not duplicated in turn notice');
});
test('targets stay on the current arena and participants', () => {
  const tree = render({ tokens: [token, { id: 'enemy', map_id: 'arena', token_type: 'monster' }, { id: 'elsewhere', map_id: 'other', token_type: 'monster' }], state: { version: 4, encounter: { active: true, battle_mode: true, turn_index: 0, participants: [{ target_type: 'token', target_id: 'skeleton' }, { target_type: 'token', target_id: 'enemy' }] } } });
  assert.deepEqual(Array.from(walk(tree).find(n => n.type === 'AttackPanel').props.targets, t => t.id), ['skeleton', 'enemy']);
});
test('passing a turn uses guarded command and prevents concurrent double clicks', async () => {
  const calls = [];
  let changes = 0;
  let finish;
  const tree = render({ onChange: async () => { changes++; } }, { sendCombatEffectCommand: body => { calls.push(body); return new Promise(resolve => { finish = resolve; }); } });
  const button = walk(tree).find(n => n.type === 'button');
  button.props.onClick(); button.props.onClick();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].action, 'next_turn');
  assert.equal(calls[0].expected_version, 4);
  finish({});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(changes, 1);
});
test('pin sheet mounts controls and successful summoning opens its sheet', () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  assert.ok(source.includes('<SummonControls token={openToken}'));
  assert.ok(source.includes('setOpenTokenId(summoned.id)'));
  assert.ok(source.includes('if (reanimated) token = reanimated'));
  assert.ok(source.includes('reanimated_by: summoned.id'));
});
