const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const walk=n=>Array.isArray(n)?n.flatMap(walk):n&&typeof n==='object'?[n,...walk(n.props?.children)]:[];
test('target confirmation never applies before Yes, No cancels, repeated Yes sends once',()=>{
 const m={exports:{}},jsx=(type,props)=>({type,props});let yes=0,no=0;
 vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/TargetConfirmation.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:m,exports:m.exports,document:{body:{}},require:id=>id==='react'?{useRef:v=>({current:v}),useEffect(){}}:id==='react-dom'?{createPortal:x=>x}:{jsx,jsxs:jsx}});
 const tree=m.exports.default({action:'Toque',target:'Ogro',busy:false,onYes:()=>yes++,onNo:()=>no++});
 assert.equal(yes,0);const buttons=walk(tree).filter(n=>n.type==='button');
 buttons.find(n=>n.props.children==='Não').props.onClick();assert.equal(no,1);assert.equal(yes,0);
 const sim=buttons.find(n=>n.props.children==='Sim');sim.props.onClick();sim.props.onClick();assert.equal(yes,1);
});
