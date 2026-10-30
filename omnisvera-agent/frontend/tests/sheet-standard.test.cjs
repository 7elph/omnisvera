const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('blood blade hides duplicated pool counter but retains resource validation',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(source.includes("!['regeneracao-vampirica', 'lamina-de-sangue'].includes(ability.id)"));
 assert.ok(source.includes('Boolean(resource && resource.current <= 0)'));
 assert.ok(source.includes("(attack.id === 'melee' || attack.id === 'ranged') ? candidates : character?.inventory"));
});
test('Dorn uses shared cards without duplicate inventory or HP panels',()=>{
 const source=fs.readFileSync('src/components/DornConstructDetails.tsx','utf8');
 assert.ok(source.includes('<SpellCard'));
 assert.ok(source.includes('TRAÇOS DE CONSTRUCTO'));
 assert.ok(!source.includes('<details'));
 assert.ok(!source.includes('character.inventory'));
 assert.ok(!source.includes('Integridade'));
 assert.ok(source.includes("['Forma Imutável', 'Mente Artificial', 'Corpo Artificial']"));
 assert.ok(source.includes('mente_artificial_6180e87c7a.png'));
 const workspace=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(workspace.includes("item.id !== 'dorn-reparo'"));
 assert.ok(workspace.includes("const title = repair ? 'Reparo'"));
});
test('ability headings occupy full width with controls below',()=>{
 const css=fs.readFileSync('src/styles.css','utf8');
 assert.match(css,/article:has\(> span > \.workspace-ability-name\) \{\s*grid-template-columns: minmax\(0, 1fr\)/);
 assert.match(css,/article:has\(> span > \.workspace-ability-name\) > span \{ grid-column: 1 \/ -1;/);
});
test('Bone Dagger is presented once in spells while keeping its existing attack resolver',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(source.includes('item.kind === "spell" || item.id === \'adaga-de-osso\''));
 assert.ok(source.includes("attacks?.filter(attack => attack.id !== 'adaga-de-osso'"));
 assert.ok(!source.includes("attack.id === 'ranged' && !attack.damage && abilities.some(a => a.id === 'adaga-de-osso' && a.active && !a.blocked)"),'Keep the ranged attack card visible as requested; Bone Dagger remains separate');
 assert.ok(source.includes("resolveSelectedAttack('adaga-de-osso', target)"));
 assert.ok(source.includes("if (ability.id === 'adaga-de-osso') return <SpellCard"));
});
test('ability and spell counters share the image heading row',()=>{
 const css=fs.readFileSync('src/styles.css','utf8');
 assert.ok(css.includes('> b { grid-column: 2; grid-row: 1; white-space: nowrap;'));
 assert.ok(css.includes(':has(> b) { grid-template-columns: minmax(0, 1fr) auto;'));
 assert.ok(css.includes('> .workspace-catalog-card-summary { display: contents; }'));
});
