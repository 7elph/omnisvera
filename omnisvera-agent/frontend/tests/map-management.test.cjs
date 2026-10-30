const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');

test('GM retains a visible quick active-map selector in Mesa without restoring library or uploads',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const central=source.slice(source.indexOf('{view !== "sheet" && <main'),source.indexOf('{(view === "table" || view === "maps") && <aside'));
  assert.match(central,/workspace-active-map-select/);
  assert.match(central,/aria-label="Mapa ativo"/);
  assert.match(central,/changeWorkspaceMap\(event.target.value\)\.catch/);
  assert.match(central,/disabled=\{Boolean\(busy \|\| battleState.encounter\?\.active\)\}/);
  assert.ok(!central.includes('<WorkspaceMapLibrary'));assert.ok(!central.includes('workspace-map-upload'));
});

test('GM map management and grid calibration are confined to the Maps sidebar, never the central header',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const side=source.slice(source.indexOf('{view === "maps" && <aside'),source.indexOf('{view !== "sheet" && <main'));
  const central=source.slice(source.indexOf('{view !== "sheet" && <main'),source.indexOf('{(view === "table" || view === "maps") && <aside'));
  for(const marker of ['<WorkspaceMapLibrary','workspace-map-upload','<GridConfiguration']){
    assert.ok(side.includes(marker),marker+' belongs in Maps');assert.ok(!central.includes(marker),marker+' must not occupy the map header');
  }
  assert.match(source,/mapUploading/);
  const upload=source.slice(source.indexOf('async function submitMap'),source.indexOf('async function submitIcon'));
  assert.ok(!upload.includes('setBusy('),'upload must not lock unrelated combat/sheet controls');
});

test('fog editor opens at the top of Maps instead of hiding below the library',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const side=source.slice(source.indexOf('{view === "maps" && <aside'),source.indexOf('{view !== "sheet" && <main'));
  assert.ok(side.indexOf('renderGmWorkspaceTools("maps")')<side.indexOf('workspace-map-management'),'Map controls precede library');
  assert.match(source,/<details open className="workspace-gm-section workspace-fog-section">/);
  assert.match(source,/<fieldset disabled=\{Boolean\(busy\) \|\| !workspace.map\?\.id\} aria-label="Editar fog do mapa atual">/);
  assert.ok(source.includes('if (mode !== "gm" || view !== "maps" || !workspace.map?.id) return;'),'Do not paint the default map while the active map is loading');
  const css=fs.readFileSync('src/components/mapManagement.css','utf8');
  assert.match(css,/\.workspace-map-controls-panel > \.workspace-gm-drawer\s*\{[^}]*height:\s*auto/);
});

test('map library has search, direct opening and an independent bounded refresh',()=>{
  const source=fs.readFileSync('src/components/WorkspaceMapLibrary.tsx','utf8');
  for(const marker of ['listWorkspaceMaps','type="search"','onSelect','Atualizar lista','workspace-map-library-list']) assert.ok(source.includes(marker),marker);
  const css=fs.readFileSync('src/components/mapManagement.css','utf8');
  assert.match(css,/overflow-y:\s*auto/);assert.match(css,/min-height:\s*44px/);
});

function writer(fetch){
  const timers=new Map();let id=0;const module={exports:{}};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/writeJson.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
    {module,exports:module.exports,fetch,AbortController,setTimeout:fn=>{timers.set(++id,fn);return id;},clearTimeout:id=>timers.delete(id)});
  return {...module.exports,timers,expire:()=>[...timers.values()].forEach(fn=>fn())};
}
test('stalled map upload expires, releases its deadline and never retries a mutation automatically',async()=>{
  let calls=0,signal;const h=writer(async(_url,options)=>{calls++;signal=options.signal;return {ok:true,json:()=>new Promise(()=>{})};});
  const result=h.writeJson('/gm/workspace/map',{},'POST',{title:'test'},'Falha ao enviar');
  await Promise.resolve();h.expire();await assert.rejects(result,/Atualize a lista/);
  assert.equal(signal.aborted,true);assert.equal(calls,1);assert.equal(h.timers.size,0);
});
test('map mutation returns backend rejection and confirmed data, cleaning up deadlines',async()=>{
  const h=writer(async()=>({ok:false,json:async()=>({detail:'Limite da imagem'})}));
  await assert.rejects(h.writeJson('/map',{},'POST',{},'Erro'),/Limite da imagem/);assert.equal(h.timers.size,0);
  const good=writer(async()=>({ok:true,json:async()=>({id:'saved-map'})}));
  assert.equal((await good.writeJson('/map',{},'POST',{},'Erro')).id,'saved-map');assert.equal(good.timers.size,0);
});
