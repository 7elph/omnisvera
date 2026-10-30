const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function render(effect){
 const module={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/attackOutcome.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module,exports:module.exports});
 return module.exports.attackOutcomeText({result:'hit',damage_total:1,breakdown:{monster_rider_results:[effect]}}).details;
}
test('disease duration uses source days, not rounds',()=>{
 const text=render({name:'Febre do Esgoto',effect:'disease_attribute',remaining_seconds:172800,duration_unit:'days',
   chance_roll:{total:1},triggered:true,attribute:'constitution',attribute_before:12,attribute_after:1,save:{total:2,target:10},resisted:false});
 assert.match(text,/2 dia\(s\)/);assert.doesNotMatch(text,/17280|rodada/);
 assert.match(text,/transmissão 1/);assert.match(text,/Constituição 12 → 1/);
});
test('failed transmission shows chance without inventing a saving throw',()=>{
 const text=render({name:'Febre do Esgoto',effect:'disease_attribute',chance_roll:{total:4},triggered:false});
 assert.match(text,/transmissão 4.*não transmitida/);assert.doesNotMatch(text,/JP|falhou|resistiu/);
});
