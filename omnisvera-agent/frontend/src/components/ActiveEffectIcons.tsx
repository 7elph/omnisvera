import type { CombatEffectsState } from '../api';
import { mediaUrlFromVaultPath } from '../api';
import { ActionArt } from './SessionActionArt';

export function activeIcons(state: CombatEffectsState | undefined, targetId: string, targetType = 'character') {
  const unique = new Map<string, NonNullable<CombatEffectsState['active_effect_icons']>[number]>();
  for (const effect of state?.active_effect_icons || []) {
    if (effect.target_id !== targetId || effect.target_type !== targetType ||
        (effect.duration === 'rounds' && Number(effect.rounds) <= 0) ||
        (effect.remaining_seconds != null && effect.remaining_seconds <= 0)) continue;
    unique.set(`${effect.card.id}:${effect.card.image_path || ''}`, effect);
  }
  return [...unique.values()];
}

export default function ActiveEffectIcons({ state, targetId, targetType = 'character', interactive = true }: {
  state?: CombatEffectsState; targetId: string; targetType?: string; interactive?: boolean;
}) {
  const effects = activeIcons(state, targetId, targetType);
  if (!effects.length) return null;
  return <span className="workspace-active-effect-icons" aria-label="Efeitos ativos">
    {effects.map(effect => {
      const remaining = effect.turns_remaining != null ? `${effect.turns_remaining} ${effect.duration_unit==='turns'?'turno(s) de exploração':effect.duration_unit==='rounds'?'rodada(s)':'turno(s)'}`
        : effect.rounds != null ? `${effect.rounds} rodada(s)`
        : effect.remaining_seconds != null ? `${effect.remaining_seconds}s` : 'ativo';
      const icon = mediaUrlFromVaultPath(effect.card.image_path);
      const turns=effect.turns_remaining ?? (effect.duration==='rounds'?effect.rounds:null);
      return <span key={`${effect.card.id}:${effect.card.image_path}`} title={`${effect.card.name} · ${remaining}`}>
        {interactive ? <ActionArt card={effect.card} iconOnly /> : icon
          ? <img src={icon} alt={effect.card.name} /> : <span role="img" aria-label={effect.card.name}>◈</span>}
        {turns!=null&&turns>0&&<b className="active-effect-turns" aria-label={`${turns} turnos restantes`}>{turns}</b>}
      </span>;
    })}
  </span>;
}
