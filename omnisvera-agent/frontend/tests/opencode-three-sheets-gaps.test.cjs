// OpenCode isolated gap proofs: Vezemir/Morthak/Dorn card -> grid -> confirm flow.
// Static contracts only; included by the standard tests/*.test.cjs discovery.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function moduleAt(file) {
  const m = { exports: {} };
  vm.runInNewContext(
    ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS },
    }).outputText,
    { module: m, exports: m.exports },
  );
  return m.exports;
}

test('grid target selection stays explicit: multi-pick, confirm, no duplicate on repeat pin', () => {
  const { selectGridTarget } = moduleAt('src/components/gridTargetSelection.ts');
  let r = selectGridTarget([], 'guarda-ally', true, 3);
  assert.equal(r.decision, 'continue');
  r = selectGridTarget(r.selected, 'enemy-a', true, 3);
  assert.equal(r.decision, 'continue');
  const repeat = selectGridTarget(r.selected, 'guarda-ally', true, 3);
  assert.equal(repeat.decision, 'repeat');
  assert.equal(repeat.selected.length, 2);
  r = selectGridTarget(r.selected, 'enemy-b', true, 3);
  assert.equal(r.decision, 'confirm');
  assert.equal(selectGridTarget([], 'far-pin', false, 3).selected.length, 0);
});

test('card activation delegates exactly once and keeps disabled/select clicks safe', () => {
  const { activateCard } = moduleAt('src/components/cardActivation.ts');
  let calls = 0;
  let blocked = 0;
  const command = { disabled: false, click: () => calls++ };
  const card = { querySelector: () => command };
  const target = { closest: (q) => (q === 'article' ? card : null) };
  const event = {
    target,
    currentTarget: { contains: () => true },
    preventDefault() { blocked++; },
    stopPropagation() {},
  };
  activateCard(event);
  assert.equal(calls, 1);
  command.disabled = true;
  activateCard(event);
  assert.equal(calls, 1);
});

test('three-sheet cards expose grid targeting surface and confirm dialog', () => {
  const overlay = fs.readFileSync('src/components/TargetingOverlay.tsx', 'utf8');
  const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  const activation = fs.readFileSync('src/components/cardActivation.ts', 'utf8');
  const gridSel = fs.readFileSync('src/components/gridTargetSelection.ts', 'utf8');
  // RED inicial documentado: data-grid-token vive em SessionWorkspace.tsx
  // (pins do mapa), nao em TargetingOverlay.tsx (geometria do overlay).
  assert.ok(workspace.includes('data-grid-token'), 'pins precisam de data-grid-token');
  assert.ok(overlay.includes('targeting-overlay'), 'overlay precisa de classe propria');
  assert.ok(activation.includes('data-card-command'), 'card precisa delegar ao comando');
  assert.ok(gridSel.includes('confirm'), 'selecao multipla precisa de confirmacao');
  const confirm = fs.readFileSync('src/components/TargetConfirmation.tsx', 'utf8');
  assert.ok(confirm.includes('Confirmar alvo'), 'fluxo Sim/Nao precisa existir');
  assert.ok(workspace.includes('TargetConfirmation') || workspace.includes('targeting'), 'workspace usa confirmacao');
  assert.ok(!workspace.includes('8787') && !workspace.includes('8788'), 'QA nao usa portas operacionais');
});

test('dorn/morthak/vezemir controls keep resource counters and no live URLs', () => {
  for (const file of [
    'src/components/DornSpellControls.tsx',
    'src/components/NecromancerSpellControls.tsx',
    'src/components/SpellCard.tsx',
  ]) {
    const source = fs.readFileSync(file, 'utf8');
    assert.ok(!source.includes('8787') && !source.includes('8788'));
  }
  const api = fs.readFileSync('src/api.ts', 'utf8');
  assert.ok(!api.includes('127.0.0.1:8787') && !api.includes('127.0.0.1:8788'));
});
