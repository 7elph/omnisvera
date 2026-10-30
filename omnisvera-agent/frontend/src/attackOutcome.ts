import type { AttackResolution, SpellCastResult } from './api';

export function monsterBreathOutcomeText(detail: {
  roll?: { formula?: string; individual_results?: number[]; total?: number };
  results?: SpellCastResult['results'];
}) {
  const results=detail.results || [],roll=detail.roll;
  const removed=results.reduce((total,result)=>total+result.damage_dealt,0);
  const conditions=results.filter(r=>r.condition?.effect_id).length;
  const hasConditions=results.some(r=>r.condition);
  return {
    summary:`${results.length} ${results.length===1?'alvo':'alvos'} · ${hasConditions?`${conditions} ${conditions===1?'condição aplicada':'condições aplicadas'}`:`${removed} PV removidos`}`,
    details:[
      roll?`Dano rolado${roll.formula?` (${roll.formula})`:''}: ${(roll.individual_results || []).join(' + ')} = ${roll.total ?? '—'}`:'',
      ...results.map(result=>{
        const condition=result.condition,immune=result.immune||condition?.immune;
        return result.target+': '+[result.save?`JP ${result.save.total}/${result.save.target} (${result.resisted?'resistiu':'falhou'})`:'',
          immune?`imune (${immune})`:condition?`${condition.name} · ${condition.effect_id?'aplicada'+(condition.duration_unit==='permanent'?' até remoção':''):'não aplicada'}`:`dano ${result.damage_dealt}`,
          result.hp?`PV ${result.hp.before} → ${result.hp.after}`:''].filter(Boolean).join(' · ');
      }),
    ].filter(Boolean).join('\n'),
  };
}

/** Presentation only: numbers come from the accepted backend receipt/ledger. */
export function attackOutcomeText(result: Partial<AttackResolution>) {
  const breakdown = result.breakdown || {};
  const actual = result.hp_before != null && result.hp_after != null
    ? Math.max(0, result.hp_before - result.hp_after) : undefined;
  const critical = breakdown.strikes?.some(strike => strike.critical);
  const outcome = breakdown.automatic_hit ? 'Acerto automático' : critical ? 'Crítico' : result.result === 'hit' ? 'Acerto' : result.result === 'miss' ? 'Erro' : 'Aplicado';
  const summary = breakdown.fumble_result?`Falha crítica · sofreu ${breakdown.fumble_result.damage} de dano da própria arma`:`${outcome} · ${actual != null ? `${actual} PV removidos` : `dano calculado ${result.damage_total ?? '—'}`}`;
  const details = [
    breakdown.automatic_hit ? 'Acerto automático; sem rolagem de acerto.'
      : result.d20 != null ? `d20 ${result.d20} + ${result.attack_bonus} = ${result.attack_total} / CA ${result.target_ac}` : '',
    ...(breakdown.strikes || []).map((strike, i) => `Golpe ${i + 1}: ${strike.d20} + ${result.attack_bonus} = ${strike.attack_total} · ${strike.result === 'hit' ? 'acerto' : 'erro'} · dano ${strike.damage_total}`),
    ...(breakdown.strikes || []).filter(strike => strike.critical).map(strike => `Crítico x${strike.critical_multiplier || 2}: somente dados base; bônus e passivas não multiplicados.`),
    `Dano calculado: ${result.damage_total ?? '—'}${result.damage_formula ? ` (${critical ? 'fórmula da ação: ' : ''}${result.damage_formula})` : ''}`,
    result.damage_rolls?.length ? `Dados de dano: ${result.damage_rolls.join(' + ')} · modificador ${result.damage_modifier ?? 0}` : '',
    actual != null ? `PV: ${result.hp_before} → ${result.hp_after} · ${actual} PV removidos` : '',
    breakdown.damage_defenses&&breakdown.damage_defenses.damage_before_defenses!==breakdown.damage_defenses.damage_after_defenses
      ? `Defesas: ${breakdown.damage_defenses.damage_before_defenses} → ${breakdown.damage_defenses.damage_after_defenses} de dano`:'',
    ...(breakdown.monster_rider_results || []).map(effect=>{
      if(effect.immune)return `${effect.name}: imune (${effect.immune})`;
      const chance=effect.chance_roll?`transmissão ${effect.chance_roll.total}`:'';
      if(effect.triggered===false)return [effect.name,chance,'não transmitida'].filter(Boolean).join(' · ');
      const save=effect.save?`JP ${effect.save.total}/${effect.save.target} (${effect.resisted?'resistiu':'falhou'})`:'';
      const secondsPerUnit=effect.duration_unit==='days'?86400:effect.duration_unit==='turns'?600:10;
      const unit=effect.duration_unit==='days'?'dia(s)':effect.duration_unit==='turns'?'turno(s) de exploração':'rodada(s)';
      const duration=effect.remaining_seconds!=null?`${effect.phase==='latent'?'início em ':''}${Math.ceil(effect.remaining_seconds/secondsPerUnit)} ${unit}`:effect.duration_unit==='permanent'?'até remoção':'';
      const attribute=({strength:'Força',dexterity:'Destreza',constitution:'Constituição',intelligence:'Inteligência',wisdom:'Sabedoria',charisma:'Carisma'} as Record<string,string>)[effect.attribute||''];
      return [effect.name,chance,save,effect.damage_dealt!=null?`dano adicional ${effect.damage_dealt}`:'',
        attribute&&effect.attribute_after!=null?`${attribute} ${effect.attribute_before} → ${effect.attribute_after}`:'',duration,effect.manual_reason||''].filter(Boolean).join(' · ');
    }),
    breakdown.resource_cost ? `Recurso consumido: ${breakdown.resource_cost.amount}` : '',
    breakdown.fumble_result?`Dano próprio: ${breakdown.fumble_result.damage} · PV ${breakdown.fumble_result.hp_before} → ${breakdown.fumble_result.hp_after}`:'',
    breakdown.drain_result ? `Drenagem: ${breakdown.drain_result.drained} PV · cura ${breakdown.drain_result.healed} · PV ${breakdown.drain_result.hp_before} → ${breakdown.drain_result.hp_after}` : '',
    ...(breakdown.manual_effects || []),
  ].filter(Boolean).join('\n');
  return { summary, details };
}
