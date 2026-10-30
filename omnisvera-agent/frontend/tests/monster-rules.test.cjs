const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function render(book) {
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync('src/components/MonsterRules.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require });
  return renderToStaticMarkup(React.createElement(module.exports.default, { book }));
}
function fixture() {
  return { name: 'Dragão', source: { edition: 'OD2', license: 'CC BY-SA 4.0', url: 'https://olddragon.com.br/monstros/dragao-dourado' },
    movement: { modes: { walk: 9, fly: 18 } }, art: { origin: 'missing' }, source_record: { hit_dice: '11+11' },
    rules: [{ id: 'breath', name: 'Baforada', category: 'active', text: 'Texto completo <script>texto</script>\nEXCEÇÃO FINAL',
      execution: { gaps: ['Área ainda assistida.'] }, action_spec: { damage_formula: '11d10', save: 'JPD', save_effect: 'halves',
        geometry: { shape: 'cone', width_m: 9, depth_m: 27 }, uses: { maximum: 3, recharge: 'day' } } }] };
}
test('bestiary displays source, movement, actual breath parameters and assisted execution', () => {
  const html = render(fixture());
  for (const text of ['OD2', '11d10', 'JPD', '27 m', '9 m', '3/dia', 'Voo: 18 m', 'Resolução assistida', 'EXCEÇÃO FINAL', 'Consultar fonte das regras']) assert.ok(html.includes(text), text);
  assert.ok(html.includes('&lt;script&gt;')); assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('Executar')); assert.ok(!html.includes('sempre ligadas'));
});
test('external mapped art is credited without claiming user uploads', () => {
  const book = fixture(); book.art = { origin: 'external_catalog', attribution: 'Oozejar', license: 'CC BY-SA 4.0', catalog_reuse_count: 3 };
  const html = render(book); assert.ok(html.includes('Arte de catálogo externo')); assert.ok(html.includes('Oozejar'));
  assert.ok(!html.includes('enviada por você'));
  assert.ok(html.includes('Imagem compartilhada por 3 entradas'));
});
test('unparsed rules keep full text visible in details, including future fields', () => {
  const book = fixture(); delete book.rules[0].action_spec; book.source_record.lore = 'Lore <preservado>';
  const html = render(book); assert.ok(html.includes('EXCEÇÃO FINAL')); assert.ok(html.includes('Lore &lt;preservado&gt;'));
  assert.equal((html.match(/<details/g) || []).length, 2);
});
