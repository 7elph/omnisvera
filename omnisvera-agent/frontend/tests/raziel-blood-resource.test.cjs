const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
function evaluate(fragment, context) {
  const code = ts.transpileModule(fragment, { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText;
  return vm.runInNewContext(code, context);
}
test('Raziel Habilidades precede vampire powers without changing other sheets', () => {
  const fragment = source.slice(source.indexOf('  const basicAbilities ='), source.indexOf('  const basicAttacks ='));
  const abilities = [{ id: 'power', kind: 'ability', group: 'Poderes vampíricos' }, { id: 'blade', kind: 'ability', group: 'Habilidades' }, { id: 'trait', kind: 'ability', group: 'Traços vampíricos' }];
  const groups = id => evaluate(fragment + '\nObject.keys(groupedAbilities)', { abilities, definition: { id } });
  assert.deepEqual(Array.from(groups('raziel')), ['Habilidades', 'Poderes vampíricos', 'Traços vampíricos']);
  assert.deepEqual(Array.from(groups('vezemir')), ['Poderes vampíricos', 'Habilidades', 'Traços vampíricos']);
});
test('both blood techniques reference the persisted blood pool even without uses metadata', () => {
  const fragment = source.slice(source.indexOf('function abilityResource('), source.indexOf('function attackDamage('));
  const resources = [{ key: 'reserva_de_sangue', current: 3, maximum: 5 }];
  for (const id of ['lamina-de-sangue', 'marca-rubra']) {
    const value = evaluate(fragment + '\nabilityResource(ability, resources)', { ability: { id }, resources });
    assert.equal(value, resources[0]);
  }
});
test('blood counter remains in Resources even when linked to catalog abilities', () => {
  const fragment = source.slice(source.indexOf('  const standaloneResources ='), source.indexOf('  const consumables ='));
  const value = evaluate(fragment + '\nstandaloneResources', { state: { resources: [{ key: 'reserva_de_sangue', label: 'Reserva de Sangue', current: 5, maximum: 5 }] }, catalogResourceKeys: new Set(['reserva_de_sangue']) });
  assert.equal(value.length, 1);
  assert.equal(value[0].maximum, 5);
  assert.ok(source.includes('resource.current}/{resource.maximum'));
  assert.ok(source.includes('canOperate && resource.key !== "reserva_de_sangue"'));
});
