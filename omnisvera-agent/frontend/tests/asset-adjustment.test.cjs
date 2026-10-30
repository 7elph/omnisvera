const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const form = fs.readFileSync('src/components/AssetAdjustmentForm.tsx', 'utf8');
const panel = fs.readFileSync('src/pages/MasterAssetPanel.tsx', 'utf8');
test('directed edits send current image, instruction and stable request id without autoapproval', () => {
  assert.match(form, /image_path: imagePath/);
  assert.match(form, /instruction: instruction.trim\(\)/);
  assert.match(form, /request_id: request.current.id/);
  assert.match(form, /if \(lock.current/);
  assert.match(form, /request.current\?\.key !== key/);
  assert.doesNotMatch(form, /\/approve/);
});
test('master panel offers library edits and before-after comparison using protected previews', () => {
  assert.match(panel, /Ajustar imagem da biblioteca/);
  assert.match(panel, /Antes · preservada/);
  assert.match(panel, /Depois · nova versão/);
  assert.match(panel, /base-preview\?token=/);
  assert.match(form, /maxLength=\{2000\}/);
  assert.match(form, /Gerar nova versão/);
});
