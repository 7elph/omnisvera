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
const model = () => load('src/scenePreparation.ts', { './spatialGrid': load('src/spatialGrid.ts') });
const assets = ['map', 'pin', 'npc', 'character', 'creature', 'threat', 'clue', 'text', 'image', 'object', 'objective', 'exit', 'environmental_effect', 'future_kind']
  .map((kind, i) => ({ id: `7:element:${i}`, kind, title: kind }));

test('six context layouts group existing elements without duplicating or fabricating assets', () => {
  const m = model();
  assert.equal(m.sceneContexts.length, 6);
  for (const context of m.sceneContexts) {
    const groups = m.contextSections(context.id, assets);
    const shown = groups.flatMap(group => group.assets);
    assert.equal(new Set(shown.map(a => a.id)).size, shown.length);
    assert.ok(shown.every(asset => assets.includes(asset)), context.id);
    assert.equal(m.contextSections(context.id, []).length, 0);
  }
  assert.ok(m.contextSections('combat', assets).some(g => g.assets.some(a => a.kind === 'creature')));
  assert.ok(m.contextSections('conversation', assets).some(g => g.assets.some(a => a.kind === 'npc')));
  assert.ok(m.contextSections('investigation', assets).some(g => g.assets.some(a => a.kind === 'clue')));
  assert.ok(m.contextSections('commerce', assets).some(g => g.assets.some(a => a.kind === 'object')));
});

test('context switches cannot reintroduce private assets into a public projection', () => {
  const m = model();
  const scene = { id: 7, status: 'draft', visibility: 'gm', private_notes: 'SECRET', participants: [], elements: [] };
  for (const context of m.sceneContexts)
    assert.equal(m.contextSections(context.id, m.sceneAssets(scene, null, true)).length, 0);
});

test('preparation sequence follows native order_index regardless of draft status and preserves the input', () => {
  const scenes = [{ id: 2, order_index: 2, status: 'draft', title: 'Second' }, { id: 1, order_index: 1, status: 'active', title: 'First' }];
  assert.equal(model().filterPreparations(scenes, '', 'all', 'all').map(s => s.id).join(','), '1,2');
  assert.equal(scenes.map(s => s.id).join(','), '2,1');
});

function harness() {
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
    '../scenePreparation': model(), './LogicalGrid': { LogicalGrid() {} }, './scenePreparation.css': {} }).ScenePreparationViewer;
  function nodes(node = tree) { return [node, ...[node?.props?.children].flat(Infinity).filter(n => n && typeof n === 'object').flatMap(n => nodes(n))]; }
  return { render(props) { cursor = 0; tree = component(props); pending.splice(0).forEach(fn => fn()); }, nodes };
}

test('contexts and the library only change local presentation; map opens on demand and publication keeps selection', () => {
  const h = harness(), calls = [];
  const scene = { id: 7, title: 'Preparation', status: 'draft', visibility: 'gm', map_id: 'one',
    public_description: 'Opening', participants: [], elements: [{ id: 1, element_type: 'clue', title: 'Clue', visibility: 'gm' }] };
  const props = { scene, workspace: { map: { id: 'one', title: 'Map' }, tokens: [] }, loading: false, error: '', onRetry() {}, onPublish: (...args) => calls.push(args) };
  h.render(props);
  assert.equal(h.nodes().filter(n => n.props.className === 'scene-map-preview').length, 0);
  const mapCard = h.nodes().find(n => n.type === 'article' && n.props['data-asset-kind'] === 'map');
  assert.ok(mapCard, 'Map has a compact card');
  const check = h.nodes(mapCard).find(n => n.type === 'input');
  check.props.onChange({ target: { checked: true } }); h.render(props);
  for (const context of model().sceneContexts) {
    h.nodes().find(n => n.type === 'button' && n.props['aria-label'] === `Contexto: ${context.label}`).props.onClick();
    h.render(props);
    assert.ok(h.nodes().some(n => n.props['data-scene-context'] === context.id));
    assert.ok(h.nodes().some(n => n.type === 'button' && n.props.children === 'Levar seleção à Mesa' && n.props.disabled === false));
  }
  assert.deepEqual(calls, []);
  const library = h.nodes().find(n => n.type === 'button' && n.props['aria-controls'] === 'scene-element-library');
  library.props.onClick(); h.render(props);
  assert.ok(h.nodes().some(n => n.props.id === 'scene-element-library'));
  const inspectMap = h.nodes().find(n => n.type === 'article' && n.props['data-asset-kind'] === 'map');
  h.nodes(inspectMap).find(n => n.props.className === 'scene-asset-inspect').props.onClick(); h.render(props);
  assert.ok(h.nodes().some(n => typeof n.type === 'function' && n.type.name === 'AssetInspector' && n.props.asset.kind === 'map'));
  assert.deepEqual(calls, []);
});
