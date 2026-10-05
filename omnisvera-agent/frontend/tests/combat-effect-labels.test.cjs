const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function render(mode) {
  const state = { round: 1, version: 1, effects: [{ id: 'fixture-effect', target_type: 'character', target_id: 'vezemir', label: 'Força Arcana', source: 'Fixture', duration: 'rounds', rounds: 2, modifiers: { strength_bonus: 3, movement_multiplier: 2, attack_bonus: 0 } }] };
  let index = 0;
  const jsx = (type, props) => ({ type, props: props || {} });
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src/components/CombatEffectsPanel.tsx'), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: name => name === 'react' ? { useState: value => [index++ === 0 ? state : value, () => {}], useRef: value => ({ current: value }), useEffect: () => {} } : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : {} });
  return module.exports.default({ mode, characters: [{ id: 'vezemir', name: 'Vezemir' }], tokens: [], onChange: async () => {} });
}
const text = n => Array.isArray(n) ? n.map(text).join('') : n && typeof n === 'object' ? text(n.props.children) : String(n ?? '');
const walk = n => !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(walk) : [n, ...walk(n.props.children)];

for (const mode of ['gm', 'player']) test(`persisted ability modifiers have readable labels for ${mode}`, () => {
  const tree = render(mode);
  const value = text(tree);
  assert.ok(value.includes('Força +3'), value);
  assert.ok(value.includes('Multiplicador de movimento +2'), value);
  assert.ok(!value.includes('undefined'), value);
  assert.ok(!value.includes('Ataque +0'), value);
  // Displaying existing ability effects does not expand GM editing controls.
  assert.equal(walk(tree).filter(n => n.type === 'input' && ['Ataque', 'Dano', 'CA', 'Ataques adicionais', 'PV por rodada (+ cura / − dano)'].includes(n.props['aria-label'])).length, mode === 'gm' ? 5 : 0);
});
