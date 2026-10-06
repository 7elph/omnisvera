const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const css = fs.readFileSync('src/styles.css', 'utf8');

test('ability name is a compact text trigger, not a padded action button', () => {
  assert.match(css, /\.workspace-action-catalog \.workspace-ability-name \{[^}]*background: transparent[^}]*font-size: \.61rem[^}]*padding: 0[^}]*min-height: 0/);
  assert.match(css, /\.workspace-action-catalog \.workspace-ability-name:focus-visible/);
  assert.match(css, /\.workspace-action-catalog button\.workspace-ability-name \{[^}]*background: transparent; border: 0/);
  assert.match(css, /article:has\(> label\) \{ grid-template-columns: minmax\(0,1fr\) auto/);
});

test('ability descriptions match inventory body typography while remaining scrollable', () => {
  for (const selector of ['workspace-item-modal', 'workspace-ability-detail']) {
    assert.match(css, new RegExp(`\\.${selector} p \\{[^}]*font-size: \\.64rem[^}]*line-height: 1\\.5`));
  }
  assert.match(css, /\.workspace-ability-detail \{[^}]*max-height: calc\(100dvh - 40px\)[^}]*overflow-y: auto/);
});
