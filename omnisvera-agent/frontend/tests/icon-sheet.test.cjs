const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const read=p=>fs.readFileSync('src/'+p,'utf8');
test('level tools and personal notes are compact icons in their native headers',()=>{
 const level=read('components/CharacterLevel.tsx');assert.match(level,/character-level-tools/);assert.match(level,/aria-label="Subir nível"/);assert.match(level,/aria-label="Correção manual de nível e XP"/);
 const sheet=read('pages/SessionWorkspace.tsx');assert.match(sheet,/workspace-attribute-tools[\s\S]*?<CharacterNotes[^>]*compact/);
});
test('inventory and loadout use the same icon-only native inspection, not inline equip controls',()=>{
 const sheet=read('pages/SessionWorkspace.tsx'),inventory=sheet.slice(sheet.indexOf('<section className="workspace-action-catalog workspace-inventory-catalog"'),sheet.indexOf('<section className="workspace-map-panel'));
 assert.match(inventory,/<InventoryItemIcon/);assert.match(sheet,/workspace-item-modal-equipment/);
 assert.match(read('components/EquipmentLoadout.tsx'),/<InventoryItemIcon/);
 assert.match(read('companionTheme.css'),/workspace-inventory-catalog[^}]*grid-template-columns: repeat\(6, minmax\(0, 1fr\)\)/);
});
test('Raziel has native attacks AND compact hemomancy, no visible spell prose summaries',()=>{
 const sheet=read('pages/SessionWorkspace.tsx');assert.match(sheet,/\{attackSection\}/);assert.match(sheet,/definition\?\.id === 'raziel'[\s\S]{0,80}hemomancyCard/);
 assert.doesNotMatch(sheet,/<small>atual \/ máximo<\/small>|Escolha um cadáver neste mapa|Sem arma à distância equipada\. Equipe|\+1 no ataque · \+1 no dano com Grisalma<\/small>/);
 assert.match(read('components/HemomancyCard.tsx'),/<SheetSection title="Hemomancia"/);
});
