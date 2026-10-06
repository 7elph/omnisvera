const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync(path.join(__dirname, '../src/components/combatActionAvailability.ts'), 'utf8');
const moduleUnderTest = { exports: {} };
vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, { module: moduleUnderTest, exports: moduleUnderTest.exports });
const block = moduleUnderTest.exports.combatActionBlock;
const encounter = { active: true, battle_mode: true, participants: [{ target_id: 'morthak', name: 'Morthak' }, { target_id: 'skeleton', name: 'Esqueleto' }], turn_index: 0, action_committed: false };

test('Morthak can use the bone dagger on his unspent turn', () => {
  assert.equal(block({ encounter }, 'morthak'), '');
  assert.equal(block({ encounter: { active: false } }, 'morthak'), '');
});
test('summoning consumes action: block another attack with explicit pass-turn guidance', () => {
  assert.match(block({ encounter: { ...encounter, action_committed: true, attacks_used: 1, attack_limit: 1 } }, 'morthak'), /passe o turno/);
  assert.match(block({ encounter: { ...encounter, attacks_used: 1, attack_limit: 1 } }, 'morthak'), /passe o turno/);
});
test('Morthak cannot attack during the skeleton turn and becomes available next round', () => {
  assert.match(block({ encounter: { ...encounter, turn_index: 1 } }, 'morthak'), /Esqueleto/);
  assert.equal(block({ encounter: { ...encounter, attacks_used: 0, attack_limit: 1 } }, 'morthak'), '');
});
test('attack handler rejects exhausted actions before constructing a zero-count request', () => {
  const workspace = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  const start = workspace.indexOf('async function resolveSelectedAttack');
  const end = workspace.indexOf('async function confirmResolvedAttack', start);
  const handler = workspace.slice(start, end);
  assert.ok(handler.indexOf('if (blocked)') < handler.indexOf('resolveCharacterAttack('));
  assert.ok(handler.indexOf('if (count < 1)') < handler.indexOf('resolveCharacterAttack('));
  assert.ok(workspace.includes('A Adaga de Osso tem seu próprio card'));
});
test('battle map retains four rows and a nonzero canvas on portrait phones', () => {
  const css = fs.readFileSync(path.join(__dirname, '../src/styles.css'), 'utf8');
  assert.ok(css.includes('.unified-workspace .workspace-map-panel:has(> .workspace-battle-banner) { grid-template-rows: auto auto minmax(0, 1fr) auto; }'));
  assert.match(css, /@media \(max-width: 720px\) and \(orientation: portrait\)[\s\S]*grid-template-rows: auto auto minmax\(320px, 58vh\) auto/);
});
