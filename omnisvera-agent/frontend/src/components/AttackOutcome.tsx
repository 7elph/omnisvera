import type { AttackResolution } from '../api';
import { attackOutcomeText } from '../attackOutcome';
import SheetDetail from './SheetDetail';

/** No automatic dialog, acknowledgment, mutation, or dismissal step. */
export default function AttackOutcome({ resolution }: { resolution: AttackResolution }) {
  if (!resolution.confirmed) return null;
  const text = attackOutcomeText(resolution);
  return <section className="workspace-attack-outcome" role="status" aria-label="Último resultado">
    <span>{resolution.actor_name} → {resolution.target_name} · {text.summary}</span>
    <SheetDetail title={`Resultado: ${resolution.attack_name}`} description={text.details} showIcon={false}>Ver resultado</SheetDetail>
  </section>;
}
