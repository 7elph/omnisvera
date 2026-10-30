const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props?.children)]:[];
const text=v=>Array.isArray(v)?v.map(text).join(''):v&&typeof v==='object'?text(v.props?.children):String(v??'');
function render(props,values=[]){
  let i=0;const calls=[],resolved=[];const mod={exports:{}};
  const jsx=(type,props)=>({type,props:props||{}});
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/NecromancerSpellControls.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:id=>id==='react'?{useState:initial=>[values[i++]??initial,()=>{}],useRef:initial=>({current:initial}),useEffect(){}}:id.includes('combatActionAvailability')?{combatActionBlock:()=>''}:id.includes('api')?{newDiceRequestId:()=> 'fixture-necro-command',useCharacterTechnique:async (...args)=>{calls.push(args);return {resolution_id:'attack:fixture',status:'pending',protocol_result:{duration_turns:6,results:[]}}}}:{jsx,jsxs:jsx}});
  return {tree:mod.exports.default({...props,onResolved:r=>resolved.push(r),onChange:async()=>{},onClose:()=>{}}),calls,resolved};
}
const props={spell:'aterrorizar',mode:'player',hp:10,rollMode:'digital',combat:{encounter:{active:false}},targets:[{id:'a',name:'A',current_hp:5},{id:'b',name:'B',current_hp:5}],resources:[{key:'aterrorrizar',current:1,maximum:1},{key:'toque_sombrio',current:1,maximum:1},{key:'magias_de_1o_circulo',current:2,maximum:4}]};
test('touch requires one target but does not ask for manual range',()=>{
  const {tree}=render({...props,spell:'toque-sombrio'});
  assert.equal(walk(tree).find(n=>n.type==='button'&&text(n)==='Conjurar').props.disabled,true);
  assert.equal(walk(tree).some(n=>n.props?.['aria-label']==='Distância dos alvos'),false);
});
test('fear selects targets authoritatively on backend once on double click',async()=>{
  const {tree,calls}=render(props);
  const b=walk(tree).find(n=>n.type==='button'&&text(n)==='Conjurar');
  assert.equal(b.props.disabled,false); b.props.onClick();b.props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls.length,1);assert.equal(calls[0][1],'aterrorizar');
  assert.equal(calls[0][2].targets,undefined);assert.equal(calls[0][2].mode,'automatic');
  assert.equal(calls[0][2].position_confirmed,undefined);
});
test('spent daily use requires explicit memorized-slot consent',()=>{
  const {tree}=render({...props,resources:props.resources.map(r=>({...r,current:r.key==='aterrorrizar'?0:r.current}))});
  assert.equal(walk(tree).find(n=>n.type==='button'&&text(n)==='Conjurar').props.disabled,true);
});
test('touch feeds physical roll into the existing attack preview',async()=>{
  const {tree,calls,resolved}=render({...props,spell:'toque-sombrio',rollMode:'physical'},[['a'],false,'17']);
  const b=walk(tree).find(n=>n.type==='button'&&text(n)==='Conjurar');b.props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls[0][2].d20,17);assert.equal(resolved[0].resolution_id,'attack:fixture');
});
test('high spells do not borrow first-circle slots and cast once',async()=>{
  const {tree,calls}=render({...props,spell:'clonagem',resources:[{key:'clonagem',current:1,maximum:1}]});
  const b=walk(tree).find(n=>n.type==='button'&&text(n)==='Conjurar');assert.equal(b.props.disabled,false);b.props.onClick();b.props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls.length,1);assert.equal(calls[0][1],'clonagem');
  const spent=render({...props,spell:'clonagem',resources:[{key:'clonagem',current:0,maximum:1},...props.resources]}).tree;
  assert.equal(walk(spent).find(n=>n.type==='button'&&text(n)==='Conjurar').props.disabled,true);
});
test('active cloning exposes concentration end instead of another cast',async()=>{
  const {tree,calls}=render({...props,spell:'clonagem',combat:{...props.combat,effects:[{necro_spell:'clonagem'}]},resources:[{key:'clonagem',current:0,maximum:1}]});
  walk(tree).find(n=>n.type==='button'&&text(n)==='Encerrar concentração').props.onClick();await new Promise(r=>setImmediate(r));
  assert.equal(calls[0][1],'clonagem');assert.equal(calls[0][2].mode,'end');
});
