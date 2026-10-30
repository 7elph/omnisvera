const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),ts=require('typescript'),vm=require('node:vm');
function load(file,requires={}){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,require:id=>requires[id]||{jsx:(type,props)=>({type,props}),jsxs:(type,props)=>({type,props})}});return m.exports;}
test('map zoom is contained in a bounded mobile scroll viewport, not document height',()=>{
 const css=fs.readFileSync('src/companionTheme.css','utf8');
 assert.match(css,/\.app-shell \.workspace-map-panel > \.workspace-map-canvas[^}]*height: clamp\(260px, 58dvh, 560px\)/s);
 assert.match(css,/\.app-shell \.workspace-map-canvas\.locked[^}]*overflow: auto/);
});
test('native sheet groups are collapsed outside combat, action groups can auto-open',()=>{
 const src=fs.readFileSync('src/components/SheetSection.tsx','utf8');
 assert.match(src,/autoOpen = false/);assert.match(src,/<details/);assert.match(src,/onToggle/);
 const sheet=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');assert.match(sheet,/<SheetSection title="Magias" autoOpen=\{battleActive\}/);
 assert.match(sheet,/workspace-status-under-vitals[\s\S]{0,220}<ActiveEffectIcons/);
 assert.doesNotMatch(fs.readFileSync('src/components/DornConstructDetails.tsx','utf8'),/EFEITOS ATIVOS|fictional_time/);
 assert.doesNotMatch(fs.readFileSync('src/components/DornProtocolControls.tsx','utf8'),/<DornDiagnosticControl/);
});
test('equipment panel renders only persisted equipped items, including custom slots',()=>{
 const jsx=(type,props)=>({type,props}),Loadout=load('src/components/EquipmentLoadout.tsx',{'../api':{mediaUrlFromVaultPath:p=>p},'./SheetDetail':{default:'SheetDetail'},'react/jsx-runtime':{jsx,jsxs:jsx}}).default;
 const item=(title,slot,equipped=true)=>({item_path:title,item_title:title,equipment_slot:slot,equipped,quantity:1,thumbnail:'icon'});
 const node=Loadout({inventory:[item('Grisalma','Corpo a corpo'),item('Grimório','Cinto'),item('Guardado','Mochila',false)]});
 const text=JSON.stringify(node);assert.match(text,/Grisalma/);assert.match(text,/Grimório/);assert.doesNotMatch(text,/Guardado/);
 assert.doesNotMatch(text,/equip_item|onClick/);
});
test('map library groups only explicit titles and preserves exploratory maps without grids',()=>{
 const {mapLibraryGroup}=load('src/components/WorkspaceMapLibrary.tsx');
 assert.equal(mapLibraryGroup({title:'Mapa de Nimalia'}),'Mundos e cidades');
 assert.equal(mapLibraryGroup({title:'Earthropo'}),'Mundos e cidades');
 assert.equal(mapLibraryGroup({title:'S7 · Âncora Partida'}),'Sessão 7');
 assert.equal(mapLibraryGroup({title:'Sessão 12 — Estrada'}),'Sessão 12');
 assert.equal(mapLibraryGroup({title:'Ruínas'}),'Outros mapas');
 assert.ok(!fs.readFileSync('src/components/WorkspaceMapLibrary.tsx','utf8').includes("'Sem grade'"),'The map list does not always include grid metadata: missing is not no-grid');
});
test('sheet sibling keys are namespaced: notes, spells and wallet cannot reconcile as one another',()=>{
 const src=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 for(const prefix of ['notes','spells','wallet'])assert.ok(src.includes('key={`'+prefix+':${'),prefix+' needs its own key namespace');
 assert.ok(!src.includes('<CharacterNotes key={character.definition.id}'));
 assert.ok(!src.includes('<CurrencyCounters key={character.definition.id}'));
});

test('equipment uses full registered character art, not its thumbnail',()=>{
 assert.match(fs.readFileSync('src/companionTheme.css','utf8'),/\.workspace-equipment-loadout \{[^}]*flex: 0 0 auto/,'Desktop scroll panel must not shrink/clamp the equipment card');
 const jsx=(type,props)=>({type,props}),Loadout=load('src/components/EquipmentLoadout.tsx',{'../api':{mediaUrlFromVaultPath:p=>p},'./SheetDetail':{default:'SheetDetail'},'react/jsx-runtime':{jsx,jsxs:jsx}}).default;
 const node=Loadout({inventory:[],cover:'full.png',portrait:'thumbnail.png'});
 const text=JSON.stringify(node);assert.match(text,/workspace-equipment-portrait/);assert.match(text,/full.png/);assert.doesNotMatch(text,/thumbnail.png/);
 assert.match(JSON.stringify(Loadout({inventory:[],portrait:'fallback.png'})),/fallback.png/);
 assert.match(JSON.stringify(Loadout({inventory:[]})),/workspace-equipment-silhouette/);
});

test('Mesa header contains horizontal tools, wallet is summary-only and log filters are opt-in',()=>{
 const src=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.match(src,/ATRIBUTOS E TESTES<\/span>\s*<div className="workspace-attribute-tools"[\s\S]*?Jogar proteção[\s\S]*?Bandeja de dados[\s\S]*?<\/header>/);
 assert.match(src,/<CurrencyCounters[^>]*summaryOnly/);
 assert.match(src,/<EquipmentLoadout[^>]*cover=\{character.definition.cover\}/);
 assert.match(src,/\[logFiltersOpen, setLogFiltersOpen\] = useState\(false\)/);
 assert.match(src,/aria-expanded=\{logFiltersOpen\}/);
 assert.match(src,/logFiltersOpen && <section[^>]*workspace-log-filters/);
});
