import type { SpellCastResult } from './api';

export function spellTargetOutcome(outcome: SpellCastResult['results'][number]) {
  const hp = outcome.hp ? ` · vida ${outcome.hp.before} → ${outcome.hp.after}` : '';
  if (outcome.condition_cure) {
    const labels = [...(outcome.removed_effects || []).map(entry => entry.label), ...(outcome.removed_conditions || [])];
    return `${outcome.target}: ${labels.length ? `removido: ${labels.join(', ')}` : 'nenhuma paralisia individual identificada'}${hp}`;
  }
  if (outcome.healing_applied !== undefined) {
    const dice = outcome.healing_roll?.individual_results;
    const modifier = outcome.healing_roll?.modifier || 0;
    const bonus = modifier ? ` ${modifier > 0 ? '+' : '−'} ${Math.abs(modifier)}` : '';
    const rolled = dice?.length ? `${dice.join(' + ')}${bonus} = ${outcome.healing_rolled}` : String(outcome.healing_rolled ?? '—');
    return `${outcome.target}: cura ${outcome.healing_applied} · rolagem ${rolled}${hp}`;
  }
  const save = outcome.save ? `JP ${outcome.save.total}/${outcome.save.target} ${outcome.resisted ? 'resistiu' : 'falhou'}` : 'sem JP';
  return `${outcome.target}: ${save} · dano ${outcome.damage_dealt}${hp}`;
}
