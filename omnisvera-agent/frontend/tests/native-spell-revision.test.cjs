const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/nativeSpellRevision.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});return m.exports;}
for(const [spell,binding] of Object.entries({'reflexos':'dorn_reflexos','teia':'dorn_teia','forca-arcana':'dorn_forca_arcana','dissipar-magia':'dorn_dissipar_magia'})) {
 test(`${spell}: sends only native revision, without client rules`,()=>{
  const c={schema_version:1,ref:`technique:dorn7:${spell}`,revision:`dorn-${spell}-campaign-v1`,executor:{binding},range:{meters:999},costs:[{amount:0}]};
  assert.equal(JSON.stringify(load().nativeSpellRevision(spell,c)),JSON.stringify({definition_revision:c.revision}));
  assert.throws(()=>load().nativeSpellRevision(spell,{...c,ref:'technique:other:reflexos'}));
  assert.throws(()=>load().nativeSpellRevision(spell,{...c,executor:{binding:'arbitrary'}}));
  assert.throws(()=>load().nativeSpellRevision(spell,{...c,revision:''}));
  assert.throws(()=>load().nativeSpellRevision(spell,{...c,schema_version:99}));
 });
}
test('legacy absent contract remains compatible, unknown contracted spell fails closed',()=>{
 assert.equal(JSON.stringify(load().nativeSpellRevision('reflexos',undefined)),'{}');
 assert.throws(()=>load().nativeSpellRevision('custom',{schema_version:1,revision:'custom-v1',executor:{binding:'custom'}}));
});
test('native spell control uses revision before generating retry key',()=>{
 const controls=fs.readFileSync('src/components/DornSpellControls.tsx','utf8');
 assert.ok(/nativeSpellRevision\(spell,\s*ability\?\.action_contract\)/.test(controls));
 assert.ok(controls.indexOf('Object.assign(payload, revision)')<controls.indexOf('const fingerprint'));
});
