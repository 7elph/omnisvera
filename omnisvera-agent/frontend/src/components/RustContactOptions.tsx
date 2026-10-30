import { useEffect, useRef, useState } from 'react';

export type RustSelection = {
  material: 'metal' | 'nonmetal'; magical: boolean; enchantment_bonus: number; enhancement_rule_ids: string[];
};
export type RustInventoryOption = {
  inventory_id: number; item_title: string; needs_metadata: boolean; bonus?: number | null;
  selection?: RustSelection | null; fingerprint?: string;
  rules: { id: string; kind: string; value: number; label?: string | null }[];
};
export type RustContactChoice = { inventory_id: number; selection: RustSelection };

const key = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
export function rustRuleEligible(rule: RustInventoryOption['rules'][number], bonus: number) {
  return ['attack_bonus', 'damage_bonus', 'armor_class_bonus'].includes(rule.kind) && rule.value === bonus && bonus > 0 &&
    !/\b(for|forca|strength|atributo|attribute|classe|class|nivel|level|maestria|mastery)\b/.test(key(rule.label || ''));
}

/** GM-only children of the shared target confirmation. No destructive defaults.
 * items are the equipped native-inventory previews for the selected grid target.
 * Parent must re-preview the choice to obtain its final fingerprint before commit.
 */
export default function RustContactOptions({ items, disabled = false, onChange }: {
  items: RustInventoryOption[]; disabled?: boolean; onChange: (choice: RustContactChoice | null) => void;
}) {
  const [draft, setDraft] = useState({ id: '', material: '', magical: '', bonus: '', rules: [] as string[] });
  const changeRef = useRef(onChange); changeRef.current = onChange;
  const signature = items.map(item => `${item.inventory_id}:${item.fingerprint || ''}`).join('|');
  useEffect(() => {
    setDraft({ id: '', material: '', magical: '', bonus: '', rules: [] });
    changeRef.current(null);
  }, [signature]);
  const item = items.find(candidate => String(candidate.inventory_id) === draft.id);
  function update(next: typeof draft) {
    setDraft(next);
    const selected = items.find(candidate => String(candidate.inventory_id) === next.id);
    if (!selected) { onChange(null); return; }
    if (!selected.needs_metadata && selected.selection) {
      onChange({ inventory_id: selected.inventory_id, selection: selected.selection }); return;
    }
    if (!next.material || !next.magical) { onChange(null); return; }
    const magical = next.magical !== 'no';
    const bonus = magical ? Number(next.bonus) : 0;
    if (magical && !(next.material === 'nonmetal' && next.magical === 'other') && (!next.bonus || !Number.isInteger(bonus) || bonus <= 0 || bonus > 10 || !next.rules.length ||
      next.rules.some(id => !selected.rules.some(rule => rule.id === id && rustRuleEligible(rule, bonus))))) {
      onChange(null); return;
    }
    onChange({ inventory_id: selected.inventory_id, selection: {
      material: next.material as RustSelection['material'], magical, enchantment_bonus: bonus,
      enhancement_rule_ids: magical ? next.rules : [],
    } });
  }
  return <fieldset className="workspace-rust-contact-options" disabled={disabled}>
    <label>Item que recebeu o contato
      <select aria-label="Item tocado pela Ferrugem" value={draft.id} onChange={event => update({
        id: event.target.value, material: '', magical: '', bonus: '', rules: [],
      })}>
        <option value="">Selecionar item equipado</option>
        {items.map(option => <option key={option.inventory_id} value={option.inventory_id}>{option.item_title}</option>)}
      </select>
    </label>
    {!items.length && <p role="status">Nenhum item equipado disponível neste inventário.</p>}
    {item && !item.needs_metadata && item.selection && <p>Material identificado · encantamento atual +{item.bonus ?? item.selection.enchantment_bonus}</p>}
    {item?.needs_metadata && <>
      <div className="workspace-inline-actions">
        <select aria-label="Material do item" value={draft.material} onChange={event => update({ ...draft, material: event.target.value })}>
          <option value="">Confirmar material</option><option value="metal">Metal</option><option value="nonmetal">Não metálico</option>
        </select>
        <select aria-label="Encantamento do item" value={draft.magical} onChange={event => update({ ...draft, magical: event.target.value, bonus: '', rules: [] })}>
          <option value="">Confirmar magia</option><option value="no">Comum</option><option value="yes">Encantamento numérico</option>
          {draft.material === 'nonmetal' && <option value="other">Mágico sem bônus numérico</option>}
        </select>
        {draft.magical === 'yes' && <select aria-label="Bônus mágico do item" value={draft.bonus} onChange={event => update({ ...draft, bonus: event.target.value, rules: [] })}>
          <option value="">Bônus</option>{Array.from({ length: 10 }, (_, i) => i + 1).map(bonus => <option key={bonus} value={bonus}>+{bonus}</option>)}
        </select>}
      </div>
      {draft.magical === 'yes' && draft.bonus && <>
        <p>Identifique apenas o encantamento, sem bônus de atributo ou classe.</p>
        {item.rules.filter(rule => rustRuleEligible(rule, Number(draft.bonus))).map(rule => <label key={rule.id}>
          <input type="checkbox" aria-label={`Encantamento: ${rule.label || rule.kind}`} checked={draft.rules.includes(rule.id)}
            onChange={event => update({ ...draft, rules: event.target.checked ? [...draft.rules, rule.id] : draft.rules.filter(id => id !== rule.id) })} />
          {rule.label || rule.kind} +{rule.value}
        </label>)}
        {!item.rules.some(rule => rustRuleEligible(rule, Number(draft.bonus))) && <p role="status">Sem componente separado compatível. Revise o cadastro do item antes de corroer.</p>}
      </>}
    </>}
  </fieldset>;
}
