const{test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),ts=require('typescript'),vm=require('node:vm');
const mod={exports:{}};const jsx=(type,props)=>({type,props});
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/NightFormSelector.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:id=>id.includes('api')?{mediaUrlFromVaultPath:p=>p}:{jsx,jsxs:jsx}});
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props.children)]:[];
test('pictures stay inside the closed dropdown, not its summary',()=>{
 const tree=mod.exports.default({value:'coruja',onChange:()=>{}});const nodes=walk(tree);
 assert.equal(tree.type,'details');assert.equal(nodes.filter(n=>n.type==='img').length,3);
 assert.equal(nodes.filter(n=>n.type==='button').length,3);
 assert.equal(walk(nodes.find(n=>n.type==='summary')).filter(n=>n.type==='img').length,0);
});
test('choosing an illustrated option updates value and closes the dropdown',()=>{
 let selected,closed=false;const nodes=walk(mod.exports.default({value:'corvo',onChange:v=>selected=v}));
 const button=nodes.find(n=>n.type==='button'&&n.props.children[1]==='Morcego');
 button.props.onClick({currentTarget:{closest:()=>({removeAttribute:()=>closed=true})}});
 assert.equal(selected,'morcego');assert.equal(closed,true);
});
