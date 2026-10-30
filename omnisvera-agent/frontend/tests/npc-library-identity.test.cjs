const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/npcLibrary.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports});
const {npcMatchesCharacter,npcPins,extraNpcPinGroups}=m.exports;
test('directory/character/pin identity removes repeated presentation without deleting instances',()=>{
 const npcs=[{id:19,name:'Thoradin'},{id:4,name:'Unidade DORN-7',source_path:'Characters/Individual/Unidade DORN-7.md'}],characters=[{id:'dorn7',name:'Unidade DORN-7'}];
 const pins=[{id:'thoradin',name:'Thoradin'},{id:'dorn7',name:'Unidade DORN-7'},{id:'lich-a',name:'Lich',current_hp:43},{id:'lich-b',name:'Lich',current_hp:34}];
 assert.ok(npcMatchesCharacter(npcs[1],characters[0]));assert.equal(npcPins(npcs[0],pins)[0].id,'thoradin');
 const groups=extraNpcPinGroups(npcs,characters,pins);assert.equal(groups.length,1);assert.equal(groups[0].tokens.length,2);assert.equal(groups[0].tokens[1].current_hp,34);assert.equal(pins.length,4);
});
test('distinct named NPCs, ambiguous names and summoned creatures remain accessible',()=>{
 const npcs=[{id:1,name:'Maera Dhal'},{id:2,name:'Maera Voss'},{id:3,name:'Guarda'},{id:4,name:'Guarda'}];
 const groups=extraNpcPinGroups(npcs,[],[{id:'a',name:'Maera Dhal'},{id:'b',name:'Maera Voss'},{id:'c',name:'Guarda'},{id:'s',name:'Maera Dhal',sheet:{summon:{caster:'morthak'}}}]);
 assert.equal(groups.length,2);assert.ok(groups.some(g=>g.tokens[0].id==='s'));assert.ok(groups.some(g=>g.tokens[0].id==='c'));
});
