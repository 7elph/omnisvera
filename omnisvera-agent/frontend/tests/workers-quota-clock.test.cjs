const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const vm = require('node:vm');
const target = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/WorkersQuotaClock.tsx', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React }
}).outputText, { exports: target.exports, module: target, require: () => ({}) });

test('quota reset follows UTC midnight, including month rollover', () => {
  for (const [now, next, countdown] of [
    ['2026-10-06T20:59:00-03:00', '2026-10-07T00:00:00Z', '00:01:00'],
    ['2026-10-06T21:00:00-03:00', '2026-10-08T00:00:00Z', '24:00:00'],
    ['2026-12-31T23:59:59Z', '2027-01-01T00:00:00Z', '00:00:01'],
  ]) {
    assert.equal(target.exports.workersQuotaReset(Date.parse(now)), Date.parse(next));
    assert.equal(target.exports.quotaCountdown(Date.parse(now)), countdown);
  }
});

test('clock never promises available quota or triggers provider requests', () => {
  const source = fs.readFileSync('src/components/WorkersQuotaClock.tsx', 'utf8');
  assert.match(source, /não saldo consultado/);
  assert.match(source, /clearInterval/);
  assert.doesNotMatch(source, /fetch\(|\/generate|cota disponível/);
});
