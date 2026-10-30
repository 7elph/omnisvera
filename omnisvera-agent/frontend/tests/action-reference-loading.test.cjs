const { test } = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), ts = require('typescript');
const tick = () => new Promise(resolve => setImmediate(resolve));
function load(file, imports = {}) {
  const module = { exports: {} };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText, { module, exports: module.exports, require: id => imports[id] || {}, console });
  return module.exports;
}
function harness(api) {
  let state = [], effects = [], pending = [], cursor = 0, tree, writes = 0;
  const hooks = {
    useState(initial) { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], v => { writes++; state[i] = typeof v === 'function' ? v(state[i]) : v; }]; },
    useEffect(fn, deps) { const i = cursor++; const old = effects[i]; if (!old || deps.some((v,j) => v !== old.deps[j])) pending.push(() => { old?.cleanup?.(); effects[i] = { deps, cleanup: fn() }; }); },
  };
  const jsx = (type, props) => ({ type, props: props || {} });
  const Component = load('src/components/CharacterActionReference.tsx', { react: hooks,
    'react/jsx-runtime': { jsx, jsxs: jsx }, '../api': { ...api, mediaUrlFromVaultPath: p => p || '' },
    '../actionReference': load('src/actionReference.ts'), '../companionIconCatalog': { iconPathForItem: () => '' } }).default;
  const props = { characters: [{ id: 'raziel', name: 'Raziel' }, { id: 'dorn7', name: 'Dorn' }], initialId: 'raziel' };
  function nodes(node = tree) { return [node, ...[node?.props?.children].flat(Infinity).filter(n => n && typeof n === 'object').flatMap(n => nodes(n))]; }
  return { render() { cursor = 0; tree = Component(props); pending.splice(0).forEach(fn => fn()); }, nodes,
    select(id) { nodes().find(n => n.props['aria-label'] === 'Personagem da cola de ações').props.onChange({ target: { value: id } }); },
    unmount() { effects.forEach(e => e?.cleanup?.()); }, writes: () => writes };
}
const sheet = id => ({ definition: { id, session_abilities: [{ id: 'skill', name: id, kind: 'ability' }] }, state: {}, inventory: [] });
const manifest = id => ({ character_id: id, actions: [{ ref: `technique:${id}:skill`, label: id, automation_scope: 'native', availability: { state: 'available', reason: 'Native' }, limitations: [] }] });
test('late manifest and sheet cannot replace a newly selected actor; reads request the non-mutating projection', async () => {
  const resolve = {}, reads = [];
  const h = harness({ getPlayableCharacter: (id, readOnly) => { reads.push([id, readOnly]); return Promise.resolve(sheet(id)); },
    getCharacterActionManifest: id => new Promise(r => { resolve[id] = r; }) });
  h.render(); h.select('dorn7'); h.render(); resolve.dorn7(manifest('dorn7')); await tick(); h.render();
  resolve.raziel(manifest('raziel')); await tick(); h.render();
  const details = h.nodes().filter(n => n.props.title);
  assert.ok(details.some(n => n.props.title === 'dorn7')); assert.ok(!details.some(n => n.props.title === 'raziel'));
  assert.ok(reads.every(([, readOnly]) => readOnly === true)); h.unmount();
});
test('manifest failure keeps descriptions with unverified status and unmount ignores pending results', async () => {
  const h = harness({ getPlayableCharacter: async id => sheet(id), getCharacterActionManifest: async () => { throw Error('offline'); } });
  h.render(); await tick(); h.render();
  assert.ok(h.nodes().some(n => n.props.role === 'status' && n.props.children.includes('Não foi possível')));
  assert.ok(JSON.stringify(h.nodes()).includes('Automação não verificada')); h.unmount();
  let finish; const pending = harness({ getPlayableCharacter: async id => sheet(id), getCharacterActionManifest: () => new Promise(r => { finish = r; }) });
  pending.render(); pending.unmount(); const before = pending.writes(); finish(manifest('raziel')); await tick();
  assert.equal(pending.writes(), before);
});
