const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/configuredGridAction.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});return m.exports;}
const contract={schema_version:1,ref:'technique:dorn7:relampago',revision:'dorn-relampago-campaign-v1',executor:{binding:'dorn_relampago'},targeting:{min_targets:1,max_targets:3},range:{mode:'ranged',meters:90}};
test('native command binds only approved handler, carries revision/map not damage or cost',()=>{
 const command=load().configuredGridCommand(contract,'scene',['a','b']);
 assert.equal(command.action,'dorn_spell_cast');assert.equal(command.payload.spell_id,'relampago');
 assert.equal(command.payload.definition_revision,contract.revision);assert.equal(command.payload.map_id,'scene');
 assert.equal(command.payload.targets.length,2);assert.equal(command.payload.damage,undefined);assert.equal(command.payload.range_m,undefined);assert.equal(command.payload.cost,undefined);
});
test('invalid binding and selection fail closed without a request',()=>{
 const build=load().configuredGridCommand;
 for(const ids of [[],['a','a'],['a','b','c','d']])assert.throws(()=>build(contract,'scene',ids));
 assert.throws(()=>build({...contract,executor:{binding:'arbitrary-url'}},'scene',['a']));
 assert.throws(()=>build({...contract,schema_version:99},'scene',['a']));
});
test('two pins for the same character behave as a repeated selection, not a new target',()=>{
 const targets=[{id:'a',entity_key:'character:ally'},{id:'b',entity_key:'character:ally'},{id:'c',entity_key:'token:c'}];
 assert.equal(load().selectionPinId(['a'],'b',targets),'a');
 assert.equal(load().selectionPinId(['a'],'c',targets),'c');
});
test('rolling deployment keeps the previous native payload when backend has no contract yet',()=>{
 const command=load().configuredGridCommand(undefined,'scene',['a']);
 assert.equal(command.action,'dorn_spell_cast');assert.equal(command.payload.spell_id,'relampago');
 assert.equal(command.payload.targets.length,1);assert.equal(command.payload.definition_revision,undefined);
 assert.throws(()=>load().configuredGridCommand(undefined,'scene',['a','b','c','d']));
});
