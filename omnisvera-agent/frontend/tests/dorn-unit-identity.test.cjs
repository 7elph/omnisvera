const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const code = ts.transpileModule(fs.readFileSync('src/components/DornUnitIdentity.tsx', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
const moduleFixture = { exports: {} };
const jsx = (type, props) => ({ type, props: props || {} });
vm.runInNewContext(code, { module: moduleFixture, exports: moduleFixture.exports, require: () => ({ jsx, jsxs: jsx }) });
const render = moduleFixture.exports.default;
const walk = value => Array.isArray(value) ? value.flatMap(walk) : value && typeof value === 'object' ? [value, ...walk(value.props?.children)] : [];
const text = value => Array.isArray(value) ? value.map(text).join('') : value && typeof value === 'object' ? text(value.props?.children) : String(value ?? '');
const fixture = () => ({ access_level: 'gm', definition: { id: 'dorn7', race: 'Constructo Arcano', abilities: { racial: 'Traço aprovado. +2 CA já incluído.' }, session_abilities: [] }, state: { current_hp: 9, maximum_hp: 13, conditions: [] }, inventory: [{ id: 1, item_title: 'Núcleo Rúnico' }, { id: 2, item_title: 'Cristal de Memória danificado' }, { id: 3, item_title: 'Kit de Reparo' }] });
function view(character = fixture(), more = {}) { return render({ character, combat: { effects: [] }, onInspectItem: () => {}, onOpenMagic: () => {}, ...more }); }

test('only GM Dorn receives the unit presentation', () => {
  assert.equal(view({ ...fixture(), access_level: 'public' }), null);
  assert.equal(view({ ...fixture(), access_level: 'owner' }), null);
  assert.equal(view({ ...fixture(), definition: { id: 'raziel' } }), null);
  assert.ok(view());
});
test('identity uses existing traits, HP, components, and explicit unknown states', () => {
  const content = text(view());
  for (const value of ['9 / 13 PV', 'Traço aprovado', 'Cristal de Memória danificado', 'Estado formal não registrado', 'Nenhum protocolo próprio aprovado']) assert.ok(content.includes(value), value);
  assert.ok(!content.includes('Núcleo estável'));
  assert.equal(walk(view()).filter(node => node.type === 'details').length, 5);
});
test('core navigation and item inspection reuse existing callbacks without changing state', () => {
  const calls = [];
  const character = fixture();
  const before = JSON.stringify(character);
  const tree = view(character, { onInspectItem: item => calls.push(item.item_title), onOpenMagic: () => calls.push('magic') });
  const buttons = walk(tree).filter(node => node.type === 'button');
  for (const button of buttons) button.props.onClick();
  assert.deepEqual(calls, ['magic', 'Núcleo Rúnico', 'Cristal de Memória danificado', 'Kit de Reparo']);
  assert.equal(JSON.stringify(character), before);
});
test('effects show actual duration and modifiers, not preparation assumptions', () => {
  const tree = view(fixture(), { combat: { effects: [{ id: 'shield', target_type: 'character', target_id: 'dorn7', label: 'Escudo registrado', rounds: 2, duration: 'rounds', modifiers: { armor_class: 4 } }, { id: 'other', target_type: 'character', target_id: 'vezemir', label: 'Privado outro', modifiers: {} }] } });
  assert.ok(text(tree).includes('2 rodada(s) restantes'));
  assert.ok(text(tree).includes('CA: +4'));
  assert.ok(!text(tree).includes('Privado outro'));
});
test('missing data does not invent unit state or inventory', () => {
  const tree = view({ access_level: 'gm', definition: { id: 'dorn7' }, state: null, inventory: [] });
  assert.ok(text(tree).includes('Traços raciais ainda não registrados'));
  assert.ok(text(tree).includes('Nenhum componente identificado'));
});
