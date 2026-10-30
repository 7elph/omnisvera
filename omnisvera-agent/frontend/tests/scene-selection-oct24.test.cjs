const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/scenePreparation.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports,require:()=>({})});
const assets=[{id:'7:element:12',kind:'clue',title:'Pista',privateText:'Segredo'},{id:'7:pin:token:test',kind:'pin',token:{id:'token:test'}},{id:'7:map',kind:'map'},{id:'7:notes',kind:'text',text:'Privado'}];
test('selection preserves native IDs and never sends private text or unselected elements',()=>{
 const value=m.exports.selectionForAssets(assets,['7:element:12','7:pin:token:test']);
 assert.equal(JSON.stringify(value),JSON.stringify({element_ids:[12],token_ids:['token:test'],include_map:false}));
 assert.ok(!JSON.stringify(value).includes('Segredo'));assert.ok(!JSON.stringify(value).includes('Privado'));
 assert.equal(m.exports.selectionForAssets(assets,['7:map']).include_map,true);
 assert.equal(m.exports.selectionForAssets(assets,[]).element_ids.length,0);
});
