import type { PlayableCharacterDefinition, SessionAbility } from '../api';

export function hemomancySelection(pack: PlayableCharacterDefinition['hemomancy'], weaponId: string, skill: boolean): SessionAbility | null {
  const weapon = pack?.weapons.find(item => item.weapon === weaponId);
  if (!weapon) return null;
  const shield = weapon.weapon === 'escudo';
  return {
    id: `hemomancia-${weapon.weapon}${skill && !shield ? '-habilidade' : ''}`,
    name: skill ? weapon.skill.name : weapon.name,
    kind: 'ability', group: 'Hemomancia', active: true, blocked: false,
    mechanics_status: 'structured', requires_target: !shield,
    description: `${weapon.damage || '+2 CA por 1 rodada'} · ${weapon.range_m == null ? 'Adjacente' : `${weapon.range_m} m`}\nInvocação: ${weapon.invocation_cost} sangue. Ataque básico sem custo enquanto esta arma está ativa.\n${weapon.skill.name}: +${weapon.skill.cost} sangue. ${weapon.skill.description}\nPassiva — ${weapon.passive.name}: ${weapon.passive.description}`,
  };
}

/** Sheet projection only: do not delete legacy abilities/resources or change their handlers. */
export function razielSheetAbilities(characterId: string | undefined, abilities: SessionAbility[], pack: PlayableCharacterDefinition['hemomancy']): SessionAbility[] {
  if (characterId !== 'raziel') return abilities;
  const retainedIds = ['caixao', 'mordida', 'forma-da-noite', 'regeneracao-vampirica', 'marca-rubra','velocidade'];
  const retained = retainedIds.flatMap(id => {
    const ability = abilities.find(item => item.id === id);
    return ability ? [{ ...ability, group: 'Habilidades' }] : [];
  });
  const skills: SessionAbility[] = [], passives: SessionAbility[] = [];
  for (const weapon of pack?.weapons || []) {
    const skill = hemomancySelection(pack, weapon.weapon, true);
    if (skill) skills.push({ ...skill, group: 'Habilidades' });
    passives.push({ id: `hemomancia-passiva-${weapon.weapon}`, name: weapon.passive.name,
      kind: 'passive', group: ['marreta','foice','lanca'].includes(weapon.weapon)?'Passivas · Feridas':'Passivas · Marca', active: false, requires_target: false,
      mechanics_status: 'structured', source: 'Hemomancia',
      description: `${weapon.passive.description}\nArma: ${weapon.name}.` });
  }
  const otherGroups = abilities.filter(ability => !retainedIds.includes(ability.id) &&
    !['habilidades', 'poderes vampíricos'].includes((ability.group || 'Habilidades').trim().toLocaleLowerCase('pt-BR')));
  return [...retained, ...skills, ...passives, ...otherGroups];
}

export function hemomancyBloodCost(pack: PlayableCharacterDefinition['hemomancy'], weaponId: string, skill: boolean, heldWeaponId: string): number | null {
  const weapon = pack?.weapons.find(item => item.weapon === weaponId);
  if (!weapon) return null;
  if (weapon.weapon === 'escudo') return weapon.invocation_cost;
  return Math.max(heldWeaponId === weaponId ? 0 : weapon.invocation_cost,skill ? weapon.skill.cost : 0);
}
