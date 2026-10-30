import { useEffect, useState } from 'react';
import { attackTargets } from '../api';

export type TargetOption = { id: string; name: string; disabled?: boolean };
export type RangeQuery = { profileId: string; attackId: string; slot?: string };

export default function TargetSelect({ targets, value, onChange, disabled = false, label, id, rangeQuery }: {
  targets: TargetOption[]; value: string; onChange: (id: string) => void;
  disabled?: boolean; label: string; id?: string; rangeQuery?: RangeQuery;
}) {
  const [validity, setValidity] = useState<Record<string, { valid: boolean; reason: string }>>({});
  useEffect(() => {
    let cancelled = false;
    setValidity({});
    if (!rangeQuery) return;
    attackTargets(rangeQuery.profileId, rangeQuery.attackId, rangeQuery.slot)
      .then(result => {
        if (cancelled || !result.gridded) return;
        const map: Record<string, { valid: boolean; reason: string }> = {};
        for (const target of result.targets) map[target.id] = { valid: target.valid, reason: target.reason };
        if (!cancelled) setValidity(map);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [rangeQuery?.profileId, rangeQuery?.attackId, rangeQuery?.slot]);
  const options = targets.map(target => {
    const rule = validity[target.id];
    if (!rule || target.disabled) return target;
    if (rule.valid) return target;
    return { ...target, disabled: true, name: `${target.name} · ${rule.reason}` };
  });
  const selected = options.some(target => target.id === value && !target.disabled) ? value : '';
  return <select id={id} className="workspace-target-select" aria-label={label} value={selected}
    disabled={disabled || !options.length} onChange={event => onChange(event.target.value)}>
    <option value="">{options.length ? 'Selecionar alvo' : 'Nenhum alvo disponível'}</option>
    {options.map(target => <option key={target.id} value={target.id} disabled={target.disabled}>{target.name}</option>)}
  </select>;
}
