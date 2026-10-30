const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const panel = fs.readFileSync('src/pages/MasterAssetPanel.tsx', 'utf8');
const form = fs.readFileSync('src/components/AssetAdjustmentForm.tsx', 'utf8');
test('official is default, 4B explicit test; generate and edit share chosen mode', () => {
  assert.match(panel, /useState<'official' \| 'test'>\('official'\)/);
  assert.match(panel, /Klein 9B \+ fallback ZeroGPU/);
  assert.match(panel, /Klein 4B \(sem fallback\)/);
  assert.match(panel, /generation_mode: generationMode/);
  assert.equal((panel.match(/generationMode=\{generationMode\}/g) || []).length, 2);
  assert.match(form, /generation_mode: generationMode/);
  assert.match(form, /parentJobId, category, generationMode/);
});
test('actual fallback displayed, independent quota and reference transfer disclosed', () => {
  assert.match(panel, /Fallback usado: Hugging Face ZeroGPU/);
  assert.match(panel, /não segue o relógio do Cloudflare/);
  assert.match(form, /referência e o pedido serão enviados/);
});
