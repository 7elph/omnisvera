const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=fs.readFileSync('src/api.ts','utf8');
const a=source.indexOf('export function mediaUrlFromVaultPath('),b=source.indexOf('function scoped(',a);
const compiled=ts.transpileModule(source.slice(a,b),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const moduleUnderTest={exports:{}};
vm.runInNewContext(compiled,{module:moduleUnderTest,exports:moduleUnderTest.exports,API_BASE:'',getAccessToken:()=> 'fixture-identity'});
const {mediaUrlFromVaultPath:media,imagePreviewUrl:preview}=moduleUnderTest.exports;
test('map and full detail URLs remain original unless preview is requested',()=>{
 assert.equal(media('zz_media/maps/arena.png'),'/media/zz_media/maps/arena.png?token=fixture-identity');
 assert.equal(media('companion-assets/item.png'),'/companion-assets/item.png');
 assert.equal(media('zz_media/item.png',128),'/media/zz_media/item.png?token=fixture-identity&preview_size=128');
});
test('icon previews preserve identity and support app art without exposing credentials externally',()=>{
 assert.equal(preview('/companion-assets/item.png'),'/media/companion-assets/item.png?preview_size=128&token=fixture-identity');
 const url=media('zz_media/item.png',128);assert.equal(preview(url),url);
 assert.equal(preview('https://example.invalid/item.png'),'https://example.invalid/item.png');
 assert.equal(media('zz_media/character.png',768),'/media/zz_media/character.png?token=fixture-identity&preview_size=768');
});
