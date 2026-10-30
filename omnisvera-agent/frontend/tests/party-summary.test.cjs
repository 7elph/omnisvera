const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const m={exports:{}};const jsx=(type,props)=>({type,props});vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/PartyMemberSummary.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,require:()=>({jsx,jsxs:jsx})});
test('party header shows class, health bar and level, without visible numeric HP',()=>{
 const tree=m.exports.default({name:'Vezemir',className:'Guerreiro',level:5,hp:22,maximumHp:27});
 const copy=tree.props.children;assert.equal(copy[0].props.children,'Vezemir');assert.equal(copy[1].props.children,'Guerreiro');
 const bar=copy[2].props.children[0],level=copy[2].props.children[1];assert.equal(bar.props['aria-valuenow'],22);assert.equal(level.props.children,5);assert.equal(level.props['aria-label'],'Nível 5');assert.ok(!JSON.stringify(copy.map(n=>n.props.children)).includes('22/27'));
});
