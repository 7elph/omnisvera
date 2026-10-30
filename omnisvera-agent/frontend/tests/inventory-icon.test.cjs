const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function compile(file,requires){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/'+file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,require:name=>requires[name]});return m.exports;}
const catalog=compile('companionIconCatalog.ts',{});
test('Kit básico and Raziel leather armor use real catalog fallback images',()=>{
 const jsx=(type,props)=>({type,props});
 const Icon=compile('components/InventoryItemIcon.tsx',{'../api':{mediaUrlFromVaultPath:p=>p},'../companionIconCatalog':catalog,react:{useState:initial=>[initial,()=>{}]},'react/jsx-runtime':{jsx,jsxs:jsx}}).default;
 for(const [name,expected] of [['Kit básico','kit-basico.jpg'],['Armadura de couro','armadura-de-couro.png']]){
  let inspected=0;const item={item_title:name,quantity:3,equipped:true};const tree=Icon({item,onInspect:()=>inspected++}),children=tree.props.children;
  assert.equal(tree.props['aria-label'],name);assert.ok(children[0].props.src.endsWith(expected));assert.equal(children[1].props.children,3);
  assert.equal(inspected,0);tree.props.onClick();assert.equal(inspected,1);
  assert.equal(Icon({item,showQuantity:false}).props.children[1],false);
 }
});
