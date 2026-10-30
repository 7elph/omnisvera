const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),path=require('node:path'),ts=require('typescript'),vm=require('node:vm');
const file=path.join(__dirname,'../src/dispelTargetSelection.ts');
const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const scope={exports:{}};vm.runInNewContext(code,scope);const {gridDispelCommand}=scope.exports;
const preview={target_token_id:'victim',target_name:'Alvo',map_id:'map',fingerprint:'position-hash',version:7,definition_revision:'rev',effects:[{id:'web-parent',label:'Teia',kind:'area'}]};
test('dispel command binds the server-selected effect, pin, position and revision',()=>{
 const command=gridDispelCommand(preview,'web-parent');
 assert.equal(command.action,'dorn_spell_cast');assert.equal(command.expected_version,7);
 assert.equal(command.payload.effect_id,'web-parent');assert.equal(command.payload.target_token_id,'victim');
 assert.equal(command.payload.target_fingerprint,'position-hash');assert.equal(command.payload.definition_revision,'rev');
 assert.equal(Object.keys(command.payload).sort().join(','),'definition_revision,effect_id,spell_id,target_fingerprint,target_token_id');
});
test('no selection or an effect from another target cannot produce a command',()=>{
 assert.throws(()=>gridDispelCommand(preview,undefined),/Escolha/);assert.throws(()=>gridDispelCommand(preview,'other-effect'),/Escolha/);
});
test('an empty preview is never promoted to a guessed effect',()=>{
 assert.throws(()=>gridDispelCommand({...preview,effects:[]},'web-parent'),/Escolha/);
});
