import { useRef, useState } from 'react';
import { CombatEffectsState, newDiceRequestId, sendCombatEffectCommand, mediaUrlFromVaultPath, type WorkspaceToken } from '../api';
import SheetDetail from './SheetDetail';
import SpellCard from './SpellCard';

export default function DornProtocolControls({ combat, onChange, gridded = false,remaining=1 }: { combat: CombatEffectsState | null; onChange: (state: CombatEffectsState) => Promise<void>; tokens?: WorkspaceToken[]; gridded?: boolean;remaining?:number }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const encounter = combat?.encounter;
  const active = !!encounter?.active;
  const current = encounter?.participants?.[encounter.turn_index ?? 0];
  const canAct = !active || (current?.target_type === 'character' && current.target_id === 'dorn7' && !encounter?.action_committed && !encounter?.attacks_used);
  const guard = combat?.effects.find(e => e.protocol === 'guard' && e.target_id === 'dorn7');
  const vanguard = combat?.effects.find(e => e.protocol === 'vanguard' && e.target_id === 'dorn7');
  async function use(action: string, payload: Record<string, unknown>) {
    if (lock.current || !combat) return;
    lock.current = true; setBusy(true); setMessage('');
    try {
      const key = JSON.stringify([action, payload, combat.version]);
      if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId('dorn') };
      const state = await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: combat.version, action, payload });
      retry.current = null;
      await onChange(state);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Falha no protocolo'); }
    finally { lock.current = false; setBusy(false); }
  }
  const disabled = busy || !combat;
  return <div className="dorn-protocol-controls">
    <SpellCard heading={<SheetDetail title="Protocolo de Guarda" icon={mediaUrlFromVaultPath('zz_media/ui/icons/uploads/protocolo_guarda_e51a549b42.jpg')} description="Protege todos os aliados a até 9 m até o próximo turno de Dorn. Os ataques são redirecionados para Dorn e ele recebe metade do dano. Recarga 5–6 em 1d6 no início do turno.">{`Protocolo de Guarda${guard ? ' · ATIVO' : ''}`}</SheetDetail>} summary={<b>{remaining}/1</b>}>
      {!guard && <>
        <div className="workspace-target-actions workspace-guard-actions">
        <button data-card-command disabled={disabled || !active || !canAct || !gridded || remaining<1} onClick={() => void use('dorn_guard',{})}>Usar</button>
        </div>
      </>}
    </SpellCard>
    <SpellCard heading={<SheetDetail title="Protocolo de Vanguarda" icon={mediaUrlFromVaultPath('zz_media/ui/icons/uploads/protocolo_vanguarda_2c8a61c1c8.jpg')} description="Dorn assume a frente da formação até desativar ou encerrar a cena.">{`Protocolo de Vanguarda${vanguard ? ' · ATIVO' : ''}`}</SheetDetail>} summary={null}><button disabled={disabled || (active && !vanguard)} onClick={() => void use('dorn_vanguard', { enabled: !vanguard })}>{vanguard ? 'Desativar Vanguarda' : 'Assumir Vanguarda'}</button></SpellCard>
    {active && !canAct && <p>Aguarde o turno de Dorn ou passe o turno já utilizado.</p>}
    {message && <p role="status">{message}</p>}
  </div>;
}
