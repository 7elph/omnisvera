const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const vm = require('node:vm');
const moduleUnderTest = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/sharedAttackTarget.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS }
}).outputText, { exports: moduleUnderTest.exports, module: moduleUnderTest });
const { sharedAttackTarget } = moduleUnderTest.exports;
const state = { encounter: { active: true, turn_sequence: 3, turn_started_at: 'now' } };
const entry = { id: 1, source_type: 'combat_action', detail: { turn_sequence: 3, turn_started_at: 'now', actor_id: 'morthak', target_id: 'wolf' } };
test('all clients derive the same last confirmed target for the current turn', () => {
  assert.equal(JSON.stringify(sharedAttackTarget(state, [entry])), JSON.stringify({ actorId: 'morthak', targetId: 'wolf' }));
  assert.equal(sharedAttackTarget(state, [entry, { ...entry, id: 2, detail: { ...entry.detail, target_id: 'spider' } }]).targetId, 'spider');
});
test('old turns, other combats, voided actions and inactive combats never retain a line', () => {
  for (const item of [{ ...entry, voided_at: 'void' }, { ...entry, detail: { ...entry.detail, turn_sequence: 2 } }, { ...entry, detail: { ...entry.detail, turn_started_at: 'other combat' } }]) {
    assert.equal(JSON.stringify(sharedAttackTarget(state, [item])), '{}');
  }
  assert.equal(JSON.stringify(sharedAttackTarget({ encounter: { active: false } }, [entry])), '{}');
});
test('attack and magic results are nonmodal docks and spells have inline target controls', () => {
  const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.match(workspace, /workspace-combat-result-dock/);
  assert.match(fs.readFileSync('src/components/SpellResolution.tsx', 'utf8'), /aria-modal="false"/);
  assert.match(workspace, /ability.id === "misseis-magicos"\) return <SpellTargetControl/);
  const inline = fs.readFileSync('src/components/SpellTargetControl.tsx', 'utf8');
  assert.match(inline, /label="Alvo de Mísseis Mágicos"/);
  assert.match(inline, /onChange=\{onSelect\}/);
  assert.match(inline, /onClick=.*onUse\(target\)/);
});
test('missiles reuse inventory card parts with controls below the name', () => {
  const inline = fs.readFileSync('src/components/SpellTargetControl.tsx', 'utf8');
  assert.ok(inline.includes('<SpellCard heading={heading} summary={summary}>'));
  const card=fs.readFileSync('src/components/SpellCard.tsx','utf8');
  for (const name of ['workspace-catalog-card-heading', 'workspace-catalog-card-summary']) assert.ok(card.includes(name));
  const css = fs.readFileSync('src/styles.css', 'utf8');
  assert.match(css, /article.workspace-spell-card \{\s*grid-template-columns: minmax\(0,1fr\)/);
  assert.match(css, /workspace-spell-target-control > select \{\s*width: 100%; max-width: 100%; min-width: 0;/);
  assert.match(css, /workspace-spell-target-control > button \{ width: auto; grid-column: 2;/);
  assert.match(css, /workspace-spell-target-control \{ display: grid; grid-template-columns: minmax\(0, 1fr\) auto;/);
});
test('history count names the loaded window and GM can include state entries without raw JSON', () => {
  const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.match(workspace, /eventos exibidos.*ledger.length.*carregados/);
  assert.match(workspace, /setIncludeStateRecords/);
  assert.doesNotMatch(workspace, /slice\(0, 250\)/);
});
test('reanimated visual derives from summon technique, preserving original image data', () => {
  const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.match(workspace, /token.sheet\?\.summon\?\.technique === "animar-mortos" \? "reanimated"/);
  assert.match(fs.readFileSync('src/styles.css', 'utf8'), /workspace-map-token.reanimated > img/);
});
