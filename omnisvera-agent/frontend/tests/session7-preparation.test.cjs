const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const esbuild = require('esbuild');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function component(name) {
  const bundle = esbuild.buildSync({ entryPoints: [`src/components/${name}.tsx`], bundle: true, write: false, platform: 'node', format: 'cjs', jsx: 'automatic', external: ['react', 'react-dom'], define: { 'import.meta.env': '{}' } });
  const module = { exports: {} };
  vm.runInNewContext(bundle.outputFiles[0].text, { module, exports: module.exports, require, console, URL, URLSearchParams, localStorage: { getItem: () => null } });
  return module.exports.default;
}

test('S7 GM reference shows gated clues and encounter is disabled before opening', () => {
  const html = renderToStaticMarkup(React.createElement(component('Session7PreparationPanel'), { scene: { request_id: 'session7-scene-06', status: 'draft', private_notes: 'Segredo do Mestre', elements: [{ id: 1, title: 'Pista', private_description: 'INT 12; falha preserva alternativa.' }] } }));
  assert.doesNotMatch(html, /Segredo do Mestre/); // Host already renders native private notes.
  assert.match(html, /INT 12/);
  assert.match(html, /<button disabled=""/);
  assert.match(html, /Incluir Dorn como aliado/);
  assert.match(html, /Iniciar Sessão 7/);
  assert.match(html, /Encerrar Sessão 7/);
  const source = fs.readFileSync('src/pages/ScenePanel.tsx', 'utf8');
  assert.ok(source.includes("mode === 'gm' && scene.request_id?.startsWith('session7-')"));
});

test('prepared encounter excludes Varkh and reserve and uses native command', () => {
  const source = fs.readFileSync('src/components/Session7PreparationPanel.tsx', 'utf8');
  assert.ok(source.includes("['vezemir', 'morthak', 'raziel'"));
  assert.ok(!source.includes('varkh'));
  assert.ok(source.includes("!t.name.includes('reserva')"));
  assert.ok(source.includes('sendCombatEffectCommand'));
  assert.ok(source.includes('combat.encounter?.active'));
  assert.ok(source.includes('updateGameSessionStatus(scene.session_id, status)'));
  assert.ok(source.includes('Encerre o combate salvo primeiro'));
});

test('Dorn diagnostic uses current native turn budget and does not expose lore', () => {
  const html = renderToStaticMarkup(React.createElement(component('DornDiagnosticControl'), { combat: { version: 1, encounter: { active: true, turn_index: 0, participants: [{ target_type: 'character', target_id: 'raziel' }] } }, onChange: async () => {} }));
  assert.match(html, /Diagnóstico da Unidade/);
  assert.match(html, /<button disabled=""/);
  assert.ok(fs.readFileSync('src/components/DornProtocolControls.tsx', 'utf8').includes('<DornDiagnosticControl'));
});
