import type { PlayableCharacterDefinition } from '../api';

type BloodWeapon = NonNullable<PlayableCharacterDefinition['hemomancy']>['weapons'][number];

/** Read-only pipeline; selecting/reading never spends blood or starts another action. */
export default function HemomancyWeaponDetails({ weapon }: { weapon?: BloodWeapon }) {
  if (!weapon) return null;
  return <div className="workspace-hemomancy-pipeline" data-card-secondary="true" aria-label="Habilidade e passiva da arma">
    <div><span>Habilidade · <strong>{weapon.skill.name}</strong></span><small>{weapon.skill.description}</small></div>
    <div><span>Passiva automática · <strong>{weapon.passive.name}</strong></span><small>{weapon.passive.description}</small></div>
  </div>;
}
