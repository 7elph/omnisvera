import { useRef, useState } from 'react';
import { removeMonsterParasite, newDiceRequestId, type CombatEffectsState } from '../api';

export default function ParasiteControl({ state, targetId, targetType = 'character', onChange }: {
  state?: CombatEffectsState; targetId: string; targetType?: string; onChange: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const retry = useRef<string | null>(null); const lock = useRef(false);
  const effect = state?.effects.find(e => e.target_type === targetType && e.target_id === targetId && e.monster_condition === 'parasite');
  if (!effect || !state) return null;
  return <span className="workspace-inline-actions"><button type="button" disabled={busy} title="Remove o parasita e consome a ação principal do turno" onClick={() => {
    if (lock.current) return; lock.current = true; setBusy(true); setError('');
    retry.current ||= newDiceRequestId('parasite-remove');
    void removeMonsterParasite(targetType, targetId, state.version, retry.current).then(async () => { retry.current = null; await onChange(); })
      .catch(reason => setError(reason instanceof Error ? reason.message : 'Falha ao remover parasita'))
      .finally(() => { lock.current = false; setBusy(false); });
  }}>Remover parasita</button>{error && <small role="alert">{error}</small>}</span>;
}
