const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
test('dead combatants remain corpse pins rather than live attack targets',()=>{
 assert.ok(source.includes('const renderedMapTokens='));assert.ok(source.includes('!token.sheet?.reanimated_by'));
 assert.ok(source.includes("const image = token.sheet?.corpse ? '' :"));
 assert.ok(source.includes('workspace-pin-corpse-label'));
 assert.ok(source.includes("token.sheet?.corpse && token.current_hp === 0"));
});
test('computed diagonal attack bonus is shown beside the pin',()=>{
 assert.ok(source.includes('workspace-pin-diagonal-bonus'));assert.ok(source.includes('+{token.tactical_attack_bonus}'));
 assert.ok(fs.readFileSync('src/components/mapManagement.css','utf8').includes('pointer-events: none'));
});
test('vines explicitly keep attack independent and darkness uses individual target saves',()=>{
 assert.ok(fs.readFileSync('src/components/VineBraceletControl.tsx','utf8').includes('sem gastar o ataque'));
 assert.ok(fs.readFileSync('src/components/DornSpellControls.tsx','utf8').includes('JP normal liberta; falha passa o turno'));
});
