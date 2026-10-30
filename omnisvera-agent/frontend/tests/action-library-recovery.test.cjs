const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript'),{createHash}=require('node:crypto');
function compile(file,imports={}){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports,require:name=>imports[name]});return m.exports;}
const retry=compile('src/commandRetry.ts'),outcome=compile('src/spellOutcome.ts');
function card(api){let cursor=0,initial=true,tree;const slots=[],effects=[];
 const react={useState(value){const i=cursor++;if(!(i in slots))slots[i]=value;return[slots[i],v=>slots[i]=v];},useRef(value){const i=cursor++;return slots[i]??={current:value};},useEffect(fn){if(initial)effects.push(fn);}};
 const jsx=(type,props)=>typeof type==='function'?type(props):({type,props:props||{}});
 const target={default:props=>jsx('select',props)};
 const component=compile('src/components/ActionCard.tsx',{'react':react,'react/jsx-runtime':{jsx,jsxs:jsx},'../api':api,'../commandRetry':retry,'../spellOutcome':outcome,'./TargetSelect':target}).default;
 const walk=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(walk):[n,...walk(n.props.children)];
 const render=()=>{cursor=0;tree=component({actionRef:'spell:example',caster:{type:'token',id:'caster'},targets:[{id:'target',name:'Alvo'}]});initial=false;};
 render();effects.forEach(fn=>fn());
 return {render,nodes:()=>walk(tree),flush:async()=>{await new Promise(setImmediate);render();}};
}
test('actual legacy card preserves pending ID on reload and retains controls after lost response',async()=>{
 const store=new Map(),calls=[],applied=new Set();let lose=true;
 const api={describeAction:async()=>({ref:'spell:example',name:'Exemplo',kind:'spell',blocks:[],executable:true}),
  newDiceRequestId:()=>`library-${calls.length+1}`,
  commandRecoveryOptions:()=>({scope:async()=>'scope',digest:async value=>createHash('sha256').update(value).digest('hex'),storage:()=>({getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)})}),
  executeActionRef:async(ref,body)=>{calls.push(body.request_id);applied.add(body.request_id);if(lose){lose=false;throw Error('response lost');}return{result:{results:[]}};}};
 let h=card(api);await h.flush();h.nodes().find(n=>n.type==='select').props.onChange('target');h.render();
 h.nodes().find(n=>n.type==='button').props.onClick();await h.flush();
 assert.equal(calls.length,1);assert.ok(h.nodes().some(n=>n.type==='button'),'Failure must retain retry controls');
 h=card(api);await h.flush();assert.equal(calls.length,1,'Mount/reload cannot resend');
 h.nodes().find(n=>n.type==='select').props.onChange('target');h.render();h.nodes().find(n=>n.type==='button').props.onClick();await h.flush();
 assert.equal(calls.length,2);assert.equal(calls[0],calls[1]);assert.equal(applied.size,1);assert.equal(store.size,0);
});
