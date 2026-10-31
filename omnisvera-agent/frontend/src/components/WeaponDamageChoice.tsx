export type PhysicalDamageType = 'slashing' | 'piercing' | 'bludgeoning';
const labels = { slashing: 'Corte', piercing: 'Perfuração', bludgeoning: 'Impacto' };

export function weaponDamageChoices(item?: {mechanics?: {damage_types?: string[] | null} | null}): PhysicalDamageType[] {
  return (item?.mechanics?.damage_types || []).filter((value): value is PhysicalDamageType => Object.hasOwn(labels, value));
}

export default function WeaponDamageChoice({ choices, value, onChange }: {
  choices: PhysicalDamageType[]; value?: PhysicalDamageType;
  onChange: (value: PhysicalDamageType | undefined) => void;
}) {
  if (!choices.length) return null;
  return <label>Tipo de dano<select aria-label="Tipo de dano da arma" value={value || ''}
    onChange={event => onChange(choices.find(choice => choice === event.target.value))}>
    <option value="">Escolher…</option>
    {choices.map(choice => <option key={choice} value={choice}>{labels[choice]}</option>)}
  </select></label>;
}
