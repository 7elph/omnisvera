const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('sheet identity contains specialization; management is not in the sheet body',()=>{
 const s=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 const body=s.slice(s.indexOf('<div className="workspace-character-copy">'),s.indexOf('<ActiveEffectIcons state={battleState} targetId={character.definition.id}'));
 assert.ok(body.includes('<SpecializationBadge'));
 assert.ok(!body.includes('<SpecializationSection'));
 assert.ok(!s.includes('<MaximumHpEditor'));
 assert.ok(s.includes('<SpecializationSection'),'Keep native management available to the GM');
});
test('Dorn hides retired spells and legacy active-spells panel, not other characters spells',()=>{
 const s=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(s.includes("definition?.id === 'dorn7' && ['levitacao', 'escuridao'].includes(item.id)"));
 assert.ok(!s.includes('<DornSpellEffects'));
 const evaluate=new Function('state','definition','catalogResourceKeys','return '+s.match(/const standaloneResources = ([^\n]+);/)[1]);
 const resources=['dorn_levitacao','dorn_escuridao'].map(key=>({key,label:key,current:1,maximum:1}));
 assert.equal(evaluate({resources},{id:'dorn7'},new Set()).length,0,'Retired counters stay hidden after ability metadata is removed');
 assert.equal(evaluate({resources},{id:'other'},new Set()).length,2,'Other sheets are unchanged');
});
test('Guard is one use button without a checkbox and preserves the existing command contract',()=>{
 const s=fs.readFileSync('src/components/DornProtocolControls.tsx','utf8');
 assert.ok(!s.includes('type="checkbox"'));
 assert.ok(s.includes("use('dorn_guard',{})"));
 assert.ok(s.includes('}>Usar</button>'));
});
