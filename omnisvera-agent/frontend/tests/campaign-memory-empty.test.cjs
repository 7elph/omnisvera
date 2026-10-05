const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/pages/CampaignMemoryPage.tsx'), 'utf8');
const code = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
}).outputText;
const moduleUnderTest = { exports: {} };
vm.runInNewContext(code, { module: moduleUnderTest, exports: moduleUnderTest.exports, require: () => ({}) });
const build = moduleUnderTest.exports.buildMemories;

for (const narrative of [undefined, null, {}, { participants: null }, { participants: [], tags: null, open_threads: {} }]) {
  test(`new session tolerates incomplete narrative ${JSON.stringify(narrative)}`, () => {
    const [memory] = build([{ id: 5, title: 'Sessão 5', status: 'active', narrative }], []);
    assert.equal(memory.title, 'Sessão 5');
    for (const key of ['participants', 'tags', 'discoveries', 'consequences', 'rewards', 'items', 'openThreads']) {
      assert.equal(Array.isArray(memory[key]), true);
      assert.equal(memory[key].length, 0);
    }
  });
}

test('historical narrative is preserved and private notes are not projected', () => {
  const [memory] = build([{ id: 1, title: 'História', status: 'completed', private_notes: 'PRIVATE',
    narrative: { participants: [{ character_id: 'morthak', name: 'Morthak' }], discoveries: [{ title: 'Porta' }] } }],
    [{ id: 'morthak', portrait: 'portrait.png' }]);
  assert.equal(memory.participants[0].portrait, 'portrait.png');
  assert.equal(memory.discoveries[0].title, 'Porta');
  assert.equal(memory.summary.includes('PRIVATE'), false);
  assert.equal(memory.chronicle.includes('PRIVATE'), false);
});
