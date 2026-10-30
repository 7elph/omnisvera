import { useRef, useState } from 'react';
import { CombatEffectsState, newDiceRequestId, sendCombatEffectCommand } from '../api';
export default function DornSpellEffects({combat,onChange}:{combat:CombatEffectsState;onChange:()=>Promise<void>}) {
  const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const lock=useRef(false);
  const retry=useRef<{key:string;id:string}|null>(null);
  const effects=combat.effects.filter(e=>e.spell && !e.environmental && (e.remaining_seconds!=null || e.immobilized));
  async function use(action:string,payload:Record<string,unknown>){
    if(lock.current)return; lock.current=true;setBusy(true);setError('');
    const key=JSON.stringify([action,payload,combat.version]);
    if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('spell-effect')};
    try{await sendCombatEffectCommand({request_id:retry.current.id,expected_version:combat.version,action,payload});retry.current=null;await onChange();}
    catch(reason){setError(reason instanceof Error?reason.message:'Falha no efeito');}finally{lock.current=false;setBusy(false);}
  }
  if(!effects.length)return null;
  return <details className="workspace-action-catalog workspace-dorn-details"><summary>Magias ativas · {effects.length}</summary>
    <p>Tempo ficcional: rodadas avançam 10 s. Fora do combate, informe o tempo transcorrido; não é relógio real.</p>
    <button disabled={busy} onClick={()=>void use('dorn_spell_time',{seconds:600})}>Avançar 10 min de exploração</button>
    {!combat.encounter?.active && <button disabled={busy} onClick={()=>void use('dorn_spell_time',{seconds:10})}>Avançar uma rodada de exploração</button>}
    {effects.map(effect=><article key={effect.id}><span>{effect.label}<small>{effect.target_id} · {effect.turns_remaining!=null ? `${effect.turns_remaining} turnos do alvo · JP normal` : `${Math.ceil((effect.remaining_seconds || 0)/60)} min restantes`}{effect.spell==='levitacao'?` · altura ${effect.altitude_meters || 0} m`:''}</small></span>
      {effect.spell==='levitacao'&&<><button disabled={busy} onClick={()=>void use('dorn_levitate_move',{effect_id:effect.id,vertical_meters:2})}>Subir 2 m</button><button disabled={busy} onClick={()=>void use('dorn_levitate_move',{effect_id:effect.id,vertical_meters:-2})}>Descer 2 m</button></>}
      {effect.spell==='levitacao'&&<button disabled={busy} onClick={()=>void use('dorn_levitate_stabilize',{effect_id:effect.id})}>Estabilizar · gastar ação</button>}
      <button disabled={busy} onClick={()=>void use('dorn_spell_end',{effect_id:effect.id})}>Encerrar efeito</button></article>)}
    {error&&<p role="alert">{error}</p>}
  </details>;
}
