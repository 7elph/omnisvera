import { useRef, useState } from 'react';
import { completeRollRequest, PlayableCharacter } from '../api';

export default function PendingLevelRolls({ character, canOperate, onApplied }: {
  character: PlayableCharacter; canOperate: boolean; onApplied: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lock = useRef(false);
  const entries = character.definition.progression?.pending_rolls || [];
  async function roll(id: number) {
    if (!canOperate || lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const result = await completeRollRequest(id, `level-hp-completion:${id}`);
      window.dispatchEvent(new CustomEvent('omnisvera-roll-created', { detail: result }));
      await onApplied();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Rolagem pendente'); }
    finally { lock.current = false; setBusy(false); }
  }
  if (!entries.length) return null;
  return <section className="workspace-action-catalog workspace-pending-level-rolls" aria-label="Progressão pendente" aria-busy={busy}>
    <header><span>PV · ROLAGEM PENDENTE</span><small>{entries.length}</small></header>
    {entries.map(entry => <article key={entry.request_id}><span>Nível {entry.level}<small>1d{entry.die} · sem cura automática</small></span>
      <button type="button" disabled={!canOperate || busy} onClick={() => void roll(entry.request_id)}>Rolar PV</button></article>)}
    {error && <p role="alert">{error}</p>}
  </section>;
}
