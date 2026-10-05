import { useEffect, useRef } from 'react';
import { Badge, date, ExperienceHistory, SignalsExplorer, Technical, type Get, type Identity, type SignalRef } from './Explorer';

export function Investigation({detail,busy,error,get,close,inspect}:{detail:Record<string,unknown>|null;busy:boolean;error:string;get:Get;close:()=>void;inspect:(id:number)=>void}) {
  const dialog=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const node=dialog.current;node?.showModal();return ()=>node?.close();},[]);
  const experience=detail?.experience as (Identity & {state_version:number;integrity_ok:boolean})|null;
  const resolution=detail?.resolution as Record<string,unknown>|null;
  const evidence=detail?.evidence as Record<string,unknown>|null;
  const refs=(detail?.signal_refs??[]) as SignalRef[];
  return <dialog ref={dialog} className="observer-investigation omnisvera-observer" aria-labelledby="investigation-title" onCancel={e=>{e.preventDefault();close();}}>
    <header><h2 id="investigation-title">Investigar previsão</h2><button autoFocus onClick={close}>Fechar</button></header>
    <p className="observer-notice">Partida → previsão → evidência → resultado → aprendizado · READ-ONLY</p>
    {busy&&<p role="status">Consultando registros persistidos…</p>}
    {error&&<p role="alert">{error}</p>}
    {detail&&<>
      <section><h3>Partida</h3><p>{detail.subject_ref?String(detail.subject_ref):'Partida não vinculada ao registro.'}</p><p>O texto da previsão não substitui uma identificação estruturada da partida.</p></section>
      <section><h3>O que foi previsto</h3><p className="observer-claim">{String(detail.claim)}</p><strong className="observer-probability">{(Number(detail.probability)*100).toFixed(1)}%</strong><p>Probabilidade registrada pelo predictor — não uma recomendação da interface.</p><Badge status={String(detail.status)}/><p>Registrada: {date(detail.created_at)}</p><p>Horizonte: {date(detail.horizon)}</p><p>O status exibido é o persistido; a tela não resolve previsões vencidas.</p></section>
      <section><h3>Evidência usada</h3><p>Snapshot: {detail.snapshot_intact?'integridade verificada':'integridade não confirmada'}.</p><p>Capturado: {date(evidence?.created_at)}</p><p>Validade atual desconhecida: não há prazo de validade presumido.</p>
        {!refs.length&&<p className="observer-notice">Nenhum sinal explicitamente referenciado. Sinais atuais ou de outras partidas não serão apresentados como fundamento desta previsão.</p>}
        {refs.map((ref,i)=><details key={i}><summary>Explorar sinal referenciado: {ref.signal_id}</summary><SignalsExplorer get={get} reference={ref}/></details>)}
      </section>
      <section><h3>Resultado observado</h3>{resolution?<><p>Resultado registrado: {String(resolution.outcome)}</p><p>Brier: {String(resolution.calibration_score??'Indisponível')} · resolvida em {date(resolution.resolved_at)}</p></>:<p>Ainda sem resultado persistido. Não é possível concluir acerto ou erro.</p>}</section>
      <section><h3>Experience associada e evolução</h3>{experience?<><p>{experience.predictor_id} · {experience.predictor_version} · estado v{experience.state_version}</p><p>Referência da previsão: {detail.experience_reference_intact===true?'confere':'não confirmada'}. Integridade: {experience.integrity_ok?'verificada':'não confirmada'}.</p><p>O histórico mostra contribuições registradas; uma versão posterior não prova, sozinha, aprendizado a partir desta previsão.</p><details><summary>Consultar histórico e contribuições</summary><ExperienceHistory key={`${experience.predictor_id}:${experience.predictor_version}`} get={get} identities={[experience]} selected={experience} inspect={inspect}/></details></>:<p>Sem Experience associada disponível.</p>}</section>
      <Technical title="Prova técnica: IDs, hashes e proveniência" value={detail}/>
    </>}
  </dialog>;
}
