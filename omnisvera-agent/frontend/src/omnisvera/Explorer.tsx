import { useRef, useState } from 'react';

export type Identity = {predictor_id:string;predictor_version:string};
export type SignalRef = {signal_id:string;entity_ref?:string;observed_at?:string;observation_hash?:string};
export type Get = <T>(path:string)=>Promise<T>;
type Signal = SignalRef & {id:number;value:unknown;unit:string|null;schema:string;recorded_at:string;source:Record<string,string>;age_seconds:number|null;freshness_at_capture:string};
type Experience = Identity & {experience_id:string;state_version:number;previous_experience_id:string|null;previous_state_version:number|null;learned_state_hash:string;integrity_computed:string;integrity_ok:boolean;learned_state_schema:string;created_at:string;performance:{resolved_predictions:number;mean_brier:number|null};source_predictions:{id:number;claim?:string;status:string}[];source_outcomes:{id:number;prediction_id?:number;outcome?:number;calibration_score?:number;resolved_at?:string;status?:string}[]};
const shown=(x:unknown)=>x===null||x===undefined?'Não registrado':String(x);
export const date=(x:unknown)=>typeof x==='string'&&!Number.isNaN(Date.parse(x))?(/[zZ]|[+-]\d\d:\d\d$/.test(x)?new Date(x).toLocaleString('pt-BR'):`${x} (fuso não registrado)`):shown(x);
export function Badge({status}:{status:string}){return <span className={`observer-badge ${['error','denied','stale','unavailable'].includes(status)?'observer-warning':''}`}>{status}</span>;}
export function Technical({title,value}:{title:string;value:unknown}){return <details><summary>{title}</summary><pre>{value==null?'Não registrado':JSON.stringify(value,null,2)}</pre></details>;}
function Pages({offset,total,size,busy,go}:{offset:number;total:number;size:number;busy:boolean;go:(n:number)=>void}){
  return <div className="observer-pagination"><button disabled={busy||offset===0} onClick={()=>go(Math.max(0,offset-size))}>Anterior</button><span>{total?`${offset+1}–${Math.min(offset+size,total)} de ${total}`:'0 registros'}</span><button disabled={busy||offset+size>=total} onClick={()=>go(offset+size)}>Próximos</button></div>;
}
function useRead<T>() {
  const [data,setData]=useState<T|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const sequence=useRef(0);
  async function load(get:Get,path:string){const id=++sequence.current;setBusy(true);setError('');
    try{const value=await get<T>(path);if(id===sequence.current)setData(value);}
    catch(e){if(id===sequence.current)setError(e instanceof Error?e.message:'Leitura indisponível.');}
    finally{if(id===sequence.current)setBusy(false);}}
  return {data,busy,error,load};
}
function ReadStatus({busy,error,hasData}:{busy:boolean;error:string;hasData:boolean}){
  return <>{busy&&<p role="status">Consultando registros…</p>}{error&&<p role="alert" className="observer-error">{error}{hasData?' Os dados abaixo são da leitura anterior; não foram atualizados.':''}</p>}</>;
}

export function SignalsExplorer({get,reference}:{get:Get;reference:SignalRef|null}){
  const initial={signal_id:reference?.signal_id??'',entity_ref:reference?.entity_ref??'',since:'',until:''};
  const [filters,setFilters]=useState(initial),[applied,setApplied]=useState(initial),[offset,setOffset]=useState(0);
  const read=useRead<{items:Signal[];total:number;read_at:string}>();
  function load(next=0,f=applied){const query=new URLSearchParams({offset:String(next)});
    for(const key of ['signal_id','entity_ref'] as const)if(f[key])query.set(key,f[key]);
    for(const key of ['since','until'] as const)if(f[key])query.set(key,new Date(f[key]).toISOString());
    setApplied(f);setOffset(next);void read.load(get,`/api/football/signals?${query}`);}
  return <section className="panel"><h2>Sinais persistidos</h2><p>Filtrar consulta apenas o banco. Não observa o mundo novamente.</p>
    <form className="observer-filters" onSubmit={e=>{e.preventDefault();load(0,filters);}}><label>Signal ID<input value={filters.signal_id} onChange={e=>setFilters({...filters,signal_id:e.target.value})}/></label><label>Entidade<input value={filters.entity_ref} onChange={e=>setFilters({...filters,entity_ref:e.target.value})}/></label><label>De (horário local)<input type="datetime-local" value={filters.since} onChange={e=>setFilters({...filters,since:e.target.value})}/></label><label>Até (horário local)<input type="datetime-local" value={filters.until} onChange={e=>setFilters({...filters,until:e.target.value})}/></label><button disabled={read.busy}>Filtrar registros</button></form>
    {reference&&<p className="observer-notice">Referência da Prediction: {reference.observed_at?date(reference.observed_at):'sem timestamp exato'}. {reference.observation_hash?`Hash: ${reference.observation_hash}`:'Sem hash da observação.'} O histórico filtrado não prova por si só qual observação foi usada.</p>}
    <ReadStatus {...read} hasData={!!read.data}/>{!read.data&&!read.busy&&!read.error&&<p>Use “Filtrar registros” para consultar os sinais persistidos.</p>}
    {read.data&&<><p>Leitura: {date(read.data.read_at)}. Idade não equivale a validade; não há TTL presumido.</p>{!read.data.items.length&&<p>Nenhum sinal persistido corresponde a estes filtros.</p>}
    {read.data.items.map(s=><article className="observer-record" key={s.id}><div className="observer-section-heading"><h3>{s.signal_id}</h3><Badge status={s.freshness_at_capture}/></div><p>{s.entity_ref??'Sem entidade'} · <strong>{shown(s.value)}</strong> {s.unit}</p><p>Observado: {date(s.observed_at)} · idade {s.age_seconds===null?'indisponível':`${Math.floor(s.age_seconds/60)} min`}</p><p>Freshness registrada na captura, não saúde ao vivo.</p><p>Origem: {Object.keys(s.source).length?Object.entries(s.source).map(([k,v])=>`${k}: ${v}`).join(' · '):'Não registrada'}</p><Technical title="Identificação e proveniência do sinal" value={{schema:s.schema,observation_hash:s.observation_hash,recorded_at:s.recorded_at,source:s.source}}/></article>)}
    <Pages offset={offset} total={read.data.total} size={30} busy={read.busy} go={n=>load(n)}/></>}
  </section>;
}

export function ExperienceHistory({get,identities,selected,inspect}:{get:Get;identities:Identity[];selected:Identity|null;inspect:(id:number)=>void}){
  const [choice,setChoice]=useState(selected?JSON.stringify(selected):''),[identity,setIdentity]=useState<Identity|null>(null),[offset,setOffset]=useState(0);
  const read=useRead<{items:Experience[];total:number}>();
  function load(x:Identity,next=0){setIdentity(x);setOffset(next);void read.load(get,`/api/football/experiences?${new URLSearchParams({...x,offset:String(next)})}`);}
  return <section className="panel"><h2>Histórico de Experience</h2><p>Versões persistidas, da mais recente à mais antiga. Nenhum aprendizado é executado aqui.</p>
    <form className="observer-filters" onSubmit={e=>{e.preventDefault();if(choice)load(JSON.parse(choice));}}><label>Predictor / versão<select value={choice} onChange={e=>setChoice(e.target.value)}><option value="">Selecione um predictor</option>{identities.map(x=><option key={`${x.predictor_id}:${x.predictor_version}`} value={JSON.stringify({predictor_id:x.predictor_id,predictor_version:x.predictor_version})}>{x.predictor_id} · {x.predictor_version}</option>)}</select></label><button disabled={!choice||read.busy}>Consultar histórico</button></form>
    {!identities.length&&<p>Nenhuma Experience Football persistida.</p>}<ReadStatus {...read} hasData={!!read.data}/>{read.data?.items.length===0&&<p>Nenhuma versão encontrada.</p>}
    {read.data?.items.map(x=><article className="observer-record" key={x.experience_id}><div className="observer-section-heading"><h3>Estado v{x.state_version}</h3><Badge status={x.integrity_ok?'integrity verified':'error'}/></div><p>{x.predictor_id} · {x.predictor_version} · {date(x.created_at)}</p><p>Anterior: {x.previous_state_version===null?'Sem versão anterior':`v${x.previous_state_version}`}</p><p>{x.performance.resolved_predictions??0} resolvidas · Brier {x.performance.mean_brier??'indisponível'}</p><Technical title="ID, hash e lineage" value={{experience_id:x.experience_id,learned_state_schema:x.learned_state_schema,learned_state_hash:x.learned_state_hash,integrity_computed:x.integrity_computed,previous_experience_id:x.previous_experience_id}}/>
    <details><summary>Predictions e Outcomes que contribuíram</summary>{!x.source_predictions.length&&<p>Nenhuma Prediction contribuinte registrada.</p>}{x.source_predictions.map(p=><p key={p.id}>{p.status==='unavailable'?`Prediction #${p.id} indisponível`:<button onClick={()=>inspect(p.id)}>Abrir Prediction #{p.id} · {p.claim}</button>}</p>)}{!x.source_outcomes.length&&<p>Nenhum Outcome contribuinte registrado.</p>}{x.source_outcomes.map(o=><p key={o.id}>Outcome #{o.id} · {o.status==='unavailable'?'indisponível':<>resultado {o.outcome} · Brier {o.calibration_score} · {date(o.resolved_at)} <button onClick={()=>inspect(o.prediction_id!)}>Abrir Prediction #{o.prediction_id}</button></>}</p>)}</details></article>)}
    {read.data&&identity&&<Pages offset={offset} total={read.data.total} size={20} busy={read.busy} go={n=>load(identity,n)}/>}
  </section>;
}
