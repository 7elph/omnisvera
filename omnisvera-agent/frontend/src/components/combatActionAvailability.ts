import type { CombatEffectsState } from "../api";

export function combatActionBlock(state: CombatEffectsState, participantId: string): string {
  const encounter = state.encounter;
  if (!encounter?.active || !encounter.battle_mode) return "";
  const current = encounter.participants?.[encounter.turn_index ?? 0];
  if (current?.target_id !== participantId) return `Aguarde o turno deste personagem. Agora: ${current?.name || "participante oculto"}.`;
  if (encounter.action_committed || (encounter.attack_limit != null && (encounter.attacks_used || 0) >= encounter.attack_limit)) {
    return "Ação deste turno já utilizada. Conclua e passe o turno antes de atacar novamente.";
  }
  return "";
}
