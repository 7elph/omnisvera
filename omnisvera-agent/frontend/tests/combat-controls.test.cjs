const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function harness(file, props, api) {
  const slots = []; let cursor = 0, tree;
  const react = {
    useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => { slots[i] = v; }]; },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
  };
  const module = { exports: {} }, jsx = (type, props) => ({ type, props: props || {} });
  const code = ts.transpileModule(fs.readFileSync(`src/components/${file}.tsx`, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, window: { dispatchEvent() {} }, CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options?.detail; } }, require: n => n === 'react' ? react : n === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : api });
  const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];
  const render = () => { cursor = 0; tree = module.exports.default(props); };
  render(); return { nodes: () => walk(tree), render, flush: async () => { await new Promise(setImmediate); render(); } };
}

test('map library disables deletion of active and official maps', () => {
  const h = harness('WorkspaceMapLibrary', { maps: [
    { id: 'active', title: 'Atual' }, { id: 'official:nimalis', title: 'Nimalis' }, { id: 'copy', title: 'Copia' },
  ], activeId: 'active', onChange: async () => {} }, {});
  const buttons = h.nodes().filter(n => n.type === 'button' && n.props.children === 'Excluir');
  assert.deepEqual(buttons.map(n => n.props.disabled), [true, true, false]);
});

test('magic preview requires confirmation and never presents a fabricated hit roll', () => {
  let confirmed = 0;
  const resolution = { actor_name: 'Morthak', target_name: 'Aranha', attack_name: 'Mísseis Mágicos', damage_formula: '1d4+2', damage_total: 5, confirmed: false, breakdown: { automatic_hit: true, resource_cost: { amount: 1 } } };
  const props = { resolution, busy: false, onConfirm: () => confirmed++, onClose: () => {} };
  const h = harness('SpellResolution', props, {});
  assert.equal(confirmed, 0);
  assert.doesNotMatch(JSON.stringify(h.nodes()), /d20|Bônus:/);
  h.nodes().find(n => n.type === 'button' && n.props.children === 'Confirmar uso e aplicar dano').props.onClick();
  assert.equal(confirmed, 1);
  props.busy = true; h.render();
  assert.equal(h.nodes().find(n => n.props.children === 'Confirmar uso e aplicar dano').props.disabled, true);
  resolution.confirmed = true; h.render();
  assert.equal(h.nodes().some(n => n.props.children === 'Confirmar uso e aplicar dano'), false);
});

test('current allied turn receives map token targets', () => {
  const source = fs.readFileSync('src/components/CombatEncounterPanel.tsx', 'utf8');
  assert.match(source, /targets=\{battleTokens\}/);
});

test('target indicator connects pin coordinates and does not intercept clicks', () => {
  const h = harness('AttackTargetLine', { tokens: [
    { id: 'pc-pin', character_id: 'vezemir', name: 'Vezemir', longitude: 25, latitude: 20 },
    { id: 'enemy', name: 'Aranha', longitude: 75, latitude: 60 },
  ], actorId: 'vezemir', targetId: 'enemy' }, {});
  const line = h.nodes().find(n => n.type === 'line');
  assert.deepEqual([line.props.x1, line.props.y1, line.props.x2, line.props.y2], [25, 20, 75, 60]);
  assert.match(fs.readFileSync('src/styles.css', 'utf8'), /\.workspace-target-line \{[^}]*pointer-events: none/);
  const absent = harness('AttackTargetLine', { tokens: [], actorId: 'hidden', targetId: 'enemy' }, {});
  assert.equal(absent.nodes().length, 0, 'hidden or missing pins have no line');
});
test('monster rolls before confirmation, prevents double click and applies only on explicit confirmation', async () => {
  const calls = [];
  const result = { resolution_id: 'attack:1', status: 'pending', attack_total: 20, target_ac: 14, result: 'hit', damage_total: 3 };
  const h = harness('MonsterAttackPanel', { token: { id: 'wolf', name: 'Lobo', sheet: { attacks: [{ name: 'Mordida', damage: '1d6', bonus: '+2' }] } }, characters: [{ id: 'raziel', name: 'Raziel' }], physical: false, onChange: async () => {} }, {
    newDiceRequestId: () => 'request-001',
    resolveMonsterAttack: async (...args) => { calls.push(['roll', ...args]); return result; },
    confirmCharacterAttack: async id => { calls.push(['confirm', id]); return { ...result, status: 'confirmed', hp_before: 10, hp_after: 7 }; },
  });
  h.nodes().find(n => n.type === 'select').props.onChange({ target: { value: 'raziel' } }); h.render();
  assert.equal(calls.length, 0, 'choosing a target does not roll or apply damage');
  assert.equal(h.nodes().filter(n => n.type === 'input').length, 0, 'digital combat never asks for damage or formula');
  const click = h.nodes().find(n => n.type === 'button').props.onClick;
  click(); click(); await h.flush();
  assert.equal(calls.length, 1); assert.equal(calls[0][2].target_id, 'raziel');
  assert.equal(calls[0][2].roll_mode, 'digital');
  assert.equal(calls[0][2].d20, undefined);
  assert.equal(calls[0][2].damage, undefined);
  assert.equal(h.nodes().find(n => n.type === 'button').props.disabled, true);
  h.nodes().find(n => n.type === 'button' && n.props.children === 'Confirmar resultado e aplicar dano').props.onClick(); await h.flush();
  assert.equal(calls[1][0], 'confirm');
});

test('off-turn summon attacks stay visible but cannot send a request', async () => {
  let calls = 0;
  const h = harness('MonsterAttackPanel', { token: { id: 'summon', name: 'Lobo reanimado', sheet: { attacks: [{ name: 'Garra', damage: '1d6', bonus: 2 }] } }, characters: [], physical: false, blocked: true, onChange: async () => {} }, {
    resolveMonsterAttack: async () => { calls++; }, newDiceRequestId: () => 'fixture',
  });
  assert.equal(h.nodes().find(n => n.type === 'fieldset').props.disabled, true);
  assert.ok(h.nodes().some(n => n.type === 'strong' && n.props.children === 'Garra'));
  h.nodes().find(n => n.type === 'button').props.onClick();
  await h.flush();
  assert.equal(calls, 0);
});

test('target line ignores summon caster alias and prefers exact pin identity', () => {
  const tokens = [
    { id: 'summon', token_type: 'monster', character_id: 'morthak', name: 'Esqueleto', longitude: 5, latitude: 5 },
    { id: 'caster', token_type: 'character', character_id: 'morthak', name: 'Morthak', longitude: 25, latitude: 20 },
    { id: 'enemy', token_type: 'monster', name: 'Aranha', longitude: 75, latitude: 60 },
  ];
  const caster = harness('AttackTargetLine', { tokens, actorId: 'morthak', targetId: 'enemy' }, {});
  assert.equal(caster.nodes().find(n => n.type === 'line').props.x1, 25);
  const summoned = harness('AttackTargetLine', { tokens, actorId: 'summon', targetId: 'enemy' }, {});
  assert.equal(summoned.nodes().find(n => n.type === 'line').props.x1, 5);
  assert.equal(harness('AttackTargetLine', { tokens }, {}).nodes().length, 0);
});

test('bone dagger routes to its server rule and loot shortcut distinguishes lair', () => {
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.match(source, /resolveSelectedAttack\('adaga-de-osso', target\)/);
  assert.match(source, /ESPÓLIOS DO ENCONTRO/);
  assert.match(source, /treasureHasCarried\(token.sheet\?\.treasure\) && <button/);
  assert.match(source, /treasureHasLair\(token.sheet\?\.treasure\) && <button/);
  assert.match(source, /techniqueRequestRef\.current\.id/);
});

test('attack UI does not invent default damage or offer inert target-only attacks', () => {
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.doesNotMatch(source, /ATTACK_DAMAGE_BY_CHARACTER/);
  assert.match(source, /canOperate && weaponPath && attack.damage/);
  assert.match(source, /Sem arma à distância equipada/);
  assert.match(source, /Equipe uma arma compatível pelo inventário/);
  assert.match(source, /Atacar · rolar acerto e dano/);
});

test('allied token can attack an enemy without converting it to a player or targeting itself', async () => {
  const calls = [];
  const h = harness('MonsterAttackPanel', { token: { id: 'dorn', name: 'Dorn 7', sheet: { attacks: [{ name: 'Punho', damage: '1d6+2', bonus: 3 }] } }, characters: [], targets: [{ id: 'dorn', token_type: 'monster', name: 'Dorn 7' }, { id: 'spider', token_type: 'monster', name: 'Aranha' }], physical: false, onChange: async () => {} }, {
    newDiceRequestId: () => 'ally-request', resolveMonsterAttack: async (...args) => { calls.push(args); return { status: 'pending' }; },
  });
  assert.equal(h.nodes().some(n => n.type === 'option' && n.props.value === 'token:dorn'), false);
  h.nodes().find(n => n.type === 'select').props.onChange({ target: { value: 'token:spider' } }); h.render();
  h.nodes().find(n => n.type === 'button').props.onClick(); await h.flush();
  assert.equal(calls[0][0], 'dorn');
  assert.equal(calls[0][1].target_type, 'token');
  assert.equal(calls[0][1].target_id, 'spider');
});

test('Master ally sheet reuses token HP; archived NPCs remain accessible outside active header', () => {
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  const sheet = fs.readFileSync('src/components/CompanionAllySheet.tsx', 'utf8');
  assert.match(source, /mode === "gm" && allies.map/);
  assert.match(source, /characters.filter\(item => !archivedIds.includes\(item.id\)\)/);
  assert.match(source, /NPCs do Mestre/);
  assert.match(source, /characters.filter\(item => archivedIds.includes\(item.id\)\)/);
  assert.match(sheet, /<TokenVitals/);
  assert.match(sheet, /<MonsterAttackPanel/);
  assert.doesNotMatch(sheet, /createWorkspaceToken|updateCharacterDefinition/);
});
test('map pins retain numerical HP beside a separately positioned bar and ally uses player layout', () => {
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  const sheet = fs.readFileSync('src/components/CompanionAllySheet.tsx', 'utf8');
  const css = fs.readFileSync('src/styles.css', 'utf8');
  assert.match(source, /workspace-pin-health-number/);
  assert.match(source, /role="progressbar"/);
  assert.match(source, /\{hpCurrent \?\? "—"\}\/\{hpMaximum\}/);
  assert.match(css, /\.workspace-map-token > \.workspace-pin-health \{ position: absolute;/);
  for (const className of ['workspace-pin-health-track', 'workspace-pin-health-number']) {
    assert.ok(css.includes(`.workspace-map-stage > button .${className} { display: block;`), 'health overlay overrides hidden legacy button spans');
  }
  assert.match(sheet, /workspace-vitals/);
  assert.match(sheet, /workspace-hp-heading/);
  assert.match(sheet, /workspace-hp-track/);
  assert.doesNotMatch(sheet, /workspace-token-modal-vitals/);
  assert.doesNotMatch(source, /<p role="status">\{attack.id === "ranged"/);
});

test('player pin cannot edit monster HP; Master invalid HP never writes', async () => {
  const props = { token: { id: 'wolf', name: 'Lobo', token_type: 'monster', current_hp: 3, maximum_hp: 12 }, editable: false, onChange: async () => {} };
  const calls = []; const api = { mediaUrlFromVaultPath: p => p, updateWorkspaceToken: async (...args) => calls.push(args) };
  const player = harness('TokenVitals', props, api);
  assert.equal(player.nodes().some(n => n.type === 'input'), false);
  assert.equal(player.nodes().some(n => n.type === 'details'), false);
  const gm = harness('TokenVitals', { ...props, editable: true }, api);
  const editor = gm.nodes().find(n => n.type === 'details');
  assert.ok(editor);
  assert.notEqual(editor.props.open, true, 'HP editing starts collapsed');
  assert.equal(gm.nodes().find(n => n.type === 'summary').props.children, 'Editar vida · Mestre');
  gm.nodes().find(n => n.type === 'input').props.onChange({ target: { value: '99' } }); gm.render();
  gm.nodes().find(n => n.type === 'button').props.onClick(); await gm.flush();
  assert.equal(calls.length, 0);
  assert.equal(gm.nodes().some(n => n.props.role === 'alert'), true);
});

test('collapsed monster HP editor preserves save and refresh behavior', async () => {
  const calls = []; let refreshed = 0;
  const gm = harness('TokenVitals', { token: { id: 'wolf', token_type: 'monster', current_hp: 3, maximum_hp: 12 }, editable: true, onChange: async () => { refreshed++; } }, { updateWorkspaceToken: async (...args) => calls.push(args) });
  gm.nodes().find(n => n.type === 'input').props.onChange({ target: { value: '5' } }); gm.render();
  gm.nodes().find(n => n.type === 'button').props.onClick(); await gm.flush();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 'wolf');
  assert.equal(calls[0][1].current_hp, 5);
  assert.equal(calls[0][1].maximum_hp, 12);
  assert.equal(refreshed, 1);
});
