import { useRef, useState } from 'react';
import { CombatEffectsState, newDiceRequestId, sendCombatEffectCommand } from '../api';

/** GM-only host is DornProtocolControls; uses the existing server INT/turn budget. */
export default function DornDiagnosticControl({ combat, onChange }: { combat: CombatEffectsState | null; onChange: (state: CombatEffectsState) => Promise<void> }) {
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState(14);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const current = combat?.encounter?.participants?.[combat.encounter.turn_index ?? 0];
  const canAct = !combat?.encounter?.active || (current?.target_id === 'dorn7' && current.target_type === 'character' && !combat.encounter.action_committed && !combat.encounter.attacks_used);
  async function diagnose() {
    if (!combat || lock.current || !canAct || !subject.trim() || difficulty < 1 || difficulty > 99) return;
    lock.current = true; setBusy(true);
    try {
      const key = JSON.stringify([subject, difficulty, combat.version]);
      if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId('diagnostic') };
      const state = await sendCombatEffectCommand({ action: 'dorn_diagnose', request_id: retry.current.id, expected_version: combat.version, payload: { subject: subject.trim(), difficulty } });
      retry.current = null;
      const result = state.protocol_result;
      setMessage(`INT ${result?.total ?? '—'}: ${result?.outcome === 'success' ? 'sucesso; informação definida pelo Mestre' : 'inconclusivo'}.`);
      await onChange(state);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Falha no diagnóstico'); }
    finally { lock.current = false; setBusy(false); }
  }
  return <details><summary>Diagnóstico da Unidade</summary><div className="workspace-target-actions">
    <input aria-label="Componente analisado" placeholder="Componente analisado" maxLength={160} value={subject} onChange={e => setSubject(e.target.value)} />
    <input aria-label="Dificuldade do diagnóstico" type="number" min={1} max={99} value={difficulty} onChange={e => setDifficulty(Number(e.target.value))} />
    <button disabled={busy || !combat || !canAct || !subject.trim() || difficulty < 1 || difficulty > 99} onClick={() => void diagnose()}>Diagnosticar</button>
  </div>{message && <p role="status">{message}</p>}</details>;
}
