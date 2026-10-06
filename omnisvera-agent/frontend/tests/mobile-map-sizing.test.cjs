const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const css = fs.readFileSync('src/styles.css', 'utf8');
const mobile = css.slice(css.lastIndexOf('@media (max-width: 720px) {'));

test('mobile map surface follows the full image instead of letterboxing a fixed-height stage', () => {
  assert.match(mobile, /workspace-map-stage:has\(> img\) \{ height: auto !important; min-height: 0/);
  assert.match(mobile, /workspace-map-stage > img \{ position: relative; display: block; inset: auto; width: 100%; height: auto/);
  assert.match(mobile, /workspace-map-panel:has\(> \.workspace-battle-banner\) \.workspace-map-canvas \{ height: auto; min-height: 0/);
  assert.ok(!mobile.includes('object-fit: cover'));
});

test('battle banner has its own row and overlays still share the image surface', () => {
  assert.match(mobile, /workspace-map-panel:has\(> \.workspace-battle-banner\) \{ min-height: 0; grid-template-rows: auto auto auto auto/);
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.ok(source.includes('left: `${token.longitude}%`, top: `${token.latitude}%`'));
});
