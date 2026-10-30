const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('map zoom explicitly stays horizontal despite legacy mobile styles',()=>{
 const css=fs.readFileSync('src/companionTheme.css','utf8');
 assert.match(css,/\.app-shell \.workspace-map-panel > header > \.workspace-map-zoom\s*\{[^}]*flex-direction:\s*row/);
});
test('map has no movement arrows or entity selector; direct pin movement and retry remain',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(!source.includes('logical-token-controls'));
 assert.ok(!source.includes('Entidade no grid'));
 assert.ok(!source.includes('Mover uma célula'));
 assert.ok(!source.includes('setGridTokenId'));
 assert.ok(source.includes('onPointerDown={(event) => { if (!targeting && canMoveToken(token))'));
 assert.ok(source.includes('Reenviar movimento pendente'));
 assert.match(source,/newDiceRequestId\('rest-all'\)/);
});
