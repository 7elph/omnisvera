const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function outcome(){
 const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/spellOutcome.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});return m.exports.spellTargetOutcome;
}
test('healing result shows actual restored HP and the roll without calling it damage',()=>{
 const text=outcome()({target:'Aliado',healing_applied:2,healing_rolled:8,healing_roll:{individual_results:[3,4],modifier:1,total:8},damage_dealt:0,hp:{before:28,after:30}});
 assert.match(text,/cura 2/);assert.match(text,/3 \+ 4 \+ 1 = 8/);assert.match(text,/28 → 30/);assert.doesNotMatch(text,/dano|sem JP/);
});
test('existing damage outcome retains saving throw, damage and HP wording',()=>{
 assert.equal(outcome()({target:'Inimigo',damage_dealt:4,save:{total:12,target:10},resisted:true,hp:{before:10,after:6}}),'Inimigo: JP 12/10 resistiu · dano 4 · vida 10 → 6');
});
test('condition removal shows effects removed instead of fictional damage or a saving throw',()=>{
 const text=outcome()({target:'Aliado',condition_cure:'paralyzed',removed_effects:[{id:'p',label:'Paralisia'}],damage_dealt:0});
 assert.equal(text,'Aliado: removido: Paralisia');assert.doesNotMatch(text,/dano|JP/);
 assert.match(outcome()({target:'Aliado',condition_cure:'paralyzed',removed_effects:[],damage_dealt:0}),/nenhuma paralisia/);
});
test('blocked source in actual Compendium handler cannot send a command',async()=>{
 const source=fs.readFileSync('src/components/CompendiumPanel.tsx','utf8'),start=source.indexOf('  async function conjureSpell('),end=source.indexOf('  const abilitySpecs',start);
 const context={spell:{id:'broken',automation:{status:'blocked'}},caster:'a',castTarget:'b',commands:{current:{pending:false}},setError(){throw Error('must not start');}};
 const run=vm.runInNewContext(ts.transpileModule(source.slice(start,end)+'\nconjureSpell',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,context);
 await run();
});
