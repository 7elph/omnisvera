const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const labels={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/specializationLabel.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:labels,exports:labels.exports});
function harness(current='necromante'){
 const slots=[],calls=[],effects=[];let cursor=0;
 const react={useState(initial){const i=cursor++;if(!(i in slots))slots[i]=initial;return[slots[i],v=>slots[i]=v];},useEffect(fn,deps){const i=cursor++;if(!effects[i]||deps.some((d,j)=>d!==effects[i].deps[j])){effects[i]?.cleanup?.();effects[i]={deps,cleanup:fn()};}}};
 const jsx=(type,props)=>({type,props}),mod={exports:{}};
 const code=ts.transpileModule(fs.readFileSync('src/components/SpecializationBadge.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
 vm.runInNewContext(code,{module:mod,exports:mod.exports,require:n=>n==='react'?react:n==='react/jsx-runtime'?{jsx,jsxs:jsx}:n.includes('specializationLabel')?labels.exports:n.includes('api')?{listSpecializations:async id=>{calls.push(id);return{current:'necromante',options:[{id:'necromante',name:'Necromante',benefits:['Toque Sombrio','Aterrorizar'],restrictions:['Regra vigente']}]};}}:{default:'SheetDetail'}});
 const character={definition:{id:'morthak',specialization:current}};
 return{calls,render(){cursor=0;return mod.exports.default({character});},flush:()=>new Promise(setImmediate)};
}
test('specialization identity has a read-only benefit summary, not selection controls',async()=>{
 const h=harness();h.render();await h.flush();const node=h.render();
 assert.equal(node.props.title,'Necromante');assert.match(node.props.description,/Toque Sombrio.*Aterrorizar/);
 assert.equal(typeof node.props.description,'string');assert.equal(h.calls.length,1);
});
test('missing specialization does not add a placeholder or fetch choices',()=>{
 const h=harness(null);assert.equal(h.render(),null);assert.equal(h.calls.length,0);
});
test('weapon specialization uses the requested name without changing persisted IDs',()=>{
 assert.equal(labels.exports.specializationLabel('guerreiro-arma','Guerreiro de Arma'),'Especialista em Armas');
 assert.equal(labels.exports.specializationLabel('necromante','Necromante'),'Necromante');
});
