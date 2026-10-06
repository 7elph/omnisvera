const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
const powerOverrides = JSON.parse(fs.readFileSync('../backend/app/data/raziel_vampire_powers.json', 'utf8'));
const abilities = JSON.parse(fs.readFileSync('../backend/app/data/session_abilities.json', 'utf8')).characters.raziel
  .map(ability => ({ ...ability, ...powerOverrides[ability.id] }));

test('night form offers three animals and regeneration does not duplicate blood counter', () => {
  assert.equal(abilities.find(a => a.id === 'forma-da-noite').uses.maximum, 3);
  for (const animal of ['corvo', 'coruja', 'morcego']) assert.ok(source.includes(`value="${animal}"`));
  assert.ok(source.includes('aria-label="Animal da Forma da Noite"'));
  assert.ok(source.includes('amount: 1, animal'));
  assert.ok(source.includes('resource && ability.id !== "regeneracao-vampirica" && <b>'));
});

test('ability descriptions escape clipping containers and scroll within the viewport', () => {
  const block = source.slice(source.indexOf('function AbilityName('), source.indexOf('function abilityResource('));
  assert.ok(block.includes('createPortal('));
  assert.ok(block.includes('document.body'));
  assert.ok(block.includes('role="dialog"'));
  assert.ok(block.includes('Fechar descrição'));
  const css = fs.readFileSync('src/styles.css', 'utf8');
  assert.match(css, /\.workspace-ability-detail \{[^}]*max-height: calc\(100dvh - 40px\)[^}]*overflow-y: auto/);
});

test('Mordida requires an explicit target and no prior normal attack', () => {
  assert.equal(abilities.find(a => a.id === 'mordida').requires_target, true);
  const start = source.indexOf('async function useAbility');
  const branch = source.slice(start, source.indexOf("if (['animar-mortos'", start));
  assert.ok(branch.includes("ability.id === 'mordida' && !target"));
  assert.ok(branch.includes("target_type: 'token', target_id: target.id"));
  assert.ok(branch.includes('setAttackResolution(result as AttackResolution)'));
  assert.ok(!branch.includes('resolution_id: last.resolution_id'));
  assert.ok(branch.includes('vampireLock.current = true'));
  assert.ok(branch.includes('combatActionBlock'));
});

test('physical Mordida uses its own d20 and confirmed drain is visible', () => {
  assert.ok(source.includes("['adaga-de-osso', 'mordida'].includes(selectedTargetAbility.id)"));
  assert.ok(source.includes('attackPhysicalD20ById[selectedTargetAbility.id]'));
  assert.ok(source.includes('attackResolution.breakdown.drain_result.healed'));
});

test('regeneration is structured, shares the five-point blood pool, and displays actual recovery', () => {
  const regeneration = abilities.find(a => a.id === 'regeneracao-vampirica');
  assert.equal(regeneration.mechanics_status, 'structured');
  assert.equal(regeneration.uses.resource_key, 'reserva_de_sangue');
  assert.equal(regeneration.uses.cost, 1);
  assert.equal(regeneration.uses.maximum, 5);
  assert.ok(source.includes('setVampireOutcome(`Regeneração:'));
  assert.ok(source.includes('vampireOutcome && <p role="status">'));
});

function controller(api, overrides = {}) {
  const start = source.indexOf('  async function useAbility(');
  const end = source.indexOf('  async function submitMessage(', start);
  const context = { combatActionBlock: () => '', battleState: {}, selectedId: 'raziel', busy: '',
    vampireLock: { current: false }, techniqueRequestRef: { current: null },
    defaultAttackRollMode: 'digital', attackPhysicalD20ById: {}, newDiceRequestId: () => 'vampire-request',
    setError() {}, setBusy() {}, setVampireOutcome() {}, setAttackResolution() {}, setTargetPickerAbilityId() {},
    refresh: async () => {}, useCharacterTechnique: api, ...overrides };
  const code = ts.transpileModule(source.slice(start, end) + '\nuseAbility', { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText;
  return { run: vm.runInNewContext(code, context), context };
}

test('Mordida controller submits target, previews attack, and locks double clicks', async () => {
  const calls = []; let resolve; let preview;
  const c = controller((...args) => { calls.push(args); return new Promise(done => { resolve = done; }); }, { setAttackResolution: value => { preview = value; } });
  const ability = { id: 'mordida' }, target = { id: 'wolf' };
  const first = c.run(ability, target);
  await c.run(ability, target);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][2].target_id, 'wolf');
  assert.equal(calls[0][2].roll_mode, 'digital');
  assert.equal(calls[0][2].resolution_id, undefined);
  resolve({ resolution_id: 'bite-preview', status: 'pending' }); await first;
  assert.equal(preview.resolution_id, 'bite-preview');
  assert.equal(c.context.vampireLock.current, false);
});

test('Regeneration controller uses server totals and refreshes the character', async () => {
  let message, refreshes = 0;
  const c = controller(async () => ({ heal_roll: 4, hp_before: 15, hp_after: 16, blood_remaining: 4 }), {
    setVampireOutcome: value => { message = value; }, refresh: async () => { refreshes++; },
  });
  await c.run({ id: 'regeneracao-vampirica' });
  assert.match(message, /PV 15 → 16/);
  assert.match(message, /Sangue restante: 4/);
  assert.equal(refreshes, 1);
});
