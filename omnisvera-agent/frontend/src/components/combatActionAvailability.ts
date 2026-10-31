import type { CombatEffectsState } from "../api";

export function conditionActionBlock(state:CombatEffectsState,participantId:string):string{
  const condition=(state.effects||[]).find(e=>e.target_id===participantId&&e.monster_condition&&e.blocks_actions);
  return condition?`${condition.label}: participante não pode agir nem se mover.`:'';
}

export function combatActionBlock(state: CombatEffectsState, participantId: string, hp?: number | null, weaponPath?:string): string {
  const condition=conditionActionBlock(state,participantId);if(condition)return condition;
  const lifeline=participantId==='vezemir' && (hp ?? -10)>-10 && (state.effects || []).some(e=>e.target_type==='character' && e.target_id==='vezemir' && Boolean((e as unknown as {defy_death?:boolean}).defy_death));
  if (hp != null && hp <= 0 && !lifeline) return 'Participante a 0 PV não pode executar ações de combate.';
  const encounter = state.encounter;
  if (!encounter?.active || !encounter.battle_mode) return "";
  const current = encounter.participants?.[encounter.turn_index ?? 0];
  if (current?.target_id !== participantId) return `Aguarde o turno deste personagem. Agora: ${current?.name || "participante oculto"}.`;
  if (encounter.pending_attack) return 'Ataque pendente: retome e confirme a prévia, ou passe o turno. Fechar a janela não permite rerrolar.';
  const ticket=encounter.item_followups?.[participantId];
  const key=[encounter.started_at,encounter.turn_sequence,current?.target_type,current?.target_id];
  const bonus=Boolean(weaponPath&&ticket?.item_path===weaponPath&&JSON.stringify(ticket.turn)===JSON.stringify(key));
  if (!bonus&&(encounter.action_committed || (encounter.attack_limit != null && (encounter.attacks_used || 0) >= encounter.attack_limit))) {
    return "Ação deste turno já utilizada. Conclua e passe o turno antes de atacar novamente.";
  }
  return "";
}

export function consumableActionBlock(state: CombatEffectsState, participantId: string, hp?: number | null): string {
  const condition=conditionActionBlock(state,participantId);if(condition)return condition;
  const encounter = state.encounter;
  if (!encounter?.active || !encounter.battle_mode) return '';
  const lifeline=participantId==='vezemir' && (hp ?? -10)>-10 && (state.effects || []).some(e=>e.target_type==='character' && e.target_id==='vezemir' && Boolean((e as unknown as {defy_death?:boolean}).defy_death));
  if (hp != null && hp <= 0 && !lifeline) return 'Participante a 0 PV não pode usar consumíveis em seu próprio turno.';
  const current = encounter.participants?.[encounter.turn_index ?? 0];
  if (current?.target_id !== participantId) return `Aguarde o turno deste personagem. Agora: ${current?.name || 'participante oculto'}.`;
  return encounter.consumable_used ? 'Consumível deste turno já utilizado. O ataque continua independente.' : '';
}
