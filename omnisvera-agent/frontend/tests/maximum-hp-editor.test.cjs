const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function loadEditor() {
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src/components/MaximumHpEditor.tsx'), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(code, { module, exports: module.exports, require: () => ({ jsx, jsxs: jsx }) });
  return module.exports;
}

test('maximum HP rules use class hit die and the already racial-adjusted Constitution modifier', () => {
  const { maximumHpRule } = loadEditor();
  assert.deepEqual({ ...maximumHpRule({ class_name: 'Guerreiro', level: 2, attribute_modifiers: { constitution: 3 } }) }, {
    hitDie: 10, constitutionModifier: 3, level: 2, firstLevelMaximum: 13,
    nextLevelMinimum: 4, nextLevelMaximum: 13, formula: '1d10+3',
  });
  assert.deepEqual({ ...maximumHpRule({ class_name: 'Hemomante', level: 2, attribute_modifiers: { constitution: 0 } }) }, {
    hitDie: 8, constitutionModifier: 0, level: 2, firstLevelMaximum: 8,
    nextLevelMinimum: 1, nextLevelMaximum: 8, formula: '1d8',
  });
  assert.equal(maximumHpRule({ class_name: 'Mago', level: 1 }), null);
});

test('the quick maximum HP editor is GM-only and limited to Vezemir and Raziel', () => {
  const source = fs.readFileSync(path.join(__dirname, '../src/pages/SessionWorkspace.tsx'), 'utf8');
  assert.ok(source.includes('mode === "gm" && (selectedId === "vezemir" || selectedId === "raziel")'));
  assert.ok(source.includes('<MaximumHpEditor definition={definition} value={state?.maximum_hp}'));
  assert.ok(source.includes('definitionAction({ maximum_hp: value })'));
});
