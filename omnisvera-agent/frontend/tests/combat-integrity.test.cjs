const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
const availability = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/combatActionAvailability.ts', 'utf8'),
  { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, { module: availability, exports: availability.exports });
const { combatActionBlock, consumableActionBlock } = availability.exports;
const encounter = { active: true, battle_mode: true, participants: [{ target_id: 'vezemir', name: 'Vezemir' }], turn_index: 0 };

test('consumable slot remains independent of a spent main action or pending attack', () => {
  assert.equal(consumableActionBlock({ encounter: { ...encounter, action_committed: true, pending_attack: 'preview' } }, 'vezemir', 10), '');
  assert.match(consumableActionBlock({ encounter: { ...encounter, consumable_used: true } }, 'vezemir', 10), /Consumível/);
  assert.match(consumableActionBlock({ encounter }, 'morthak', 10), /Aguarde/);
  assert.match(consumableActionBlock({ encounter }, 'vezemir', 0), /0 PV/);
  assert.equal(combatActionBlock({ encounter: { ...encounter, consumable_used: true } }, 'vezemir', 10), '');
  assert.match(combatActionBlock({ encounter: { ...encounter, pending_attack: 'preview' } }, 'vezemir', 10), /retome/);
  assert.match(combatActionBlock({ encounter }, 'vezemir', 0), /0 PV/);
});

function handler(name, next, context) {
  const code = source.slice(source.indexOf(`  async function ${name}(`), source.indexOf(`  async function ${next}(`));
  return vm.runInNewContext(ts.transpileModule(code + `\n${name}`, { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText, context);
}

test('item retry preserves its key and two clicks before render send only one mutation', async () => {
  let resolve, failure = true, calls = [], serial = 0;
  const context = { selectedId: 'vezemir', busy: '', mutationLock: { current: false }, itemRequestRef: { current: null },
    battleState: { encounter }, character: { state: { current_hp: 10 } }, consumableActionBlock,
    newDiceRequestId: () => 'item-' + ++serial, setBusy() {}, setError() {}, refresh: async () => {},
    applyCharacterStateAction: (...args) => { calls.push(args); return failure ? new Promise((_, reject) => { resolve = () => reject(new Error('lost response')); }) : Promise.resolve({}); } };
  const run = handler('stateAction', 'restAllCharacters', context);
  const first = run('use_item', { item_path: 'potion' }, 'Poção');
  await run('use_item', { item_path: 'potion' }, 'Poção');
  assert.equal(calls.length, 1); resolve(); await first;
  failure = false; await run('use_item', { item_path: 'potion' }, 'Poção');
  assert.equal(calls[0][4], calls[1][4]);
  assert.equal(context.mutationLock.current, false);
});

test('confirmed item use followed by refresh failure does not invite another dose', async () => {
  let error = '';
  const context = { selectedId: 'vezemir', busy: '', mutationLock: { current: false }, itemRequestRef: { current: null },
    battleState: { encounter }, character: { state: { current_hp: 10 } }, consumableActionBlock,
    newDiceRequestId: () => 'stable-item', setBusy() {}, setError: value => { error = value; },
    refresh: async () => { throw new Error('offline'); }, applyCharacterStateAction: async () => ({}) };
  await handler('stateAction', 'restAllCharacters', context)('use_item', { item_path: 'potion' }, 'Poção');
  assert.match(error, /Ação aplicada.*não repita/);
});

test('normal attack retry preserves its dice key and locks before the next render', async () => {
  let reject, calls = [], serial = 0;
  const context = { selectedId: 'vezemir', busy: '', mutationLock: { current: false }, attackRequestRef: { current: null },
    battleState: {}, character: { state: { current_hp: 10 }, definition: { attacks: [{ id: 'melee' }] } }, combatActionBlock,
    attackTargetFor: () => ({ id: 'enemy' }), workspace: { table_mode: 'digital' }, battleActive: false,
    attackCountById: {}, attackPhysicalD20ById: {}, attackWeaponById: {}, newDiceRequestId: () => 'attack-' + ++serial,
    setBusy() {}, setError() {}, setTargetLine() {}, setAttackResolution() {}, setBattleState() {},
    resolveCharacterAttack: (...args) => { calls.push(args); return new Promise((_, fail) => { reject = fail; }); } };
  const run = handler('resolveSelectedAttack', 'confirmResolvedAttack', context);
  let first = run('melee'); await run('melee'); assert.equal(calls.length, 1);
  reject(new Error('lost response')); await first;
  first = run('melee'); assert.equal(calls.length, 2);
  assert.equal(calls[0][1].request_id, calls[1][1].request_id);
  reject(new Error('lost response')); await first;
});
