const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/companionIconCatalog.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});
test('shop uses actual inventory art including verbose legacy equipment names',()=>{
 for(const [name,filename] of [['Espada longa','espada-longa.png'],['Armadura de couro +2 – +6 7 kg 20 PO','armadura-de-couro.png'],['Escudo de aço +2 – – 7 kg 15 PO','escudo-de-aco.png'],['Vara Vara de madeira com 3 m de comprimento 0,5 kg 1 PP','vara-de-3-m.png']]){
  const icon=m.exports.iconPathForItem(name);assert.ok(icon.endsWith(filename));assert.ok(fs.existsSync('../..'+'/'+icon));
 }
 const shop=fs.readFileSync('src/components/MapCommerce.tsx','utf8');assert.ok(shop.includes('<CommerceItemImage name={offer.name}'));assert.match(shop,/Estoque disponível/);assert.match(shop,/disponíveis/);
});
test('failed shop image and inventory fallback settle on a non-network placeholder',()=>{
 let state;
 const subject={exports:{}},jsx=(type,props)=>({type,props});
 vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/CommerceItemImage.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:subject,exports:subject.exports,require:id=>id==='react'?{useState:initial=>[state??initial,value=>{state=typeof value==='function'?value(state):value;}]}:id==='../api'?{mediaUrlFromVaultPath:p=>p}:id==='../companionIconCatalog'?{iconPathForItem:()=> 'item.png'}:{jsx,jsxs:jsx}});
 const render=()=>subject.exports.default({name:'Espada'});
 let tree=render();assert.equal(tree.type,'img');tree.props.onError();tree=render();assert.equal(tree.type,'img');assert.match(tree.props.src,/inventario.jpg/);tree.props.onError();assert.equal(render().type,'svg');
});
