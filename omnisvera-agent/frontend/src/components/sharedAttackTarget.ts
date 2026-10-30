import type { CombatEffectsState, SessionLedgerEntry } from '../api';

// Use only the already-authorized ledger payload. Hidden/missing endpoints
// are subsequently rejected by AttackTargetLine's visible-pin lookup.
export function sharedAttackTarget(state: CombatEffectsState, ledger: SessionLedgerEntry[]) {
  const encounter = state.encounter;
  if (!encounter?.active) return {};
  const last = ledger.filter(entry => !entry.voided_at && entry.source_type === 'combat_action'
    && entry.detail?.turn_sequence === encounter.turn_sequence
    && entry.detail?.turn_started_at === encounter.turn_started_at)
    .sort((a, b) => b.id - a.id)[0];
  return last ? { actorId: String(last.detail?.actor_id || ''), targetId: String(last.detail?.target_id || '') } : {};
}
