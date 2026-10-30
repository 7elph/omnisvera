const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(file,imports){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText,{module:m,exports:m.exports,require:id=>{if(id in imports)return imports[id];throw Error(id);},console});return m.exports;}
function harness(api){let cursor=0,state=[],effects=[],pending=[],tree;const hooks={useState(initial){const i=cursor++;if(!(i in state))state[i]=initial;return[state[i],v=>{state[i]=typeof v==='function'?v(state[i]):v;}];},useRef(initial){const i=cursor++;if(!(i in state))state[i]={current:initial};return state[i];},useEffect(fn,deps){const i=cursor++;const prev=effects[i];if(!prev||deps.some((v,j)=>v!==prev.deps[j]))pending.push(()=>{prev?.cleanup?.();effects[i]={deps,cleanup:fn()};});}};const jsx=(type,props)=>({type,props:props||{}});const component=load('src/components/SceneWorkshopPanel.tsx',{'react':hooks,'react/jsx-runtime':{jsx,jsxs:jsx},'../sceneWorkshop':api}).default;const render=()=>{cursor=0;tree=component({});pending.splice(0).forEach(f=>f());};const nodes=(n=tree)=>[n,...[n?.props?.children].flat(Infinity).filter(v=>v&&typeof v==='object').flatMap(nodes)];return{render,nodes,unmount:()=>effects.forEach(e=>e?.cleanup?.())};}
const tick=()=>new Promise(r=>setImmediate(r));
const HASH='a'.repeat(64);
const summary={initialized:true,worker:{state:'stopped'},counts:{text:{queued:276}},stats:{samples:0,average_ms:null,p50_ms:null,p95_ms:null},table_state:'inactive',admission:{free_ram_mb:400,min_free_ram_mb:512,ram_ok:true},jobs:[{id:7,entity_type:'session',entity_id:'7',queue:'text',status:'awaiting_approval',purpose:'npc_lore',revision:'r1'}]};
const preview=(overrides={})=>({...summary.jobs[0],output_hash:HASH,preview:{draft:'O anão oferece reparos.',facts:['Nimalis'],suggestions:['Uma encomenda'],questions:[]},...overrides});
const byText=(h,text)=>h.nodes().find(n=>n.type==='button'&&n.props.children===text);
async function openJob(api){
  const h=harness(api);h.render();
  h.nodes().find(n=>n.type==='details').props.onToggle({currentTarget:{open:true}});await tick();h.render();
  const card=h.nodes().find(n=>n.type==='button'&&n.props['aria-label']==='Ver bloco 7');
  await card.props.onClick();h.render();
  return h;
}
async function openImport(h,sceneId=3){
  await byText(h,'Revisar e guardar em cena').props.onClick();h.render();
  await tick();h.render();
  const select=h.nodes().find(n=>n.type==='select');
  assert.ok(select);
  select.props.onChange({target:{value:String(sceneId)}});h.render();
}

test('helper posts the exact review contract and lists existing GM scenes',async()=>{
  const calls=[],listCalls=[];const scenes=[{id:3,title:'Cena A',status:'draft',location_name:'A'},{id:4,title:'Cena B',status:'active',archived:true,location_name:'B'}];
  const api=load('src/sceneWorkshop.ts',{'./api':{workshopRequest:async(...args)=>{calls.push(args);return{job_id:7,decision:'import',status:'completed',scene_id:3,element_id:9,output_hash:HASH,revision:'r1',request_id:'review-request-001'};},listScenes:async()=>{listCalls.push(1);return scenes;}}});
  const body={decision:'import',scene_id:3,expected_revision:'r1',expected_output_hash:HASH.toUpperCase(),request_id:'review-request-001'};
  const result=await api.reviewWorkshopJob(7,body);
  assert.equal(result.element_id,9);
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],'/gm/ai-workshop/jobs/7/review');
  assert.equal(calls[0][1],'POST');
  assert.equal(calls[0][2].decision,'import');
  assert.equal(calls[0][2].scene_id,3);
  assert.equal(calls[0][2].expected_revision,'r1');
  assert.equal(calls[0][2].expected_output_hash,HASH);
  assert.equal(calls[0][2].request_id,'review-request-001');
  assert.throws(()=>api.reviewWorkshopJob(7,{...body,scene_id:null}));
  assert.throws(()=>api.reviewWorkshopJob(7,{...body,expected_output_hash:'bad'}));
  const available=await api.listWorkshopScenes();
  assert.equal(available.length,1);
  assert.equal(available[0].id,3);
  assert.equal(available[0].title,'Cena A');
  assert.equal(available[0].status,'draft');
  assert.equal(available[0].location_name,'A');
  assert.equal(listCalls.length,1);
});

test('GM confirms import into an explicit scene, locks busy and refreshes',async()=>{
  let reads=0;const reviews=[];
  const api={getWorkshop:async()=>{reads++;return summary;},getWorkshopJob:async()=>preview(),listWorkshopScenes:async()=>[{id:3,title:'Cena A',status:'draft'}],reviewWorkshopJob:async(id,body)=>{reviews.push({id,body});return{job_id:id,decision:body.decision,status:'completed',scene_id:body.scene_id,element_id:9,output_hash:body.expected_output_hash,revision:body.expected_revision,request_id:body.request_id,reviewed_at:'2026-10-26T12:00:00+00:00'};}};
  const h=await openJob(api);
  await openImport(h);
  const confirm=byText(h,'Confirmar importação');
  assert.ok(confirm);
  await confirm.props.onClick();await tick();h.render();
  assert.equal(reviews.length,1);
  assert.equal(reviews[0].id,7);
  assert.equal(reviews[0].body.decision,'import');
  assert.equal(reviews[0].body.scene_id,3);
  assert.equal(reviews[0].body.expected_revision,'r1');
  assert.equal(reviews[0].body.expected_output_hash,HASH);
  assert.match(reviews[0].body.request_id,/^[A-Za-z0-9._:-]{8,120}$/);
  assert.ok(reads>=2);
});

test('failed review stays visible and retries with the same request_id',async()=>{
  let attempts=0;const requests=[];
  const api={getWorkshop:async()=>summary,getWorkshopJob:async()=>preview(),listWorkshopScenes:async()=>[{id:3,title:'Cena A',status:'draft'}],reviewWorkshopJob:async(id,body)=>{attempts++;requests.push(body.request_id);if(attempts===1)throw Error('Sem conexão');return{job_id:id,decision:body.decision,status:'completed',scene_id:body.scene_id,element_id:9,output_hash:HASH,revision:'r1',request_id:body.request_id};}};
  const h=await openJob(api);
  await openImport(h);
  await byText(h,'Confirmar importação').props.onClick();h.render();
  assert.ok(h.nodes().some(n=>n.props.role==='alert'));
  const retry=byText(h,'Tentar importação novamente');
  assert.ok(retry);
  await retry.props.onClick();await tick();h.render();
  assert.equal(attempts,2);
  assert.equal(requests[0],requests[1]);
});

test('reject requires explicit confirmation and does not pick a scene',async()=>{
  let sceneReads=0;const reviews=[];
  const api={getWorkshop:async()=>summary,getWorkshopJob:async()=>preview(),listWorkshopScenes:async()=>{sceneReads++;return[{id:3,title:'Cena A',status:'draft'}];},reviewWorkshopJob:async(id,body)=>{reviews.push(body);return{job_id:id,decision:'reject',status:'cancelled',scene_id:null,element_id:null,output_hash:HASH,revision:'r1',request_id:body.request_id};}};
  const h=await openJob(api);
  await byText(h,'Rejeitar rascunho').props.onClick();h.render();
  assert.equal(reviews.length,0);
  assert.match(h.nodes().filter(n=>typeof n.props.children==='string').map(n=>n.props.children).join(' '),/campanha não é alterada/);
  await byText(h,'Confirmar rejeição').props.onClick();await tick();h.render();
  assert.equal(reviews.length,1);
  assert.equal(reviews[0].decision,'reject');
  assert.equal(reviews[0].scene_id,null);
  assert.equal(sceneReads,0);
});

test('code drafts are labeled analysis/suggestion and double submits stay locked',async()=>{
  let calls=0,release;const pendingReview=new Promise(resolve=>{release=resolve;});
  const api={getWorkshop:async()=>summary,getWorkshopJob:async()=>preview({queue:'code'}),listWorkshopScenes:async()=>[{id:3,title:'Cena A',status:'draft'}],reviewWorkshopJob:async()=>{calls++;return pendingReview;}};
  const h=await openJob(api);
  assert.ok(h.nodes().some(n=>typeof n.props.children==='string'&&n.props.children.includes('Análise/sugestão textual de código')));
  await openImport(h);
  const first=byText(h,'Confirmar importação').props.onClick();
  const second=byText(h,'Confirmar importação').props.onClick();
  assert.equal(calls,1);
  release({job_id:7,decision:'import',status:'completed',scene_id:3,element_id:9,output_hash:HASH,revision:'r1',request_id:'review-lock-001'});
  await first;await second;
});

test('detail without output_hash cannot start a review',async()=>{
  const api={getWorkshop:async()=>summary,getWorkshopJob:async()=>preview({output_hash:undefined}),listWorkshopScenes:async()=>[],reviewWorkshopJob:async()=>{throw Error('não deveria chamar');}};
  const h=await openJob(api);
  assert.ok(!h.nodes().some(n=>n.type==='button'&&n.props.children==='Revisar e guardar em cena'));
  assert.ok(h.nodes().some(n=>typeof n.props.children==='string'&&n.props.children.includes('sem hash ou revisão')));
});

test('repeated content warning is readable and blocks import while preserving rejection',async()=>{
  const api={getWorkshop:async()=>summary,getWorkshopJob:async()=>preview({status:'needs_review',preview:{draft:'Rascunho preservado.',quality_notes:['repeated_content']}}),listWorkshopScenes:async()=>[],reviewWorkshopJob:async()=>{throw Error('must not import');}};
  const h=await openJob(api);
  assert.equal(byText(h,'Revisar e guardar em cena').props.disabled,true);
  assert.ok(byText(h,'Rejeitar rascunho'));
  assert.ok(h.nodes().some(n=>n.props.className==='warning-text'&&JSON.stringify(n.props.children).includes('trechos repetidos')));
});
