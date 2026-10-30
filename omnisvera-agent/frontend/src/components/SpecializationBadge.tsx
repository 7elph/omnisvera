import { useEffect, useState } from 'react';
import { listSpecializations, PlayableCharacter, SpecializationOption } from '../api';
import SheetDetail from './SheetDetail';
import { specializationLabel } from '../specializationLabel';

/** Identity summary only. Choosing a specialization stays in GM management. */
export default function SpecializationBadge({ character }: { character: PlayableCharacter }) {
  const [option, setOption] = useState<SpecializationOption | null>(null);
  const id = character.definition.id;
  const current = character.definition.specialization;
  useEffect(() => {
    let cancelled = false;
    setOption(null);
    if (current) listSpecializations(id).then(result => {
      if (!cancelled) setOption(result.options.find(entry => entry.id === result.current) || null);
    }).catch(() => { /* Persisted name remains readable if the catalogue is unavailable. */ });
    return () => { cancelled = true; };
  }, [id, current]);
  if (!current) return null;
  const title = specializationLabel(current, option?.name);
  const summary = [option?.benefits.length ? `Benefícios: ${option.benefits.join(' · ')}` : '',
    option?.restrictions.length ? `Restrições: ${option.restrictions.join(' · ')}` : ''].filter(Boolean).join('\n\n');
  return <SheetDetail title={title} showIcon={false} description={summary || 'Especialização atual. As habilidades estão nos cards da ficha.'}><b>{title}</b></SheetDetail>;
}
