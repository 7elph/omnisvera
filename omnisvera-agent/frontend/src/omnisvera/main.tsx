import { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import '../styles.css';
import './style.css';
import './explorer.css';
import { Badge, date, ExperienceHistory, SignalsExplorer, type Identity, type SignalRef } from './Explorer';
import { Investigation } from './Investigation';

type Prediction = {id:number;claim:string;probability:number;status:string;horizon:string;evidence_mode:string};
type Football = {environment_label:string;predictions:Prediction[];total:number;metrics:{evidence_mode:string;count:number;mean_brier:number|null;first_resolved_at:string;last_resolved_at:string}[];experiences:Record<string,unknown>[]};
type Monitor = {read_at:string;football_last_run:{run_started_at:string;success:number}|null;events:{timestamp:string;action:string;result:string;duration_ms:number}[];scheduler:{run_started_at:string;success:number;signals_seen:number}[]};
function App(){
  const [page,setPage]=useState('football');
  const [signalRef,setSignalRef]=useState<SignalRef|null>(null),[selectedExperience,setSelectedExperience]=useState<Identity|null>(null);
  const detailSequence=useRef(0);
  const [drawerOpen,setDrawerOpen]=useState(false),[detailError,setDetailError]=useState('');
  const [detailBusy,setDetailBusy]=useState(false);
  const [token,setToken]=useState(''); const [connected,setConnected]=useState(false);
  const [football,setFootball]=useState<Football|null>(null); const [monitor,setMonitor]=useState<Monitor|null>(null);
  const [detail,setDetail]=useState<Record<string,unknown>|null>(null); const [error,setError]=useState('');
  const [busy,setBusy]=useState(false); const [offset,setOffset]=useState(0);
  async function get<T,>(path:string):Promise<T>{const r=await fetch(path,{headers:{'X-Omnisvera-App-Token':token},cache:'no-store'});if(!r.ok)throw Error(r.status===401?'Token inválido.':r.status===403?'Leitura não autorizada.':r.status===422?'Filtros inválidos. Confira o período.':'Dados indisponíveis. Verifique o serviço e o schema.');return r.json();}
  async function load(page=0){setBusy(true);setError('');try{const f=await get<Football>(`/api/football?offset=${page}`);setFootball(f);setOffset(page);setConnected(true);try{setMonitor(await get<Monitor>('/api/monitor'));}catch{setMonitor(null);setError('Monitor indisponível. A leitura do Football está disponível.');}}catch(e){setError(String(e));}finally{setBusy(false);}}
  async function inspect(id:number){const seq=++detailSequence.current;setDrawerOpen(true);setDetailError('');setDetail(null);setDetailBusy(true);try{const value=await get<Record<string,unknown>>(`/api/football/predictions/${id}`);if(seq===detailSequence.current)setDetail(value);}catch(e){if(seq===detailSequence.current)setDetailError(String(e));}finally{if(seq===detailSequence.current)setDetailBusy(false);}}
  return <div className="app-shell omnisvera-observer"><header className="hero"><h1>OMNISVERA</h1><span>READ-ONLY · abrir ou atualizar não executa predictors</span></header>
    <main><div className="observer-heading"><div><p>WORLD / FOOTBALL</p><h1>Football</h1><p>Estado persistido, resultados observados e experiência acumulada.</p></div>{connected&&<button disabled={busy} onClick={()=>load(offset)}>Atualizar leitura</button>}</div>
    {error&&<p role="alert" className="observer-error">{error}{connected?' Última leitura preservada; atualização não confirmada.':''}</p>}
    {!connected?<form className="panel" onSubmit={e=>{e.preventDefault();void load();}}><h2>Acesso do operador</h2><p>Use o token exclusivo do Omnisvera App.</p><input aria-label="Token do App" type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)}/><button disabled={busy||!token}>Entrar</button></form>:<>
    <nav className="observer-nav" aria-label="Leituras do Football">{['football','signals','experience'].map((p,i)=><button key={p} aria-current={page===p?'page':undefined} onClick={()=>{setPage(p);setSignalRef(null);setSelectedExperience(null);}}>{['Predictions e sistema','Sinais','Experience'][i]}</button>)}</nav>
    <p className="observer-environment">{football?.environment_label}</p>
    {page==='signals'&&<SignalsExplorer key={JSON.stringify(signalRef)} get={get} reference={signalRef}/>}
    {page==='experience'&&<ExperienceHistory key={JSON.stringify(selectedExperience)} get={get} identities={(football?.experiences??[]).map(x=>({predictor_id:String(x.predictor_id),predictor_version:String(x.predictor_version)}))} selected={selectedExperience} inspect={inspect}/>}
    {page==='football'&&<>
    <section className="observer-metrics"><article className="panel"><small>Predictions registradas</small><h2>{football?.total}</h2></article>{football?.metrics.map(m=><article className="panel" key={m.evidence_mode}><small>Brier · {m.evidence_mode}</small><h2>{m.mean_brier?.toFixed(4)??'—'}</h2><p>{m.count} resolvidas · menor é melhor</p><small>Resoluções: {date(m.first_resolved_at)} — {date(m.last_resolved_at)}</small></article>)}<article className="panel"><small>Accuracy</small><h2>Indisponível</h2><p>Critério de classificação não definido.</p></article><article className="panel"><small>ROI</small><h2>Indisponível</h2><p>Odds e stakes não registrados.</p></article></section>
    <div className="observer-grid"><section className="panel"><h2>Predictions</h2><p>Abrir uma previsão não executa o modelo.</p>{!football?.predictions.length&&<p>Nenhuma previsão Football persistida nesta página.</p>}{football?.predictions.map(p=><button className="observer-prediction" key={p.id} onClick={()=>inspect(p.id)}><span>#{p.id} · {p.claim}<small>{p.status} · {p.evidence_mode} · horizonte {p.horizon}</small></span><strong>{(p.probability*100).toFixed(1)}%</strong></button>)}<div className="observer-pagination"><button disabled={busy||offset===0} onClick={()=>load(Math.max(0,offset-30))}>Anterior</button><button disabled={busy||offset+30>=(football?.total??0)} onClick={()=>load(offset+30)}>Próximas</button></div>
    <h2>Experiences atuais</h2>{!football?.experiences.length&&<p>Nenhuma Experience Football persistida.</p>}{football?.experiences.map((x,i)=><article key={i}><strong>{String(x.predictor_id)} · {String(x.predictor_version)}</strong><p>Estado v{String(x.latest_state_version??x.state_version)} · integridade {x.integrity_ok?'verificada':'não confirmada'}</p></article>)}</section>
    <aside className="panel"><h2>System Monitor</h2>{monitor?<p><Badge status={error?'unavailable':'healthy'}/> Banco legível na leitura de {date(monitor.read_at)}.</p>:<p><Badge status="unavailable"/> Monitor indisponível; nenhum estado de saúde confirmado.</p>}<p>Serviços ao vivo: não consultados. Estes eventos são históricos, não um teste de saúde atual.</p><h3>Atualização do Football</h3>{monitor?.football_last_run?<><p>Última execução: {date(monitor.football_last_run.run_started_at)} · {monitor.football_last_run.success?'concluída':'falhou'}</p><p>{monitor.football_last_run.success?'Esta é a última atualização registrada, não uma garantia de dados atuais.':'A última execução não concluiu. A atualização dos sinais pode estar incompleta; o impacto exato não está comprovado.'}</p></>:<p>Sem execução identificada para Football.</p>}<h3>Últimas execuções registradas</h3>{monitor&&!monitor.events.length&&<p>Sem eventos registrados.</p>}{monitor?.events.map((e,i)=><div className="observer-event" key={i}><code>{e.action}</code><Badge status={e.result}/><small>{date(e.timestamp)} · {e.duration_ms?.toFixed(0)} ms</small></div>)}<h3>Scheduler</h3>{monitor&&!monitor.scheduler.length&&<p>Nenhuma execução registrada.</p>}{monitor?.scheduler.map((r,i)=><p key={i}><Badge status={r.success?'success':'error'}/> {date(r.run_started_at)} · {r.signals_seen} sinais</p>)}</aside></div>
    </>}
    </>}{drawerOpen&&<Investigation detail={detail} busy={detailBusy} error={detailError} get={get} inspect={inspect} close={()=>{detailSequence.current++;setDrawerOpen(false);setDetail(null);setDetailBusy(false);}}/>}</main></div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
