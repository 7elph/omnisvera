const{test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),ts=require('typescript'),vm=require('node:vm');
const mod={exports:{}};const jsx=(type,props)=>({type,props});
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/NightFormControl.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:()=>({jsx,jsxs:jsx})});
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props.children)]:[];
test('active form can be switched off at zero uses without activating again',()=>{
 let activated=0,ended=0;const tree=mod.exports.default({animal:'corvo',busy:false,canActivate:false,selector:'selector',onActivate:()=>activated++,onDeactivate:()=>ended++});
 const nodes=walk(tree),button=nodes.find(n=>n.type==='button');
 assert.equal(button.props.role,'switch');assert.equal(button.props['aria-checked'],true);assert.equal(button.props.disabled,false);assert.equal(button.props.children,'Desativar');
 assert.ok(nodes.find(n=>n.type==='small').props.children.includes('Corvo'));button.props.onClick();assert.equal(ended,1);assert.equal(activated,0);
});
test('inactive form respects remaining uses and busy prevents repeat requests',()=>{
 const render=(animal,busy,canActivate)=>walk(mod.exports.default({animal,busy,canActivate,selector:'selector',onActivate(){},onDeactivate(){}})).find(n=>n.type==='button');
 assert.equal(render(null,false,false).props.disabled,true);
 assert.equal(render(null,false,true).props.disabled,false);
 assert.equal(render('coruja',true,false).props.disabled,true);
 assert.equal(render(null,false,true).props['aria-checked'],false);
});
test('sheet wires off to persisted end action, keeps authoritative active art and a single toggle',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.ok(source.includes("onDeactivate={() => void stateAction('end_night_form', {}, 'Desativar Forma da Noite')}"));
 assert.ok(source.includes("state?.animal_form || techniqueModeById[ability.id] || 'corvo'"));
 assert.ok(!source.includes('>Retornar à forma normal</button>'));
});
