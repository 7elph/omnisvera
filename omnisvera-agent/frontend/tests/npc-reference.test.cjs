const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
test('quick locations belong only to Maps sidebar',()=>{
 const maps=source.slice(source.indexOf('{view === "maps" && <aside'),source.indexOf('{view !== "sheet" && <main'));
 assert.ok(maps.includes('<LocationQuickPin'));
 assert.equal((source.match(/<LocationQuickPin/g)||[]).length,1);
});
test('Master NPC reference reuses directory and all-map tokens, with explicit navigation',()=>{
 const library=fs.readFileSync('src/components/MasterNpcLibrary.tsx','utf8');
 assert.match(library,/listMasterNpcTokens/);assert.match(library,/<NpcDirectory/);
 assert.match(library,/Buscar fichas e pins/);assert.match(library,/onOpenCharacter/);assert.match(library,/onOpenToken/);
 const directory=fs.readFileSync('src/pages/NpcDirectory.tsx','utf8');
 assert.match(directory,/Voltar para a lista de NPCs/);
  assert.match(source,/Voltar para NPCs/);
  assert.match(source,/detail: 'npcs'/);
});
test('Master can place a directory NPC on the current map without revealing it',()=>{
 const library=fs.readFileSync('src/components/MasterNpcLibrary.tsx','utf8');
 assert.match(library,/createWorkspaceToken/);
 assert.match(library,/Colocar no mapa/);
 assert.match(library,/visible_to_players: false/);
 assert.match(library,/map_id: currentMap/);
 assert.match(source,/mapId=\{workspace\.map\?\.id \|\| "default"\}/);
});
