const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function load(file, imports = {}) {
  const m = { exports: {} };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText, { module: m, exports: m.exports, require: id => {
    if (id in imports) return imports[id]; throw Error(id);
  }, console });
  return m.exports;
}
function model() { return load('src/scenePreparation.ts', { './spatialGrid': load('src/spatialGrid.ts') }); }
const scene = { id: 23, title: 'Sexta · Conclave', location_name: 'Nimalis', status: 'draft', visibility: 'gm',
  image_path: 'cover.jpg', map_id: 'map:one', public_description: 'Abertura', private_notes: 'SEGREDO',
  participants: [{ id: 1, public_label: 'Operador', npc_source: 'monster:one', participant_type: 'creature', visible_to_players: false }],
  elements: [{ id: 2, title: 'Pista oculta', element_type: 'clue', status: 'hidden', visibility: 'gm', private_description: 'MANDANTE' }], checklist: { identity: true } };
const token = { id: 'monster:one', name: 'Operador', map_id: 'map:one', token_type: 'monster', image_path: 'operator.jpg',
  visible_to_players: false, latitude: 10, longitude: 20, conditions: [] };
const workspace = { map: { id: 'map:one', title: 'Mapa', image_path: 'map.jpg', visible_to_players: true }, tokens: [token] };
test('private preparation projects existing texts, linked creature image, elements and pins', () => {
  const assets = model().sceneAssets(scene, workspace, false);
  assert.ok(assets.some(a => a.kind === 'text' && a.text === 'SEGREDO'));
  assert.ok(assets.some(a => a.kind === 'creature' && a.image === 'operator.jpg'));
  assert.ok(assets.some(a => a.kind === 'clue' && a.privateText === 'MANDANTE'));
  assert.equal(assets.filter(a => a.kind === 'pin').length, 1);
});
test('public preview of a draft cannot expose its cover, texts, roster or pins', () => {
  assert.equal(model().sceneAssets(scene, workspace, true).length, 0);
});
test('NPC cards use their existing descriptions but do not project a private directory record', () => {
  const s = { ...scene, status: 'active', visibility: 'table', participants: [{ id: 1, public_label: 'Contato',
    participant_type: 'npc', visible_to_players: true, npc: { visible_to_players: false,
      public_description: 'CADASTRO RESERVADO', private_description: 'SEGREDO NPC', portrait_path: 'private.jpg' } }] };
  const assets = model().sceneAssets(s, null, false);
  assert.ok(assets.some(a => a.privateText?.includes('SEGREDO NPC')));
  assert.doesNotMatch(JSON.stringify(model().sceneAssets(s, null, true)), /CADASTRO RESERVADO|SEGREDO NPC|private.jpg/);
});
test('public preview keeps only published data and filters hidden and fog-covered pins', () => {
  const published = { ...scene, status: 'active', visibility: 'table', elements: [
    ...scene.elements, { id: 3, title: 'Encontrada', element_type: 'clue', visibility: 'table', status: 'revealed', public_description: 'DADO', private_description: 'OUTRO SEGREDO' }],
    participants: [{ id: 2, participant_type: 'npc', public_label: 'NPC público', visible_to_players: true, private_status: 'NÃO MOSTRAR' }] };
  const visible = { ...token, id: 'visible', visible_to_players: true, sheet: { notes: 'SEGREDO DA FICHA' } };
  const fogged = { ...visible, id: 'fogged', longitude: 50, latitude: 50 };
  const ws = { ...workspace, tokens: [token, visible, fogged], fog: { exploration: {
    enabled: true, columns: 32, rows: 24, revealed_cells: [], mist_density: { '16:12': 1 } } } };
  const assets = model().sceneAssets(published, ws, true);
  assert.equal(assets.filter(a => a.kind === 'pin').length, 1);
  assert.ok(assets.some(a => a.title === 'Encontrada'));
  assert.doesNotMatch(JSON.stringify(assets), /SEGREDO|MANDANTE|NÃO MOSTRAR|Pista oculta/);
});
test('wrong map and foreign pins never bleed into a selected scene', () => {
  assert.equal(model().sceneAssets(scene, { ...workspace, map: { ...workspace.map, id: 'another' } }, false).filter(a => a.kind === 'pin').length, 0);
  assert.equal(model().sceneAssets(scene, { ...workspace, tokens: [{ ...token, map_id: 'other' }] }, false).filter(a => a.kind === 'pin').length, 0);
});
test('preview viewport has a fixed responsive height, not only a growing max-height', () => {
  const css = fs.readFileSync('src/components/scenePreparation.css', 'utf8');
  const rules = [...css.matchAll(/\.scene-map-preview-viewport\s*\{([^}]+)\}/g)];
  assert.match(rules[0][1], /(?:^|;)\s*height:\s*min\(58dvh, 580px\)/);
  assert.match(rules.at(-1)[1], /(?:^|;)\s*height:\s*48dvh/);
});

test('logical center overrides screen coordinates and remains independent of zoom', () => {
  const p = model().scenePinPoint({ ...token, grid_position: { map_id: 'map:one', cell_x: 8, cell_y: 12, footprint_w: 1, footprint_h: 1 } },
    { map_id: 'map:one', cols: 32, rows: 24, origin_x: 0, origin_y: 0 });
  assert.equal(p.longitude, 26.5625); assert.equal(p.latitude, 52.083333333333336);
  assert.equal(model().scenePinPoint(token).longitude, 20);
});
test('public fog honors native persisted coordinates even when a legacy logical cell differs', () => {
  const ws = { ...workspace, map: { ...workspace.map, grid: { map_id: 'map:one', cols: 32, rows: 24, origin_x: 0, origin_y: 0 } },
    fog: { exploration: { enabled: true, columns: 32, rows: 24, revealed_cells: [], mist_density: { '16:12': 1 } } } };
  assert.equal(model().pinInPublicView({ ...token, visible_to_players: true, latitude: 50, longitude: 50,
    grid_position: { map_id: 'map:one', cell_x: 8, cell_y: 12, footprint_w: 1, footprint_h: 1 } }, ws), false);
});
test('library searches accent-insensitively and filters session/status without mutating order', () => {
  const original = [scene, { ...scene, id: 24, status: 'paused', session_id: 7, title: 'Maré Baixa' }];
  assert.equal(model().filterPreparations(original, 'mare', 'paused', '7')[0].id, 24);
  assert.equal(model().filterPreparations(original, '', 'all', 'unassigned').length, 1);
  assert.equal(original[0].id, 23);
});
test('gallery integration is GM admin only and no longer mounts the live workspace beside Scenes', () => {
  const source = fs.readFileSync('src/pages/ScenePanel.tsx', 'utf8');
  assert.match(source, /privateAdmin && <ScenePreparationLibrary/);
  assert.match(source, /privateAdmin && <ScenePreparationViewer/);
  const app = fs.readFileSync('src/App.tsx', 'utf8');
  assert.match(app, /page !== "scenes" && <SessionWorkspace/);
  const view = fs.readFileSync('src/components/ScenePreparationGallery.tsx', 'utf8');
  assert.doesNotMatch(view, /publishScene|updateScene|moveWorkspaceToken|configureMapGrid|dangerouslySetInnerHTML/);
  assert.match(view, /showModal/); assert.match(view, /onCancel/); assert.match(view, /loading="lazy"/);
});

function harness(exportName) {
  let state = [], effects = [], pending = [], cursor = 0, tree;
  const hooks = {
    useState(initial) { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], v => { state[i] = typeof v === 'function' ? v(state[i]) : v; }]; },
    useRef(initial) { const i = cursor++; if (!(i in state)) state[i] = { current: initial }; return state[i]; },
    useMemo(fn) { return fn(); },
    useEffect(fn, deps) { const i = cursor++; const old = effects[i]; if (!old || deps.some((v,j) => v !== old.deps[j])) pending.push(() => { old?.cleanup?.(); effects[i] = { deps, cleanup: fn() }; }); },
  };
  const jsx = (type, props) => ({ type, props: props || {} });
  const component = load('src/components/ScenePreparationGallery.tsx', { react: hooks,
    'react/jsx-runtime': { jsx, jsxs: jsx }, '../api': { mediaUrlFromVaultPath: p => p || '' },
    '../scenePreparation': model(), './LogicalGrid': { LogicalGrid() {} }, './scenePreparation.css': {} })[exportName];
  function nodes(node = tree) { return [node, ...[node?.props?.children].flat(Infinity).filter(n => n && typeof n === 'object').flatMap(n => nodes(n))]; }
  return {
    render(props) { cursor = 0; tree = component(props); pending.splice(0).forEach(fn => fn()); return tree; }, nodes,
    button(text) { return nodes().find(n => n.type === 'button' && n.props.children === text); },
  };
}
test('library card opens a preparation without publishing, search handles empty results', () => {
  const selected = [], h = harness('ScenePreparationLibrary');
  const props = { scenes: [scene], maps: [], sessions: [], selectedId: null, onSelect: id => selected.push(id), onCreate() {}, onRefresh() {} };
  h.render(props); h.nodes().find(n => n.props.className?.includes('scene-library-card')).props.onClick();
  assert.deepEqual(selected, [23]);
  h.nodes().find(n => n.type === 'input').props.onChange({ target: { value: 'inexistente' } }); h.render(props);
  assert.ok(h.nodes().some(n => n.props.children === 'Nenhuma preparação neste filtro.'));
});
test('viewer filters cards, opens read-only inspector and closes private detail on public toggle', () => {
  const h = harness('ScenePreparationViewer'), props = { scene, workspace, loading: false, error: '', onRetry() {} };
  h.render(props);
  const card = h.nodes().find(n => n.props.className?.includes('scene-asset-inspect') && n.type === 'button');
  card.props.onClick(); h.render(props);
  assert.ok(h.nodes().some(n => typeof n.type === 'function' && n.type.name === 'AssetInspector'));
  h.button('Conteúdo público').props.onClick(); h.render(props);
  assert.equal(h.nodes().filter(n => typeof n.type === 'function' && n.type.name === 'AssetInspector').length, 0);
  assert.ok(h.nodes().some(n => n.props.role === 'status' && n.props.children.includes('ainda não foi publicado')));
});
test('preview map zoom is bounded and uses percentage geometry without move handlers', () => {
  const css = fs.readFileSync('src/components/scenePreparation.css', 'utf8');
  assert.match(css, /\.scene-map-preview-viewport\s*\{[^}]*max-height:[^}]*overflow: auto/);
  assert.match(css, /@media \(max-width: 680px\)/);
  const source = fs.readFileSync('src/components/ScenePreparationGallery.tsx', 'utf8');
  assert.match(source, /LogicalGrid grid=\{map.grid\}/);
  assert.doesNotMatch(source, /onPointerMove|onDrag|selectWorkspaceMap|requestAnimationFrame/);
});

function pageHarness(overrides = {}) {
  let state = [], effects = [], pending = [], cursor = 0, tree, writes = 0;
  const hooks = {
    useState(initial) { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], v => { writes++; state[i] = typeof v === 'function' ? v(state[i]) : v; }]; },
    useRef(initial) { const i = cursor++; if (!(i in state)) state[i] = { current: initial }; return state[i]; },
    useMemo(fn) { return fn(); },
    useEffect(fn, deps) { const i = cursor++; const old = effects[i]; if (!old || deps.some((v,j) => v !== old.deps[j])) pending.push(() => { old?.cleanup?.(); effects[i] = { deps, cleanup: fn() }; }); },
  };
  const second = { ...scene, id: 24, map_id: 'map:two', title: 'Outra preparação' };
  const api = { getActiveScene: async () => null, listScenes: async () => [scene, second], listGameSessions: async () => [],
    listWorkspaceMaps: async () => [], listPlayableCharacters: async () => [], listNpcs: async () => [],
    mediaUrlFromVaultPath: p => p || '', ...overrides };
  const jsx = (type, props) => ({ type, props: props || {} });
  function Library() {} function Viewer() {}
  const m = { exports: {} };
  const imports = { react: hooks, 'react/jsx-runtime': { jsx, jsxs: jsx }, '../api': api,
    '../components/ScenePreparationGallery': { ScenePreparationLibrary: Library, ScenePreparationViewer: Viewer } };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/pages/ScenePanel.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX },
  }).outputText, { module: m, exports: m.exports, require: id => imports[id] || { default() {} }, console, Error,
    localStorage: { getItem: () => null, setItem() {} }, CustomEvent: class {},
    document: { getElementById: () => null }, window: { dispatchEvent() {}, addEventListener() {}, removeEventListener() {}, requestAnimationFrame: fn => fn() } });
  function nodes(node = tree) { return [node, ...[node?.props?.children].flat(Infinity).filter(n => n && typeof n === 'object').flatMap(n => nodes(n))]; }
  return { render() { cursor = 0; tree = m.exports.default({ mode: 'gm', surface: 'admin' }); pending.splice(0).forEach(fn => fn()); },
    library: () => nodes().find(n => n.type === Library)?.props, viewer: () => nodes().find(n => n.type === Viewer)?.props,
    unmount() { effects.forEach(e => e?.cleanup?.()); }, writes: () => writes };
}
const tick = () => new Promise(resolve => setImmediate(resolve));
test('late workspace response cannot replace the selected preparation map', async () => {
  const resolve = {}, calls = [];
  const h = pageHarness({ getSessionWorkspace: id => { calls.push(id); return new Promise(r => { resolve[id] = r; }); } });
  h.render(); await tick(); h.render(); assert.equal(calls[0], 'map:one');
  h.library().onSelect(24); h.render();
  resolve['map:two']({ map: { id: 'map:two' }, tokens: [] }); await tick(); h.render();
  resolve['map:one'](workspace); await tick(); h.render();
  assert.equal(h.viewer().scene.id, 24); assert.equal(h.viewer().workspace.map.id, 'map:two'); h.unmount();
});
test('map request failure is visible and retry reads only the selected map', async () => {
  let attempts = 0;
  const h = pageHarness({ getSessionWorkspace: async id => { assert.equal(id, 'map:one'); if (++attempts === 1) throw Error('conexão interrompida'); return workspace; } });
  h.render(); await tick(); h.render(); await tick(); h.render();
  assert.match(h.viewer().error, /conexão interrompida/);
  h.viewer().onRetry(); h.render(); await tick(); h.render();
  assert.equal(attempts, 2); assert.equal(h.viewer().workspace.map.id, 'map:one'); h.unmount();
});
test('unmount discards pending map data and a missing map does not show fallback pins', async () => {
  let resolve;
  const h = pageHarness({ getSessionWorkspace: () => new Promise(r => { resolve = r; }) });
  h.render(); await tick(); h.render(); h.unmount(); const before = h.writes(); resolve(workspace); await tick();
  assert.equal(h.writes(), before);
  const bad = pageHarness({ getSessionWorkspace: async () => ({ ...workspace, map: { id: 'wrong' } }) });
  bad.render(); await tick(); bad.render(); await tick(); bad.render();
  assert.equal(bad.viewer().workspace, null); assert.match(bad.viewer().error, /não está disponível/); bad.unmount();
});
test('an old library refresh cannot undo an explicit card selection', async () => {
  let reads = 0, resolve;
  const second = { ...scene, id: 24, title: 'Segunda', map_id: 'map:two' };
  const h = pageHarness({ listScenes: () => ++reads === 1 ? Promise.resolve([scene, second]) : new Promise(r => { resolve = r; }),
    getSessionWorkspace: async id => ({ map: { id }, tokens: [] }) });
  h.render(); await tick(); h.render();
  h.library().onRefresh(); h.library().onSelect(24); h.render();
  resolve([scene]); await tick(); h.render();
  assert.equal(h.viewer().scene.id, 24); h.unmount();
});
test('rendered preview uses native grid, percentage footprints and bounded read-only controls', () => {
  const React = require('react'), { renderToStaticMarkup } = require('react-dom/server'), esbuild = require('esbuild');
  const bundle = esbuild.buildSync({ entryPoints: ['src/components/ScenePreparationGallery.tsx'], bundle: true,
    write: false, platform: 'node', format: 'cjs', jsx: 'automatic', define: { 'import.meta.env': '{}' },
    loader: { '.css': 'empty' }, external: ['react', '../api', './api'] });
  const m = { exports: {} };
  vm.runInNewContext(bundle.outputFiles[0].text, { module: m, exports: m.exports,
    require: id => id === '../api' || id === './api' ? { mediaUrlFromVaultPath: p => p || '' } : require(id), console });
  const grid = { map_id: 'map:one', cols: 32, rows: 24, origin_x: 0, origin_y: 0 };
  const ws = { ...workspace, map: { ...workspace.map, grid }, tokens: [{ ...token,
    grid_position: { map_id: 'map:one', cell_x: 8, cell_y: 12, footprint_w: 1, footprint_h: 1 } }] };
  const compact = renderToStaticMarkup(React.createElement(m.exports.ScenePreparationViewer, { scene, workspace: ws, loading: false, error: '', onRetry() {} }));
  assert.match(compact, /scene-map-card/); assert.doesNotMatch(compact, /scene-map-preview-surface|Grid lógico/);
  const html = renderToStaticMarkup(React.createElement(m.exports.SceneMapPreview, { workspace: ws, pins: model().sceneAssets(scene, ws, false).filter(a => a.kind === 'pin'), publicOnly: false, onInspect() {} }));
  assert.match(html, /Grid lógico 32 por 24/); assert.match(html, /width:3\.125%/);
  assert.match(html, /left:26\.5625%/); assert.match(html, /Reduzir prévia/); assert.match(html, /Somente leitura/);
  assert.doesNotMatch(html, /draggable="true"|Mirar|Usar habilidade/);
});
