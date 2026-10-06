import { useRef, useState } from 'react';
import { CombatEffectsState, newDiceRequestId, sendCombatEffectCommand } from '../api';

export default function DornProtocolControls({ combat, onChange }: { combat: CombatEffectsState | null; onChange: (state: CombatEffectsState) => Promise<void> }) {
  const [ally, setAlly] = useState('');
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState('12');
  const [position, setPosition] = useState(false);
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
      const result = state.protocol_result;
      setMessage(result?.total != null ? `INT: ${result.total} / dificuldade ${result.difficulty} · ${result.outcome === 'success' ? 'Sucesso — Mestre define a informação objetiva.' : 'Diagnóstico inconclusivo.'}` : 'Protocolo atualizado.');
      await onChange(state);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Falha no protocolo'); }
    finally { lock.current = false; setBusy(false); }
  }
  const disabled = busy || !combat;
  return <div className="dorn-protocol-controls">
    <article><strong>Protocolo de Guarda{guard ? ' · ATIVO' : ''}</strong><small>Ação · até o início do próximo turno de Dorn</small>
      <p>Uma interposição, antes da rolagem. Dorn recebe o ataque sem bônus.</p>
      {guard ? <small>Aliado: {encounter?.participants?.find(p => p.target_id === guard.ally_id)?.name || guard.ally_id}. No ataque do inimigo, confirme “Interpor Dorn” antes de rolar.</small> : <>
        <label>Aliado<select value={ally} onChange={e => setAlly(e.target.value)}><option value="">Escolher aliado</option>{encounter?.participants?.filter(p => p.target_type === 'character' && p.target_id !== 'dorn7').map(p => <option key={p.target_id} value={p.target_id}>{p.name}</option>)}</select></label>
        <label><input type="checkbox" checked={position} onChange={e => setPosition(e.target.checked)} /> Posição permite interposição</label>
        <button disabled={disabled || !active || !canAct || !ally || !position} onClick={() => void use('dorn_guard', { ally_id: ally, position_confirmed: position })}>Ativar Guarda · gastar ação</button>
      </>}
    </article>
    <article><strong>Protocolo de Vanguarda{vanguard ? ' · ATIVO' : ''}</strong><small>Exploração · até desativar ou encerrar cena</small><p>Dorn assume a frente; exposição ao perigo decidida pelo Mestre. Sem detecção ou proteção automática.</p><button disabled={disabled || (active && !vanguard)} onClick={() => void use('dorn_vanguard', { enabled: !vanguard })}>{vanguard ? 'Desativar Vanguarda' : 'Assumir Vanguarda'}</button></article>
    <article><strong>Diagnóstico da Unidade</strong><small>Ação · teste de INT · resolução do Mestre</small><label>Mecanismo / componente<input maxLength={160} value={subject} onChange={e => setSubject(e.target.value)} /></label><label>Dificuldade (Mestre)<input type="number" min={1} max={99} value={difficulty} onChange={e => setDifficulty(e.target.value)} /></label><button disabled={disabled || !canAct || !subject.trim() || Number(difficulty) < 1 || Number(difficulty) > 99} onClick={() => void use('dorn_diagnose', { subject, difficulty: Number(difficulty) })}>Diagnosticar · rolar INT</button><small>Sem revelação automática de lore. Falha: inconclusivo.</small></article>
    {active && !canAct && <p>Aguarde o turno de Dorn ou passe o turno já utilizado.</p>}
    {message && <p role="status">{message}</p>}
  </div>;
}
