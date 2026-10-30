import type { DispelPreview } from '../api';

export default function DispelEffectOptions({ effects, selected, onChange }: {
  effects: DispelPreview['effects']; selected?:string; onChange:(id:string)=>void;
}) {
  return <fieldset className="workspace-dispel-options"><legend>Magia a dissipar</legend>
    {effects.map(effect=><label key={effect.id} className="workspace-inline-actions">
      <input type="radio" name="dispel-effect" value={effect.id} checked={effect.id===selected} onChange={()=>onChange(effect.id)} />
      <span>{effect.label}{effect.kind==='area'?' · área inteira':''}</span>
    </label>)}
  </fieldset>;
}
