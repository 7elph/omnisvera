const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const path=require('node:path');

function harness(access='gm', send=async()=>({}), summaryOnly=false) {
  const slots=[], effects=[], calls=[]; let cursor=0, tree;
  const react={
    useState(initial){const i=cursor++;if(!(i in slots))slots[i]=initial;return [slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v];},
    useRef(initial){const i=cursor++;return slots[i]??={current:initial};},
    useEffect(fn){const i=cursor++;if(!slots[i]){slots[i]=true;effects.push(fn);}},
  };
  const jsx=(type,props)=>({type,props:props||{}});
  const module={exports:{}};
  const code=ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/components/CurrencyCounters.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,Error,require:name=>({react,'./SheetDetail':{default:'SheetDetail'},'react/jsx-runtime':{jsx,jsxs:jsx},'../api':{applyCharacterStateAction:async(...args)=>{calls.push(args);return send(...args);}}}[name])});
  const character={access_level:access,definition:{id:'vezemir'},state:{coins:10}};
  const walk=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(walk):[n,...walk(n.props.children)];
  function render(){cursor=0;tree=module.exports.default({character,onChange:async()=>{},summaryOnly});while(effects.length)effects.shift()();return tree;}
  render();render();
  return {render,calls,nodes:()=>walk(tree),find:label=>walk(tree).find(n=>n.props['aria-label']===label)};
}

test('player wallet shows ascending coin balances only; no heading or spend/edit controls',()=>{
  const h=harness('owner');
  assert.equal(h.find('Ouro: saldo').props.children,10);
  assert.equal(h.nodes().filter(n=>['input','button','select'].includes(n.type)).length,0);
  assert.deepEqual(h.nodes().filter(n=>n.type==='strong').map(n=>n.props['aria-label']),['Cobre: saldo','Prata: saldo','Ouro: saldo','Platina: saldo']);
  assert.equal(h.nodes().filter(n=>['header','summary','small'].includes(n.type)).length,0);
});

test('master Mesa summary has only balances while the full sheet retains the editor',()=>{
  const h=harness('gm',async()=>({}),true);
  assert.equal(h.nodes().filter(n=>['input','button','select','summary','header','small'].includes(n.type)).length,0);
  assert.equal(h.find('Ouro: saldo').props.children,10);
  assert.ok(harness('gm').find('Aplicar Ouro'));
  const editor=h.nodes().find(n=>n.type==='SheetDetail');assert.ok(editor,'GM can open the native editor from its balances');
  assert.equal(editor.props.title,'Editar moedas');assert.equal(editor.props.description.props.expanded,true);
  assert.equal(harness('owner').nodes().filter(n=>n.type==='SheetDetail').length,0,'Players never receive the editor');
});
test('master can increase and player cannot see other character balances',()=>{
  const h=harness('gm');h.find('Aumentar Ouro').props.onClick();h.render();
  assert.equal(h.find('Ouro').props.value,'11');
  assert.equal(h.find('Aplicar Ouro').props.disabled,false);
  assert.equal(harness('public').render(),null);
});
test('apply sends target balance, original balance and guards double click',async()=>{
  const h=harness();h.find('Diminuir Ouro').props.onClick();h.render();
  const save=h.find('Aplicar Ouro').props.onClick;
  save();save();await new Promise(setImmediate);
  assert.equal(h.calls.length,1);
  assert.equal(h.calls[0][0],'vezemir');assert.equal(h.calls[0][1],'set_currency');
  assert.equal(JSON.stringify(h.calls[0][2]),JSON.stringify({currency:'gold',value:9,expected_balance:10}));
});
test('failed request retains typed balance and shows error',async()=>{
  const h=harness('gm',async()=>{throw new Error('Offline');});
  h.find('Diminuir Ouro').props.onClick();h.render();h.find('Aplicar Ouro').props.onClick();
  await new Promise(setImmediate);h.render();
  assert.equal(h.find('Ouro').props.value,'9');
  assert.ok(h.nodes().some(n=>n.props.role==='alert'&&n.props.children==='Offline'));
});
