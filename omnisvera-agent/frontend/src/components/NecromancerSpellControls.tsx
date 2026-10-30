import { useEffect, useRef, useState } from 'react';
import { AttackResolution, CombatEffectsState, CharacterResource, WorkspaceToken, newDiceRequestId, useCharacterTechnique } from '../api';
import { combatActionBlock } from './combatActionAvailability';
import { mediaUrlFromVaultPath } from '../api';
import ActionControlCard from './ActionControlCard';

type Props = { spell:string; mode:'gm'|'player'; targets:WorkspaceToken[]; resources:CharacterResource[];
  combat:CombatEffectsState; hp:number; rollMode:'digital'|'physical';
  onResolved:(result:AttackResolution)=>void; onChange:()=>Promise<void>; onClose:()=>void;
  gridded?:boolean; attackerTokenId?:string; attackerCharacterId?:string;
  ability?:{description?:string|null;image_path?:string|null} };

export default function NecromancerSpellControls(props:Props) {
  const touch=props.spell==='toque-sombrio';
  const high=['clonagem','magia-da-morte'].includes(props.spell);
  const [selected,setSelected]=useState<string[]>([]);
  const [memorized,setMemorized]=useState(false);
  const [physical,setPhysical]=useState('');
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [result,setResult]=useState('');
  const lock=useRef(false), retry=useRef<{key:string;id:string}|null>(null);
  const free=props.resources.find(r=>r.key===(high?props.spell.replaceAll('-','_'):touch?'toque_sombrio':'aterrorrizar'));
  const slots=props.resources.find(r=>r.key==='magias_de_1o_circulo');
  const extra=!(free && free.current>0);
  const block=combatActionBlock(props.combat,'morthak',props.hp);
  const chosen=props.targets.filter(t=>selected.includes(t.id));
  const valid=(!touch || chosen.length===1)
    && (!extra || (!high && memorized && (slots?.current || 0)>0))
    && (!touch || props.rollMode!=='physical' || (Number(physical)>=1 && Number(physical)<=20));
  const cloning=props.spell==='clonagem' && (props.combat.effects || []).some(e=>e.necro_spell==='clonagem');
  const armId=useRef("");

  useEffect(() => {
    if (!props.gridded || !touch) return;
    const confirm = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!detail.targetId || detail.armId !== armId.current) return;
      armId.current = "";
      window.dispatchEvent(new CustomEvent('omnisvera-targeting-clear', { detail: { armId: detail.armId } }));
      void cast(detail.targetId);
    };
    window.addEventListener('omnisvera-targeting-confirm', confirm);
    return () => window.removeEventListener('omnisvera-targeting-confirm', confirm);
  });

  async function cast(targetOverride?: string) {
    const gridValid = targetOverride
      && (!extra || (!high && memorized && (slots?.current || 0)>0))
      && (!touch || props.rollMode!=='physical' || (Number(physical)>=1 && Number(physical)<=20));
    if(lock.current || (!valid && !gridValid) || block)return;
    lock.current=true;setBusy(true);setError('');setResult('');
    const chosenIds = targetOverride ? [targetOverride] : chosen.map(t=>t.id);
    const payload={mode:props.rollMode==='digital'?'automatic':undefined,use_memorized:extra && memorized,
      ...(touch?{target_type:'token' as const,target_id:chosenIds[0],roll_mode:props.rollMode,
        ...(props.rollMode==='physical'?{d20:Number(physical)}:{})}:{})};
    const key=JSON.stringify([props.spell,payload]);
    if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('necro')};
    let accepted=false;
    try {
      const response=await useCharacterTechnique('morthak',props.spell,{...payload,request_id:retry.current.id});
      accepted=true;retry.current=null;
      if(touch){
        if((response as AttackResolution).status==='pending')props.onResolved(response as AttackResolution);
        props.onClose();
      }
      else if(high){
        const spell=(response as {protocol_result?:{spell:string;hp_after?:number;results:Array<{target:string;execution?:string;saving_throw?:{success:boolean}}>}}).protocol_result;
        setResult((spell?.results || []).map(t=>`${t.target}: ${t.execution || (t.saving_throw?.success?'resistiu':'morto')}`).join(' · ')+(spell?.hp_after!=null?` · PV de Morthak: ${spell.hp_after}`:''));
      } else {
        const spell=(response as {protocol_result?:{duration_turns:number;results:Array<{target:string;skipped?:string;effect?:unknown;saving_throw?:{success:boolean}}>}}).protocol_result;
        setResult((spell?.results || []).map(t=>`${t.target}: ${t.skipped || (t.effect?'aterrorizado': 'resistiu')}`).join(' · ')+` · ${spell?.duration_turns} turnos individuais`);
      }
      await props.onChange();
    } catch(cause) {setError(accepted?'Magia aceita. Aguarde a sincronização; não conjure novamente.':cause instanceof Error?cause.message:'Falha na magia');}
    finally {lock.current=false;setBusy(false);}
  }

  async function endCloning(){
    if(lock.current)return;lock.current=true;setBusy(true);setError('');
    const key='clonagem-end';
    if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('necro-end')};
    let accepted=false;
    try{await useCharacterTechnique('morthak','clonagem',{mode:'end',request_id:retry.current.id});accepted=true;retry.current=null;await props.onChange();}
    catch(cause){setError(accepted?'Concentração encerrada; aguarde sincronização.':cause instanceof Error?cause.message:'Falha ao encerrar');}
    finally{lock.current=false;setBusy(false);}
  }

  return <ActionControlCard title={high?(props.spell==='clonagem'?'Clonagem':'Magia da Morte'):touch?'Toque Sombrio':'Aterrorizar'} label="Conjuração de Necromante" onClose={props.onClose}
    icon={props.ability?.image_path ? mediaUrlFromVaultPath(props.ability.image_path) || undefined : undefined}
    description={props.ability?.description || (high?(props.spell==='clonagem'?'Consome 1 fragmento de cristal e 1 uso diário. No combate, clones aparecem no próximo turno de Morthak e duram 5 rodadas.':'Texto literal atinge criaturas elegíveis, inclusive aliados, por proximidade. JPC evita; Morthak perde 90% dos PV atuais.'):touch?'Selecione um alvo adjacente no grid. No modo Digital, acerto, dano e efeito são aplicados automaticamente.':'O backend seleciona os inimigos no raio pelo grid e confere DV e JPS automaticamente.')}
    summary={<small>Uso diário: {free?.current || 0}/{free?.maximum || 0}</small>}>
    {props.spell==='magia-da-morte' && <p role="status">Atenção: pode atingir inclusive aliados elegíveis; Morthak perde 90% dos PV atuais.</p>}
    {touch && props.gridded
      ? <button disabled={busy || Boolean(block)} onClick={() => {
          armId.current = crypto.randomUUID();
          window.dispatchEvent(new CustomEvent('omnisvera-targeting-arm', { detail: {
            actionRef: `technique:morthak:toque-sombrio`, actionLabel: "Morthak · Toque Sombrio",
            attackerTokenId: props.attackerTokenId || "", attackerCharacterId: props.attackerCharacterId || "morthak",
            slot: "touch", armId: armId.current,
          } }));
        }}>Mirar no grid</button>
      : touch && props.targets.filter(t=>t.current_hp!=null && t.current_hp>0).map(t=><label key={t.id}>
      <input type="checkbox" checked={selected.includes(t.id)} disabled={busy} onChange={e=>setSelected(previous=>e.target.checked?(touch?[t.id]:[...previous,t.id]):previous.filter(id=>id!==t.id))}/>{t.name}
    </label>)}
    {touch && props.rollMode==='physical' && <label>d20 físico<input aria-label="d20 físico de Toque Sombrio" type="number" min="1" max="20" value={physical} onChange={e=>setPhysical(e.target.value)}/></label>}
    <p>Uso diário: {free?.current || 0}/{free?.maximum || 0}{!high && ` · Magias memorizadas: ${slots?.current || 0}`}</p>
    {extra && !high && <label><input type="checkbox" checked={memorized} onChange={e=>setMemorized(e.target.checked)}/>Consumir uma magia memorizada de 1º círculo</label>}
    {block && <p role="status">{block}</p>}
    {cloning?<button disabled={busy} onClick={()=>void endCloning()}>Encerrar concentração</button>:<button disabled={busy || !valid || Boolean(block)} onClick={()=>void cast()}>Conjurar</button>}
    <button disabled={busy} onClick={props.onClose}>Fechar</button>
    {result && <p role="status">{result}</p>}{error && <p role="alert">{error}</p>}
  </ActionControlCard>;
}
