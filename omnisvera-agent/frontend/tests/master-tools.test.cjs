const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
const heading = fs.readFileSync('src/components/MasterToolHeading.tsx', 'utf8');
const css = fs.readFileSync('src/styles.css', 'utf8');
const vm = require('node:vm');

test('NPC library entry is rendered only inside the Mestre tools, never over sheets', () => {
  assert.equal((source.match(/\{section === 'master' && npcLibraryToggle\}/g) || []).length, 1);
  assert.ok(!source.includes('!gmToolsOpen && npcLibraryToggle'));
  const tools = source.slice(source.indexOf('function renderGmWorkspaceTools('), source.indexOf('function renderGmWorkspaceTools(') + 450);
  assert.ok(tools.includes('if (mode !== "gm" || (section === "master" && !gmToolsOpen)) return null;'));
  const sheetNavigation = source.slice(source.indexOf('<div className="party-status-list">'), source.indexOf('{view === "table" && <aside'));
  assert.ok(sheetNavigation.includes('setNpcLibraryOpen(false); setGmToolsOpen(false);'));
});

test('all Mestre tools reuse compact heading, with collapsible table summary', () => {
  for (const title of ['Assets IA', 'Resumo da mesa', 'Pedir rolagem', 'Descanso geral', 'Combate', 'Itens e loot', 'Edição do Mestre', 'NPCs do Mestre']) {
    assert.ok(source.includes(`title="${title}"`), title);
  }
  assert.match(source, /<details className="workspace-gm-section workspace-table-summary">/);
  assert.match(heading, /workspace-tool-copy/);
  assert.match(css, /\.workspace-master-overview \{ padding: 0; gap: \.3rem; \}/);
});

test('Mestre can explicitly load a sheet while the tools drawer stays open', () => {
  assert.match(source, /aria-label="Ficha para edição do Mestre"/);
  assert.match(source, /Carregar ficha/);
  assert.match(source, /gmEditorIdRef\.current !== selectedIdRef\.current/);
  assert.match(source, /\[selectedId, mode, gmToolsOpen, gmEditorId\]/);
  assert.match(source, /character\.definition\.id === gmEditorId/);
});

test('open GM drawer fetches only the explicitly loaded sheet and preserves its notes', async () => {
  const body = source.slice(source.indexOf('async function loadCharacter()'), source.indexOf('async function loadArchiveItems('));
  const calls = [], sheets = [], notes = [];
  const detail = { definition: { id: 'raziel' }, state: { session_notes: 'fixture notes' } };
  const context = {
    mode: 'gm', characterRequestRef: { current: 0 }, gmToolsOpenRef: { current: true },
    gmEditorIdRef: { current: '' }, selectedIdRef: { current: 'raziel' }, currentModeRef: { current: 'gm' },
    getPlayableCharacter: async id => { calls.push(id); return detail; },
    setError: () => {},
    setCharacter: sheet => sheets.push(sheet), setSessionNotes: note => notes.push(note),
  };
  vm.createContext(context);
  vm.runInContext(body, context);
  await context.loadCharacter();
  assert.equal(calls.length, 0);
  assert.equal(sheets.at(-1), null);
  context.gmEditorIdRef.current = 'raziel';
  await context.loadCharacter();
  assert.deepEqual(calls, ['raziel']);
  assert.equal(sheets.at(-1), detail);
  assert.deepEqual(notes, ['fixture notes']);
});
