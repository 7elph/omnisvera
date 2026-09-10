const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');

function moduleFor(file, dependencies = {}) {
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src', file), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: name => dependencies[name] || {}, console });
  return module.exports;
}

test('new pins avoid overlap with occupied map coordinates', () => {
  const { nextPinPosition } = moduleFor('components/pinPlacement.ts');
  const tokens = [];
  for (let n = 0; n < 20; n++) {
    const next = nextPinPosition(tokens);
    assert.ok(!tokens.some(t => Math.abs(t.latitude-next.latitude) < 5 && Math.abs(t.longitude-next.longitude) < 5));
    tokens.push(next);
  }
});

test('location form uses ready catalog, real pin endpoint, map and double-submit lock', async () => {
  const slots = [], pending = []; let cursor = 0, tree;
  const calls = [];
  const react = {
    useState(initial) { const i=cursor++; if (!(i in slots)) slots[i]=initial; return [slots[i], value => slots[i]=typeof value==='function'?value(slots[i]):value]; },
    useRef(initial) { const i=cursor++; return slots[i]??={current:initial}; },
    useEffect(fn,deps) { const i=cursor++; if(!slots[i]) { slots[i]=deps; pending.push(fn); } },
  };
  const jsx=(type,props)=>({type,props:props||{}});
  const component = moduleFor('components/LocationQuickPin.tsx', {
    react, 'react/jsx-runtime': { jsx, jsxs:jsx },
    '../companionIconCatalog': { COMPANION_ICON_CATALOG: [{id:'nimalis',label:'Nimalis',category:'map',path:'map/nimalis.png'}] },
    './pinPlacement': moduleFor('components/pinPlacement.ts'),
    '../api': { listWorldLocations:async()=>[], mediaUrlFromVaultPath:x=>x, createWorkspaceToken:async payload=>{calls.push(payload);return payload;} },
  }).default;
  function render() { cursor=0; tree=component({mapId:'official:nimalis',tokens:[],onChange:async()=>{}}); while(pending.length) pending.shift()(); }
  const walk=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(walk):[n,...walk(n.props.children)];
  render(); await new Promise(setImmediate); render();
  walk(tree).find(n=>n.type==='select').props.onChange({target:{value:'nimalis'}}); render();
  const submit=walk(tree).find(n=>n.type==='form').props.onSubmit;
  await Promise.all([submit({preventDefault(){}}),submit({preventDefault(){}})]);
  assert.equal(calls.length,1);
  assert.equal(calls[0].token_type,'location');
  assert.equal(calls[0].map_id,'official:nimalis');
  assert.equal(calls[0].image_path,'map/nimalis.png');
  assert.equal(calls[0].visible_to_players,false);
});

test('table controls keep master combat separate from sheets and use table roll mode', () => {
  const source=fs.readFileSync(path.join(__dirname,'../src/pages/SessionWorkspace.tsx'),'utf8');
  assert.ok(source.includes('ref={combatPanelRef}'));
  assert.equal(source.split('<summary className="workspace-action-card"><b aria-hidden="true">').length - 1, 4);
  assert.equal((source.match(/<span>COMBATE<\/span>/g)||[]).length, 1);
  assert.ok(!source.includes('<strong>Combate</strong>'));
  assert.ok(!source.includes('<strong>Itens e loot</strong>'));
  assert.ok(!source.includes('<strong>Mapa e criaturas</strong>'));
  assert.ok(!source.includes('<strong>Preparar cena</strong>'));
  assert.ok(source.includes('<span>EDIÇÃO DO MESTRE</span>'));
  assert.ok(source.includes('<span>ASSETS IA</span>'));
  assert.ok(!source.includes('setAttackRollModeById'));
  assert.ok(!source.includes('Modo de rolagem de'));
  assert.ok(source.includes('item.source_type === "combat_action"'));
  const items=source.indexOf('ref={itemToolsRef}');
  const loot=source.indexOf('workspace-loot-resolutions',items);
  const editor=source.indexOf('ref={gmEditorRef}',items);
  assert.ok(items < loot && loot < editor);
  for(const step of ['1 · Identificar item','2 · Imagem (opcional)','3 · Regras (opcional)','4 · Conferir']) assert.ok(source.includes(step));
  assert.ok(!source.includes('open={!itemDraft.name.trim()}'));
});

test('player can follow active combat map without GM editing controls', () => {
  const state={round:1,version:0,effects:[],encounter:{active:true,title:'Combate',map_id:'official:nimalis',participants:[]}};
  let index=0, followed;
  const jsx=(type,props)=>({type,props:props||{}});
  const Component=moduleFor('components/CombatEncounterPanel.tsx',{
    react:{useState:value=>[index++===0?state:value,()=>{}],useRef:value=>({current:value}),useEffect:()=>{}},
    'react/jsx-runtime':{jsx,jsxs:jsx},
  }).default;
  const tree=Component({mode:'player',mapId:'dungeon',characters:[],tokens:[],onChange:async()=>{},onFollowMap:id=>followed=id});
  const walk=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(walk):[n,...walk(n.props.children)];
  const buttons=walk(tree).filter(n=>n.type==='button');
  assert.deepEqual(buttons.map(n=>n.props.children),['Ir ao mapa do combate']);
  buttons[0].props.onClick();
  assert.equal(followed,'official:nimalis');
});
