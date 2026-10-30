import {useRef,useState} from 'react';
import {CombatEffectsState,newDiceRequestId,sendCombatEffectCommand} from '../api';
export default function NecromancerEffects({combat,onChange}:{combat:CombatEffectsState;onChange:()=>Promise<void>}) {
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const lock=useRef(false),retry=useRef<{key:string;id:string}|null>(null);
  const effects=combat.effects.filter(e=>e.necro_spell==='aterrorrizar');
  async function use(action:string,payload:Record<string,unknown>) {
    if(lock.current)return;lock.current=true;setBusy(true);setError('');
    const key=JSON.stringify([action,payload]);
    if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('necro-effect')};
    try {await sendCombatEffectCommand({request_id:retry.current.id,expected_version:combat.version,action,payload});retry.current=null;await onChange();}
    catch(cause){setError(cause instanceof Error?cause.message:'Falha ao atualizar efeito');}
    finally{lock.current=false;setBusy(false);}
  }
  if(!effects.length)return null;
  return <details className="workspace-action-catalog"><summary>Aterrorizar · efeitos ativos</summary>
    <p>A duração diminui automaticamente ao terminar o turno de cada alvo.</p>
    {effects.some(e=>!e.target_turn_duration) && <button disabled={busy} onClick={()=>void use('necro_spell_time',{turns:1})}>Avançar 1 turno de exploração (efeito antigo)</button>}
    {effects.map(e=><div key={e.id}><span>{e.label} · {e.target_id} · {e.turns_remaining} turno(s)</span>
      <button disabled={busy} onClick={()=>void use('necro_spell_end',{effect_id:e.id})}>Encerrar Aterrorizar</button></div>)}
    {error && <p role="alert">{error}</p>}
  </details>;
}
