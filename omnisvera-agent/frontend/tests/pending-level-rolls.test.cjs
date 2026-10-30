const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync('src/components/PendingLevelRolls.tsx', 'utf8');
test('pending HP uses the existing server roll with a stable completion key and double-click lock', () => {
  assert.match(source, /if \(!canOperate \|\| lock.current\) return/);
  assert.match(source, /completeRollRequest\(id, `level-hp-completion:\$\{id\}`\)/);
  assert.match(source, /finally \{ lock.current = false/);
  assert.match(source, /await onApplied\(\)/);
});
test('pending progression remains visible without granting an unauthorized roll', () => {
  assert.match(source, /disabled=\{!canOperate \|\| busy\}/);
  assert.match(source, /PV · ROLAGEM PENDENTE/);
  assert.match(source, /sem cura automática/);
  assert.match(source, /role="alert"/);
});
