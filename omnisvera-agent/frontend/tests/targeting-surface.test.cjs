const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function render(grid,ring){const m={exports:{}},jsx=(type,props)=>({type,props});vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/TargetingOverlay.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,require:()=>({jsx,jsxs:jsx})});return m.exports.default({grid,ring});}
const grid={cols:20,rows:10,cell_size_m:1.5,origin_x:0,origin_y:0,distance_rule:'chebyshev'};
test('range surface fills the entire map and shows authoritative area under pins',()=>{
 const tree=render(grid,{origin:{cell_x:5,cell_y:4},rangeCells:6});
 assert.equal(tree.props.width,'100%');assert.equal(tree.props.height,'100%');
 assert.ok(tree.props.children.flat().some(n=>n?.props?.className==='targeting-area'));
 const css=fs.readFileSync('src/styles.css','utf8');assert.match(css,/\.targeting-overlay\s*\{[^}]*z-index:\s*3/);
});
test('range scale uses grid cells, not token dimensions',()=>{
 const tree=render(grid,{origin:{cell_x:5,cell_y:4},rangeCells:6});
 const ring=tree.props.children.flat().find(n=>n?.type==='ellipse');assert.equal(ring.props.rx,30);assert.equal(ring.props.ry,60);
});
