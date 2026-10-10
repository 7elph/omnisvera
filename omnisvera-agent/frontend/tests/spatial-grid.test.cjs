const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const math={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/spatialGrid.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:math,exports:math.exports});
const grid={map_id:'one',cols:32,rows:24,origin_x:0,origin_y:0,cell_size_m:1.5,distance_rule:'chebyshev'};
const plain=value=>JSON.parse(JSON.stringify(value));
test('logical token center is independent of image dimensions and zoom',()=>{
  const position={map_id:'one',cell_x:8,cell_y:12,footprint_w:1,footprint_h:1};
  const point=math.exports.tokenProjection(grid,position,{longitude:0,latitude:0});
  assert.deepEqual(plain(point),{longitude:26.5625,latitude:52.083333333333336});
  for(const width of [320,768,1280,3840]) assert.equal((point.longitude*width/100)/width,point.longitude/100);
  assert.deepEqual(plain(math.exports.cellAt(grid,point.longitude,point.latitude)),[8,12]);
});
test('map switch never uses another map position; origin and edges snap safely',()=>{
  assert.equal(math.exports.tokenProjection(grid,{map_id:'other'},{longitude:12,latitude:45}).longitude,12);
  assert.deepEqual(plain(math.exports.cellAt({...grid,origin_x:10,origin_y:5},-50,200)),[0,23]);
});
test('simple trajectories always start at current cell and remain adjacent',()=>{
  for(const rule of ['chebyshev','manhattan']) {
    const path=plain(math.exports.simplePath([8,12],[10,11],rule));
    assert.deepEqual(path[0],[8,12]);assert.deepEqual(path.at(-1),[10,11]);
    path.slice(1).forEach((b,i)=>assert.equal(Math.max(Math.abs(b[0]-path[i][0]),Math.abs(b[1]-path[i][1])),1));
    assert.equal(path.length,rule==='chebyshev'?3:4);
  }
});
test('native workspace awaits backend confirmation and cancels mobile pointer interruptions',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const submit=source.slice(source.indexOf('async function confirmGridMove'),source.indexOf('function gridMoveCommand'));
  assert.ok(submit.indexOf('await moveGridEntity')<submit.indexOf('setWorkspace'));
  assert.match(submit,/setPendingGridCommand\(\{mapId,command\}\)/);
  assert.match(source,/event.type === 'pointercancel'/);
  assert.match(source,/tokenProjection\(workspace.map\?\.grid,token.grid_position,token\)/);
  assert.match(source,/Mover uma célula/);
});
test('movement command carries cells, versions and stable retry identity, rejects HTTP failures',async()=>{
  const calls=[];const mod={exports:{}};
  const source=fs.readFileSync('src/spatialCommands.ts','utf8').replaceAll('import.meta.env.VITE_API_BASE_URL','""');
  class HttpError extends Error {constructor(status,message){super(message);this.status=status;}}
  vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:mod,exports:mod.exports,AbortController,setTimeout,clearTimeout,require:name=>name==='./api'?{getAccessToken:()=> 'qa-only'}:{HttpError},fetch:async(url,init)=>{calls.push(JSON.parse(init.body));return {ok:false,status:409,json:async()=>({detail:'Movimento acima do limite'})};}});
  const command={request_id:'same-request',token_id:'one',mode:'COMBAT_MOVE',path:[[1,1],[2,1]],expected_position_version:1,expected_grid_version:1,expected_combat_version:5};
  for(let i=0;i<2;i++) await assert.rejects(mod.exports.moveGridEntity('map:qa',command),/acima do limite/);
  assert.deepEqual(calls,[command,command]);
});
