const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(file,imports){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports,require:id=>{if(id in imports)return imports[id];throw Error(id);},console});return m.exports;}
test('API uses only authenticated private routes and server verified evidence',async()=>{
 const calls=[];const api=load('src/sceneLabApi.ts',{'./api':{sceneLabRequest:async(...args)=>{calls.push(args);return [];},newSceneRequestId:()=> 'lab-id'}});
 await api.listLabProposals(14);await api.getLabProposal(3);await api.attachLabEvidence(3,{request_id:'x',expected_version:2,run_id:'test-'+ 'a'.repeat(32)});
 assert.equal(calls[0][0],'/gm/scenes/14/lab/proposals');assert.equal(calls[1][0],'/gm/scene-lab/proposals/3');
 assert.equal(calls[2][0],'/gm/scene-lab/proposals/3/evidence');assert.equal(calls[2][1],'POST');assert.equal(calls[2][2].summary,undefined);
});
function harness(api){
 let cursor=0,state=[],effects=[],pending=[],tree;const hooks={
 useState(initial){const i=cursor++;if(!(i in state))state[i]=initial;return[state[i],value=>{state[i]=typeof value==='function'?value(state[i]):value;}];},
 useRef(initial){const i=cursor++;if(!(i in state))state[i]={current:initial};return state[i];},
 useEffect(callback,deps){const i=cursor++;const prev=effects[i];if(!prev||deps.some((v,j)=>v!==prev.deps[j]))pending.push(()=>{prev?.cleanup?.();effects[i]={deps,cleanup:callback()};});},
 };
 const jsx=(type,props)=>({type,props:props||{}});const component=load('src/components/SceneLabPanel.tsx',{'react':hooks,'react/jsx-runtime':{jsx,jsxs:jsx},'../sceneLabApi':api}).default;
 function render(sceneId=14){cursor=0;tree=component({sceneId});pending.splice(0).forEach(fn=>fn());return tree;}
 function nodes(node=tree){return[node,...[node?.props?.children].flat(Infinity).filter(v=>v&&typeof v==='object').flatMap(n=>nodes(n))];}
 return{render,nodes,find:label=>nodes().find(n=>n.props['aria-label']===label||n.props.children===label),unmount:()=>effects.forEach(e=>e?.cleanup?.())};
}
const row={id:1,scene_id:14,title:'Proposta',kind:'action',version:1,status:'draft',content:{},history:[{version:1,event:'create',detail:{}}],revisions:[{version:1,title:'Proposta',content:{},created_at:'2026-10-16'}],evidence:null};
function mocks(extra={}){let i=0;return{listLabProposals:async()=>[row],getLabProposal:async()=>row,newLabRequestId:()=> 'req-'+ ++i,createLabProposal:async()=>row,updateLabProposal:async()=>row,attachLabEvidence:async()=>row,decideLabProposal:async()=>row,...extra};}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('collapsed laboratory is lazy; lost create response retries same intent receipt',async()=>{
 const calls=[];let reads=0;const h=harness(mocks({listLabProposals:async()=>{reads++;return[];},createLabProposal:async(...args)=>{calls.push(args);if(calls.length===1)throw Error('rede perdida');return row;}}));
 h.render();assert.equal(reads,0);await h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});await tick();h.render();assert.equal(reads,1);
 h.find('Título da proposta').props.onChange({target:{value:'Nova'}});h.render();await h.find('Criar proposta privada').props.onClick();h.render();
 assert.ok(h.nodes().some(n=>n.props.role==='alert'));await h.find('Criar proposta privada').props.onClick();h.render();
 assert.equal(calls.length,2);assert.equal(calls[0][1].request_id,calls[1][1].request_id);assert.equal(calls[0][1].scene_id,undefined);
});
test('late request from previous scene is discarded',async()=>{
 let resolve;const h=harness(mocks({listLabProposals:()=>new Promise(r=>resolve=r)}));h.render(14);
 void h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});h.render(15);resolve([row]);await tick();h.render(15);
 assert.equal(h.nodes().filter(n=>n.type==='button'&&String(n.props.children).includes('Proposta ·')).length,0);h.unmount();
});
test('panel is mounted only on private administration, not live player view',()=>{
 const src=fs.readFileSync('src/pages/ScenePanel.tsx','utf8');assert.match(src,/mode === ['"]gm['"] && surface === ['"]admin['"] && <SceneLabPanel/);
 const panel=fs.readFileSync('src/components/SceneLabPanel.tsx','utf8');assert.match(panel,/Aprovar não publica/);assert.doesNotMatch(panel,/dangerouslySetInnerHTML|execute_action|\/publish/);
});
test('invalid proposal JSON does not send an operation',async()=>{
 let writes=0;const h=harness(mocks({createLabProposal:async()=>{writes++;return row;}}));h.render();
 h.find('Título da proposta').props.onChange({target:{value:'Título'}});h.find('Conteúdo JSON da proposta').props.onChange({target:{value:'[]'}});h.render();
 await h.find('Criar proposta privada').props.onClick();h.render();assert.equal(writes,0);assert.ok(h.nodes().some(n=>n.props.role==='alert'));
});
test('same-tick double click sends once; edit pins current revision and server result advances it',async()=>{
 const calls=[];let resolve;const h=harness(mocks({updateLabProposal:(...args)=>{calls.push(args);return new Promise(r=>resolve=r);}}));h.render();
 void h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});await tick();h.render();
 await h.nodes().find(n=>n.type==='button'&&Array.isArray(n.props.children)&&n.props.children[0]==='Proposta').props.onClick();await tick();h.render();
 h.find('Conteúdo JSON da proposta').props.onChange({target:{value:'{"effect":"review"}'}});h.render();
 const button=h.find('Salvar nova revisão');const first=button.props.onClick();await button.props.onClick();assert.equal(calls.length,1);assert.equal(calls[0][1].expected_version,1);
 resolve({...row,version:2,content:{effect:'review'}});await first;h.render();
 assert.ok(h.nodes().some(n=>n.props.role==='status'&&n.props.children.includes(2)));
});
test('a late mutation cannot open proposal in another scene',async()=>{
 let resolve;const h=harness(mocks({createLabProposal:()=>new Promise(r=>resolve=r)}));h.render(14);
 h.find('Título da proposta').props.onChange({target:{value:'Privado'}});h.render(14);const first=h.find('Criar proposta privada').props.onClick();h.render(15);
 resolve(row);await first;h.render(15);assert.equal(h.find('Salvar nova revisão'),undefined);assert.equal(h.find('Título da proposta').props.value,'');
});
test('unmounted panel discards pending fetch without writing state',async()=>{
 let resolve;const h=harness(mocks({listLabProposals:()=>new Promise(r=>resolve=r)}));h.render();
 void h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});h.unmount();resolve([row]);await tick();
 assert.equal(h.nodes().filter(n=>n.type==='button'&&Array.isArray(n.props.children)&&n.props.children[0]==='Proposta').length,0);
});
test('real evidence object and immutable revisions render without array assumptions',async()=>{
 const realistic={...row,evidence:{run_id:'test-'+ 'b'.repeat(32),summary:{status:'PASS'},scope:'existing_code_only_not_proposal_execution'},revisions:[...row.revisions,{version:2,title:'Proposta 2',content:{approved:false},created_at:'2026-10-16'}]};
 const h=harness(mocks({getLabProposal:async()=>realistic}));h.render();void h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});await tick();h.render();
 h.nodes().find(n=>n.type==='button'&&Array.isArray(n.props.children)&&n.props.children[0]==='Proposta').props.onClick();await tick();h.render();
 assert.ok(h.nodes().some(n=>n.type==='pre'&&n.props.children.includes('existing_code_only_not_proposal_execution')));
 assert.ok(h.nodes().some(n=>n.type==='pre'&&n.props.children.includes('"approved": false')));
 assert.ok(h.find('Eventos de revisão'));assert.ok(h.nodes().some(n=>typeof n.props.children==='string'&&n.props.children.includes('não executa o JSON')));
});
test('mutation receipt without revisions is enriched through separate detail read',async()=>{
 const {revisions,...receipt}=row;const calls=[];
 const h=harness(mocks({createLabProposal:async(...args)=>{calls.push(args);return receipt;},getLabProposal:async id=>{assert.equal(id,row.id);return row;}}));h.render();
 h.find('Título da proposta').props.onChange({target:{value:'Proposta'}});h.render();await h.find('Criar proposta privada').props.onClick();h.render();
 assert.equal(calls.length,1);assert.ok(h.nodes().some(n=>n.type==='summary'&&Array.isArray(n.props.children)&&n.props.children[0]==='Revisão '&&n.props.children[1]===1));
 assert.equal(h.nodes().filter(n=>n.props.role==='alert').length,0);
});
test('post-confirmation detail failure preserves receipt and never retries write on refresh',async()=>{
 const {revisions,...receipt}=row;let writes=0,ids=0;
 const h=harness(mocks({newLabRequestId:()=> 'receipt-'+ ++ids,createLabProposal:async()=>{writes++;return receipt;},getLabProposal:async()=>{throw Error('read lost');}}));h.render();
 h.find('Título da proposta').props.onChange({target:{value:'Proposta'}});h.render();await h.find('Criar proposta privada').props.onClick();h.render();
 assert.equal(writes,1);assert.equal(ids,1);assert.equal(h.find('Criar proposta privada'),undefined);assert.ok(h.find('Salvar nova revisão'));
 assert.ok(h.nodes().some(n=>n.props.role==='status'));assert.ok(h.nodes().some(n=>n.props.role==='alert'&&n.props.children.includes('Proposta confirmada')));
 h.find('Atualizar propostas').props.onClick();await tick();h.render();assert.equal(writes,1);assert.equal(ids,1);
});
test('post-confirmation history response cannot replace another scene',async()=>{
 let resolve;const h=harness(mocks({createLabProposal:async()=>row,getLabProposal:()=>new Promise(r=>resolve=r)}));h.render(14);
 h.find('Título da proposta').props.onChange({target:{value:'Proposta'}});h.render(14);const write=h.find('Criar proposta privada').props.onClick();await tick();h.render(15);
 resolve(row);await write;h.render(15);assert.equal(h.find('Salvar nova revisão'),undefined);assert.equal(h.find('Título da proposta').props.value,'');
});
