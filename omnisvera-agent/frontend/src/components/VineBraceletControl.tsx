import { useEffect, useRef, useState } from 'react';
import { useVineBracelet, mediaUrlFromVaultPath, WorkspaceToken } from '../api';
import TargetSelect from './TargetSelect';
import SheetDetail from './SheetDetail';

export default function VineBraceletControl({ icon, equipped, disabled, tokens, onChange, remaining = 2, maximum = 2, gridded=tokens.some(t=>Boolean(t.grid_position)), attackerTokenId=tokens.find(t=>t.character_id==='vezemir')?.id || '' }: {
  icon?: string | null; equipped: boolean; disabled: boolean;
  tokens: WorkspaceToken[]; onChange: () => Promise<void>;
  remaining?: number; maximum?: number;
  gridded?:boolean; attackerTokenId?:string;
}) {
  const [target, setTarget] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const requestId = useRef<string | null>(null);
  const lock = useRef(false);
  const armId=useRef('');
  useEffect(()=>{
    const confirm=(event:Event)=>{
      const detail=(event as CustomEvent).detail;
      if(!detail?.armId || detail.armId!==armId.current || !tokens.some(t=>t.id===detail.targetId))return;
      armId.current='';requestId.current=null;void use(detail.targetId);
    };
    window.addEventListener('omnisvera-targeting-confirm',confirm);
    return()=>window.removeEventListener('omnisvera-targeting-confirm',confirm);
  });
  async function use(targetOverride?:string) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError('');
    requestId.current ||= `vines-${crypto.randomUUID()}`;
    try { await useVineBracelet(targetOverride || target, requestId.current); requestId.current = null; await onChange(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Falha ao usar a pulseira'); }
    finally { lock.current = false; setBusy(false); }
  }
  return <article tabIndex={0}>
<span><SheetDetail title="Pulseira de Vinhas" icon={mediaUrlFromVaultPath(icon)} description="Alcance: 9 m. Durante até 3 turnos do alvo, faz automaticamente d20 + bônus de JP contra sua JP normal. Sucesso liberta e permite agir; falha passa o turno. Dois usos por descanso. Conta como o consumível do turno, sem gastar o ataque; não consome o item." /><b>{remaining}/{maximum}</b></span>
    {!gridded && <TargetSelect label="Alvo da Pulseira de Vinhas" value={target} targets={tokens.filter(t => t.character_id !== 'vezemir' && (t.current_hp == null || t.current_hp > 0)).map(t => ({ id: t.id, name: t.name }))} disabled={disabled || busy || !equipped} onChange={id => { setTarget(id); requestId.current = null; }} />}
    <button data-card-command disabled={disabled || busy || !equipped || (!gridded && !target) || remaining <= 0} onClick={() => {
      if(!gridded){void use();return;}
      armId.current=crypto.randomUUID();window.dispatchEvent(new CustomEvent('omnisvera-targeting-arm',{detail:{armId:armId.current,actionRef:'technique:vezemir:pulseira-de-vinhas',actionLabel:'Pulseira de Vinhas',attackerCharacterId:'vezemir',attackerTokenId,slot:'ranged'}}));
    }}>{busy ? 'Usando…' : 'Usar'}</button>
    {!equipped && <small>Equipe para usar</small>}{error && <p role="alert">{error}</p>}
  </article>;
}
