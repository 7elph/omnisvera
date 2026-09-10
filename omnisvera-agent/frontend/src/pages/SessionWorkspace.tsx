import { FormEvent, PointerEvent as ReactPointerEvent, useEffect, useMemo, useRef, useState } from "react";
import MasterAssetPanel from "./MasterAssetPanel";
import {
  applyCharacterStateAction,
  AttackResolution,
  confirmCharacterAttack,
  connectSessionRealtime,
  createWorkspaceToken,
  deleteSessionItem,
  getPlayableCharacter,
  getSessionWorkspace,
  heartbeatSessionWorkspace,
  listPlayableCharacters,
  listSessionLedger,
  listSessionItems,
  listWorkspaceTargetInventory,
  listWorkspaceItemCatalog,
  listWorkspaceMonsterCatalog,
  listWorkspaceLoot,
  listWorkspaceIcons,
  listWorkspaceMaps,
  leaveSessionWorkspace,
  mediaUrlFromVaultPath,
  moveWorkspaceToken,
  newDiceRequestId,
  PlayableCharacter,
  PlayableCharacterSummary,
  InventoryItem,
  ItemEffectRule,
  ItemMechanics,
  MonsterCatalogEntry,
  MonsterCatalogResponse,
  LootResolution,
  LootReward,
  NoteSummary,
  rollCharacterAction,
  resolveCharacterAttack,
  grantSessionItem,
  rechargeSessionItems,
  resolveWorkspaceLoot,
  revealWorkspaceLoot,
  distributeWorkspaceLoot,
  finalizeWorkspaceLootRolls,
  updateWorkspaceLoot,
  removeWorkspaceToken,
  removeWorkspaceTargetItem,
  saveSessionItem,
  sendWorkspaceMessage,
  selectWorkspaceMap,
  SessionAbility,
  SessionItem,
  SessionLedgerEntry,
  updateCharacterDefinition,
  updateWorkspaceView,
  updateWorkspaceTableMode,
  updateWorkspaceMapVisibility,
  uploadWorkspaceIcon,
  uploadWorkspaceIconFile,
  updateWorkspaceToken,
  uploadWorkspaceMap,
  updateWorkspaceFog,
  WorkspaceSnapshot,
  WorkspaceFog,
  WorkspaceIcon,
  WorkspaceMap,
  WorkspaceToken,
  WorkspaceTokenSheet,
} from "../api";
import DiceTray from "../components/DiceTray";
import CharacterNotes from "../components/CharacterNotes";
import CurrencyCounters from "../components/CurrencyCounters";
import ArmorClassValue from "../components/ArmorClassValue";
import CharacterLevel from "../components/CharacterLevel";
import CombatEncounterPanel from "../components/CombatEncounterPanel";
import LocationQuickPin from "../components/LocationQuickPin";
import MaximumHpEditor from "../components/MaximumHpEditor";
import { nextPinPosition } from "../components/pinPlacement";
import MistParticleOverlay from "../components/MistParticleOverlay";
import { COMPANION_ICON_CATALOG, cleanItemDisplayName, iconPathForItem } from "../companionIconCatalog";

type Props = { mode: "gm" | "player"; view?: "table" | "maps" | "memory" };
type ItemDraft = { id: number; name: string; item_type: string; description: string; effects: string; effect_rules: ItemEffectRule[]; mechanics: ItemMechanics; usable: boolean; image_path: string };
type DraggingToken = {
  id: string;
  element: HTMLButtonElement;
  pointerId: number;
  original: { latitude: number; longitude: number };
  latest: { latitude: number; longitude: number };
};

type TimelineEntry = {
  id: string;
  timestamp: string;
  actor: string;
  actorId?: string | null;
  kind: "roll" | "action" | "event" | "state" | "message";
  title: string;
  detail?: string;
};

const ATTRIBUTES: Array<[string, string]> = [
  ["strength", "Força"], ["dexterity", "Destreza"], ["constitution", "Constituição"],
  ["intelligence", "Inteligência"], ["wisdom", "Sabedoria"], ["charisma", "Carisma"],
];

const CHARACTER_COLORS: Record<string, string> = {
  sage: "#d6a858", vezemir: "#de9148", raziel: "#d35a75", varkh: "#4fc2b3", morthak: "#a987e8", guest: "#c7cbd0",
};

const DEFAULT_FOG: WorkspaceFog = {
  exploration: { enabled: false, revealed_cells: [], mist_density: {}, columns: 32, rows: 24 },
  battle: { enabled: false, revealed_cells: [], mist_density: {}, columns: 32, rows: 24 },
};

const EMPTY_MONSTER_DRAFT = {
  name: "", current_hp: 10, maximum_hp: 10, color: "#b94c4c", image_path: "", visible_to_players: true, marker: "⚔", conditions: "",
  role: "Inimigo", level: 1, armor_class: 10, initiative: 0, description: "", attacks: "", abilities: "", notes: "",
  source_monster_id: "", source_url: "", hit_dice: "", hit_points: "", saving_throw: null as number | null, morale: null as number | null,
  experience_points: null as number | null, treasure: "", movement: "", category: "", size: "", alignment: "", habitat: "",
};

const CREATURE_MARKERS = [
  { label: "Inimigo", marker: "⚔", role: "Inimigo", color: "#b94c4c" },
  { label: "Morto-vivo", marker: "☠", role: "Morto-vivo", color: "#88729d" },
  { label: "Fera", marker: "◆", role: "Fera", color: "#9b713d" },
  { label: "Arcano", marker: "✦", role: "Criatura arcana", color: "#7663bd" },
  { label: "NPC", marker: "●", role: "NPC", color: "#4f8c9d" },
];

function markerForMonster(monster: MonsterCatalogEntry) {
  const category = monster.category.toLocaleLowerCase("pt-BR");
  if (category.includes("morto-vivo")) return CREATURE_MARKERS[1];
  if (category.includes("animal") || category.includes("besta") || category.includes("inseto")) return CREATURE_MARKERS[2];
  if (category.includes("constructo") || category.includes("dragão") || category.includes("extraplanar")) return CREATURE_MARKERS[3];
  return CREATURE_MARKERS[0];
}

function catalogSearchKey(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
}

function treasureHasCarried(value?: string) {
  return /[P-V]/i.test(String(value || "").replace(/\([^)]*\)/g, ""));
}

function treasureHasLair(value?: string) {
  const code = String(value || "");
  return /\([^)]*[A-V][^)]*\)/i.test(code) || /[A-O]/i.test(code.replace(/\([^)]*\)/g, ""));
}

function newEffectRule(): ItemEffectRule {
  return { id: globalThis.crypto?.randomUUID?.() || `rule-${Date.now()}`, trigger: "on_use", kind: "heal_hp", target: "", value: 1, formula: "", label: "", stacking: "stack", duration: "instant", condition: "" };
}

function newItemDraft(): ItemDraft {
  return { id: 0, name: "", item_type: "item", description: "", effects: "", effect_rules: [] as ItemEffectRule[], mechanics: { equipment_slots: [] as string[], damage_formula: "", consume_mode: "none" as const, charges_max: 0, recharge: "none" as const, slot_limit: 1 }, usable: false, image_path: "" };
}

function itemPreset(kind: "potion" | "weapon" | "armor" | "relic"): ItemDraft {
  const draft = newItemDraft();
  if (kind === "potion") return { ...draft, item_type: "Consumível", usable: true, mechanics: { ...draft.mechanics, consume_mode: "quantity" as const }, effect_rules: [{ ...newEffectRule(), formula: "1d6+2", label: "Recupera pontos de vida" }] };
  if (kind === "weapon") return { ...draft, item_type: "Arma", mechanics: { ...draft.mechanics, equipment_slots: ["Corpo a corpo", "À distância"], damage_formula: "1d6" } };
  if (kind === "armor") return { ...draft, item_type: "Armadura", mechanics: { ...draft.mechanics, equipment_slots: ["Armadura"] }, effect_rules: [{ ...newEffectRule(), trigger: "while_equipped" as const, kind: "armor_class_bonus" as const, value: 2, stacking: "non_stack" as const, duration: "equipped" as const, label: "+2 CA" }] };
  return { ...draft, item_type: "Relíquia", usable: true, mechanics: { ...draft.mechanics, equipment_slots: ["Acessório"], consume_mode: "charges" as const, charges_max: 3, recharge: "inn_rest" as const, slot_limit: 3 }, effect_rules: [{ ...newEffectRule(), kind: "temporary_hp" as const, value: 3, label: "Concede PV temporários" }] };
}

function describeItemRule(rule: ItemEffectRule) {
  const trigger = rule.trigger === "on_use" ? "Ao usar" : "Equipado";
  const attribute = ATTRIBUTES.find(([key]) => key === rule.target)?.[1] || rule.target;
  const detail = rule.kind === "heal_hp" ? `cura ${rule.formula || rule.value} PV`
    : rule.kind === "temporary_hp" ? `concede ${rule.formula || rule.value} PV temporários`
    : rule.kind === "restore_resource" ? `restaura ${rule.formula || rule.value} de ${rule.target || "recurso"}`
      : rule.kind === "add_condition" ? `aplica ${rule.target || "condição"}`
        : rule.kind === "attribute_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} em ${attribute || "atributo"}`
          : rule.kind === "skill_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} em ${rule.target || "perícia"}`
            : rule.kind === "saving_throw_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} em proteção`
          : rule.kind === "armor_class_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} CA`
            : rule.kind === "attack_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} em ataques ${rule.target || "todos"}`
              : rule.kind === "damage_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} no dano ${rule.target || ""}`
                : rule.kind === "movement_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} metros`
                  : rule.kind === "maximum_hp_bonus" ? `${rule.value >= 0 ? "+" : ""}${rule.value} PV máximo`
                    : rule.kind === "grant_ability" ? `concede ${rule.target || "habilidade"}`
                      : `${rule.kind === "resistance" ? "resistência" : rule.kind === "immunity" ? "imunidade" : "vulnerabilidade"} a ${rule.target || "tipo não informado"}`;
  return `${trigger}: ${detail}${rule.condition ? ` · se ${rule.condition}` : ""}${rule.label ? ` · ${rule.label}` : ""}`;
}

function characterColor(characterId?: string | null) {
  return CHARACTER_COLORS[String(characterId || "").toLocaleLowerCase("pt-BR")] || "#d6a858";
}

function isConsumable(item: PlayableCharacter["inventory"][number]) {
  const type = String(item.item_type || "").toLocaleLowerCase("pt-BR");
  return Boolean(item.usable || type.includes("consum") || type.includes("poção") || type.includes("potion"));
}

function itemLooksLikeShield(item: PlayableCharacter["inventory"][number]) {
  const text = `${item.item_title} ${item.item_type || ""}`.toLocaleLowerCase("pt-BR");
  return text.includes("escudo") || text.includes("muralha");
}

function itemLooksLikeRangedWeapon(item: PlayableCharacter["inventory"][number]) {
  const text = `${item.item_title} ${item.item_type || ""}`.toLocaleLowerCase("pt-BR");
  return /arco|besta|dist[aâ]ncia|ranged/.test(text);
}

function itemLooksLikeWeapon(item: PlayableCharacter["inventory"][number]) {
  const text = normalizedName(`${item.item_title} ${item.item_type || ""}`);
  return Boolean(item.damage_formula || /\barma\b|cajado|bordao|espada|machado|adaga|lanca|martelo|maca|mangual|foice|sabre|tridente/.test(text));
}

function itemLooksLikeArmor(item: PlayableCharacter["inventory"][number]) {
  const text = `${item.item_title} ${item.item_type || ""}`.toLocaleLowerCase("pt-BR");
  return text.includes("armadura") || text.includes("manto");
}

function possibleEquipmentSlots(item: PlayableCharacter["inventory"][number]) {
  if (itemLooksLikeArmor(item)) return ["Armadura"];
  if (itemLooksLikeShield(item)) return ["Mão secundária"];
  if (itemLooksLikeWeapon(item) || itemLooksLikeRangedWeapon(item)) return ["Corpo a corpo", "À distância"];
  if (item.mechanics?.equipment_slots?.length) return item.mechanics.equipment_slots;
  return ["Acessório"];
}

function normalizedName(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").replace(/[^a-z0-9]+/g, " ").trim();
}

function formatClock(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "--:--" : date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function CharacterPortrait({ character }: { character: PlayableCharacterSummary }) {
  const image = mediaUrlFromVaultPath(character.portrait);
  return image ? <img src={image} alt="" /> : <span>{character.name.slice(0, 1).toUpperCase()}</span>;
}

function NumericEditor({ label, value, min = 0, max = 999, onSave }: { label: string; value?: number | null; min?: number; max?: number; onSave: (value: number) => Promise<void> }) {
  const [draft, setDraft] = useState(String(value ?? ""));
  const [saving, setSaving] = useState(false);
  useEffect(() => setDraft(String(value ?? "")), [value]);
  async function save() {
    const parsed = Number(draft);
    if (!Number.isFinite(parsed)) return;
    setSaving(true);
    try { await onSave(Math.max(min, Math.min(max, Math.round(parsed)))); } finally { setSaving(false); }
  }
  return <label className="workspace-number-editor"><span>{label}</span><div><input type="number" min={min} max={max} value={draft} onChange={(event) => setDraft(event.target.value)} /><button disabled={saving || draft === String(value ?? "")} onClick={() => void save()}>Salvar</button></div></label>;
}

const SKILL_OPTIONS = ["Atletismo", "Conhecimento", "Furtividade", "Manipulação", "Percepção", "Sobrevivência"];

function LegacyItemRuleEditor({ rules, onChange }: { rules: ItemEffectRule[]; onChange: (rules: ItemEffectRule[]) => void }) {
  const update = (ruleId: string, fields: Partial<ItemEffectRule>) => onChange(rules.map((rule) => rule.id === ruleId ? { ...rule, ...fields } : rule));
  return <section className="workspace-item-rule-editor">
    <header><span>REGRAS EXECUTÁVEIS</span><small>{rules.length} configuradas</small><button type="button" onClick={() => onChange([...rules, newEffectRule()])}>+ Regra</button></header>
    {rules.map((rule) => <article key={rule.id}>
      <select value={rule.trigger} onChange={(event) => { const trigger = event.target.value as ItemEffectRule["trigger"]; update(rule.id, { trigger, kind: trigger === "on_use" ? "heal_hp" : "attribute_bonus", target: "", value: 1 }); }}><option value="on_use">Ao usar</option><option value="while_equipped">Enquanto equipado</option></select>
      <select value={rule.kind} onChange={(event) => update(rule.id, { kind: event.target.value as ItemEffectRule["kind"], target: "", value: 1 })}>{rule.trigger === "on_use" ? <><option value="heal_hp">Curar PV</option><option value="restore_resource">Restaurar recurso</option><option value="add_condition">Aplicar condição</option></> : <><option value="attribute_bonus">Bônus de atributo</option><option value="armor_class_bonus">Bônus de CA</option><option value="grant_ability">Conceder habilidade</option></>}</select>
      {rule.kind === "attribute_bonus" && <select value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })}><option value="">Escolher atributo</option>{ATTRIBUTES.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>}
      {rule.kind === "restore_resource" && <input value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })} placeholder="Recurso · ex.: mana" />}
      {rule.kind === "add_condition" && <input value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })} placeholder="Condição aplicada" />}
      {rule.kind === "grant_ability" && <input value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })} placeholder="Nome da habilidade" />}
      {!['add_condition', 'grant_ability'].includes(rule.kind) && <input type="number" min={-99} max={999} value={rule.value} onChange={(event) => update(rule.id, { value: Number(event.target.value) })} aria-label="Valor do efeito" />}
      <input value={rule.label || ""} onChange={(event) => update(rule.id, { label: event.target.value })} placeholder="Descrição curta" />
      <button type="button" onClick={() => onChange(rules.filter((item) => item.id !== rule.id))}>Remover</button>
    </article>)}
    {!rules.length && <p>Adicione regras para o item alterar a ficha automaticamente.</p>}
  </section>;
}

const EQUIPPED_RULE_KINDS: Array<[ItemEffectRule["kind"], string]> = [
  ["attribute_bonus", "Bônus de atributo"], ["skill_bonus", "Bônus de perícia"], ["saving_throw_bonus", "Bônus de proteção"],
  ["armor_class_bonus", "Bônus de CA"], ["attack_bonus", "Bônus de ataque"], ["damage_bonus", "Bônus de dano"],
  ["movement_bonus", "Bônus de movimento"], ["maximum_hp_bonus", "Bônus de PV máximo"], ["grant_ability", "Conceder habilidade"],
  ["resistance", "Resistência"], ["immunity", "Imunidade"], ["vulnerability", "Vulnerabilidade"],
];
const USE_RULE_KINDS: Array<[ItemEffectRule["kind"], string]> = [
  ["heal_hp", "Curar PV"], ["temporary_hp", "Conceder PV temporários"], ["restore_resource", "Restaurar recurso"], ["add_condition", "Aplicar condição"],
];
const DEFAULT_RESOURCE_OPTIONS = [
  ["mana", "Mana"], ["reserva_de_sangue", "Reserva de Sangue"], ["pontos_alquimicos", "Pontos Alquímicos"],
  ["misseis_magicos", "Mísseis Mágicos"], ["forca_arcana", "Força Arcana"], ["velocidade", "Velocidade"],
];

function ItemRuleEditor({ rules, resources = [], onChange }: { rules: ItemEffectRule[]; resources?: Array<{ key: string; label: string }>; onChange: (rules: ItemEffectRule[]) => void }) {
  const update = (id: string, fields: Partial<ItemEffectRule>) => onChange(rules.map((rule) => rule.id === id ? { ...rule, ...fields } : rule));
  const resourceOptions = [...new Map([...DEFAULT_RESOURCE_OPTIONS, ...resources.map((item) => [item.key, item.label])].map((item) => [item[0], item])).values()];
  return <section className="workspace-item-rule-editor advanced">
    <header><span>REGRAS EXECUTÁVEIS</span><small>{rules.length} configuradas</small><button type="button" onClick={() => onChange([...rules, newEffectRule()])}>+ Regra</button></header>
    {rules.map((rule) => <article key={rule.id}>
      <select value={rule.trigger} onChange={(event) => { const trigger = event.target.value as ItemEffectRule["trigger"]; update(rule.id, { trigger, kind: trigger === "on_use" ? "heal_hp" : "attribute_bonus", target: "", value: 1, formula: "", duration: trigger === "on_use" ? "instant" : "equipped" }); }}><option value="on_use">Ao usar</option><option value="while_equipped">Enquanto equipado</option></select>
      <select value={rule.kind} onChange={(event) => update(rule.id, { kind: event.target.value as ItemEffectRule["kind"], target: "", value: 1, formula: "" })}>{(rule.trigger === "on_use" ? USE_RULE_KINDS : EQUIPPED_RULE_KINDS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      {rule.kind === "attribute_bonus" && <select value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })}><option value="">Escolher atributo</option>{ATTRIBUTES.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>}
      {rule.kind === "skill_bonus" && <select value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })}><option value="">Escolher perícia</option>{SKILL_OPTIONS.map((skill) => <option key={skill} value={skill}>{skill}</option>)}</select>}
      {rule.kind === "restore_resource" && <select value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })}><option value="">Escolher recurso</option>{resourceOptions.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>}
      {["attack_bonus", "damage_bonus"].includes(rule.kind) && <select value={rule.target || "all"} onChange={(event) => update(rule.id, { target: event.target.value })}><option value="all">Todos</option><option value="melee">Corpo a corpo</option><option value="ranged">À distância</option></select>}
      {["add_condition", "grant_ability", "resistance", "immunity", "vulnerability"].includes(rule.kind) && <input value={rule.target || ""} onChange={(event) => update(rule.id, { target: event.target.value })} placeholder={rule.kind === "grant_ability" ? "Nome da habilidade" : rule.kind === "add_condition" ? "Condição aplicada" : "Tipo · ex.: fogo"} />}
      {!['add_condition', 'grant_ability', 'resistance', 'immunity', 'vulnerability'].includes(rule.kind) && <input type="number" min={-99} max={999} value={rule.value} onChange={(event) => update(rule.id, { value: Number(event.target.value) })} aria-label="Valor fixo do efeito" />}
      {rule.trigger === "on_use" && ["heal_hp", "temporary_hp", "restore_resource"].includes(rule.kind) && <input value={rule.formula || ""} onChange={(event) => update(rule.id, { formula: event.target.value })} placeholder="Fórmula opcional · 1d6+2" />}
      {rule.trigger === "while_equipped" && <select value={rule.stacking || "stack"} onChange={(event) => update(rule.id, { stacking: event.target.value as ItemEffectRule["stacking"] })}><option value="stack">Acumula</option><option value="highest">Usar o maior</option><option value="non_stack">Não acumula</option><option value="replace">Substitui</option></select>}
      <select value={rule.duration || (rule.trigger === "on_use" ? "instant" : "equipped")} onChange={(event) => update(rule.id, { duration: event.target.value as ItemEffectRule["duration"] })}><option value="instant">Instantâneo</option><option value="round">1 rodada</option><option value="scene">Até o fim da cena</option><option value="rest">Até descansar</option><option value="equipped">Enquanto equipado</option></select>
      {rule.trigger === "while_equipped" && <input value={rule.condition || ""} onChange={(event) => update(rule.id, { condition: event.target.value })} placeholder="Condição opcional · ex.: contra mortos-vivos" />}
      <input value={rule.label || ""} onChange={(event) => update(rule.id, { label: event.target.value })} placeholder="Descrição curta" />
      <button type="button" onClick={() => onChange(rules.filter((item) => item.id !== rule.id))}>Remover</button>
    </article>)}
    {!rules.length && <p>Adicione regras para o item alterar a ficha automaticamente.</p>}
  </section>;
}

const EQUIPMENT_SLOTS = ["Corpo a corpo", "À distância", "Mão secundária", "Armadura", "Acessório"];

function ItemMechanicsEditor({ mechanics, onChange }: { mechanics: ItemMechanics; onChange: (mechanics: ItemMechanics) => void }) {
  const toggleSlot = (slot: string) => onChange({ ...mechanics, equipment_slots: mechanics.equipment_slots.includes(slot) ? mechanics.equipment_slots.filter((item) => item !== slot) : [...mechanics.equipment_slots, slot] });
  return <section className="workspace-item-mechanics">
    <header><span>EQUIPAMENTO E CONSUMO</span><small>encaixes, dano, cargas e recarga</small></header>
    <div className="workspace-item-slot-options">{EQUIPMENT_SLOTS.map((slot) => <label key={slot}><input type="checkbox" checked={mechanics.equipment_slots.includes(slot)} onChange={() => toggleSlot(slot)} /> {slot}</label>)}</div>
    <label><span>Fórmula de dano</span><input value={mechanics.damage_formula || ""} onChange={(event) => onChange({ ...mechanics, damage_formula: event.target.value })} placeholder="Ex.: 1d6+2" /></label>
    <label><span>Ao usar</span><select value={mechanics.consume_mode} onChange={(event) => onChange({ ...mechanics, consume_mode: event.target.value as ItemMechanics["consume_mode"] })}><option value="none">Não consumir</option><option value="quantity">Consumir 1 unidade</option><option value="charges">Consumir 1 carga</option></select></label>
    {mechanics.consume_mode === "charges" && <><label><span>Cargas máximas</span><input type="number" min={1} max={999} value={mechanics.charges_max} onChange={(event) => onChange({ ...mechanics, charges_max: Math.max(1, Number(event.target.value)) })} /></label><label><span>Recarga</span><select value={mechanics.recharge} onChange={(event) => onChange({ ...mechanics, recharge: event.target.value as ItemMechanics["recharge"] })}><option value="none">Sem recarga</option><option value="inn_rest">Descanso completo</option><option value="scene">Fim da cena</option><option value="dawn">Amanhecer</option></select></label></>}
    <label><span>Limite no mesmo encaixe</span><input type="number" min={1} max={8} value={mechanics.slot_limit} onChange={(event) => onChange({ ...mechanics, slot_limit: Math.max(1, Math.min(8, Number(event.target.value))) })} /></label>
  </section>;
}

function ItemEffectPreview({ rules, character }: { rules: ItemEffectRule[]; character: PlayableCharacter | null }) {
  const equipped = rules.filter((rule) => rule.trigger === "while_equipped" && !rule.condition);
  const total = (kind: ItemEffectRule["kind"], target = "") => equipped.filter((rule) => rule.kind === kind && (rule.target || "") === target).reduce((sum, rule) => sum + Number(rule.value || 0), 0);
  const armor = Number(character?.definition.defenses?.armor_class || 0);
  const armorBonus = total("armor_class_bonus");
  const previews = ATTRIBUTES.map(([key, label]) => ({ label, before: Number(character?.definition.attributes?.[key] || 0), bonus: total("attribute_bonus", key) })).filter((item) => item.bonus);
  return <section className="workspace-item-preview"><header><span>PRÉVIA NA FICHA ATIVA</span><small>{character?.definition.name || "Selecione um personagem"}</small></header>{armorBonus !== 0 && <p>CA {armor || "—"} → {armor ? armor + armorBonus : `+${armorBonus}`}</p>}{previews.map((item) => <p key={item.label}>{item.label} {item.before || "—"} → {item.before ? item.before + item.bonus : `${item.bonus >= 0 ? "+" : ""}${item.bonus}`}</p>)}{rules.filter((rule) => rule.trigger === "on_use").map((rule) => <p key={rule.id}>{describeItemRule(rule)}</p>)}{!armorBonus && !previews.length && !rules.some((rule) => rule.trigger === "on_use") && <p>Nenhuma alteração automática configurada.</p>}</section>;
}

type EffectBreakdownEntry = NonNullable<NonNullable<PlayableCharacter["definition"]["item_effects"]>["breakdown"]>[number];

function EffectBreakdownModal({ title, base, effective, entries, onClose, onRoll }: { title: string; base?: number | null; effective?: number | null; entries: EffectBreakdownEntry[]; onClose: () => void; onRoll?: () => void }) {
  return <div className="workspace-item-modal-backdrop" role="presentation" onClick={onClose}><section className="workspace-effect-breakdown" role="dialog" aria-modal="true" aria-label={`Detalhes de ${title}`} onClick={(event) => event.stopPropagation()}><header><div><small>COMPOSIÇÃO DO VALOR</small><h2>{title}</h2></div><button type="button" onClick={onClose}>×</button></header><strong className="workspace-effect-equation">{base ?? "—"} base {entries.filter((entry) => entry.active).map((entry) => `${entry.value >= 0 ? "+" : "−"} ${Math.abs(entry.value)}`).join(" ")} = {effective ?? "—"}</strong>{entries.map((entry) => <article key={`${entry.item_path}:${entry.rule_id}`} className={entry.active ? "" : "conditional"}><b>{entry.item_title}</b><span>{entry.value >= 0 ? "+" : ""}{entry.value} · {entry.label || entry.kind}</span>{entry.condition && <small>Condicional: {entry.condition}</small>}</article>)}{!entries.length && <p>Nenhum modificador de item está afetando este valor.</p>}{onRoll && <button type="button" onClick={onRoll}>Jogar teste</button>}</section></div>;
}

function abilityResource(ability: SessionAbility, resources: NonNullable<PlayableCharacter["state"]>["resources"]) {
  if (ability.uses?.resource_key) {
    const wanted = ability.uses.resource_key.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    return resources.find((item) => item.key === wanted) || null;
  }
  if (ability.circle) return resources.find((item) => item.label.toLocaleLowerCase("pt-BR").includes(`${ability.circle}º círculo`)) || null;
  return null;
}

const ATTACK_DAMAGE_BY_CHARACTER: Record<string, Record<string, string>> = {
  morthak: { melee: "1d4", ranged: "1d4" },
  varkh: { melee: "1d4", ranged: "1d4" },
  raziel: { melee: "1d4", ranged: "1d4" },
  vezemir: { melee: "2d6", ranged: "1d6" },
};

function attackDamage(characterId: string | undefined, attack: { id?: string; damage?: string | null }, equippedMeleeDamage?: string | null) {
  const equippedDamage = (attack.id === "melee" || attack.id === "ranged") ? equippedMeleeDamage : null;
  return attack.damage || equippedDamage || ATTACK_DAMAGE_BY_CHARACTER[String(characterId || "").toLowerCase()]?.[String(attack.id || "").toLowerCase()] || "1d4";
}

async function fileAsBase64(file: File) {
  if (file.size > 5 * 1024 * 1024) throw new Error("A imagem deve possuir no máximo 5 MB.");
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (let index = 0; index < bytes.length; index += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
    }
    return window.btoa(binary);
  } catch {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error("Não foi possível ler a imagem. Salve-a no aparelho e tente selecioná-la novamente."));
      reader.onabort = () => reject(new Error("A seleção da imagem foi cancelada."));
      reader.onload = () => resolve(String(reader.result || "").split(",", 2)[1] || "");
      reader.readAsDataURL(file);
    });
  }
}

export default function SessionWorkspace({ mode, view = "table" }: Props) {
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [selectedId, setSelectedId] = useState(() => mode === "player" ? "" : localStorage.getItem("omnisvera_selected_character") || "");
  const [character, setCharacter] = useState<PlayableCharacter | null>(null);
  const [ledger, setLedger] = useState<SessionLedgerEntry[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot>({ table_mode: "digital", messages: [], presence: [], tokens: [], fog: DEFAULT_FOG });
  const [workspaceMaps, setWorkspaceMaps] = useState<WorkspaceMap[]>([]);
  const [message, setMessage] = useState("");
  const [condition, setCondition] = useState("");
  const [attackCountById, setAttackCountById] = useState<Record<string, number>>({});
  const [sessionNotes, setSessionNotes] = useState("");
  const [mapTitle, setMapTitle] = useState("");
  const [mapFile, setMapFile] = useState<File | null>(null);
  const [mapVisibleToPlayers, setMapVisibleToPlayers] = useState(false);
  const [playerMapId, setPlayerMapId] = useState(() => mode === "player" ? localStorage.getItem("omnisvera_player_map_id") || "" : "");
  const [mapZoom, setMapZoom] = useState(() => {
    const saved = Number(localStorage.getItem("omnisvera_session_map_zoom") || 1);
    return Number.isFinite(saved) ? Math.max(1, Math.min(3, saved)) : 1;
  });
  const [sessionItems, setSessionItems] = useState<SessionItem[]>([]);
  const [archiveItems, setArchiveItems] = useState<NoteSummary[]>([]);
  const [archiveItemsLoading, setArchiveItemsLoading] = useState(false);
  const [itemDraft, setItemDraft] = useState<ItemDraft>(newItemDraft);
  const [itemImage, setItemImage] = useState<File | null>(null);
  const [itemImageIcon, setItemImageIcon] = useState<WorkspaceIcon | null>(null);
  const [itemImagePreparing, setItemImagePreparing] = useState(false);
  const [grantDraft, setGrantDraft] = useState({ item_id: "", character_id: "", quantity: 1 });
  const [inventoryTargetId, setInventoryTargetId] = useState("");
  const [managedInventory, setManagedInventory] = useState<InventoryItem[]>([]);
  const [inventoryItemPath, setInventoryItemPath] = useState("");
  const [inventoryRemoveQuantity, setInventoryRemoveQuantity] = useState(1);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [destroyItemId, setDestroyItemId] = useState(0);
  const [monsterDraft, setMonsterDraft] = useState(EMPTY_MONSTER_DRAFT);
  const [editingMonsterId, setEditingMonsterId] = useState<string | null>(null);
  const [monsterImage, setMonsterImage] = useState<File | null>(null);
  const [monsterCatalog, setMonsterCatalog] = useState<MonsterCatalogResponse | null>(null);
  const [monsterCatalogSearch, setMonsterCatalogSearch] = useState("");
  const [selectedCatalogMonsterId, setSelectedCatalogMonsterId] = useState("");
  const [lootResolutions, setLootResolutions] = useState<LootResolution[]>([]);
  const [lootRecipients, setLootRecipients] = useState<Record<string, string>>({});
  const [gmToolsOpen, setGmToolsOpen] = useState(mode === "gm" && view === "table");
  const [fogLayer, setFogLayer] = useState<"exploration" | "battle">("exploration");
  const [fogTool, setFogTool] = useState<"add" | "remove">("add");
  const [fogBrush, setFogBrush] = useState(1.5);
  const [fogDensity, setFogDensity] = useState(1);
  const [iconFilter, setIconFilter] = useState<"all" | "map" | "items">("all");
  const [iconSearch, setIconSearch] = useState("");
  const [uploadedIcons, setUploadedIcons] = useState<WorkspaceIcon[]>([]);
  const [iconTitle, setIconTitle] = useState("");
  const [iconCategory, setIconCategory] = useState<"map" | "items">("items");
  const [iconFile, setIconFile] = useState<File | null>(null);
  const [openTokenId, setOpenTokenId] = useState<string | null>(null);
  const [openCharacterDetail, setOpenCharacterDetail] = useState<PlayableCharacter | null>(null);
  const [openItem, setOpenItem] = useState<PlayableCharacter["inventory"][number] | null>(null);
  const [effectBreakdownOpen, setEffectBreakdownOpen] = useState<string | null>(null);
  const [equipMenuItemPath, setEquipMenuItemPath] = useState<string | null>(null);
  const [attackTargetById, setAttackTargetById] = useState<Record<string, string>>({});
  const [attackPhysicalD20ById, setAttackPhysicalD20ById] = useState<Record<string, string>>({});
  const [attackResolution, setAttackResolution] = useState<AttackResolution | null>(null);
  const [targetPickerAttackId, setTargetPickerAttackId] = useState<string | null>(null);
  const [targetPickerAbilityId, setTargetPickerAbilityId] = useState<string | null>(null);
  const [loadingTokenDetail, setLoadingTokenDetail] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedIdRef = useRef(selectedId);
  const gmToolsOpenRef = useRef(gmToolsOpen);
  const charactersRef = useRef<PlayableCharacterSummary[]>([]);
  const refreshingRef = useRef(false);
  const mapViewportRef = useRef<HTMLDivElement>(null);
  const mapCanvasRef = useRef<HTMLDivElement>(null);
  const draggingTokenRef = useRef<DraggingToken | null>(null);
  const paintingFogRef = useRef(false);
  const fogPaintLayerRef = useRef<WorkspaceFog["exploration"] | null>(null);
  const fogPaintLayerKeyRef = useRef<"exploration" | "battle" | null>(null);
  const fogPaintSettingsRef = useRef({ tool: fogTool, brush: fogBrush, density: fogDensity });
  const fogMutationVersionRef = useRef(0);
  const fogSavePendingRef = useRef(false);
  const ledgerLoadedRef = useRef(false);
  const knownRollIdsRef = useRef(new Set<string>());
  const rollLedgerInitializedRef = useRef(false);
  const mapViewSaveTimerRef = useRef<number | null>(null);
  const gmEditorRef = useRef<HTMLDetailsElement>(null);
  const itemStudioRef = useRef<HTMLDetailsElement>(null);
  const itemToolsRef = useRef<HTMLDetailsElement>(null);
  const combatPanelRef = useRef<HTMLDetailsElement>(null);
  const attackCatalogRef = useRef<HTMLElement>(null);
  const focusAttacksRef = useRef(false);

  useEffect(() => {
    if (!gmToolsOpen && character && focusAttacksRef.current && attackCatalogRef.current) {
      focusAttacksRef.current = false;
      attackCatalogRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [gmToolsOpen, character]);
  const workspaceAuxLoadedRef = useRef(false);
  const playerMapIdRef = useRef(playerMapId);
  const activeMapIdRef = useRef("");
  const archiveItemsLoadedRef = useRef(false);

  async function loadOverview(forceAuxiliary = false) {
    const fogVersionAtRequest = fogMutationVersionRef.current;
    const fogSavePendingAtRequest = fogSavePendingRef.current;
    const shouldLoadAuxiliary = forceAuxiliary || !workspaceAuxLoadedRef.current;
    const [summaryItems, initialSnapshot, itemItems, ledgerItems, mapItems, iconItems, lootItems] = await Promise.all([
      listPlayableCharacters(), getSessionWorkspace(mode === "player" ? playerMapIdRef.current || undefined : undefined), mode === "gm" && shouldLoadAuxiliary ? listSessionItems().catch(() => []) : Promise.resolve(null), listSessionLedger(150), mode === "player" || shouldLoadAuxiliary ? listWorkspaceMaps().catch(() => []) : Promise.resolve(null), mode === "gm" && shouldLoadAuxiliary ? listWorkspaceIcons().catch(() => []) : Promise.resolve(null), mode === "gm" && shouldLoadAuxiliary ? listWorkspaceLoot().catch(() => []) : Promise.resolve(null),
    ]);
    let snapshot = initialSnapshot;
    if (
      mode === "player"
      && initialSnapshot.active_map_id
      && initialSnapshot.active_map_id !== activeMapIdRef.current
      && initialSnapshot.map?.id !== initialSnapshot.active_map_id
    ) {
      // A newly opened scene changes the table's active map. Follow that change
      // once, while preserving the player's freedom to browse other public maps
      // until the Master opens another map.
      snapshot = await getSessionWorkspace();
    }
    if (mode === "player") activeMapIdRef.current = snapshot.active_map_id || "";
    const ordered = [...summaryItems].sort((a, b) => Number(b.access_level === "owner") - Number(a.access_level === "owner"));
    const currentSelection = selectedIdRef.current;
    const ownerId = ordered.find((item) => item.access_level === "owner")?.id || "";
    const preferred = mode === "player"
      ? ownerId
      : ordered.some((item) => item.id === currentSelection)
        ? currentSelection
        : ownerId || ordered[0]?.id || "";
    charactersRef.current = ordered;
    setCharacters(ordered);
    setWorkspace((current) => ({
      ...snapshot,
      fog: fogSavePendingAtRequest || fogSavePendingRef.current || paintingFogRef.current || fogVersionAtRequest !== fogMutationVersionRef.current
        ? (current.fog || DEFAULT_FOG)
        : (snapshot.fog || DEFAULT_FOG),
    }));
    if (mode === "player" && snapshot.map?.id && snapshot.map.id !== playerMapIdRef.current) {
      playerMapIdRef.current = snapshot.map.id;
      setPlayerMapId(snapshot.map.id);
      localStorage.setItem("omnisvera_player_map_id", snapshot.map.id);
    } else if (mode === "player" && !snapshot.map && playerMapIdRef.current) {
      playerMapIdRef.current = "";
      setPlayerMapId("");
      localStorage.removeItem("omnisvera_player_map_id");
    }
    if (mapItems) setWorkspaceMaps(mapItems);
    if (itemItems) {
      setSessionItems(itemItems);
      setGrantDraft((current) => current.item_id || !itemItems.length
        ? current
        : { ...current, item_id: `session:${itemItems[0].id}`, character_id: current.character_id || selectedIdRef.current });
    }
    if (iconItems) setUploadedIcons(iconItems);
    if (lootItems) setLootResolutions(lootItems);
    if (shouldLoadAuxiliary) workspaceAuxLoadedRef.current = true;
    ledgerLoadedRef.current = true;
    setLedger(ledgerItems);
    if (preferred && preferred !== currentSelection) {
      selectedIdRef.current = preferred;
      setSelectedId(preferred);
      localStorage.setItem("omnisvera_selected_character", preferred);
    } else if (mode === "player" && !preferred && currentSelection) {
      selectedIdRef.current = "";
      setSelectedId("");
      setCharacter(null);
      localStorage.removeItem("omnisvera_selected_character");
    }
  }

  async function loadCharacter() {
    if (mode === "gm" && gmToolsOpenRef.current) {
      setCharacter(null);
      return;
    }
    const activeId = selectedIdRef.current;
    if (!activeId) return;
    const detail = await getPlayableCharacter(activeId);
    setCharacter(detail);
    setSessionNotes(detail.state?.session_notes || "");
  }

  async function loadArchiveItems(force = false) {
    if (mode !== "gm" || (!force && archiveItemsLoadedRef.current) || archiveItemsLoading) return;
    setArchiveItemsLoading(true);
    try {
      const notes = await listWorkspaceItemCatalog();
      setArchiveItems(notes);
      archiveItemsLoadedRef.current = true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha ao carregar a lista de itens.");
    } finally {
      setArchiveItemsLoading(false);
    }
  }

  useEffect(() => {
    gmToolsOpenRef.current = gmToolsOpen;
  }, [gmToolsOpen]);

  useEffect(() => {
    void heartbeatSessionWorkspace().catch(() => undefined);
    void loadOverview().catch((reason) => setError(reason instanceof Error ? reason.message : "Falha ao carregar a mesa."));
    const heartbeat = window.setInterval(() => void heartbeatSessionWorkspace().catch(() => undefined), 20_000);
    const leave = () => { if (mode === "player") void leaveSessionWorkspace().catch(() => undefined); };
    window.addEventListener("pagehide", leave);
    const refresh = window.setInterval(() => {
      if (refreshingRef.current || paintingFogRef.current || fogSavePendingRef.current || draggingTokenRef.current) return;
      refreshingRef.current = true;
      void loadOverview().then(loadCharacter).catch(() => undefined).finally(() => { refreshingRef.current = false; });
    }, 15_000);
    return () => { window.clearInterval(heartbeat); window.clearInterval(refresh); window.removeEventListener("pagehide", leave); leave(); };
  }, [mode]);

  useEffect(() => {
    if (mode !== "gm") return;
    let active = true;
    void listWorkspaceMonsterCatalog()
      .then((catalog) => { if (active) setMonsterCatalog(catalog); })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar o bestiário."); });
    return () => { active = false; };
  }, [mode]);

  useEffect(() => {
    selectedIdRef.current = selectedId;
    setCharacter(null);
    void loadCharacter().catch((reason) => setError(reason instanceof Error ? reason.message : "Falha ao carregar o personagem."));
  }, [selectedId, mode, gmToolsOpen]);

  useEffect(() => {
    let active = true;
    let disconnect: () => void = () => {};
    const refreshFromRealtime = () => {
      if (!active || refreshingRef.current || paintingFogRef.current || fogSavePendingRef.current || draggingTokenRef.current) return;
      refreshingRef.current = true;
      void loadOverview().then(loadCharacter).catch(() => undefined).finally(() => { refreshingRef.current = false; });
    };
    void connectSessionRealtime(refreshFromRealtime).then((stop) => {
      if (active) disconnect = stop;
      else stop();
    }).catch(() => undefined);
    return () => { active = false; disconnect(); };
  }, [mode]);

  useEffect(() => {
    const refreshRolls = () => void loadCharacter().catch(() => undefined);
    window.addEventListener("omnisvera-roll-created", refreshRolls);
    return () => window.removeEventListener("omnisvera-roll-created", refreshRolls);
  }, []);

  useEffect(() => {
    const openTools = () => { if (mode === "gm") setGmToolsOpen(true); };
    window.addEventListener("omnisvera-open-gm-tools", openTools);
    return () => window.removeEventListener("omnisvera-open-gm-tools", openTools);
  }, [mode]);

  useEffect(() => {
    if (mode === "gm") void loadArchiveItems();
  }, [gmToolsOpen, mode]);

  useEffect(() => {
    const viewport = mapViewportRef.current;
    if (!viewport || mode !== "gm") return;
    const zoomWithWheel = (event: WheelEvent) => {
      event.preventDefault();
      changeMapZoom(mapZoom + (event.deltaY < 0 ? .1 : -.1), event.clientX, event.clientY);
    };
    viewport.addEventListener("wheel", zoomWithWheel, { passive: false });
    return () => viewport.removeEventListener("wheel", zoomWithWheel);
  }, [mapZoom]);

  useEffect(() => {
    const view = workspace.view;
    const viewport = mapViewportRef.current;
    if (!view || !viewport) return;
    setMapZoom(Math.max(1, Math.min(3, Number(view.zoom) || 1)));
    window.requestAnimationFrame(() => {
      const maxLeft = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
      const maxTop = Math.max(0, viewport.scrollHeight - viewport.clientHeight);
      viewport.scrollLeft = Math.max(0, Math.min(maxLeft, Number(view.scroll_left || 0) * maxLeft));
      viewport.scrollTop = Math.max(0, Math.min(maxTop, Number(view.scroll_top || 0) * maxTop));
    });
  }, [workspace.view?.zoom, workspace.view?.scroll_left, workspace.view?.scroll_top]);

  useEffect(() => {
    if (!ledgerLoadedRef.current) return;
    const rollEntries = ledger.filter((item) => item.source_type === "dice_roll" && item.event_kind === "roll" && !item.voided_at);
    if (!rollLedgerInitializedRef.current) {
      rollEntries.forEach((item) => knownRollIdsRef.current.add(item.source_id));
      rollLedgerInitializedRef.current = true;
      return;
    }
    rollEntries
      .filter((item) => !knownRollIdsRef.current.has(item.source_id))
      .sort((a, b) => a.id - b.id)
      .forEach((item) => {
        knownRollIdsRef.current.add(item.source_id);
        const detail = item.detail || {};
        const results = Array.isArray(detail.results) ? detail.results.map(Number).filter(Number.isFinite) : [];
        if (!results.length) return;
        window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: {
          id: Number(item.source_id) || item.id,
          label: item.title || "Rolagem de dados",
          formula: String(detail.formula || detail.dice || "1d20"),
          dice: String(detail.dice || String(detail.formula || "1d20").match(/\d+d\d+/i)?.[0] || "1d20"),
          modifier: Number(detail.modifier || 0),
          individual_results: results,
          total: Number(detail.total ?? results.reduce((sum, value) => sum + value, 0)),
          character_id: item.character_id,
          roll_type: "remote",
          created_at: item.created_at,
        } }));
      });
  }, [ledger]);

  useEffect(() => {
    localStorage.setItem("omnisvera_session_map_zoom", String(mapZoom));
  }, [mapZoom]);

  async function refresh(updated?: PlayableCharacter) {
    if (updated) setCharacter(updated);
    await loadOverview();
    await loadCharacter();
    window.dispatchEvent(new CustomEvent("omnisvera-character-state"));
  }

  async function stateAction(action: string, payload: Record<string, unknown>, label: string) {
    if (!selectedId || busy) return;
    setBusy(label); setError("");
    try { await refresh(await applyCharacterStateAction(selectedId, action, payload, label)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível atualizar a ficha."); }
    finally { setBusy(""); }
  }

  async function restAllCharacters() {
    if (mode !== "gm" || busy || !characters.length) return;
    setBusy("rest-all"); setError("");
    try {
      await Promise.all(characters.map((item) => applyCharacterStateAction(
        item.id,
        "rest_at_inn",
        {},
        "Descanso geral concedido pelo Mestre",
      )));
      await loadOverview();
      await loadCharacter();
      window.dispatchEvent(new CustomEvent("omnisvera-character-state"));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível concluir o descanso geral."); }
    finally { setBusy(""); }
  }

  async function changeTableMode(tableMode: "digital" | "physical" | "test") {
    if (mode !== "gm" || busy || workspace.table_mode === tableMode) return;
    setBusy("table-mode"); setError("");
    try {
      const updated = await updateWorkspaceTableMode(tableMode);
      setWorkspace((current) => ({ ...current, table_mode: updated.table_mode }));
      await loadOverview();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível alterar o modo da mesa.");
    } finally { setBusy(""); }
  }

  async function definitionAction(fields: Record<string, unknown>) {
    if (mode !== "gm" || !selectedId || busy) return;
    setBusy("definition"); setError("");
    try { await refresh(await updateCharacterDefinition(selectedId, fields, "Ajuste manual do Mestre")); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o modificador."); }
    finally { setBusy(""); }
  }

  async function roll(rollType: string, sourceId?: string, targetValue?: number) {
    if (!selectedId || busy) return;
    setBusy(`roll:${rollType}:${sourceId || ""}`); setError("");
    try {
      const createdRoll = await rollCharacterAction(selectedId, { request_id: newDiceRequestId("workspace"), roll_type: rollType, source_id: sourceId, target_value: targetValue, visibility: "table" });
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: createdRoll }));
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível realizar a ação."); }
    finally { setBusy(""); }
  }

  async function resolveSelectedAttack(attackId: string) {
    if (!selectedId || busy) return;
    const target = attackTargetFor(attackId);
    if (!target) {
      setError("Selecione um alvo antes de resolver o ataque.");
      return;
    }
    const rollMode = workspace.table_mode === "physical" ? "physical" : "digital";
    const allowed = character?.definition.attacks?.find(a => a.id === attackId)?.attack_count || 1;
    const count = Math.min(allowed, attackCountById[attackId] || 1);
    const physicalValues = (attackPhysicalD20ById[attackId] || "").trim().split(/[ ,;]+/).map(Number);
    if (rollMode === "physical" && (physicalValues.length !== count || physicalValues.some(v => !Number.isInteger(v) || v < 1 || v > 20))) {
      setError(`Informe ${count} resultado(s) bruto(s) de d20, entre 1 e 20, separados por espaço.`);
      return;
    }
    setBusy(`attack:${attackId}`); setError("");
    try {
      const resolution = await resolveCharacterAttack(selectedId, {
        request_id: newDiceRequestId("attack"),
        attack_id: attackId,
        target_type: "token",
        target_id: target.id,
        roll_mode: rollMode,
        attack_count: count,
        ...(rollMode === "physical" ? { d20s: physicalValues } : {}),
      });
      setAttackResolution(resolution);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível resolver o ataque.");
    } finally {
      setBusy("");
    }
  }

  async function confirmResolvedAttack() {
    if (!attackResolution || attackResolution.confirmed || busy) return;
    setBusy(`confirm:${attackResolution.resolution_id}`); setError("");
    try {
      const confirmed = await confirmCharacterAttack(attackResolution.resolution_id);
      setAttackResolution(confirmed);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível confirmar o ataque.");
    } finally {
      setBusy("");
    }
  }

  async function useAbility(ability: SessionAbility, target?: WorkspaceToken) {
    const resource = abilityResource(ability, character?.state?.resources || []);
    if (ability.requires_equipped_item && !requiredItemForAbility(ability)) {
      setError(`Equipe ${ability.requires_equipped_item} para usar ${ability.name}.`);
      return;
    }
    if (ability.blocked) {
      setError(`${ability.name} ainda está bloqueado.`);
      return;
    }
    if (ability.id === "caixao") {
      await stateAction("rest_at_inn", {}, `${character?.definition.name || "Personagem"} descansou no Caixão`);
      const refreshed = character?.state?.resources.find((item) => item.key === "caixao");
      if (refreshed) await stateAction("consume_resource", { resource_key: refreshed.key, amount: 1 }, `Usou ${ability.name}`);
      return;
    }
    if (resource) {
      await stateAction("consume_resource", { resource_key: resource.key, amount: ability.uses?.cost || 1 }, `Usou ${ability.name}${target ? ` em ${target.name}` : ""}`);
      return;
    }
    setBusy(`ability:${ability.id}`);
    try {
      await sendWorkspaceMessage(`${character?.definition.name || "Personagem"} usou ${ability.name}${target ? ` em ${target.name}` : ""}.`, "action");
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao registrar a habilidade."); }
    finally { setBusy(""); }
  }

  async function submitMessage(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || busy) return;
    setBusy("message"); setError("");
    try { await sendWorkspaceMessage(message.trim()); setMessage(""); await loadOverview(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível enviar a mensagem."); }
    finally { setBusy(""); }
  }

  async function submitMap(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !mapFile || !mapTitle.trim() || busy) return;
    setBusy("map"); setError("");
    try {
      const dataBase64 = await fileAsBase64(mapFile);
      await uploadWorkspaceMap({ title: mapTitle.trim(), filename: mapFile.name, content_type: mapFile.type || "application/octet-stream", data_base64: dataBase64, visible_to_players: mapVisibleToPlayers });
      setMapFile(null); setMapTitle(""); setMapVisibleToPlayers(false); await loadOverview(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível trocar a imagem."); }
    finally { setBusy(""); }
  }

  async function submitIcon(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !iconFile || !iconTitle.trim() || busy) return;
    setBusy("icon"); setError("");
    try {
      const dataBase64 = await fileAsBase64(iconFile);
      const icon = await uploadWorkspaceIcon({ label: iconTitle.trim(), category: iconCategory, filename: iconFile.name, content_type: iconFile.type || "application/octet-stream", data_base64: dataBase64 });
      setUploadedIcons((current) => [icon, ...current]);
      workspaceAuxLoadedRef.current = false;
      await loadOverview(true);
      setIconTitle(""); setIconFile(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível carregar o ícone."); }
    finally { setBusy(""); }
  }

  async function selectItemImage(file: File | null) {
    setItemImage(file); setItemImageIcon(null); setError("");
    if (!file) return;
    setItemImagePreparing(true);
    try {
      const label = itemDraft.name.trim() || file.name.replace(/\.[^.]+$/, "") || "Item";
      const icon = await uploadWorkspaceIconFile({ label, category: "items", file });
      setItemImageIcon(icon);
      setItemDraft((current) => ({ ...current, image_path: icon.path }));
      setUploadedIcons((current) => [icon, ...current.filter((item) => item.id !== icon.id)]);
      workspaceAuxLoadedRef.current = false;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível preparar a imagem do item.");
    } finally {
      setItemImagePreparing(false);
      const input = document.querySelector<HTMLInputElement>(".workspace-item-image-upload input[type='file']");
      if (input) input.value = "";
    }
  }

  async function changeWorkspaceMap(mapId: string) {
    if (mode !== "gm" || !mapId || busy) return;
    setBusy("map-select"); setError("");
    try { await selectWorkspaceMap(mapId); await loadOverview(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível trocar o mapa."); }
    finally { setBusy(""); }
  }

  async function browseWorkspaceMap(mapId: string) {
    if (mode !== "player" || !mapId || busy) return;
    playerMapIdRef.current = mapId;
    setPlayerMapId(mapId);
    localStorage.setItem("omnisvera_player_map_id", mapId);
    setBusy("map-browse"); setError("");
    try { await loadOverview(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível abrir o mapa."); }
    finally { setBusy(""); }
  }

  async function changeMapVisibility(mapId: string, visibleToPlayers: boolean) {
    if (mode !== "gm" || !mapId || busy) return;
    setBusy("map-visibility"); setError("");
    try { await updateWorkspaceMapVisibility(mapId, visibleToPlayers); await loadOverview(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível alterar a visibilidade do mapa."); }
    finally { setBusy(""); }
  }

  async function pinCharacter(characterId: string) {
    if (mode !== "gm" || busy) return;
    const summary = characters.find((item) => item.id === characterId);
    if (!summary) return;
    setBusy(`pin:${characterId}`); setError("");
    try {
      await createWorkspaceToken({
        token_type: "character", character_id: characterId, name: summary.name,
        color: characterColor(characterId), ...nextPinPosition(workspace.tokens), map_id: workspace.map?.id || "default",
      });
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível posicionar o personagem."); }
    finally { setBusy(""); }
  }

  function applyCatalogMonster() {
    const monster = monsterCatalog?.monsters.find((item) => item.id === selectedCatalogMonsterId);
    if (!monster) return;
    const marker = markerForMonster(monster);
    const hp = monster.average_hp ?? Number(monster.hit_points.match(/\d+/)?.[0] || 10);
    const level = Number(monster.hit_dice.match(/\d+/)?.[0] || 1);
    const identity = [monster.category, monster.size, monster.alignment].filter(Boolean).join(" · ");
    setMonsterDraft((current) => ({
      ...current,
      name: monster.name,
      current_hp: hp,
      maximum_hp: hp,
      color: marker.color,
      image_path: current.image_path || monster.image_path || "",
      marker: marker.marker,
      role: monster.category || "Inimigo",
      level,
      armor_class: monster.armor_class ?? 10,
      description: [
        identity,
        monster.habitat ? `Habitat: ${monster.habitat}` : "",
        `DV ${monster.hit_dice || "—"} · PV ${monster.hit_points || "—"} · JP ${monster.saving_throw ?? "—"} · MO ${monster.morale ?? "—"} · MV ${monster.movement || "—"} · XP ${monster.experience_points ?? "—"}`,
      ].filter(Boolean).join("\n"),
      attacks: monster.attacks.map((attack) => [attack.name, attack.damage, attack.bonus ?? "", attack.count ? `${attack.count}× · ${attack.raw}` : attack.raw].join(" | ")).join("\n"),
      abilities: monster.abilities.map((ability) => `${ability.name}: ${ability.description}`).join("\n"),
      notes: `Encontro ${monster.encounter || "—"} · Tesouro ${monster.treasure || "—"}`,
      source_monster_id: monster.id,
      source_url: monster.source_url,
      hit_dice: monster.hit_dice,
      hit_points: monster.hit_points,
      saving_throw: monster.saving_throw,
      morale: monster.morale,
      experience_points: monster.experience_points,
      treasure: monster.treasure,
      movement: monster.movement,
      category: monster.category,
      size: monster.size,
      alignment: monster.alignment,
      habitat: monster.habitat,
    }));
    setMonsterImage(null);
  }

  async function pinLocationIcon(icon: { label: string; path: string }) {
    if (mode !== "gm" || busy) return;
    setBusy("pin-location"); setError("");
    try {
      await createWorkspaceToken({ token_type: "location", name: icon.label, image_path: icon.path,
        visible_to_players: false, sheet: { role: "Local", marker: "⌖" }, ...nextPinPosition(workspace.tokens), map_id: workspace.map?.id || "default" });
      await loadOverview();
    } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível criar o pin"); }
    finally { setBusy(""); }
  }

  async function createMonster(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !monsterDraft.name.trim() || busy) return;
    setBusy("monster"); setError("");
    try {
      const imageData = monsterImage ? await fileAsBase64(monsterImage) : undefined;
      const conditions = monsterDraft.conditions.split(",").map((item) => item.trim()).filter(Boolean);
      const maximumHp = Math.max(1, Math.min(99999, Math.round(Number(monsterDraft.maximum_hp) || 1)));
      const currentHp = Math.max(0, Math.min(maximumHp, Math.round(Number(monsterDraft.current_hp) || 0)));
      const sheet: WorkspaceTokenSheet = {
        marker: monsterDraft.marker,
        role: monsterDraft.role.trim() || "Inimigo",
        level: monsterDraft.level,
        armor_class: monsterDraft.armor_class,
        initiative: monsterDraft.initiative,
        description: monsterDraft.description.trim(),
        attacks: monsterDraft.attacks.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
          const [name, damage, bonus, notes] = line.split("|").map((part) => part.trim());
          return { name, damage, bonus, notes };
        }),
        abilities: monsterDraft.abilities.split("\n").map((item) => item.trim()).filter(Boolean),
        notes: monsterDraft.notes.trim(),
        source: monsterDraft.source_monster_id ? { catalog_id: "old-dragon-2-srd", monster_id: monsterDraft.source_monster_id, url: monsterDraft.source_url, license: "CC BY-SA 4.0" } : undefined,
        hit_dice: monsterDraft.hit_dice || undefined,
        hit_points: monsterDraft.hit_points || undefined,
        saving_throw: monsterDraft.saving_throw,
        morale: monsterDraft.morale,
        experience_points: monsterDraft.experience_points,
        treasure: monsterDraft.treasure || undefined,
        movement: monsterDraft.movement || undefined,
        category: monsterDraft.category || undefined,
        size: monsterDraft.size || undefined,
        alignment: monsterDraft.alignment || undefined,
        habitat: monsterDraft.habitat || undefined,
      };
      let savedToken: WorkspaceToken;
      if (editingMonsterId) {
        savedToken = await updateWorkspaceToken(editingMonsterId, { name: monsterDraft.name.trim(), color: monsterDraft.color, visible_to_players: monsterDraft.visible_to_players, maximum_hp: maximumHp, current_hp: currentHp, image_path: monsterDraft.image_path || undefined, conditions, sheet });
      } else {
        savedToken = await createWorkspaceToken({
          token_type: "monster", name: monsterDraft.name.trim(), color: monsterDraft.color,
          visible_to_players: monsterDraft.visible_to_players,
          maximum_hp: maximumHp, current_hp: currentHp, image_path: monsterDraft.image_path || undefined,
          ...nextPinPosition(workspace.tokens), image_filename: monsterImage?.name, image_data_base64: imageData, conditions, sheet, map_id: workspace.map?.id || "default",
        });
      }
      setWorkspace((current) => ({ ...current, tokens: editingMonsterId ? current.tokens.map((item) => item.id === savedToken.id ? savedToken : item) : [...current.tokens, savedToken] }));
      setMonsterDraft(EMPTY_MONSTER_DRAFT); setMonsterImage(null); setEditingMonsterId(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível criar o monstro."); }
    finally { setBusy(""); }
  }

  function editMonster(token: WorkspaceToken) {
    setEditingMonsterId(token.id);
    const sheet = token.sheet || {};
    setMonsterDraft({
      ...EMPTY_MONSTER_DRAFT, name: token.name, current_hp: token.current_hp ?? 0, maximum_hp: token.maximum_hp ?? 10,
      color: token.color, image_path: token.image_path || "", conditions: token.conditions.join(", "),
      visible_to_players: token.visible_to_players, marker: sheet.marker || "⚔",
      role: sheet.role || "Inimigo", level: sheet.level || 1, armor_class: sheet.armor_class || 10, initiative: sheet.initiative || 0,
      description: sheet.description || "", attacks: (sheet.attacks || []).map((attack) => [attack.name, attack.damage || "", attack.bonus ?? "", attack.notes || ""].join(" | ")).join("\n"),
      abilities: (sheet.abilities || []).join("\n"), notes: sheet.notes || "",
      source_monster_id: sheet.source?.monster_id || "", source_url: sheet.source?.url || "", hit_dice: sheet.hit_dice || "", hit_points: sheet.hit_points || "",
      saving_throw: sheet.saving_throw ?? null, morale: sheet.morale ?? null, experience_points: sheet.experience_points ?? null,
      treasure: sheet.treasure || "", movement: sheet.movement || "", category: sheet.category || "", size: sheet.size || "",
      alignment: sheet.alignment || "", habitat: sheet.habitat || "",
    });
    setMonsterImage(null);
  }

  async function toggleMonsterVisibility(token: WorkspaceToken) {
    if (mode !== "gm" || busy) return;
    setBusy(`visibility:${token.id}`); setError("");
    try {
      const saved = await updateWorkspaceToken(token.id, { visible_to_players: !token.visible_to_players });
      setWorkspace((current) => ({ ...current, tokens: current.tokens.map((item) => item.id === saved.id ? saved : item) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível alterar a visibilidade do marcador."); }
    finally { setBusy(""); }
  }

  async function openTokenDetails(token: WorkspaceToken) {
    if (token.character_id) {
      const summary = characterById.get(token.character_id);
      if (mode !== "gm" && summary?.access_level !== "owner") return;
      selectedIdRef.current = token.character_id;
      setSelectedId(token.character_id);
      localStorage.setItem("omnisvera_selected_character", token.character_id);
      setGmToolsOpen(false);
      setOpenTokenId(null);
      setOpenCharacterDetail(null);
      return;
    }
    setOpenTokenId(token.id);
    setOpenCharacterDetail(null);
    if (!token.character_id) return;
    setLoadingTokenDetail(true);
    try { setOpenCharacterDetail(await getPlayableCharacter(token.character_id)); }
    catch { setOpenCharacterDetail(null); }
    finally { setLoadingTokenDetail(false); }
  }

  async function removeMonster(token: WorkspaceToken) {
    if (mode !== "gm" || busy) return;
    if (!window.confirm(`Remover o monstro "${token.name}" do mapa?`)) return;
    setBusy(`remove-monster:${token.id}`); setError("");
    try {
      await removeWorkspaceToken(token.id);
      setWorkspace((current) => ({ ...current, tokens: current.tokens.filter((item) => item.id !== token.id) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível remover o monstro."); }
    finally { setBusy(""); }
  }

  async function refreshLoot() {
    const resolutions = await listWorkspaceLoot();
    setLootResolutions(resolutions);
    return resolutions;
  }

  async function generateTokenLoot(token: WorkspaceToken, scope: "carried" | "lair", rollMode: "digital" | "quick" | "requested" = "digital") {
    if (mode !== "gm" || busy) return;
    const lairId = scope === "lair" ? window.prompt("Identificador deste covil (ex.: ruinas-norte):", `${token.map_id || "mapa"}-covil`)?.trim() : undefined;
    if (scope === "lair" && !lairId) return;
    setBusy(`loot:${token.id}:${scope}`); setError("");
    try {
      const resolution = await resolveWorkspaceLoot({ request_id: newDiceRequestId("loot"), token_id: token.id, scope, roll_mode: rollMode, lair_id: lairId, roller_character_id: rollMode === "requested" ? (selectedIdRef.current || charactersRef.current[0]?.id) : undefined });
      setLootResolutions((current) => [...current.filter((item) => item.resolution_id !== resolution.resolution_id), resolution]);
      setLootRecipients((current) => ({ ...current, ...Object.fromEntries(resolution.rewards.map((reward) => [`${resolution.resolution_id}:${reward.id}`, current[`${resolution.resolution_id}:${reward.id}`] || selectedIdRef.current || charactersRef.current[0]?.id || ""])) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível gerar o espólio."); }
    finally { setBusy(""); }
  }

  async function finalizeLootRolls(resolution: LootResolution) {
    if (busy) return;
    setBusy(`loot-finalize:${resolution.resolution_id}`); setError("");
    try {
      const finalized = await finalizeWorkspaceLootRolls(resolution.resolution_id);
      setLootResolutions((current) => current.map((item) => item.resolution_id === finalized.resolution_id ? finalized : item));
      setLootRecipients((current) => ({ ...current, ...Object.fromEntries(finalized.rewards.map((reward) => [`${finalized.resolution_id}:${reward.id}`, current[`${finalized.resolution_id}:${reward.id}`] || selectedIdRef.current || charactersRef.current[0]?.id || ""])) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "As rolagens ainda não foram concluídas."); }
    finally { setBusy(""); }
  }

  function editLootReward(resolutionId: string, rewardId: string, fields: Partial<LootReward>) {
    setLootResolutions((current) => current.map((resolution) => resolution.resolution_id !== resolutionId ? resolution : {
      ...resolution, rewards: resolution.rewards.map((reward) => reward.id === rewardId ? { ...reward, ...fields } : reward),
    }));
  }

  async function saveLootDraft(resolution: LootResolution) {
    if (busy) return;
    setBusy(`loot-save:${resolution.resolution_id}`); setError("");
    try {
      const saved = await updateWorkspaceLoot(resolution.resolution_id, resolution.rewards);
      setLootResolutions((current) => current.map((item) => item.resolution_id === saved.resolution_id ? saved : item));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o espólio."); }
    finally { setBusy(""); }
  }

  async function revealLootDraft(resolution: LootResolution) {
    if (busy) return;
    setBusy(`loot-reveal:${resolution.resolution_id}`); setError("");
    try {
      const revealed = await revealWorkspaceLoot(resolution.resolution_id);
      setLootResolutions((current) => current.map((item) => item.resolution_id === revealed.resolution_id ? revealed : item));
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível revelar o espólio."); }
    finally { setBusy(""); }
  }

  async function distributeLootDraft(resolution: LootResolution) {
    if (busy) return;
    const allocations = resolution.rewards.map((reward) => ({
      reward_id: reward.id,
      character_id: lootRecipients[`${resolution.resolution_id}:${reward.id}`] || selectedIdRef.current || charactersRef.current[0]?.id || "",
      quantity: reward.quantity,
    }));
    if (allocations.some((allocation) => !allocation.character_id)) { setError("Escolha um personagem para cada recompensa."); return; }
    if (!window.confirm(`Distribuir integralmente o espólio de ${resolution.source_name}?`)) return;
    setBusy(`loot-distribute:${resolution.resolution_id}`); setError("");
    try {
      const distributed = await distributeWorkspaceLoot(resolution.resolution_id, { request_id: newDiceRequestId("loot-distribution"), allocations });
      setLootResolutions((current) => current.map((item) => item.resolution_id === distributed.resolution_id ? distributed : item));
      await Promise.all([refreshLoot(), loadOverview()]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível distribuir o espólio."); }
    finally { setBusy(""); }
  }

  function tokenCoordinates(event: ReactPointerEvent<HTMLDivElement>) {
    const rect = mapCanvasRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return {
      latitude: Math.max(0, Math.min(100, (event.clientY - rect.top) / rect.height * 100)),
      longitude: Math.max(0, Math.min(100, (event.clientX - rect.left) / rect.width * 100)),
    };
  }

  function queueWorkspaceViewSave(zoom = mapZoom) {
    if (mode !== "gm") return;
    const viewport = mapViewportRef.current;
    if (!viewport) return;
    const maxLeft = Math.max(1, viewport.scrollWidth - viewport.clientWidth);
    const maxTop = Math.max(1, viewport.scrollHeight - viewport.clientHeight);
    const payload = {
      zoom,
      scroll_left: viewport.scrollLeft / maxLeft,
      scroll_top: viewport.scrollTop / maxTop,
    };
    if (mapViewSaveTimerRef.current) window.clearTimeout(mapViewSaveTimerRef.current);
    mapViewSaveTimerRef.current = window.setTimeout(() => {
      void updateWorkspaceView(payload).catch(() => undefined);
    }, 220);
  }

  function changeMapZoom(nextZoom: number, clientX?: number, clientY?: number) {
    const viewport = mapViewportRef.current;
    const zoom = Math.max(1, Math.min(3, Math.round(nextZoom * 10) / 10));
    if (!viewport || zoom === mapZoom) return;
    const rect = viewport.getBoundingClientRect();
    const anchorX = clientX == null ? viewport.clientWidth / 2 : clientX - rect.left;
    const anchorY = clientY == null ? viewport.clientHeight / 2 : clientY - rect.top;
    const relativeX = (viewport.scrollLeft + anchorX) / Math.max(1, viewport.scrollWidth);
    const relativeY = (viewport.scrollTop + anchorY) / Math.max(1, viewport.scrollHeight);
    setMapZoom(zoom);
    window.requestAnimationFrame(() => {
      viewport.scrollLeft = relativeX * viewport.scrollWidth - anchorX;
      viewport.scrollTop = relativeY * viewport.scrollHeight - anchorY;
      queueWorkspaceViewSave(zoom);
    });
  }

  function canMoveToken(token: WorkspaceToken) {
    return mode === "gm" || (mode === "player" && token.character_id === selectedId);
  }

  function previewTokenMove(event: ReactPointerEvent<HTMLDivElement>) {
    const dragging = draggingTokenRef.current;
    if (!dragging) return;
    const coordinates = tokenCoordinates(event);
    if (!coordinates) return;
    dragging.latest = coordinates;
    dragging.element.style.left = `${coordinates.longitude}%`;
    dragging.element.style.top = `${coordinates.latitude}%`;
  }

  async function finishTokenMove(event: ReactPointerEvent<HTMLDivElement>) {
    const dragging = draggingTokenRef.current;
    draggingTokenRef.current = null;
    if (!dragging) return;
    if (dragging.element.hasPointerCapture?.(dragging.pointerId)) dragging.element.releasePointerCapture(dragging.pointerId);
    const coordinates = dragging.latest || tokenCoordinates(event);
    if (!coordinates) return;
    setWorkspace((current) => ({ ...current, tokens: current.tokens.map((item) => item.id === dragging.id ? { ...item, ...coordinates } : item) }));
    setBusy(`move:${dragging.id}`);
    try {
      const savedToken = await moveWorkspaceToken(dragging.id, coordinates.latitude, coordinates.longitude);
      setWorkspace((current) => ({ ...current, tokens: current.tokens.map((item) => item.id === savedToken.id ? savedToken : item) }));
    }
    catch (reason) {
      setWorkspace((current) => ({ ...current, tokens: current.tokens.map((item) => item.id === dragging.id ? { ...item, ...dragging.original } : item) }));
      setError(reason instanceof Error ? reason.message : "Não foi possível salvar a posição.");
    }
    finally { setBusy(""); }
  }

  function fogCellFromEvent(event: ReactPointerEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const layer = fogPaintLayerRef.current || (workspace.fog || DEFAULT_FOG)[fogLayer];
    if (!rect || !layer || rect.width <= 0 || rect.height <= 0) return null;
    return {
      column: Math.max(0, Math.min(layer.columns - 1, Math.floor((event.clientX - rect.left) / rect.width * layer.columns))),
      row: Math.max(0, Math.min(layer.rows - 1, Math.floor((event.clientY - rect.top) / rect.height * layer.rows))),
    };
  }

  function paintFog(event: ReactPointerEvent<HTMLDivElement>) {
    if (mode !== "gm" || view !== "maps" || !paintingFogRef.current) return;
    const center = fogCellFromEvent(event);
    if (!center) return;
    const currentFog = workspace.fog || DEFAULT_FOG;
    const layerKey = fogPaintLayerKeyRef.current || fogLayer;
    const layer = fogPaintLayerRef.current || currentFog[layerKey];
    const settings = fogPaintSettingsRef.current;
    const mistDensity = { ...(layer.mist_density || {}) };
    const radius = Math.max(0.5, settings.brush / 2);
    const firstRow = Math.floor(center.row - radius);
    const lastRow = Math.ceil(center.row + radius);
    const firstColumn = Math.floor(center.column - radius);
    const lastColumn = Math.ceil(center.column + radius);
    for (let row = firstRow; row <= lastRow; row += 1) {
      for (let column = firstColumn; column <= lastColumn; column += 1) {
        if (column < 0 || row < 0 || column >= layer.columns || row >= layer.rows) continue;
        if ((column - center.column) ** 2 + (row - center.row) ** 2 > radius ** 2) continue;
        const key = `${column}:${row}`;
        if (settings.tool === "add") mistDensity[key] = settings.density;
        else delete mistDensity[key];
      }
    }
    const nextLayer = { ...layer, mist_density: mistDensity };
    fogPaintLayerRef.current = nextLayer;
    setWorkspace((current) => ({ ...current, fog: { ...(current.fog || DEFAULT_FOG), [layerKey]: nextLayer } }));
  }

  function beginFogPaint(event: ReactPointerEvent<HTMLDivElement>) {
    if (mode !== "gm" || view !== "maps") return;
    event.preventDefault();
    event.stopPropagation();
    paintingFogRef.current = true;
    fogMutationVersionRef.current += 1;
    const currentLayer = (workspace.fog || DEFAULT_FOG)[fogLayer];
    fogPaintLayerKeyRef.current = fogLayer;
    fogPaintSettingsRef.current = { tool: fogTool, brush: fogBrush, density: fogDensity };
    fogPaintLayerRef.current = { ...currentLayer, mist_density: { ...(currentLayer.mist_density || {}) } };
    event.currentTarget.setPointerCapture?.(event.pointerId);
    paintFog(event);
  }

  async function finishFogPaint(event?: ReactPointerEvent<HTMLDivElement>) {
    if (!paintingFogRef.current) return;
    paintingFogRef.current = false;
    event?.currentTarget.releasePointerCapture?.(event.pointerId);
    if (mode !== "gm") return;
    const layerKey = fogPaintLayerKeyRef.current || fogLayer;
    const layer = fogPaintLayerRef.current || (workspace.fog || DEFAULT_FOG)[layerKey];
    const settings = fogPaintSettingsRef.current;
    fogPaintLayerRef.current = null;
    fogPaintLayerKeyRef.current = null;
    fogSavePendingRef.current = true;
    setBusy(`fog:${layerKey}`); setError("");
    try {
      const saved = await updateWorkspaceFog({ map_id: workspace.map?.id || "default", layer: layerKey, enabled: layer.enabled || settings.tool === "add", revealed_cells: layer.revealed_cells, mist_density: layer.mist_density || {} });
      setWorkspace((current) => ({ ...current, fog: { ...(current.fog || DEFAULT_FOG), [layerKey]: saved } }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar a fog do mapa."); }
    finally { fogSavePendingRef.current = false; setBusy(""); }
  }

  async function toggleFog(enabled: boolean) {
    if (mode !== "gm" || busy) return;
    const currentFog = workspace.fog || DEFAULT_FOG;
    const layer = currentFog[fogLayer];
    const mist_density = enabled && Object.keys(layer.mist_density || {}).length === 0
      ? Object.fromEntries(Array.from({ length: layer.rows * layer.columns }, (_, index) => [`${index % layer.columns}:${Math.floor(index / layer.columns)}`, fogDensity]))
      : layer.mist_density || {};
    setBusy(`fog-toggle:${fogLayer}`); setError("");
    try {
      const saved = await updateWorkspaceFog({ map_id: workspace.map?.id || "default", layer: fogLayer, enabled, revealed_cells: layer.revealed_cells, mist_density });
      setWorkspace((current) => ({ ...current, fog: { ...(current.fog || DEFAULT_FOG), [fogLayer]: saved } }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível alternar a fog."); }
    finally { setBusy(""); }
  }

  async function setAllFog(filled: boolean) {
    if (mode !== "gm" || busy) return;
    const currentFog = workspace.fog || DEFAULT_FOG;
    const layer = currentFog[fogLayer];
    const mist_density = filled
      ? Object.fromEntries(Array.from({ length: layer.rows * layer.columns }, (_, index) => [`${index % layer.columns}:${Math.floor(index / layer.columns)}`, fogDensity]))
      : {};
    setBusy(`fog-reset:${fogLayer}`); setError("");
    try {
      const saved = await updateWorkspaceFog({ map_id: workspace.map?.id || "default", layer: fogLayer, enabled: layer.enabled || filled, revealed_cells: layer.revealed_cells, mist_density });
      setWorkspace((current) => ({ ...current, fog: { ...(current.fog || DEFAULT_FOG), [fogLayer]: saved } }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível limpar a fog."); }
    finally { setBusy(""); }
  }

  async function saveItem(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !itemDraft.name.trim() || busy) return;
    setBusy("item"); setError("");
    try {
      let imagePath = itemDraft.image_path;
      const savedItem = await saveSessionItem({
        name: itemDraft.name.trim(), item_type: itemDraft.item_type.trim() || "item", image_path: imagePath || null,
        description: itemDraft.description.trim(), effects: itemDraft.effects.split("\n").map((item) => item.trim()).filter(Boolean), effect_rules: itemDraft.effect_rules, mechanics: itemDraft.mechanics,
        usable: itemDraft.usable,
      }, itemDraft.id || undefined);
      setSessionItems((current) => [...current.filter((item) => item.id !== savedItem.id), savedItem].sort((a, b) => a.name.localeCompare(b.name, "pt-BR")));
      setGrantDraft((current) => ({ ...current, item_id: `session:${savedItem.id}`, character_id: current.character_id || selectedIdRef.current }));
      setItemDraft(newItemDraft());
      setItemImage(null); setItemImageIcon(null);
      await loadOverview(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o item."); }
    finally { setBusy(""); }
  }

  function duplicateItemDraft() {
    setItemDraft((current) => ({ ...current, id: 0, name: current.name ? `Cópia de ${current.name}` : "" }));
    setItemImage(null); setItemImageIcon(null);
  }

  async function rechargeItems(cycle: "scene" | "dawn") {
    if (mode !== "gm" || busy) return;
    setBusy(`recharge:${cycle}`); setError("");
    try {
      const result = await rechargeSessionItems(cycle);
      await refresh();
      window.alert(`${result.recharged} item(ns) recarregado(s).`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível recarregar os itens."); }
    finally { setBusy(""); }
  }

  async function destroySelectedItem() {
    const selectedItem = sessionItems.find((item) => item.id === destroyItemId);
    if (mode !== "gm" || !selectedItem || busy) return;
    if (!window.confirm(`Destruir definitivamente o item "${selectedItem.name}"?`)) return;
    setBusy("item-delete"); setError("");
    try {
      await deleteSessionItem(selectedItem.id);
      setSessionItems((current) => current.filter((item) => item.id !== selectedItem.id));
      setGrantDraft((current) => current.item_id === `session:${selectedItem.id}` ? { ...current, item_id: "" } : current);
      setDestroyItemId(0);
      if (itemDraft.id === selectedItem.id) {
        setItemDraft(newItemDraft());
        setItemImage(null); setItemImageIcon(null);
      }
      await loadOverview(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível destruir o item."); }
    finally { setBusy(""); }
  }

  async function grantItem(event: FormEvent) {
    event.preventDefault();
    const characterId = grantDraft.character_id || selectedId;
    if (mode !== "gm" || !characterId || !grantDraft.item_id || busy) return;
    setBusy("grant"); setError("");
    try {
      const [source, rawId] = grantDraft.item_id.split(":");
      if (source === "note") {
        await applyCharacterStateAction(characterId, "grant_item", { note_id: Number(rawId), quantity: grantDraft.quantity }, "Mestre concedeu item do Arquivo");
      } else {
        await grantSessionItem({ character_id: characterId, item_id: Number(rawId), quantity: grantDraft.quantity });
      }
      setGrantDraft((current) => ({ ...current, item_id: "" }));
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível conceder o item."); }
    finally { setBusy(""); }
  }

  async function loadManagedInventory(targetId: string) {
    setInventoryTargetId(targetId);
    setInventoryItemPath("");
    setManagedInventory([]);
    if (!targetId) return;
    setInventoryLoading(true); setError("");
    try {
      const items = await listWorkspaceTargetInventory(targetId);
      setManagedInventory(items);
      setInventoryItemPath(items[0]?.item_path || "");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível carregar o inventário."); }
    finally { setInventoryLoading(false); }
  }

  async function removeManagedItem(event: FormEvent) {
    event.preventDefault();
    const item = managedInventory.find((entry) => entry.item_path === inventoryItemPath);
    if (mode !== "gm" || !inventoryTargetId || !item || busy) return;
    const quantity = Math.max(1, Math.min(item.quantity, Math.round(inventoryRemoveQuantity) || 1));
    setBusy("inventory-remove"); setError("");
    try {
      const items = await removeWorkspaceTargetItem({ target_id: inventoryTargetId, item_path: item.item_path, quantity });
      setManagedInventory(items);
      setInventoryItemPath(items.some((entry) => entry.item_path === item.item_path) ? item.item_path : (items[0]?.item_path || ""));
      setInventoryRemoveQuantity(1);
      if (inventoryTargetId === selectedIdRef.current) await loadCharacter();
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível retirar o item."); }
    finally { setBusy(""); }
  }

  const definition = character?.definition;
  const state = character?.state;
  const canOperate = character?.access_level !== "public";
  const [hpDraft, setHpDraft] = useState<number | "">(state?.current_hp ?? "");
  useEffect(() => setHpDraft(state?.current_hp ?? ""), [selectedId, state?.current_hp]);
  const inventoryRemovalControls = <form onSubmit={removeManagedItem}>
    <select value={inventoryTargetId} onChange={(event) => void loadManagedInventory(event.target.value)}>
      <option value="">Escolher personagem, NPC ou monstro</option>
      <optgroup label="Personagens">
        {characters.map((item) => <option key={`inventory-character:${item.id}`} value={item.id}>{item.name}</option>)}
      </optgroup>
      {workspace.tokens.some((token) => token.token_type === "monster") && <optgroup label="NPCs e monstros">
        {workspace.tokens.filter((token) => token.token_type === "monster").map((token) => <option key={`inventory-token:${token.id}`} value={token.id}>{token.name}{token.sheet?.role ? ` · ${token.sheet.role}` : ""}</option>)}
      </optgroup>}
    </select>
    <select value={inventoryItemPath} disabled={!inventoryTargetId || inventoryLoading || !managedInventory.length} onChange={(event) => setInventoryItemPath(event.target.value)}>
      <option value="">{inventoryLoading ? "Carregando inventário…" : managedInventory.length ? "Escolher item para retirar" : inventoryTargetId ? "Este inventário está vazio" : "Escolha primeiro o alvo"}</option>
      {managedInventory.map((item) => <option key={item.item_path} value={item.item_path}>{cleanItemDisplayName(item.item_title)} · {item.quantity}</option>)}
    </select>
    <input aria-label="Quantidade a retirar" type="number" min={1} max={managedInventory.find((item) => item.item_path === inventoryItemPath)?.quantity || 999} value={inventoryRemoveQuantity} onChange={(event) => setInventoryRemoveQuantity(Number(event.target.value))} />
    <button disabled={!inventoryTargetId || !inventoryItemPath || Boolean(busy) || inventoryLoading}>{busy === "inventory-remove" ? "Retirando…" : "Retirar do inventário"}</button>
  </form>;
  const mapTitleShown = workspace.map?.title || (mode === "gm" ? "Mapa de Nimalis" : "Nenhum mapa disponível");
  const mapImagePath = workspace.map?.image_path || (mode === "gm" ? "zz_media/maps/mapa_de_nimalis.png" : "");
  const fog = workspace.fog || DEFAULT_FOG;
  const fogLayers = mode === "gm" ? [fog[fogLayer]] : [fog.exploration, fog.battle].filter((layer) => layer.enabled);
  const fogColumns = fog[fogLayer].columns || 32;
  const fogRows = fog[fogLayer].rows || 24;
  const fogCells = Array.from({ length: fogColumns * fogRows }, (_, index) => `${index % fogColumns}:${Math.floor(index / fogColumns)}`);
  const fogIsRevealed = (cell: string) => fogLayers.every((layer) => {
    const density = layer.mist_density || {};
    if (Object.keys(density).length > 0) return Number(density[cell] || 0) <= 0;
    return layer.revealed_cells.length === 0 || layer.revealed_cells.includes(cell);
  });
  const mistDensityByCell = useMemo(() => {
    const result: Record<string, number> = {};
    fogLayers.forEach((layer) => Object.entries(layer.mist_density || {}).forEach(([cell, amount]) => {
      result[cell] = Math.max(result[cell] || 0, amount);
    }));
    return result;
  }, [fogLayers]);
  const presenceByCharacter = useMemo(() => new Map(workspace.presence.filter((item) => item.character_id).map((item) => [item.character_id as string, item.online])), [workspace.presence]);
  const nameById = useMemo(() => new Map(characters.map((item) => [item.id, item.name])), [characters]);
  const characterById = useMemo(() => new Map(characters.map((item) => [item.id, item])), [characters]);
  const abilities = (definition?.session_abilities || []).filter((item) => item.id !== "hemomancia" && item.id !== "grimorio-de-mago");
  const spells = abilities.filter((item) => item.kind === "spell");
  const basicAbilities = abilities.filter((item) => !["spell", "resource", "attack"].includes(item.kind));
  const groupedAbilities = basicAbilities.reduce<Record<string, SessionAbility[]>>((groups, ability) => {
    const group = ability.group || "Habilidades";
    (groups[group] ||= []).push(ability);
    return groups;
  }, {});
  const basicAttacks = abilities.filter((item) => item.kind === "attack");
  const equipmentAttacks = basicAttacks;
  const catalogResourceKeys = new Set(
    abilities
      .filter((item) => Boolean(item.uses) && item.kind !== "resource")
      .map((item) => abilityResource(item, state?.resources || [])?.key)
      .filter((key): key is string => Boolean(key)),
  );
  const standaloneResources = (state?.resources || []).filter((resource) => !catalogResourceKeys.has(resource.key) && !resource.label.toLocaleLowerCase("pt-BR").startsWith("magias de "));
  const consumables = character?.inventory.filter(isConsumable) || [];
  const carriedItems = character?.inventory.filter((item) => !isConsumable(item)) || [];
  const equippedItems = carriedItems.filter((item) => item.equipped);
  const equippedCombatItems = equippedItems.filter((item) => Boolean(item.damage_formula) || itemLooksLikeShield(item));
  const equippedWeapons = equippedCombatItems.filter((item) => Boolean(item.damage_formula) && !itemLooksLikeShield(item));
  const meleeSlotWeapons = equippedWeapons.filter((item) => normalizedName(item.equipment_slot || "").includes("corpo a corpo"));
  const legacyMeleeWeapons = equippedWeapons.filter((item) => !item.equipment_slot && !itemLooksLikeRangedWeapon(item));
  const equippedMeleeWeapon = definition?.id === "vezemir"
    ? meleeSlotWeapons.find((item) => normalizedName(item.item_title).includes("grisalma")) || meleeSlotWeapons[0] || legacyMeleeWeapons.find((item) => normalizedName(item.item_title).includes("grisalma")) || legacyMeleeWeapons[0]
    : meleeSlotWeapons[0] || legacyMeleeWeapons[0];
  const equippedRangedWeapon = equippedWeapons.find((item) => normalizedName(item.equipment_slot || "").includes("distancia"))
    || equippedWeapons.find((item) => !item.equipment_slot && itemLooksLikeRangedWeapon(item));
  const itemEffectBreakdown = definition?.item_effects?.breakdown || [];
  const openBreakdownEntries = effectBreakdownOpen === "armor"
    ? itemEffectBreakdown.filter((entry) => entry.kind === "armor_class_bonus")
    : itemEffectBreakdown.filter((entry) => entry.kind === "attribute_bonus" && entry.target === effectBreakdownOpen);
  const diceIcon = mediaUrlFromVaultPath(iconPathForItem("dados"));
  const allIcons = useMemo(() => [...COMPANION_ICON_CATALOG, ...uploadedIcons.map((icon) => ({ id: icon.id, label: icon.label, category: icon.category, path: icon.path }))], [uploadedIcons]);
  const filteredIcons = useMemo(() => allIcons.filter((icon) => (iconFilter === "all" || icon.category === iconFilter) && (!iconSearch.trim() || `${icon.label} ${icon.id}`.toLocaleLowerCase("pt-BR").includes(iconSearch.trim().toLocaleLowerCase("pt-BR")))), [allIcons, iconFilter, iconSearch]);
  const filteredCatalogMonsters = useMemo(() => {
    const search = catalogSearchKey(monsterCatalogSearch.trim());
    const monsters = monsterCatalog?.monsters || [];
    return search ? monsters.filter((monster) => catalogSearchKey(`${monster.name} ${monster.category} ${monster.habitat}`).includes(search)) : monsters;
  }, [monsterCatalog, monsterCatalogSearch]);
  const selectedCatalogMonster = useMemo(
    () => monsterCatalog?.monsters.find((monster) => monster.id === selectedCatalogMonsterId) || null,
    [monsterCatalog, selectedCatalogMonsterId],
  );
  const openToken = openTokenId ? workspace.tokens.find((token) => token.id === openTokenId) || null : null;

  const attackTargets = workspace.tokens.filter((token) => token.token_type !== "location" && (mode === "gm" || token.character_id !== selectedId));
  const defaultAttackRollMode: "digital" | "physical" = workspace.table_mode === "physical" ? "physical" : "digital";
  const attackTargetFor = (attackId: string) => attackTargets.find((token) => token.id === attackTargetById[attackId]);
  const attackTargetControl = (attackId: string) => {
    const target = attackTargetFor(attackId);
    return <button type="button" className="workspace-attack-target" onClick={() => setTargetPickerAttackId((current) => current === attackId ? null : attackId)}>{target ? `Alvo: ${target.name}` : "Selecionar alvo"}</button>;
  };
  const requiredItemForAbility = (ability: SessionAbility) => {
    if (!ability.requires_equipped_item) return null;
    const wanted = normalizedName(ability.requires_equipped_item);
    return character?.inventory.find((item) => item.equipped && normalizedName(item.item_title).includes(wanted)) || null;
  };
  const abilityTargetControl = (ability: SessionAbility) => (
    <button type="button" className="workspace-attack-target" onClick={() => setTargetPickerAbilityId((current) => current === ability.id ? null : ability.id)}>Selecionar alvo</button>
  );
  const selectedTargetAbility = abilities.find((ability) => ability.id === targetPickerAbilityId) || null;

  const attackSection = <section ref={attackCatalogRef} className="workspace-action-catalog workspace-attack-catalog">
    <header><span>ATAQUES</span><small>{(definition?.attacks?.length || 0) + equipmentAttacks.length}</small></header>
    {definition?.attacks?.map((attack) => {
      const fallbackWeapon = attack.id === "ranged" ? equippedRangedWeapon : attack.id === "melee" ? equippedMeleeWeapon : null;
      const weaponPath = attack.weapon_item_path || fallbackWeapon?.item_path;
      const weapon = weaponPath ? character?.inventory.find((item) => item.item_path === weaponPath) || fallbackWeapon : fallbackWeapon;
      const attackEquipment = attack.equipment?.length ? attack.equipment : weapon ? [{ ...weapon, role: "weapon" as const }] : [];
      const damage = attackDamage(definition?.id, attack, weapon?.damage_formula);
      const weaponTitle = attackEquipment.find((item) => item.role === "weapon")?.item_title || weapon?.item_title;
      return <article key={attack.id}>
        <div className="workspace-catalog-card-heading workspace-attack-card-heading">{attackEquipment.length > 0 && <span className="workspace-attack-equipment-icons">{attackEquipment.map((item) => { const icon = mediaUrlFromVaultPath(item.thumbnail || item.cover || iconPathForItem(item.item_title, item.item_type)); return icon ? <img key={item.item_path} src={icon} alt={cleanItemDisplayName(item.item_title)} title={`${cleanItemDisplayName(item.item_title)} · ${item.role === "weapon" ? "arma" : "suporte"}`} /> : null; })}</span>}<strong>{attack.name}</strong></div>
        <div className="workspace-catalog-card-summary"><small>{damage}{attack.range ? ` · ${attack.range}` : ""}{weaponTitle ? ` · ${cleanItemDisplayName(weaponTitle)}` : ""}</small><b>{attack.attack_bonus == null ? "—" : `${attack.attack_bonus >= 0 ? "+" : ""}${attack.attack_bonus}`}</b></div>
        {canOperate && <div className="workspace-inline-actions">
          {attackTargetControl(attack.id)}
          {(attack.attack_count || 1) > 1 && <label>Ataques nesta ação<select aria-label={`Quantidade de ataques de ${attack.name}`} value={Math.min(attack.attack_count || 1, attackCountById[attack.id] || 1)} onChange={e => setAttackCountById(current => ({ ...current, [attack.id]: Number(e.target.value) }))}>{Array.from({ length: attack.attack_count || 1 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}</select></label>}
          {defaultAttackRollMode === "physical" && <input aria-label={`Resultado físico de ${attack.name}`} type="text" inputMode="text" value={attackPhysicalD20ById[attack.id] || ""} onChange={(event) => setAttackPhysicalD20ById((current) => ({ ...current, [attack.id]: event.target.value }))} placeholder={(attackCountById[attack.id] || 1) > 1 ? "d20 de cada golpe · ex.: 15 8" : "d20 físico"} />}
          <button type="button" title="Calcula acerto e dano. O HP só muda após confirmar." disabled={Boolean(busy) || !attackTargetFor(attack.id) || !weaponPath} onClick={() => void resolveSelectedAttack(attack.id)}>{defaultAttackRollMode === "physical" ? "Conferir ataque" : "Rolar e conferir ataque"}</button>
        </div>}
      </article>;
    })}
    {equipmentAttacks.map((attack) => {
      const damage = attackDamage(definition?.id, attack);
      return <article key={attack.id}><div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{attack.name}</strong></div><div className="workspace-catalog-card-summary"><small>{damage}</small><b>—</b></div>{canOperate && <div className="workspace-inline-actions">{attackTargetControl(attack.id)}</div>}</article>;
    })}
    {targetPickerAttackId && <div className="workspace-attack-target-popover"><header><strong>Alvos no mapa atual</strong><button type="button" onClick={() => setTargetPickerAttackId(null)} aria-label="Fechar lista de alvos">×</button></header>{attackTargets.length ? attackTargets.map((token) => <button type="button" key={token.id} disabled={Boolean(busy)} className={attackTargetById[targetPickerAttackId] === token.id ? "active" : ""} onClick={() => { const attackId = targetPickerAttackId; setAttackTargetById((current) => ({ ...current, [attackId]: token.id })); setTargetPickerAttackId(null); }}><span style={{ color: token.color }}>{token.name}</span><small>{token.token_type === "monster" ? "Monstro / NPC" : "Personagem"} · CA {token.sheet?.armor_class ?? characterById.get(token.character_id || "")?.armor_class ?? "—"}</small></button>) : <p>Nenhum alvo disponível no mapa atual.</p>}{<button type="button" disabled={Boolean(busy)} onClick={() => { setAttackTargetById((current) => { const nextTargets = { ...current }; delete nextTargets[targetPickerAttackId]; return nextTargets; }); setTargetPickerAttackId(null); }}>Limpar alvo</button>}</div>}
  </section>;

  const timeline = useMemo(() => {
    // Character state events retain the complete before/after payload for audit and
    // rollback, but every player-facing mutation also records a readable action.
    // Showing both duplicates the action and leaks implementation JSON into the
    // session narrative, so the workspace timeline only renders narrative events.
    const entries: TimelineEntry[] = ledger.filter((item) => item.event_kind !== "state").map((item) => {
      const detail = item.detail || {};
      let detailText = "";
      if (item.event_kind === "roll") {
        const results = Array.isArray(detail.results) ? detail.results.join(", ") : "";
        detailText = `${String(detail.formula || "")}: [${results}] = ${String(detail.total ?? "")}`;
      }
      if (item.source_type === "combat_action") {
        const breakdown = detail.breakdown as AttackResolution["breakdown"] | undefined;
        detailText = (breakdown?.strikes || []).map((s, i) => `Golpe ${i + 1}: ${s.d20} + ${String(detail.attack_bonus)} = ${s.attack_total} / CA ${String(detail.target_ac)} · ${s.result === "hit" ? "acerto" : "erro"} · dano ${s.damage_total}`).join("\n");
        detailText += `\nPV: ${String(detail.hp_before)} → ${String(detail.hp_after)}`;
      }
      return {
      id: `ledger-${item.id}`,
      timestamp: item.created_at,
      actor: nameById.get(item.character_id || "") || item.actor_name || item.actor_id,
      actorId: item.character_id,
      kind: (["roll", "action", "state", "message"].includes(item.event_kind) ? item.event_kind : "event") as TimelineEntry["kind"],
      title: item.title,
      detail: detailText || undefined,
    }; });
    return entries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 250);
  }, [ledger, nameById]);

  useEffect(() => { if (timelineRef.current) timelineRef.current.scrollTop = 0; }, [timeline.length]);

  function renderGmWorkspaceTools(section: "master" | "maps" = "master") {
    if (mode !== "gm" || (section === "master" && !gmToolsOpen)) return null;
    return <section className="workspace-gm-drawer">
      {section === "master" && <details className="workspace-gm-section"><summary className="workspace-action-card"><b aria-hidden="true">▧</b><span>ASSETS IA</span><small>Gerar, revisar e aprovar imagens</small></summary><MasterAssetPanel onApproved={() => { void listWorkspaceIcons().then(setUploadedIcons); }} /></details>}
      {section === "maps" && <header className="workspace-gm-drawer-heading"><div><small>MAPAS</small><strong>Controles do mapa</strong></div></header>}
      {section === "maps" && <>
      <details className="workspace-gm-section workspace-fog-section">
        <summary><span>FOG DO MAPA</span><small>pintar e revelar o mapa</small></summary>
        <section className="workspace-fog-tools">
          <header><small>pinte o mapa e revele apenas o necessário aos jogadores</small><label><input type="checkbox" checked={fog[fogLayer].enabled} onChange={(event) => void toggleFog(event.target.checked)} /> Ativa</label></header>
          <div className="workspace-fog-toolbar"><button type="button" className={fogLayer === "exploration" ? "active" : ""} onClick={() => setFogLayer("exploration")}>Exploração</button><button type="button" className={fogLayer === "battle" ? "active" : ""} onClick={() => setFogLayer("battle")}>Batalha</button><span className="workspace-fog-divider" /><button type="button" className={fogTool === "add" ? "active" : ""} onClick={() => setFogTool("add")}>Pintar névoa</button><button type="button" className={fogTool === "remove" ? "active" : ""} onClick={() => setFogTool("remove")}>Apagar névoa</button><label>Densidade <input type="range" min={0.01} max={1} step={0.01} value={fogDensity} onChange={(event) => setFogDensity(Number(event.target.value))} /><output>{Math.round(fogDensity * 100)}%</output></label><label>Pincel redondo <input type="range" min={0.5} max={6} step={0.25} value={fogBrush} onChange={(event) => setFogBrush(Number(event.target.value))} /><output>{fogBrush.toLocaleString("pt-BR")} células</output></label><button type="button" onClick={() => void setAllFog(false)}>Limpar névoa</button><button type="button" onClick={() => void setAllFog(true)}>Preencher névoa</button></div>
        </section>
      </details>
      <details className="workspace-gm-section">
        <summary><span>CONTROLE DE ÍCONES E PINS</span><small>personagens, monstros e NPCs</small></summary>
        <section className="workspace-map-tools workspace-pin-controls">
          <section className="workspace-monster-catalog"><header><strong>BESTIÁRIO OFICIAL OD2</strong><small>{monsterCatalog ? `${filteredCatalogMonsters.length} exibidos · ${monsterCatalog.image_count} com arte · ${monsterCatalog.total} fichas` : "Carregando biblioteca…"}</small></header><input value={monsterCatalogSearch} onChange={(event) => setMonsterCatalogSearch(event.target.value)} placeholder="Buscar por nome, tipo ou habitat" /><div><select aria-label="Monstro do bestiário" value={selectedCatalogMonsterId} onChange={(event) => setSelectedCatalogMonsterId(event.target.value)}><option value="">Selecione uma ficha…</option>{filteredCatalogMonsters.map((monster) => <option key={monster.id} value={monster.id}>{monster.image_path ? "▣ " : ""}{monster.name} · DV {monster.hit_dice || "—"} · CA {monster.armor_class ?? "—"}</option>)}</select><button type="button" disabled={!selectedCatalogMonsterId} onClick={applyCatalogMonster}>Carregar no formulário</button></div>{selectedCatalogMonster && <article className="workspace-monster-catalog-preview">{selectedCatalogMonster.image_path ? <img src={mediaUrlFromVaultPath(selectedCatalogMonster.image_path)} alt={`Ilustração de ${selectedCatalogMonster.name}`} /> : <span aria-hidden="true">{markerForMonster(selectedCatalogMonster).marker}</span>}<div><strong>{selectedCatalogMonster.name}</strong><small>{selectedCatalogMonster.category || "Criatura"} · DV {selectedCatalogMonster.hit_dice || "—"} · CA {selectedCatalogMonster.armor_class ?? "—"}</small><small>{selectedCatalogMonster.image_attribution ? `Arte: ${selectedCatalogMonster.image_attribution} · ${selectedCatalogMonster.image_license}` : "Sem correspondência segura no pacote; você ainda pode escolher uma imagem."}</small></div></article>}{monsterDraft.source_monster_id && <small>Base carregada: {monsterDraft.name} · SRD OD2 · CC BY-SA 4.0. A imagem própria do Mestre sempre tem prioridade.</small>}</section>
          <div><header><span>PERSONAGENS NO MAPA</span><small>arraste os avatares para posicionar</small></header><div>{characters.map((item) => { const pinned = workspace.tokens.some((token) => token.character_id === item.id); return <button type="button" key={item.id} disabled={pinned || Boolean(busy)} style={{ color: characterColor(item.id) }} onClick={() => void pinCharacter(item.id)}>{pinned ? "✓" : "+"} {item.name}</button>; })}</div><div className="workspace-pin-list">{workspace.tokens.map((token) => <div key={token.id}><span><strong style={{ color: token.color }}>{token.name}</strong><small>{token.token_type === "monster" ? "Monstro/NPC" : token.token_type === "location" ? "Local" : "Personagem"} · {token.latitude.toFixed(1)}, {token.longitude.toFixed(1)}</small></span><button type="button" onClick={() => void openTokenDetails(token)}>{token.character_id ? "Selecionar" : token.token_type === "location" ? "Detalhes" : "Ficha"}</button></div>)}</div><section className="workspace-monster-manager"><header><span>MONSTROS E NPCS NO MAPA</span><small>gerencie os marcadores criados</small></header>{workspace.tokens.filter((token) => token.token_type === "monster").map((token) => <div className="workspace-monster-row" key={token.id}><span><strong style={{ color: token.color }}>{token.sheet?.marker || "⚔"} {token.name}</strong><small>{token.current_hp ?? "—"}/{token.maximum_hp ?? "—"} PV · {token.visible_to_players ? "visível" : "oculto"} · Tesouro {token.sheet?.treasure || "—"}</small></span><button type="button" disabled={Boolean(busy)} onClick={() => void toggleMonsterVisibility(token)}>{token.visible_to_players ? "Ocultar" : "Revelar"}</button><button type="button" disabled={Boolean(busy)} onClick={() => void openTokenDetails(token)}>Ficha</button><button type="button" disabled={Boolean(busy)} onClick={() => editMonster(token)}>Editar</button>{token.current_hp === 0 && token.sheet?.treasure && token.sheet.treasure !== "-" && <button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "carried")}>Gerar espólio</button>}{token.current_hp === 0 && /[A-O]/i.test(token.sheet?.treasure || "") && <button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "lair")}>Gerar covil</button>}<button type="button" disabled={Boolean(busy)} onClick={() => void removeMonster(token)}>Remover</button></div>)}{!workspace.tokens.some((token) => token.token_type === "monster") && <p className="workspace-empty-monsters">Nenhum monstro ou NPC criado.</p>}</section></div>
          <LocationQuickPin mapId={workspace.map?.id || "default"} tokens={workspace.tokens} onChange={refresh} />
          <form className="workspace-monster-form" onSubmit={createMonster}><header><span>{editingMonsterId ? "EDITAR MONSTRO / NPC" : "CRIAR E PINAR RAPIDAMENTE"}</span><small>nome, PV e CA bastam; imagem e ficha completa são opcionais</small></header><div className="workspace-monster-quick-presets">{CREATURE_MARKERS.map((preset) => <button type="button" key={preset.label} onClick={() => setMonsterDraft((current) => ({ ...current, marker: preset.marker, role: preset.role, color: preset.color }))}><span>{preset.marker}</span>{preset.label}</button>)}</div><input value={monsterDraft.name} onChange={(event) => setMonsterDraft({ ...monsterDraft, name: event.target.value })} placeholder="Nome do monstro ou NPC" /><div className="workspace-monster-hp"><label><span>PV atual</span><input type="number" min={0} max={99999} inputMode="numeric" aria-label="PV atual restante" value={monsterDraft.current_hp} onChange={(event) => setMonsterDraft({ ...monsterDraft, current_hp: event.target.value === "" ? 0 : Number(event.target.value) })} /></label><label><span>PV máximo</span><input type="number" min={1} max={99999} inputMode="numeric" aria-label="PV máximo" value={monsterDraft.maximum_hp} onChange={(event) => setMonsterDraft({ ...monsterDraft, maximum_hp: event.target.value === "" ? 1 : Number(event.target.value) })} /></label></div><div className="workspace-monster-sheet-grid"><input value={monsterDraft.role} onChange={(event) => setMonsterDraft({ ...monsterDraft, role: event.target.value })} placeholder="Tipo / função" /><select aria-label="Símbolo do marcador" value={monsterDraft.marker} onChange={(event) => setMonsterDraft({ ...monsterDraft, marker: event.target.value })}>{CREATURE_MARKERS.map((preset) => <option key={preset.marker} value={preset.marker}>{preset.marker} {preset.label}</option>)}</select><input type="number" min={0} max={99} value={monsterDraft.armor_class} onChange={(event) => setMonsterDraft({ ...monsterDraft, armor_class: Number(event.target.value) })} placeholder="CA" /><input type="number" min={-30} max={30} value={monsterDraft.initiative} onChange={(event) => setMonsterDraft({ ...monsterDraft, initiative: Number(event.target.value) })} placeholder="Iniciativa" /></div><label className="workspace-monster-visibility"><input type="checkbox" checked={monsterDraft.visible_to_players} onChange={(event) => setMonsterDraft({ ...monsterDraft, visible_to_players: event.target.checked })} /><span>{monsterDraft.visible_to_players ? "Mostrar aos jogadores ao criar" : "Preparar oculto e revelar depois"}</span></label><details className="workspace-monster-advanced"><summary>Ficha avançada opcional</summary><input type="number" min={1} max={30} value={monsterDraft.level} onChange={(event) => setMonsterDraft({ ...monsterDraft, level: Number(event.target.value) })} placeholder="Nível" /><input value={monsterDraft.conditions} onChange={(event) => setMonsterDraft({ ...monsterDraft, conditions: event.target.value })} placeholder="Status separados por vírgula" /><textarea value={monsterDraft.description} onChange={(event) => setMonsterDraft({ ...monsterDraft, description: event.target.value })} placeholder="Descrição da ficha" /><textarea value={monsterDraft.attacks} onChange={(event) => setMonsterDraft({ ...monsterDraft, attacks: event.target.value })} placeholder="Ataques: nome | dano | bônus | observações (um por linha)" /><textarea value={monsterDraft.abilities} onChange={(event) => setMonsterDraft({ ...monsterDraft, abilities: event.target.value })} placeholder="Habilidades (uma por linha)" /><textarea value={monsterDraft.notes} onChange={(event) => setMonsterDraft({ ...monsterDraft, notes: event.target.value })} placeholder="Notas do Mestre" /></details><input type="color" value={monsterDraft.color} onChange={(event) => setMonsterDraft({ ...monsterDraft, color: event.target.value })} title="Cor do marcador" /><label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMonsterImage(event.target.files?.[0] || null)} /><span>{monsterImage?.name || (monsterDraft.image_path ? "Imagem atual selecionada" : `${monsterDraft.marker} Usar símbolo agora ou escolher imagem`)}</span></label><button disabled={!monsterDraft.name.trim() || Boolean(busy)}>{editingMonsterId ? "Salvar ficha" : monsterDraft.visible_to_players ? "Criar, pinar e mostrar" : "Criar pin oculto"}</button>{editingMonsterId && <button type="button" onClick={() => { setEditingMonsterId(null); setMonsterDraft(EMPTY_MONSTER_DRAFT); }}>Cancelar</button>}</form>
        </section>
      </details>
      <details className="workspace-gm-section workspace-icon-section">
      <summary><span>CATÁLOGO DE ÍCONES</span><small>mapas e itens</small></summary>
      <section className="workspace-icon-catalog">
        <header><small>mapas, itens e marcadores</small><b>{filteredIcons.length}/{allIcons.length}</b></header>
        <div className="workspace-icon-toolbar"><input value={iconSearch} onChange={(event) => setIconSearch(event.target.value)} placeholder="Buscar ícone..." /><button type="button" className={iconFilter === "all" ? "active" : ""} onClick={() => setIconFilter("all")}>Todos</button><button type="button" className={iconFilter === "map" ? "active" : ""} onClick={() => setIconFilter("map")}>Mapa</button><button type="button" className={iconFilter === "items" ? "active" : ""} onClick={() => setIconFilter("items")}>Itens</button></div><form className="workspace-icon-upload" onSubmit={submitIcon}><input value={iconTitle} onChange={(event) => setIconTitle(event.target.value)} placeholder="Nome do novo ícone" /><select value={iconCategory} onChange={(event) => setIconCategory(event.target.value as "map" | "items")}><option value="items">Item</option><option value="map">Mapa</option></select><label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setIconFile(event.target.files?.[0] || null)} /><span>{iconFile?.name || "Escolher imagem do PC/celular"}</span></label><button disabled={!iconTitle.trim() || !iconFile || Boolean(busy)}>{busy === "icon" ? "Carregando…" : "Carregar ícone"}</button></form>
        <div className="workspace-icon-grid">{filteredIcons.map((icon) => <article key={`${icon.category}:${icon.id}`}><img src={mediaUrlFromVaultPath(icon.path)} alt="" /><strong>{icon.label}</strong><small>{icon.category === "map" ? "Mapa" : "Item"}</small><div><button type="button" onClick={() => setItemDraft((current) => ({ ...current, image_path: icon.path }))}>Usar em item</button>{icon.category === "map" && <button type="button" disabled={Boolean(busy)} onClick={() => void pinLocationIcon(icon)}>Criar pin oculto neste mapa</button>}</div></article>)}</div>
      </section>
      </details>
      </>}
      {section === "master" && <section className="workspace-master-overview">
        <header><div><small>RESUMO DA MESA</small><strong>{characters.length} personagens · {workspace.presence.filter((item) => item.online && item.actor_role === "player").length} jogadores online</strong></div><span>{workspace.map?.title || "Sem mapa ativo"}</span></header>
        <section className={`workspace-table-mode workspace-table-mode-${workspace.table_mode}`}>
          <div><small>MODO DA MESA</small><strong>{workspace.table_mode === "digital" ? "Digital" : workspace.table_mode === "physical" ? "Física" : "Teste"}</strong><p>{workspace.table_mode === "digital" ? "O Companion faz as rolagens por padrão." : workspace.table_mode === "physical" ? "Ataques pedem o valor bruto do dado físico por padrão." : "Simula sozinho a visão dos jogadores. As alterações continuam reais."}</p></div>
          <div role="group" aria-label="Modo operacional da mesa"><button type="button" className={workspace.table_mode === "digital" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("digital")}>Digital</button><button type="button" className={workspace.table_mode === "physical" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("physical")}>Física</button><button type="button" className={workspace.table_mode === "test" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("test")}>Teste</button></div>
        </section>
        <nav className="workspace-master-shortcuts" aria-label="Atalhos do Mestre">
          <button type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray", { detail: { panel: "request", characterId: selectedId } }))}><b>⚄</b><span><strong>Pedir rolagem</strong><small>Escolher jogador e teste</small></span></button>
          <button type="button" disabled={Boolean(busy) || !characters.length} onClick={() => void restAllCharacters()}><b>☾</b><span><strong>Descanso geral</strong><small>Restaurar os quatro personagens</small></span></button>
        </nav>
        <details ref={combatPanelRef} className="workspace-gm-section"><summary className="workspace-action-card"><b aria-hidden="true">⚔</b><span>COMBATE</span><small>Iniciativa, efeitos e multiataque</small></summary><CombatEncounterPanel mode={mode} tableMode={workspace.table_mode} mapId={workspace.map?.id || "default"} characters={characters} tokens={workspace.tokens} onChange={refresh} onPins={() => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "maps" }))} /></details>
      </section>}
      {section === "master" && <details ref={itemToolsRef} className="workspace-gm-section">
        <summary className="workspace-action-card"><b aria-hidden="true">◇</b><span>ITENS E LOOT</span><small>Criar, editar e distribuir espólios</small></summary>
        <section className="workspace-loot-resolutions">
          <header><div><small>ESPÓLIOS</small><strong>Gerar → revisar → revelar → distribuir</strong></div><button type="button" disabled={Boolean(busy)} onClick={() => void refreshLoot()}>Atualizar</button></header>
          {workspace.tokens.filter((token) => token.token_type === "monster" && token.current_hp === 0 && token.sheet?.treasure && token.sheet.treasure !== "-").map((token) => <div className="workspace-loot-source" key={`loot-source:${token.id}`}><span><strong>{token.name}</strong><small>0 PV · código {token.sheet?.treasure}</small></span>{treasureHasCarried(token.sheet?.treasure) && <><button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "carried", "digital")}>Sortear carregado</button><button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "carried", "quick")}>Usar rápido</button><button type="button" disabled={Boolean(busy) || !selectedId} onClick={() => void generateTokenLoot(token, "carried", "requested")}>Pedir rolagens a {characters.find((item) => item.id === selectedId)?.name || "jogador"}</button></>}{treasureHasLair(token.sheet?.treasure) && <button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "lair", "digital")}>Sortear covil</button>}</div>)}
          {!lootResolutions.length && <p>Nenhum espólio gerado. Reduza um monstro a 0 PV e use “Gerar espólio” nos controles do mapa.</p>}
          {lootResolutions.map((resolution) => <article key={resolution.resolution_id}>
            <header><span><strong>{resolution.source_name}</strong><small>Código {resolution.treasure_code} · {resolution.treasure_scope === "lair" ? "Covil" : "Carregado"} · {resolution.roll_mode === "quick" ? "Rápido" : resolution.roll_mode === "requested" ? "Rolagens solicitadas" : "Aleatório"}</small></span><b>{resolution.status === "draft" ? resolution.roll_mode === "requested" && !resolution.finalized_at ? "Aguardando jogador" : "Rascunho privado" : resolution.status === "revealed" ? "Revelado" : "Distribuído"}</b></header>
            {resolution.roll_mode === "requested" && !resolution.finalized_at && <p className="workspace-loot-pending">{resolution.pending_requests.length} rolagem(ns) enviada(s) para {characters.find((item) => item.id === resolution.pending_requests[0]?.roller_character_id)?.name || "o jogador"}. O jogador deve abrir os dados e concluir todas.</p>}
            <div className="workspace-loot-rewards">{resolution.rewards.length ? resolution.rewards.map((reward) => <label key={reward.id}>
              {resolution.status === "draft" ? <><input value={reward.name} onChange={(event) => editLootReward(resolution.resolution_id, reward.id, { name: event.target.value })} /><input aria-label={`Quantidade de ${reward.name}`} type="number" min={1} max={999999} value={reward.quantity} onChange={(event) => editLootReward(resolution.resolution_id, reward.id, { quantity: Math.max(1, Number(event.target.value) || 1) })} /></> : <span><strong>{reward.quantity}× {reward.name}</strong>{reward.description && <small>{reward.description}</small>}</span>}
              {resolution.status === "draft" && reward.gm_notes && <small>{reward.gm_notes}</small>}{resolution.status === "revealed" && <select aria-label={`Destino de ${reward.name}`} value={lootRecipients[`${resolution.resolution_id}:${reward.id}`] || selectedId || characters[0]?.id || ""} onChange={(event) => setLootRecipients((current) => ({ ...current, [`${resolution.resolution_id}:${reward.id}`]: event.target.value }))}>{characters.map((characterOption) => <option key={characterOption.id} value={characterOption.id}>{characterOption.name}</option>)}</select>}
            </label>) : <p>{resolution.roll_mode === "requested" && !resolution.finalized_at ? "O resultado será montado quando todas as solicitações forem concluídas." : "Nenhum tesouro foi encontrado nas rolagens."}</p>}</div>
            <footer>{resolution.status === "draft" && resolution.roll_mode === "requested" && !resolution.finalized_at ? <button type="button" disabled={Boolean(busy)} onClick={() => void finalizeLootRolls(resolution)}>Conferir rolagens e montar espólio</button> : resolution.status === "draft" ? <><button type="button" disabled={Boolean(busy)} onClick={() => void saveLootDraft(resolution)}>Salvar ajustes</button><button type="button" disabled={Boolean(busy)} onClick={() => void revealLootDraft(resolution)}>Revelar aos jogadores</button></> : null}{resolution.status === "revealed" && <button type="button" disabled={Boolean(busy) || !resolution.rewards.length} onClick={() => void distributeLootDraft(resolution)}>Confirmar distribuição</button>}{resolution.status === "distributed" && <small>Itens entregues exatamente uma vez e registrados no ledger.</small>}</footer>
          </article>)}
        </section>
        <details ref={itemStudioRef} className="workspace-item-studio workspace-gm-subsection">
          <summary><span>CRIAR E EDITAR ITENS</span><button type="button" onClick={(event) => { event.preventDefault(); setItemDraft(newItemDraft()); setItemImage(null); setItemImageIcon(null); }}>Novo</button></summary>
          <div className="workspace-item-presets"><span>MODELOS</span><button type="button" onClick={() => setItemDraft(itemPreset("potion"))}>Poção</button><button type="button" onClick={() => setItemDraft(itemPreset("weapon"))}>Arma</button><button type="button" onClick={() => setItemDraft(itemPreset("armor"))}>Armadura</button><button type="button" onClick={() => setItemDraft(itemPreset("relic"))}>Relíquia com cargas</button>{itemDraft.id > 0 && <button type="button" onClick={duplicateItemDraft}>Duplicar item</button>}</div>
          <div className="workspace-item-presets"><span>RECARGAS</span><button type="button" disabled={Boolean(busy)} onClick={() => void rechargeItems("scene")}>Fim de cena</button><button type="button" disabled={Boolean(busy)} onClick={() => void rechargeItems("dawn")}>Amanhecer</button><small>Descanso na estalagem recarrega automaticamente.</small></div>
          <form onSubmit={saveItem}>
            <details className="workspace-gm-subsection" open>
              <summary>{itemDraft.name.trim() ? "☑" : "☐"} 1 · Identificar item</summary>
              <input aria-label="Nome do item" value={itemDraft.name} onChange={e => setItemDraft({ ...itemDraft, name: e.target.value })} placeholder="Nome do item" required />
              <input aria-label="Tipo do item" value={itemDraft.item_type} onChange={e => setItemDraft({ ...itemDraft, item_type: e.target.value })} placeholder="Tipo" />
              <textarea value={itemDraft.description} onChange={e => setItemDraft({ ...itemDraft, description: e.target.value })} placeholder="Descrição (opcional)" />
            </details>
            <details className="workspace-gm-subsection"><summary>{itemDraft.image_path ? "☑" : "☐"} 2 · Imagem (opcional)</summary><label className="workspace-item-image-upload">{itemDraft.image_path && !itemImage && <img src={mediaUrlFromVaultPath(itemDraft.image_path)} alt="Ícone atual do item" />}<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => void selectItemImage(event.target.files?.[0] || null)} /><span>{itemImagePreparing ? "Enviando imagem…" : itemImageIcon ? `${itemImage?.name || "Imagem"} · pronta` : itemImage?.name || (itemDraft.image_path ? "Trocar imagem do item" : "Escolher imagem do PC/celular")}</span></label></details>
            <details className="workspace-gm-subsection"><summary>{itemDraft.effect_rules.length ? "☑" : "☐"} 3 · Regras (opcional)</summary>
              <ItemMechanicsEditor mechanics={itemDraft.mechanics} onChange={mechanics => setItemDraft(current => ({ ...current, mechanics, usable: current.usable || mechanics.consume_mode !== "none" }))} />
              <ItemRuleEditor rules={itemDraft.effect_rules} onChange={effect_rules => setItemDraft(current => ({ ...current, effect_rules, usable: current.usable || effect_rules.some(rule => rule.trigger === "on_use") }))} />
              <textarea value={itemDraft.effects} onChange={e => setItemDraft({ ...itemDraft, effects: e.target.value })} placeholder="Efeitos descritivos · um por linha" />
              <label><input type="checkbox" checked={itemDraft.usable} onChange={e => setItemDraft({ ...itemDraft, usable: e.target.checked })} /> Consumível / utilizável</label>
            </details>
            <details className="workspace-gm-subsection"><summary>4 · Conferir</summary><strong>{itemDraft.name || "Item sem nome"}</strong><p>{itemDraft.item_type} · {itemDraft.effect_rules.length} regra(s)</p><ItemEffectPreview rules={itemDraft.effect_rules} character={character} /></details>
            <button disabled={!itemDraft.name.trim() || Boolean(busy) || itemImagePreparing}>{itemImagePreparing ? "Enviando imagem…" : busy === "item" ? "Salvando…" : itemDraft.id ? "Salvar alterações do item" : "Criar item"}</button>
          </form>
          <div className="workspace-item-list">{sessionItems.map((item) => <button type="button" key={item.id} onClick={() => { setItemDraft({ id: item.id, name: item.name, item_type: item.item_type, description: item.description || "", effects: item.effects.join("\n"), effect_rules: item.effect_rules || [], mechanics: item.mechanics || newItemDraft().mechanics, usable: item.usable, image_path: item.image_path || "" }); setItemImage(null); setItemImageIcon(null); }}><strong>{item.name}</strong><small>{item.item_type} · {item.effect_rules?.length || 0} regras</small></button>)}</div>
          <form className="workspace-grant-item" onSubmit={grantItem}><select value={grantDraft.item_id} onFocus={() => { if (!archiveItems.length) void loadArchiveItems(true); }} onChange={(event) => setGrantDraft({ ...grantDraft, item_id: event.target.value })}><option value="">{archiveItemsLoading ? "Carregando itens…" : archiveItems.length || sessionItems.length ? `Selecionar item · ${archiveItems.length + sessionItems.length} disponíveis` : "Catálogo vazio · tocar para recarregar"}</option>{archiveItems.length > 0 && <optgroup label={`Arquivo de itens · ${archiveItems.length}`}>{archiveItems.map((item) => <option key={`note:${item.id}`} value={`note:${item.id}`}>{item.title}</option>)}</optgroup>}{sessionItems.length > 0 && <optgroup label="Itens da sessão">{sessionItems.map((item) => <option key={`session:${item.id}`} value={`session:${item.id}`}>{item.name}</option>)}</optgroup>}</select><select value={grantDraft.character_id || selectedId} onChange={(event) => setGrantDraft({ ...grantDraft, character_id: event.target.value })}>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><input type="number" min={1} max={999} value={grantDraft.quantity} onChange={(event) => setGrantDraft({ ...grantDraft, quantity: Number(event.target.value) })} /><button disabled={!grantDraft.item_id || Boolean(busy)}>Dar ao personagem</button></form>
          <section className="workspace-item-destroy">
            <header><span>DESTRUIR ITEM</span><small>remove do catálogo da sessão</small></header>
            <select value={destroyItemId || ""} onChange={(event) => setDestroyItemId(Number(event.target.value) || 0)}>
              <option value="">Selecionar item para destruir · {sessionItems.length} criados</option>
              {sessionItems.map((item) => <option key={`destroy:${item.id}`} value={item.id}>{item.name} · {item.item_type}</option>)}
            </select>
            <p>{destroyItemId ? "A exclusão será confirmada antes de acontecer." : "Itens que ainda estiverem em inventários não poderão ser destruídos."}</p>
            <button type="button" disabled={!destroyItemId || Boolean(busy)} onClick={() => void destroySelectedItem()}>{busy === "item-delete" ? "Destruindo…" : "Destruir item selecionado"}</button>
          </section>
          <section className="workspace-inventory-manager">
            <header><span>RETIRAR ITENS</span><small>personagens, NPCs e monstros</small></header>
            {inventoryRemovalControls}
          </section>
        </details>
      </details>}
      {section === "master" && <details ref={gmEditorRef} className="workspace-gm-section workspace-edit-section">
        <summary className="workspace-action-card"><b aria-hidden="true">✎</b><span>EDIÇÃO DO MESTRE</span><small>Ajustar as fichas dos personagens</small></summary>
        <section className="workspace-gm-tools">
          <details className="workspace-gm-subsection">
            <summary>Editar ficha de {definition?.name || "personagem selecionado"}</summary>
        <div className="workspace-gm-numbers"><NumericEditor label="PV atual" value={state?.current_hp} max={state?.maximum_hp || 999} onSave={(value) => stateAction("set_hp", { value }, "PV ajustado pelo Mestre")} /><NumericEditor label="PV máximo" value={state?.maximum_hp} min={1} onSave={(value) => definitionAction({ maximum_hp: value })} /><NumericEditor label="Nível" value={definition?.level} min={1} max={20} onSave={(value) => definitionAction({ level: value })} /><NumericEditor label="Classe de Armadura base" value={definition?.defenses?.base_armor_class ?? definition?.defenses?.armor_class} onSave={(value) => definitionAction({ armor_class: value })} /><NumericEditor label="Iniciativa" value={definition?.defenses?.initiative} min={-30} max={30} onSave={(value) => definitionAction({ initiative: value })} />{ATTRIBUTES.map(([key, label]) => <NumericEditor key={key} label={label} value={definition?.base_attributes?.[key] ?? definition?.attributes?.[key]} min={1} max={30} onSave={(value) => definitionAction({ attributes: { [key]: value } })} />)}</div>
        <form onSubmit={(event) => { event.preventDefault(); if (condition.trim()) { void stateAction("add_condition", { condition: condition.trim() }, `Adicionou ${condition.trim()}`); setCondition(""); } }}><input value={condition} onChange={(event) => setCondition(event.target.value)} placeholder="Nova condição" /><button disabled={!condition.trim() || Boolean(busy)}>Adicionar status</button></form>
        <label className="workspace-session-notes"><span>Notas da sessão do Mestre</span><textarea value={sessionNotes} onChange={(event) => setSessionNotes(event.target.value)} /><button disabled={Boolean(busy) || sessionNotes === (state?.session_notes || "")} onClick={() => void stateAction("set_session_notes", { value: sessionNotes }, "Atualizou notas da sessão")}>Salvar notas</button></label>

        <button className="workspace-rest-button" disabled={Boolean(busy)} onClick={() => void stateAction("rest_at_inn", {}, "Descanso completo no INN")}>Descanso completo · restaurar vida, status, magias e habilidades</button>
          </details>
        </section>
      </details>}
    </section>;
  }

  return <section className={`session-workspace unified-workspace workspace-view-${view}`}>
    <header className="party-status-header">
      {mode === "gm" ? <button type="button" className={`party-status-title party-master-summary ${gmToolsOpen ? "active" : ""}`} onClick={() => setGmToolsOpen(true)} aria-label="Abrir painel do Mestre"><span>PAINEL DO MESTRE</span><strong>Omnisvera</strong><small>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} online · abrir resumo</small></button> : <div className="party-status-title"><span>MESA ÚNICA</span><strong>Omnisvera</strong><small>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} online</small></div>}
      <div className="party-status-list">{characters.map((item) => {
        const hpPercent = item.maximum_hp ? Math.max(0, Math.min(100, Number(item.current_hp || 0) / item.maximum_hp * 100)) : 0;
        const online = Boolean(presenceByCharacter.get(item.id));
        const selectable = mode === "gm" || item.access_level === "owner";
        return <button key={item.id} type="button" data-character={item.id} disabled={!selectable} aria-label={selectable ? `Abrir ficha de ${item.name}` : `${item.name} no grupo`} className={!gmToolsOpen && selectedId === item.id ? "active" : ""} onClick={() => { if (!selectable) return; setGmToolsOpen(false); selectedIdRef.current = item.id; setSelectedId(item.id); localStorage.setItem("omnisvera_selected_character", item.id); }}>
          <span className="workspace-avatar"><CharacterPortrait character={item} /><i className={online ? "online" : "offline"} title={online ? "Online" : "Offline"} /></span>
          <span><strong style={{ color: characterColor(item.id) }}>{item.name}</strong><small>{item.conditions.length ? item.conditions.join(" · ") : `${item.class_name || "Personagem"} · Nv. ${item.level || 1}`}</small><i><b style={{ width: `${hpPercent}%` }} /></i></span>
          <em>{item.current_hp ?? "—"}/{item.maximum_hp ?? "—"}</em>
        </button>;
      })}</div>
    </header>
    {mode === "player" && <div className={`workspace-table-mode-banner workspace-table-mode-${workspace.table_mode}`}>Mesa {workspace.table_mode === "digital" ? "digital" : workspace.table_mode === "physical" ? "física" : "em teste"}</div>}

    {error && <p className="workspace-error">{error}</p>}
    <div className="session-workspace-grid">
      {view === "table" && <aside className={`workspace-character-panel ${gmToolsOpen ? "gm-tools-active" : ""}`}>
        {mode === "gm" && gmToolsOpen ? renderGmWorkspaceTools() : character ? <>
          <header className="workspace-character-identity">
            {mediaUrlFromVaultPath(definition?.portrait) ? <img src={mediaUrlFromVaultPath(definition?.portrait)} alt={`Retrato de ${definition?.name}`} /> : <span>{definition?.name.slice(0, 1)}</span>}
            <CharacterLevel key={character.definition.id} level={definition?.level || 1} experience={definition?.progression?.experience ?? null} canEdit={mode === "gm"} onSave={async (fields) => { await refresh(await updateCharacterDefinition(character.definition.id, fields, "Edição de nível e XP")); }} />
            <div className="workspace-character-copy"><small>PERSONAGEM</small><h2 style={{ color: characterColor(definition?.id) }}>{definition?.name}</h2>{definition?.epithet && <p>{definition.epithet}</p>}<div><b>{definition?.race || "Raça"}</b><b>{definition?.class_name || "Classe"}</b></div></div>
          </header>

          {character.access_level !== "public" && <CharacterNotes key={character.definition.id} characterId={character.definition.id} />}
          <section className="workspace-vitals"><div className="workspace-hp-heading"><span><small>VIDA</small><strong>{state?.current_hp ?? "—"}<em>/ {state?.maximum_hp ?? "—"}</em></strong></span><span className="workspace-armor-class"><small>CA</small><strong><ArmorClassValue defenses={definition?.defenses} inventory={character.inventory} /></strong></span></div><div className="workspace-hp-track"><i style={{ width: `${state?.maximum_hp ? Math.max(0, Math.min(100, Number(state.current_hp || 0) / state.maximum_hp * 100)) : 0}%` }} /></div></section>
          {ATTRIBUTES.some(([key]) => itemEffectBreakdown.some((entry) => entry.kind === "attribute_bonus" && entry.target === key && entry.active)) && <div className="workspace-attribute-effect-details">{ATTRIBUTES.filter(([key]) => itemEffectBreakdown.some((entry) => entry.kind === "attribute_bonus" && entry.target === key && entry.active)).map(([key, label]) => <button type="button" key={key} onClick={() => setEffectBreakdownOpen(key)}>Detalhar {label}</button>)}</div>}
          <div className="workspace-hp-quick-controls" aria-label="Ajuste rápido de vida"><button type="button" disabled={!canOperate || Boolean(busy)} onClick={() => setHpDraft(Math.max(0, Number(hpDraft || state?.current_hp || 0) - 1))}>−</button><input type="number" min={0} max={state?.maximum_hp || 99999} value={hpDraft} onChange={(event) => setHpDraft(event.target.value === "" ? "" : Number(event.target.value))} aria-label="PV" /><button type="button" disabled={!canOperate || Boolean(busy)} onClick={() => setHpDraft(Math.min(state?.maximum_hp || 99999, Number(hpDraft || state?.current_hp || 0) + 1))}>+</button><button type="button" disabled={!canOperate || Boolean(busy) || hpDraft === ""} onClick={() => void stateAction("set_hp", { value: Number(hpDraft) }, "PV ajustado")}>Aplicar</button></div>{mode === "gm" && (selectedId === "vezemir" || selectedId === "raziel") && definition && <MaximumHpEditor definition={definition} value={state?.maximum_hp} disabled={Boolean(busy)} onSave={(value) => definitionAction({ maximum_hp: value })} />}

          <section className="workspace-conditions workspace-status-under-vitals">{state?.conditions.length ? <div className="workspace-condition-list">{state.conditions.map((item) => <span key={item}>{item}{mode === "gm" && <button onClick={() => void stateAction("remove_condition", { condition: item }, `Removeu ${item}`)}>×</button>}</span>)}</div> : <p>STATUS - Nenhum</p>}</section>
          {mode === "player" && <CombatEncounterPanel mode={mode} tableMode={workspace.table_mode} mapId={workspace.map?.id || "default"} characters={characters} tokens={workspace.tokens} onChange={refresh} onFollowMap={id => void browseWorkspaceMap(id)} />}

          {(Object.keys(definition?.item_effects?.skill_modifiers || {}).length > 0 || (definition?.item_effects?.resistances.length || 0) > 0 || (definition?.item_effects?.immunities.length || 0) > 0 || (definition?.item_effects?.vulnerabilities.length || 0) > 0) && <section className="workspace-item-traits"><header><span>EFEITOS DE ITENS</span></header><div>{Object.entries(definition?.item_effects?.skill_modifiers || {}).map(([skill, bonus]) => <button type="button" key={`skill:${skill}`} disabled={!canOperate || Boolean(busy)} onClick={() => void roll("skill", skill)}><strong>{skill}</strong><small>{bonus >= 0 ? "+" : ""}{bonus} · jogar perícia</small></button>)}{definition?.item_effects?.resistances.map((target) => <span key={`resistance:${target}`}><strong>Resistência</strong><small>{target}</small></span>)}{definition?.item_effects?.immunities.map((target) => <span key={`immunity:${target}`}><strong>Imunidade</strong><small>{target}</small></span>)}{definition?.item_effects?.vulnerabilities.map((target) => <span key={`vulnerability:${target}`}><strong>Vulnerabilidade</strong><small>{target}</small></span>)}</div></section>}

          <section className="workspace-attributes"><header><span>ATRIBUTOS E TESTES</span></header><div>{ATTRIBUTES.map(([key, label]) => { const itemBonus = Number(definition?.attributes?.[key] || 0) - Number(definition?.base_attributes?.[key] ?? definition?.attributes?.[key] ?? 0); return <button key={key} disabled={!canOperate || Boolean(busy)} onClick={() => void roll("attribute", key)}><span>{label}</span><strong>{definition?.attributes?.[key] ?? "—"}</strong><small>{definition?.attribute_modifiers?.[key] == null ? "N/C" : `${Number(definition.attribute_modifiers[key]) >= 0 ? "+" : ""}${definition.attribute_modifiers[key]}`}{itemBonus !== 0 ? ` · item ${itemBonus > 0 ? "+" : ""}${itemBonus}` : ""}</small></button>; })}</div><button className="workspace-save-roll" disabled={!canOperate || Boolean(busy)} onClick={() => void roll("saving_throw")}>Jogar proteção{Number(definition?.defenses?.saving_throw_bonus || 0) !== 0 ? ` · item ${Number(definition?.defenses?.saving_throw_bonus) > 0 ? "+" : ""}${definition?.defenses?.saving_throw_bonus}` : ""}</button><button className="workspace-dice-tray-button" type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray"))}>{diceIcon ? <img src={diceIcon} alt="" /> : <span>⚄</span>} Bandeja de dados</button></section>

          {(standaloneResources.length > 0 || consumables.length > 0) && <section className="workspace-action-catalog workspace-resource-catalog"><header><span>RECURSOS</span><small>atual / máximo</small></header>{standaloneResources.map((resource) => <article key={resource.key}><span><strong>{resource.label}</strong></span><b>{resource.current}/{resource.maximum}</b>{canOperate && <button disabled={Boolean(busy) || resource.current <= 0} onClick={() => void stateAction("consume_resource", { resource_key: resource.key, amount: 1 }, `Usou ${resource.label}`)}>Usar</button>}</article>)}{consumables.map((item) => { const title = cleanItemDisplayName(item.item_title); const executesRules = item.effect_rules?.some((rule) => rule.trigger === "on_use"); const available = item.charges_max ? Number(item.charges_current ?? item.charges_max) : item.quantity; return <article key={item.item_path}><span><strong>{title}</strong></span><b>{item.charges_max ? `${available}/${item.charges_max} cargas` : item.quantity}</b>{canOperate && <button disabled={Boolean(busy) || available <= 0} onClick={() => void stateAction(executesRules ? "use_item" : "change_quantity", executesRules ? { item_path: item.item_path } : { item_path: item.item_path, quantity: Math.max(0, item.quantity - 1) }, `Usou ${title}`)}>Usar</button>}</article>; })}</section>}

          {attackSection}
          {spells.length > 0 && <section className="workspace-action-catalog"><header><span>MAGIAS</span><small>{spells.length}</small></header>{spells.map((ability) => { const resource = abilityResource(ability, state?.resources || []); const requiredItem = requiredItemForAbility(ability); const requirementMissing = Boolean(ability.requires_equipped_item && !requiredItem); const requiredIcon = requiredItem ? mediaUrlFromVaultPath(requiredItem.thumbnail || requiredItem.cover || iconPathForItem(requiredItem.item_title, requiredItem.item_type)) : ""; return <article key={ability.id}><span><strong className="workspace-ability-name">{requiredIcon && <img src={requiredIcon} alt="" />}{ability.name}</strong><small>{requirementMissing ? `Requer ${ability.requires_equipped_item} equipada` : ability.circle ? `${ability.circle}º círculo` : "magia"}</small></span>{resource && <b>{resource.current}/{resource.maximum}</b>}{canOperate && <button disabled={Boolean(busy) || Boolean(resource && resource.current <= 0) || Boolean(ability.blocked) || requirementMissing} onClick={() => void useAbility(ability)}>{ability.blocked ? "Bloqueado" : requirementMissing ? "Equipar item" : "Usar"}</button>}</article>; })}</section>}

          {Object.entries(groupedAbilities).map(([group, groupEntries]) => { const medal = definition?.id === "vezemir" && normalizedName(group) === "poderes" ? character?.inventory.find((item) => normalizedName(item.item_title).includes("medalhao")) : null; const medalIcon = medal ? mediaUrlFromVaultPath(medal.thumbnail || medal.cover || iconPathForItem(medal.item_title, medal.item_type)) : ""; return <section className="workspace-action-catalog" key={group}><header><span className="workspace-group-title">{medalIcon && <img src={medalIcon} alt="" />}{group.toUpperCase()}</span><small>{groupEntries.length}</small></header>{groupEntries.map((ability) => { const resource = abilityResource(ability, state?.resources || []); const requiredItem = requiredItemForAbility(ability); const requirementMissing = Boolean(ability.requires_equipped_item && !requiredItem); const requiredIcon = requiredItem ? mediaUrlFromVaultPath(requiredItem.thumbnail || requiredItem.cover || iconPathForItem(requiredItem.item_title, requiredItem.item_type)) : ""; return <article key={ability.id}><span><strong className="workspace-ability-name">{requiredIcon && <img src={requiredIcon} alt="" />}{ability.name}</strong>{requirementMissing ? <small>Requer {ability.requires_equipped_item} equipado</small> : !ability.active && <small>Passiva</small>}</span>{resource && <b>{resource.current}/{resource.maximum}</b>}{ability.active && canOperate && (ability.requires_target ? <div className="workspace-inline-actions">{abilityTargetControl(ability)}</div> : <button disabled={Boolean(busy) || Boolean(resource && resource.current <= 0) || Boolean(ability.blocked) || requirementMissing} onClick={() => void useAbility(ability)}>{ability.blocked ? "Bloqueado" : requirementMissing ? "Equipar item" : "Usar"}</button>)}</article>; })}</section>; })}

          {targetPickerAbilityId && selectedTargetAbility && <div className="workspace-attack-target-popover"><header><strong>Escolha o alvo de {selectedTargetAbility.name}</strong><button type="button" onClick={() => setTargetPickerAbilityId(null)} aria-label="Fechar lista de alvos">×</button></header>{attackTargets.length ? attackTargets.map((token) => <button type="button" key={token.id} disabled={Boolean(busy)} onClick={() => { setTargetPickerAbilityId(null); void useAbility(selectedTargetAbility, token); }}><span style={{ color: token.color }}>{token.name}</span><small>{token.token_type === "monster" ? "Monstro / NPC" : "Personagem"}</small></button>) : <p>Nenhum alvo disponível no mapa atual.</p>}</div>}

          <section className="workspace-action-catalog workspace-inventory-catalog"><header><span>INVENTÁRIO</span><small>{carriedItems.length}</small></header>{carriedItems.length ? carriedItems.map((item) => { const title = cleanItemDisplayName(item.item_title); const icon = mediaUrlFromVaultPath(item.thumbnail || item.cover || iconPathForItem(item.item_title, item.item_type)); const slots = possibleEquipmentSlots(item); const menuOpen = equipMenuItemPath === item.item_path; return <article className={item.equipped ? "equipped" : ""} key={item.item_path} role="button" tabIndex={0} onClick={() => setOpenItem(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setOpenItem(item); } }}><div className="workspace-catalog-card-heading">{icon ? <img src={icon} alt="" /> : <span className="inventory-inline-placeholder">◈</span>}<span><strong>{title}</strong></span></div><div className="workspace-catalog-card-summary"><small>{item.equipped ? `${item.equipment_slot || "Equipado"} · clique para ler` : "Guardado · clique para ler"}</small><b>Qtd. {item.quantity}</b></div>{canOperate && (item.equipped ? <button disabled={Boolean(busy)} onClick={(event) => { event.stopPropagation(); setEquipMenuItemPath(null); void stateAction("unequip_item", { item_path: item.item_path }, `Guardou ${title}`); }}>Guardar</button> : <div className="workspace-equip-control"><button disabled={Boolean(busy)} onClick={(event) => { event.stopPropagation(); setEquipMenuItemPath(menuOpen ? null : item.item_path); }}>{menuOpen ? "Fechar" : "Equipar ▾"}</button>{menuOpen && <div className="workspace-equip-menu" onClick={(event) => event.stopPropagation()}>{slots.map((slot) => <button type="button" key={slot} onClick={() => { setEquipMenuItemPath(null); void stateAction("equip_item", { item_path: item.item_path, equipment_slot: slot }, `Equipou ${title} · ${slot}`); }}>Equipar em {slot}</button>)}</div>}</div>)}</article>; }) : <p>Nenhum item não consumível registrado.</p>}</section>
          <CurrencyCounters key={character.definition.id} character={character} onChange={refresh} />


          {false && <section className="workspace-gm-tools">
            <header><span>FERRAMENTAS DO MESTRE</span><small>edição completa</small></header>
            <div className="workspace-gm-numbers"><NumericEditor label="PV atual" value={state?.current_hp} max={state?.maximum_hp || 999} onSave={(value) => stateAction("set_hp", { value }, "PV ajustado pelo Mestre")} /><NumericEditor label="PV máximo" value={state?.maximum_hp} min={1} onSave={(value) => definitionAction({ maximum_hp: value })} /><NumericEditor label="Nível" value={definition?.level} min={1} max={20} onSave={(value) => definitionAction({ level: value })} /><NumericEditor label="Classe de Armadura" value={definition?.defenses?.armor_class} onSave={(value) => definitionAction({ armor_class: value })} /><NumericEditor label="Iniciativa" value={definition?.defenses?.initiative} min={-30} max={30} onSave={(value) => definitionAction({ initiative: value })} />{ATTRIBUTES.map(([key, label]) => <NumericEditor key={key} label={label} value={definition?.attributes?.[key]} min={1} max={30} onSave={(value) => definitionAction({ attributes: { [key]: value } })} />)}</div>
            <form onSubmit={(event) => { event.preventDefault(); if (condition.trim()) { void stateAction("add_condition", { condition: condition.trim() }, `Adicionou ${condition.trim()}`); setCondition(""); } }}><input value={condition} onChange={(event) => setCondition(event.target.value)} placeholder="Nova condição" /><button disabled={!condition.trim() || Boolean(busy)}>Adicionar status</button></form>
            <label className="workspace-session-notes"><span>Notas da sessão do Mestre</span><textarea value={sessionNotes} onChange={(event) => setSessionNotes(event.target.value)} /><button disabled={Boolean(busy) || sessionNotes === (state?.session_notes || "")} onClick={() => void stateAction("set_session_notes", { value: sessionNotes }, "Atualizou notas da sessão")}>Salvar notas</button></label>
            <section className="workspace-item-studio">
              <header><span>CRIAR E EDITAR ITENS</span><button type="button" onClick={() => setItemDraft(newItemDraft())}>Novo</button></header>
              <form onSubmit={saveItem}><input value={itemDraft.name} onChange={(event) => setItemDraft({ ...itemDraft, name: event.target.value })} placeholder="Nome do item" /><input value={itemDraft.item_type} onChange={(event) => setItemDraft({ ...itemDraft, item_type: event.target.value })} placeholder="Tipo" /><textarea value={itemDraft.description} onChange={(event) => setItemDraft({ ...itemDraft, description: event.target.value })} placeholder="Descrição" /><textarea value={itemDraft.effects} onChange={(event) => setItemDraft({ ...itemDraft, effects: event.target.value })} placeholder="Um efeito por linha" /><label><input type="checkbox" checked={itemDraft.usable} onChange={(event) => setItemDraft({ ...itemDraft, usable: event.target.checked })} /> Consumível / utilizável</label><button disabled={!itemDraft.name.trim() || Boolean(busy)}>{itemDraft.id ? "Salvar item" : "Criar item"}</button></form>
              <div className="workspace-item-list">{sessionItems.map((item) => <button type="button" key={item.id} onClick={() => setItemDraft({ id: item.id, name: item.name, item_type: item.item_type, description: item.description || "", effects: item.effects.join("\n"), effect_rules: item.effect_rules || [], mechanics: item.mechanics || newItemDraft().mechanics, usable: item.usable, image_path: item.image_path || "" })}><strong>{item.name}</strong><small>{item.item_type}</small></button>)}</div>
              <form className="workspace-grant-item" onSubmit={grantItem}><select value={grantDraft.item_id} onChange={(event) => setGrantDraft({ ...grantDraft, item_id: event.target.value })}><option value="">Selecionar item</option>{archiveItems.length > 0 && <optgroup label="Arquivo de itens">{archiveItems.map((item) => <option key={`note:${item.id}`} value={`note:${item.id}`}>{item.title}</option>)}</optgroup>}{sessionItems.length > 0 && <optgroup label="Itens da sessão">{sessionItems.map((item) => <option key={`session:${item.id}`} value={`session:${item.id}`}>{item.name}</option>)}</optgroup>}</select><select value={grantDraft.character_id || selectedId} onChange={(event) => setGrantDraft({ ...grantDraft, character_id: event.target.value })}>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><input type="number" min={1} max={999} value={grantDraft.quantity} onChange={(event) => setGrantDraft({ ...grantDraft, quantity: Number(event.target.value) })} /><button disabled={!grantDraft.item_id || Boolean(busy)}>Dar ao personagem</button></form>
            </section>
            <button className="workspace-rest-button" disabled={Boolean(busy)} onClick={() => void stateAction("rest_at_inn", {}, "Descanso completo no INN")}>Descanso completo · restaurar vida, status, magias e habilidades</button>
          </section>}
        </> : <p className="workspace-loading">Carregando personagem…</p>}
      </aside>}

      {view === "maps" && <aside className="workspace-character-panel workspace-map-controls-panel">
        {renderGmWorkspaceTools("maps")}
      </aside>}

      <main className="workspace-map-panel">
        <header>
          <div>
            <small>IMAGEM DA SESSÃO</small>
            <h2>{mapTitleShown}</h2>
            {workspaceMaps.length > 0 && <label className="workspace-map-select">
              {mode === "gm" ? "Mapa em edição" : "Explorar mapa"}
              <select value={mode === "gm" ? workspace.map?.id || "" : playerMapId} onChange={(event) => mode === "gm" ? void changeWorkspaceMap(event.target.value) : void browseWorkspaceMap(event.target.value)}>
                {workspaceMaps.map((item) => <option key={item.id} value={item.id}>{item.title}{mode === "gm" && !item.visible_to_players ? " · privado" : ""}</option>)}
              </select>
            </label>}
            {mode === "gm" && view !== "memory" && workspace.map?.id && <label className="workspace-map-public-toggle">
              <input type="checkbox" checked={Boolean(workspace.map.visible_to_players)} disabled={Boolean(busy)} onChange={(event) => void changeMapVisibility(String(workspace.map?.id), event.target.checked)} />
              <span>{workspace.map.visible_to_players ? "Jogadores podem visualizar e navegar neste mapa" : "Mapa privado do Mestre"}</span>
            </label>}
          </div>
          <div className="workspace-map-zoom" aria-label="Zoom do mapa"><button type="button" disabled={mapZoom <= 1} onClick={() => changeMapZoom(mapZoom - .1)} aria-label="Diminuir zoom">−</button><output>{Math.round(mapZoom * 100)}%</output><button type="button" disabled={mapZoom >= 3} onClick={() => changeMapZoom(mapZoom + .1)} aria-label="Aumentar zoom">+</button><button type="button" disabled={mapZoom === 1} onClick={() => changeMapZoom(1)}>Ajustar</button></div>
          {mode === "gm" && view !== "memory" && <form className="workspace-map-upload" onSubmit={submitMap}>
            <input value={mapTitle} onChange={(event) => setMapTitle(event.target.value)} placeholder="Nome da imagem" />
            <label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMapFile(event.target.files?.[0] || null)} /><span>{mapFile?.name || "Escolher imagem"}</span></label>
            <label className="workspace-map-public-toggle"><input type="checkbox" checked={mapVisibleToPlayers} onChange={(event) => setMapVisibleToPlayers(event.target.checked)} /><span>Disponível para os jogadores</span></label>
            <button disabled={!mapTitle.trim() || !mapFile || Boolean(busy)}>Salvar na biblioteca</button>
          </form>}
        </header>
        <div ref={mapViewportRef} className={`workspace-map-canvas ${mode === "gm" ? "editable" : "locked"}`} onScroll={() => queueWorkspaceViewSave()} onPointerMove={previewTokenMove} onPointerUp={(event) => void finishTokenMove(event)} onPointerCancel={(event) => void finishTokenMove(event)} onPointerLeave={(event) => { if (draggingTokenRef.current && event.buttons === 0) void finishTokenMove(event); }}>
          <div ref={mapCanvasRef} className={`workspace-map-stage ${mode === "gm" && view === "maps" ? "fog-editing" : ""}`} style={{ width: `${mapZoom * 100}%`, height: `${mapZoom * 100}%` }}>
            {mapImagePath ? <img src={mediaUrlFromVaultPath(mapImagePath)} alt={mapTitleShown} draggable={false} /> : <p className="workspace-map-empty">O Mestre ainda não disponibilizou mapas para os jogadores.</p>}
            <div className="workspace-map-grid" aria-hidden="true" />
            {(mode === "gm" || fogLayers.length > 0) && <div className={`workspace-map-fog ${mode === "gm" && view === "maps" ? "editor" : ""}`} style={{ gridTemplateColumns: `repeat(${fogColumns}, 1fr)`, gridTemplateRows: `repeat(${fogRows}, 1fr)` }} onPointerDown={beginFogPaint} onPointerMove={paintFog} onPointerUp={(event) => void finishFogPaint(event)} onPointerCancel={(event) => void finishFogPaint(event)} onLostPointerCapture={() => void finishFogPaint()}>
              {fogCells.map((cell) => { const density = mistDensityByCell[cell] || 0; return <div key={cell} className={`workspace-fog-cell ${fogIsRevealed(cell) ? "revealed" : "hidden"} ${density > 0 ? "mist-active" : ""}`} style={density > 0 ? { backgroundColor: `rgba(210,220,226,${Math.min(.42, density * .34)})` } : undefined} aria-hidden="true" />; })}
            </div>}
            {Object.keys(mistDensityByCell).length > 0 && <MistParticleOverlay densityByCell={mistDensityByCell} columns={fogColumns} rows={fogRows} />}
            {workspace.tokens.map((token) => { const summary = token.character_id ? characterById.get(token.character_id) : undefined; const image = mediaUrlFromVaultPath(token.image_path || summary?.portrait); const hpCurrent = summary?.current_hp ?? token.current_hp; const hpMaximum = summary?.maximum_hp ?? token.maximum_hp; const conditions = summary?.conditions || token.conditions; return <button type="button" key={token.id} className={`workspace-map-token ${token.token_type} ${canMoveToken(token) ? "movable" : ""}`} style={{ left: `${token.longitude}%`, top: `${token.latitude}%`, borderColor: token.color, color: token.color }} onPointerDown={(event) => { if (canMoveToken(token)) { event.preventDefault(); event.stopPropagation(); event.currentTarget.setPointerCapture?.(event.pointerId); draggingTokenRef.current = { id: token.id, element: event.currentTarget, pointerId: event.pointerId, original: { latitude: token.latitude, longitude: token.longitude }, latest: { latitude: token.latitude, longitude: token.longitude } }; } }} onClick={() => void openTokenDetails(token)} title={`${token.name} · latitude ${token.latitude.toFixed(2)} · longitude ${token.longitude.toFixed(2)}${conditions.length ? ` · ${conditions.join(", ")}` : ""}`}>
              {image ? <img src={image} alt="" draggable={false} /> : <i>{token.sheet?.marker || token.name.slice(0, 1).toUpperCase()}</i>}<strong>{token.name}</strong>{hpMaximum != null && <small>{hpCurrent ?? "—"}/{hpMaximum} PV</small>}
            </button>; })}
          </div>
        </div>
        <footer><span><i className="online" /> Mesa sincronizada</span><span>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} jogadores online</span><span>{timeline.length} registros</span></footer>
      </main>

      {(view === "table" || view === "maps") && <aside className="workspace-timeline-panel">
        <header><div><small>{view === "maps" ? "REGISTRO DO MAPA" : "REGISTRO DA SESSÃO"}</small><h2>{view === "maps" ? "Ações no mapa" : "Ações e conversa"}</h2></div><span>{timeline.length}</span></header>
        <form className="workspace-log-composer" onSubmit={submitMessage}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder={view === "maps" ? "Registrar observação do mapa…" : "Escreva sua mensagem…"} /><button disabled={!message.trim() || Boolean(busy)}>Enviar</button></form>
        <div className="workspace-timeline" ref={timelineRef}>{timeline.length ? timeline.map((entry) => <article key={entry.id} className={entry.kind}><div><i>{entry.kind === "roll" ? "◈" : entry.kind === "message" ? "✦" : entry.kind === "state" ? "±" : "→"}</i><time>{formatClock(entry.timestamp)}</time></div><section><header><strong style={{ color: characterColor(entry.actorId) }}>{entry.actor}</strong><small>{entry.kind === "roll" ? "rolagem" : entry.kind === "message" ? "mensagem" : entry.kind === "state" ? "estado" : "ação"}</small></header><p>{entry.title}</p>{entry.detail && <pre>{entry.detail}</pre>}</section></article>) : <p className="workspace-empty-log">O registro da sessão começará com a primeira ação ou mensagem.</p>}</div>
      </aside>}
    </div>
    {attackResolution && <div className="workspace-item-modal-backdrop" role="presentation" onClick={() => setAttackResolution(null)}><section className="workspace-item-modal" role="dialog" aria-modal="true" aria-label="Resolução do ataque" onClick={(event) => event.stopPropagation()}><header><div><small>RESOLUÇÃO DO ATAQUE</small><h2>{attackResolution.actor_name} → {attackResolution.target_name}</h2></div><button type="button" onClick={() => setAttackResolution(null)} aria-label="Fechar resolução">×</button></header><div className="workspace-token-modal-meta"><span>{attackResolution.roll_mode === "physical" ? "Dado físico" : "Rolagem digital"}: {attackResolution.d20}</span><span>Bônus: {attackResolution.attack_bonus >= 0 ? "+" : ""}{attackResolution.attack_bonus}</span><span>Total: {attackResolution.attack_total}</span><span>CA: {attackResolution.target_ac}</span></div><div className="workspace-item-modal-meta"><strong>{attackResolution.result === "hit" ? "ACERTO" : "ERRO"}</strong><span>Dano: {attackResolution.damage_total} ({attackResolution.damage_formula})</span>{attackResolution.confirmed && <span>HP: {attackResolution.hp_before} → {attackResolution.hp_after}</span>}</div>{attackResolution.breakdown.strikes?.map((strike, index) => <p key={index}>Golpe {index + 1}: d20 {strike.d20} + {attackResolution.attack_bonus} = {strike.attack_total} · {strike.result === "hit" ? "Acerto" : "Erro"} · dano {strike.damage_total}</p>)}<p>Base {attackResolution.breakdown.attack?.base_bonus ?? 0} · equipamento {Number(attackResolution.breakdown.attack?.equipment_bonus || 0) >= 0 ? "+" : ""}{attackResolution.breakdown.attack?.equipment_bonus ?? 0} · efeitos {Number(attackResolution.breakdown.attack?.effect_bonus || 0) >= 0 ? "+" : ""}{attackResolution.breakdown.attack?.effect_bonus ?? 0}{attackResolution.breakdown.equipment?.length ? ` · ${attackResolution.breakdown.equipment.map((item) => item.item_title).join(" + ")}` : ""}</p>{attackResolution.confirmed ? <button type="button" onClick={() => setAttackResolution(null)}>Concluído</button> : <button type="button" disabled={Boolean(busy)} onClick={() => void confirmResolvedAttack()}>{busy.startsWith("confirm:") ? "Aplicando…" : "Confirmar e aplicar"}</button>}</section></div>}
    {effectBreakdownOpen && <EffectBreakdownModal title={effectBreakdownOpen === "armor" ? "Classe de Armadura" : ATTRIBUTES.find(([key]) => key === effectBreakdownOpen)?.[1] || effectBreakdownOpen} base={effectBreakdownOpen === "armor" ? definition?.defenses?.unmodified_armor_class ?? definition?.defenses?.base_armor_class : definition?.base_attributes?.[effectBreakdownOpen]} effective={effectBreakdownOpen === "armor" ? definition?.defenses?.armor_class : definition?.attributes?.[effectBreakdownOpen]} entries={openBreakdownEntries} onClose={() => setEffectBreakdownOpen(null)} onRoll={effectBreakdownOpen !== "armor" ? () => { const key = effectBreakdownOpen; setEffectBreakdownOpen(null); void roll("attribute", key); } : undefined} />}
{openToken?.token_type === "location" && <div className="workspace-token-modal-backdrop" onClick={() => setOpenTokenId(null)}><section className="workspace-token-modal" role="dialog" aria-label={`Local ${openToken.name}`} onClick={e => e.stopPropagation()}><header><h2>{openToken.name}</h2><button onClick={() => setOpenTokenId(null)}>Fechar local</button></header>{openToken.image_path && <img src={mediaUrlFromVaultPath(openToken.image_path)} alt="" width={96} />}<p>{openToken.sheet?.description}</p><small>{openToken.latitude.toFixed(1)}, {openToken.longitude.toFixed(1)}</small></section></div>}
    {openToken && openToken.token_type !== "location" && <div className="workspace-token-modal-backdrop" role="presentation" onClick={() => setOpenTokenId(null)}><section className="workspace-token-modal" role="dialog" aria-modal="true" aria-label={`Ficha de ${openToken.name}`} onClick={(event) => event.stopPropagation()}><header><div><small>{openToken.token_type === "monster" ? "MONSTRO / NPC" : "PERSONAGEM"}</small><h2 style={{ color: openToken.color }}>{openToken.name}</h2></div><button type="button" onClick={() => setOpenTokenId(null)} aria-label="Fechar ficha">×</button></header>{loadingTokenDetail ? <p>Carregando ficha…</p> : <><div className="workspace-token-modal-vitals"><strong>VIDA {openCharacterDetail?.state?.current_hp ?? openToken.current_hp ?? "—"} / {openCharacterDetail?.state?.maximum_hp ?? openToken.maximum_hp ?? "—"}</strong><span>{(openCharacterDetail?.state?.conditions || openToken.conditions).length ? (openCharacterDetail?.state?.conditions || openToken.conditions).join(" · ") : "STATUS - Nenhum"}</span></div><div className="workspace-token-modal-meta"><span>Mapa: {openToken.map_id || "default"}</span><span>Latitude: {openToken.latitude.toFixed(2)}</span><span>Longitude: {openToken.longitude.toFixed(2)}</span>{openCharacterDetail ? <><span>Classe: {openCharacterDetail.definition.class_name}</span><span>Nível: {openCharacterDetail.definition.level}</span><span>CA: <ArmorClassValue defenses={openCharacterDetail.definition.defenses} inventory={openCharacterDetail.inventory} /></span></> : <><span>Função: {openToken.sheet?.role || "Inimigo"}</span><span>Nível: {openToken.sheet?.level ?? "—"}</span><span>CA: {openToken.sheet?.armor_class ?? "—"}</span><span>Iniciativa: {openToken.sheet?.initiative ?? "—"}</span></>}</div>{openCharacterDetail ? <div className="workspace-token-modal-body"><p>{openCharacterDetail.definition.epithet || openCharacterDetail.definition.race}</p><h3>Ataques</h3>{openCharacterDetail.definition.attacks?.map((attack) => <p key={attack.id}>{attack.name} · {attack.damage || "dano não configurado"}</p>)}</div> : <div className="workspace-token-modal-body">{openToken.sheet?.description && <p>{openToken.sheet.description}</p>}{(openToken.sheet?.attacks || []).length > 0 && <><h3>Ataques</h3>{openToken.sheet?.attacks?.map((attack, index) => <p key={`${attack.name}-${index}`}>{attack.name} · {attack.damage || "dano não configurado"}{attack.bonus ? ` · ${attack.bonus}` : ""}{attack.notes ? ` · ${attack.notes}` : ""}</p>)}</>}{(openToken.sheet?.abilities || []).length > 0 && <><h3>Habilidades</h3>{openToken.sheet?.abilities?.map((ability) => <p key={ability}>{ability}</p>)}</>}{openToken.sheet?.notes && <><h3>Notas</h3><p>{openToken.sheet.notes}</p></>}</div>}</>}</section></div>}
    {openItem && <div className="workspace-item-modal-backdrop" role="presentation" onClick={() => setOpenItem(null)}><section className="workspace-item-modal" role="dialog" aria-modal="true" aria-label={`Informações de ${cleanItemDisplayName(openItem.item_title)}`} onClick={(event) => event.stopPropagation()}><header><div>{mediaUrlFromVaultPath(openItem.thumbnail || openItem.cover || iconPathForItem(openItem.item_title, openItem.item_type)) && <img src={mediaUrlFromVaultPath(openItem.thumbnail || openItem.cover || iconPathForItem(openItem.item_title, openItem.item_type))} alt="" />}<div><small>{openItem.item_type || "Item"}</small><h2>{cleanItemDisplayName(openItem.item_title)}</h2></div></div><button type="button" onClick={() => setOpenItem(null)} aria-label="Fechar informações do item">×</button></header><div className="workspace-item-modal-meta"><span>{openItem.equipped ? `Equipado${openItem.equipment_slot ? ` · ${openItem.equipment_slot}` : ""}` : "Guardado"}</span><span>Quantidade: {openItem.quantity}</span>{openItem.damage_formula && <span>Dano: {openItem.damage_formula}</span>}</div>{openItem.description && <p>{openItem.description}</p>}{(openItem.effects || []).length > 0 && <div><h3>Efeitos</h3>{openItem.effects?.map((effect) => <p key={effect}>{effect}</p>)}</div>}{(openItem.effect_rules || []).length > 0 && <div><h3>Efeitos automáticos</h3>{openItem.effect_rules?.map((rule) => <p key={rule.id}>{describeItemRule(rule)}</p>)}</div>}{openItem.notes && <div><h3>Notas</h3><p>{openItem.notes}</p></div>}</section></div>}
    <DiceTray mode={mode} triggerHidden targetTokens={workspace.tokens} />
  </section>;
}
