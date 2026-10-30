import { useEffect, useRef, useState } from 'react';
import { chooseSpecialization, listSpecializations, PlayableCharacter, SpecializationOption } from '../api';
import { specializationLabel } from '../specializationLabel';

export default function SpecializationSection({ character, canOperate, onApplied }: {
  character: PlayableCharacter; canOperate: boolean; onApplied: () => Promise<void>;
}) {
  const [options, setOptions] = useState<SpecializationOption[] | null>(null);
  const [current, setCurrent] = useState<string | null>(character.definition.specialization ?? null);
  const [weapon, setWeapon] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [revision, setRevision] = useState(0);
  const lock = useRef(false);
  const id = character.definition.id;
  useEffect(() => {
    let cancelled = false;
    setOptions(null); setLoadError(''); setCurrent(character.definition.specialization ?? null);
    listSpecializations(id).then(result => { if (!cancelled) { setOptions(result.options); setCurrent(result.current); } }).catch(reason => {
      if (!cancelled) { setOptions([]); setLoadError(reason instanceof Error ? reason.message : 'Falha ao carregar a especialização'); }
    });
    return () => { cancelled = true; };
  }, [id, character.definition.specialization, revision]);
  if (options !== null && options.length === 0 && !loadError) return null;
  const weapons = (character.inventory || []).filter(item => item.equipped || (item.quantity || 0) > 0).slice(0, 20);
  async function confirm(spec: string | null) {
    if (!canOperate || lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const result = await chooseSpecialization(id, spec, weapon || undefined, spec ? `Especialização escolhida: ${spec}` : "Sem especialização");
      setCurrent(result.specialization);
      await onApplied();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Escolha de especialização'); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="workspace-action-catalog workspace-specialization" aria-label="Especialização" aria-busy={options === null || busy}>
    <header><span>ESPECIALIZAÇÃO</span><small>{specializationLabel(current, options?.find(option => option.id === current)?.name)}</small></header>
    {options === null && <p role="status">Carregando benefícios…</p>}
    {loadError && <div className="workspace-specialization-load-error"><p role="alert">{loadError}</p><button type="button" onClick={() => setRevision(value => value + 1)}>Tentar novamente</button></div>}
    <div className="workspace-specialization-options">
    {(options ?? []).map(option => <article className="workspace-specialization-option" key={option.id}>
      <div className="workspace-specialization-heading">
        <strong>{specializationLabel(option.id, option.name)}</strong>
        <small className="workspace-specialization-status">{option.current ? "Atual" : option.eligible ? "Disponível" : "Indisponível"}</small>
      </div>
      {option.benefits.length > 0 && <div className="workspace-specialization-benefits"><strong>Benefícios</strong><ul>{option.benefits.map(benefit => <li key={benefit}>{benefit}</li>)}</ul></div>}
      {option.restrictions.length > 0 && <div className="workspace-specialization-benefits"><strong>Restrições</strong><ul>{option.restrictions.map(restriction => <li key={restriction}>{restriction}</li>)}</ul></div>}
      {!option.eligible && option.reasons.length > 0 && <p className="workspace-specialization-reason">{option.reasons.join('; ')}</p>}
      {Boolean(option.requires?.weapon_choice) && option.eligible && !option.current && <label className="workspace-specialization-weapon">Arma da Maestria<select value={weapon} disabled={busy} onChange={e => setWeapon(e.target.value)}>
        <option value="">Selecionar arma</option>
        {weapons.map(item => <option key={item.item_path} value={item.item_path}>{item.item_title}</option>)}
      </select></label>}
      {!option.current && <button className="workspace-specialization-choose" type="button" disabled={!canOperate || busy || !option.eligible || (Boolean(option.requires?.weapon_choice) && !weapon)} onClick={() => void confirm(option.id)}>Escolher</button>}
    </article>)}
    {current && <button type="button" disabled={!canOperate || busy} onClick={() => void confirm(null)}>Continuar sem especialização</button>}
    {error && <p role="alert">{error}</p>}
    </div>
  </section>;
}
