const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');

function harness() {
  const slots=[],effects=[],calls=[];let cursor=0,tree;
  const react={
    useState(initial){const i=cursor++;if(!(i in slots))slots[i]=initial;return[slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v];},
    useRef(initial){const i=cursor++;return slots[i]??={current:initial};},
    useEffect(fn,deps){const i=cursor++;if(!slots[i]||deps.some((x,j)=>x!==slots[i][j])){slots[i]=deps;effects.push(fn);}},
  };
  const jsx=(type,props)=>({type,props:props||{}});const module={exports:{}};
  const code=ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/components/RustContactOptions.tsx'),'utf8'),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX},
  }).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,require:name=>({react,'react/jsx-runtime':{jsx,jsxs:jsx}}[name])});
  const rules=[{id:'magic',kind:'attack_bonus',value:3,label:'Encantamento'},
    {id:'for',kind:'damage_bonus',value:3,label:'FOR +3'},
    {id:'mastery',kind:'attack_bonus',value:3,label:'Maestria de armas'}];
  let items=[{inventory_id:17,item_title:'Arma teste',needs_metadata:true,rules,fingerprint:'revision1'}];
  const walk=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(walk):[n,...walk(n.props.children)];
  const render=()=>{cursor=0;tree=module.exports.default({items,onChange:value=>calls.push(value)});while(effects.length)effects.shift()();return tree;};
  const find=label=>walk(tree).find(n=>n.props['aria-label']===label);
  const choose=(label,value)=>{find(label).props.onChange({target:{value}});render();};
  render();render();
  return {calls,find,choose,render,nodes:()=>walk(tree),items:value=>{items=value;render();render();},last:()=>calls.at(-1)};
}

test('no equipped item or material is destructively selected by default',()=>{
  const h=harness();assert.equal(h.last(),null);assert.equal(h.find('Item tocado pela Ferrugem').props.value,'');
  h.choose('Item tocado pela Ferrugem','17');assert.equal(h.last(),null);
  assert.equal(h.find('Material do item').props.value,'');assert.equal(h.find('Encantamento do item').props.value,'');
});

test('common contact becomes confirmable only after explicit material and magic',()=>{
  const h=harness();h.choose('Item tocado pela Ferrugem','17');h.choose('Material do item','metal');assert.equal(h.last(),null);
  h.choose('Encantamento do item','no');
  assert.equal(JSON.stringify(h.last()),JSON.stringify({inventory_id:17,selection:{material:'metal',magical:false,enchantment_bonus:0,enhancement_rule_ids:[]}}));
});

test('magic requires a separate compatible component and excludes STR/mastery',()=>{
  const h=harness();h.choose('Item tocado pela Ferrugem','17');h.choose('Material do item','metal');h.choose('Encantamento do item','yes');h.choose('Bônus mágico do item','3');
  assert.equal(h.last(),null);
  assert.equal(h.nodes().filter(n=>n.type==='input').length,1);
  const checkbox=h.find('Encantamento: Encantamento');checkbox.props.onChange({target:{checked:true}});h.render();
  assert.equal(h.last().selection.enchantment_bonus,3);assert.equal(JSON.stringify(h.last().selection.enhancement_rule_ids),'["magic"]');
  h.choose('Bônus mágico do item','2');assert.equal(h.last(),null);
  assert.ok(h.nodes().some(n=>n.props.role==='status'&&String(n.props.children).includes('Revise')));
});

test('known instance uses saved metadata while source revision resets confirmation',()=>{
  const h=harness();const selected={material:'metal',magical:true,enchantment_bonus:3,enhancement_rule_ids:['magic']};
  const item={inventory_id:17,item_title:'Arma',needs_metadata:false,bonus:2,selection:selected,rules:[],fingerprint:'known'};
  h.items([item]);h.choose('Item tocado pela Ferrugem','17');assert.equal(h.last().selection,selected);
  assert.equal(h.find('Material do item'),undefined);
  h.items([{...item,fingerprint:'changed'}]);assert.equal(h.last(),null);assert.equal(h.find('Item tocado pela Ferrugem').props.value,'');
});
