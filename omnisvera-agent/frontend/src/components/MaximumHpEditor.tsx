import type { PlayableCharacterDefinition } from "../api";

type HpRule = { hitDie: number; constitutionModifier: number; level: number; firstLevelMaximum: number; nextLevelMinimum: number; nextLevelMaximum: number; formula: string };

const HIT_DIE_BY_CLASS: Record<string, number> = { guerreiro: 10, hemomante: 8 };

function normalized(value: unknown) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").trim();
}

export function maximumHpRule(definition: PlayableCharacterDefinition): HpRule | null {
  const hitDie = HIT_DIE_BY_CLASS[normalized(definition.class_name)];
  if (!hitDie) return null;
  const constitutionModifier = Number(definition.attribute_modifiers?.constitution || 0);
  const level = Math.max(1, Number(definition.level || 1));
  return {
    hitDie, constitutionModifier, level,
    firstLevelMaximum: Math.max(1, hitDie + constitutionModifier),
    nextLevelMinimum: Math.max(1, 1 + constitutionModifier),
    nextLevelMaximum: Math.max(1, hitDie + constitutionModifier),
    formula: `1d${hitDie}${constitutionModifier === 0 ? "" : constitutionModifier > 0 ? `+${constitutionModifier}` : constitutionModifier}`,
  };
}

export default function MaximumHpEditor({ definition, value, disabled, onSave }: { definition: PlayableCharacterDefinition; value?: number | null; disabled?: boolean; onSave: (value: number) => Promise<void> }) {
  const rule = maximumHpRule(definition);
  if (!rule) return null;
  return <section className="workspace-hp-maximum-editor" aria-label="Ajustar PV máximo">
    <div><strong>PV máximo</strong><small>Nível 1: D{rule.hitDie} cheio + CON {rule.constitutionModifier >= 0 ? "+" : ""}{rule.constitutionModifier} = {rule.firstLevelMaximum}. No nível {rule.level}, cada avanço soma {rule.formula} ({rule.nextLevelMinimum}–{rule.nextLevelMaximum} PV).</small></div>
    <label><input key={`${definition.id || definition.name}:${value ?? ""}`} type="number" min={1} max={999} inputMode="numeric" defaultValue={value ?? ""} aria-label="Novo PV máximo" /><button type="button" disabled={disabled} onClick={async (event) => { const input = event.currentTarget.parentElement?.querySelector("input"); const next = Math.max(1, Math.min(999, Math.round(Number(input?.value || 0)))); if (next && next !== value) await onSave(next); }}>Salvar máximo</button></label>
  </section>;
}
