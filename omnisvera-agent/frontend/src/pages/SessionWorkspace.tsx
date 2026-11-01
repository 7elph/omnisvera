import SpriteStudio from '../components/SpriteStudio';
import MapLootChest from '../components/MapLootChest';
import {collectWorkspaceLoot} from '../api';
import {showMerchantMapToken} from '../commercePresentation';
import AnimatedSprite from '../components/AnimatedSprite';
import DispelEffectOptions from '../components/DispelEffectOptions';
import { invokeSkeleton } from '../skeletonInvocation';
import {gridDispelCommand} from '../dispelTargetSelection';
import {getGridDispelPreview,type DispelPreview} from '../api';
import MonsterAttackPanel from '../components/MonsterAttackPanel';
import RustContactOptions, { type RustContactChoice } from '../components/RustContactOptions';
import ParasiteControl from '../components/ParasiteControl';
import { getMonsterContactPreview, type MonsterContactPreview } from '../api';
import { FormEvent, PointerEvent as ReactPointerEvent, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { LogicalGrid, GridConfiguration } from '../components/LogicalGrid';
import TargetingOverlay from '../components/TargetingOverlay';
import { activateCard } from '../components/cardActivation';
import { selectGridTarget } from '../components/gridTargetSelection';
import { configuredGridCommand, selectionPinId } from '../components/configuredGridAction';
import type { NativeActionContract } from '../api';
import TargetConfirmation from '../components/TargetConfirmation';
import AttackDirectionChoice from '../components/AttackDirectionChoice';
import WeaponDamageChoice, {weaponDamageChoices, type PhysicalDamageType} from '../components/WeaponDamageChoice';
import { cellAt, simplePath, tokenProjection } from '../spatialGrid';
import type { Cell, MapGrid, GridPosition, SpatialCommand } from '../spatialGrid';
import { moveGridEntity, SpatialCommandError } from '../spatialCommands';
import MasterAssetPanel from "./MasterAssetPanel";
import CompendiumPanel from "../components/CompendiumPanel";
import MerchantPanel from "../components/MerchantPanel";
import MapCommerce from '../components/MapCommerce';
import PartyMemberSummary from '../components/PartyMemberSummary';
import MasterToolHeading from '../components/MasterToolHeading';
import TokenVitals from "../components/TokenVitals";
import SkeletonReward from '../components/SkeletonReward';
import VineBraceletControl from '../components/VineBraceletControl';
import SummonControls from "../components/SummonControls";
import { combatActionBlock, consumableActionBlock } from "../components/combatActionAvailability";
import BloodReinforcement from '../components/BloodReinforcement';
import CompanionAllySheet from "../components/CompanionAllySheet";
import MasterNpcLibrary from "../components/MasterNpcLibrary";
import CharacterActionReference from "../components/CharacterActionReference";
import { filterActivity } from '../actionReference';
import WorkspaceMapLibrary from "../components/WorkspaceMapLibrary";
import DornProtocolControls from "../components/DornProtocolControls";
import DornSpellControls from '../components/DornSpellControls';
import NecromancerSpellControls from '../components/NecromancerSpellControls';
import NecromancerEffects from '../components/NecromancerEffects';
import NightFormSelector, { NIGHT_FORMS } from '../components/NightFormSelector';
import NightFormControl from '../components/NightFormControl';
import PendingAttacks from "../components/PendingAttacks";
import SpellResolution from "../components/SpellResolution";
import AttackOutcome from '../components/AttackOutcome';
import SheetSection from '../components/SheetSection';
import EquipmentLoadout from '../components/EquipmentLoadout';
import InventoryItemIcon, {inventoryQuantity} from '../components/InventoryItemIcon';
import { attackOutcomeText, monsterBreathOutcomeText } from '../attackOutcome';
import SpellTargetControl from "../components/SpellTargetControl";
import TargetSelect from '../components/TargetSelect';
import SpellCard from "../components/SpellCard";
import SheetDetail from "../components/SheetDetail";
import { ActionTitle } from '../components/SessionActionArt';
import ActiveEffectIcons from '../components/ActiveEffectIcons';
import type { SessionActionCard } from '../api';
import AttackTargetLine from "../components/AttackTargetLine";
import { sharedAttackTarget } from "../components/sharedAttackTarget";
import {
  applyCharacterStateAction,
  getCombatEffects,
  CombatEffectsState,
  AttackResolution,
  confirmCharacterAttack,
  connectSessionRealtime,
  createWorkspaceToken,
  deleteSessionItem,
  getPlayableCharacter,
  getSessionWorkspace,
  getCompanionRoster,
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
  imagePreviewUrl,
  moveWorkspaceToken,
  newDiceRequestId,
  PlayableCharacter,
  PlayableCharacterSummary,
  GridRing,
  GridApproach,
  getGridRange,
  getMonsterBreathPreview,
  MonsterBreathPreview,
  getGridApproach,
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
  useCharacterTechnique,
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
  sendCombatEffectCommand,
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
import PendingLevelRolls from '../components/PendingLevelRolls';
import SpecializationSection from '../components/SpecializationSection';
import SpecializationBadge from '../components/SpecializationBadge';
import HemomancyCard from '../components/HemomancyCard';
import HemomancyWeaponIcon from '../components/HemomancyWeaponIcon';
import MapSpellEffects from '../components/MapSpellEffects';
import { hemomancySelection, hemomancyBloodCost, razielSheetAbilities } from '../components/hemomancySelection';
import { applyDornApprovedBuild } from '../api';
import DornConstructDetails from '../components/DornConstructDetails';
import CharacterNotes from "../components/CharacterNotes";
import CurrencyCounters from "../components/CurrencyCounters";
import ArmorClassValue from "../components/ArmorClassValue";
import CharacterLevel from "../components/CharacterLevel";
import CombatEncounterPanel from "../components/CombatEncounterPanel";
import LocationQuickPin from "../components/LocationQuickPin";
import { nextPinPosition } from "../components/pinPlacement";
import MistParticleOverlay from "../components/MistParticleOverlay";
import { COMPANION_ICON_CATALOG, cleanItemDisplayName, iconPathForItem } from "../companionIconCatalog";

type Props = { mode: "gm" | "player"; view?: "table" | "maps" | "npcs" | "memory" | "sheet" };
type ItemDraft = { id: number; name: string; item_type: string; description: string; effects: string; effect_rules: ItemEffectRule[]; mechanics: ItemMechanics; usable: boolean; image_path: string };
type DraggingToken = {
  grid?: MapGrid;
  position?: GridPosition;
  combatVersion?: number;
  combatActive?: boolean;
  id: string;
  element: HTMLButtonElement;
  pointerId: number;
  original: { latitude: number; longitude: number };
  latest: { latitude: number; longitude: number };
};

type TimelineEntry = {
  summary?: string;
  cards?: SessionActionCard[];
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
  if (item.item_type === 'currency') return [];
  if (item.mechanics?.family === 'ammunition') return [];
  if (item.mechanics?.equipment_slots?.length) return item.mechanics.equipment_slots;
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
  const image = mediaUrlFromVaultPath(character.portrait, 128);
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

function AbilityName({ ability, icon }: { ability: SessionAbility; icon?: string }) {
  const [open, setOpen] = useState(false);
  const uses = ability.uses;
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [open]);
  return <><button type="button" className="workspace-ability-name" onClick={() => setOpen(true)} onContextMenu={event=>{event.preventDefault();setOpen(true);}} aria-haspopup="dialog">{icon ? <img src={imagePreviewUrl(icon)} alt="" loading="lazy" decoding="async" /> : null}{ability.name}</button>
    {open && createPortal(<div className="workspace-item-modal-backdrop workspace-ability-backdrop" onClick={() => setOpen(false)}><section className="workspace-ability-detail" role="dialog" aria-modal="true" aria-label={ability.name} onClick={event => event.stopPropagation()}>
      <header><h2>{ability.name}</h2><button type="button" autoFocus aria-label="Fechar descrição" onClick={() => setOpen(false)}>×</button></header>
      {icon && <img className="workspace-detail-image" src={icon} alt={`Imagem de ${ability.name}`} />}
      {ability.description ? <p>{ability.description}</p> : <p>Sem descrição cadastrada.</p>}
      <small>
        {uses ? `Custo: ${uses.cost || 1}× ${uses.label}` : "Sem custo de recurso"}
        {ability.mechanics_status === "partial" ? " · Parcial — Mestre adjudica" : ""}
        {ability.source ? ` · Fonte: ${ability.source}` : ""}
      </small>
    </section></div>, document.body)}
  </>;
}

function abilityResource(ability: SessionAbility, resources: NonNullable<PlayableCharacter["state"]>["resources"]) {
  if (ability.id === "lamina-de-sangue" || ability.id === "marca-rubra") {
    return resources.find((item) => item.key === "reserva_de_sangue") || null;
  }
  if (ability.uses?.resource_key) {
    const wanted = ability.uses.resource_key.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    return resources.find((item) => item.key === wanted) || null;
  }
  if (ability.circle) return resources.find((item) => item.label.toLocaleLowerCase("pt-BR").includes(`${ability.circle}º círculo`)) || null;
  return null;
}

function attackDamage(characterId: string | undefined, attack: { id?: string; damage?: string | null }, equippedMeleeDamage?: string | null) {
  const equippedDamage = (attack.id === "melee" || attack.id === "ranged") ? equippedMeleeDamage : null;
  return attack.damage || equippedDamage || "Dano não configurado";
}

async function fileAsBase64(file: File, maximumMB = 5) {
  if (file.size > maximumMB * 1024 * 1024) throw new Error(`A imagem deve possuir no máximo ${maximumMB} MB.`);
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
  const [spriteStudioOpen,setSpriteStudioOpen]=useState(false);
  const [allies, setAllies] = useState<WorkspaceToken[]>([]);
  const [archivedIds, setArchivedIds] = useState<string[]>(["varkh"]);
  const [selectedAllyId, setSelectedAllyId] = useState("");
  useEffect(() => {
    const promoted = () => { setSelectedAllyId(""); setSelectedId("dorn7"); localStorage.setItem("omnisvera_selected_character", "dorn7"); };
    window.addEventListener("omnisvera-companion-promoted", promoted);
    return () => window.removeEventListener("omnisvera-companion-promoted", promoted);
  }, []);
  const [npcLibraryOpen, setNpcLibraryOpen] = useState(false);
  const [npcSheetOpen, setNpcSheetOpen] = useState(false);
  const [referenceToken, setReferenceToken] = useState<WorkspaceToken | null>(null);
  const [selectedId, setSelectedId] = useState(() => mode === "player" ? "" : localStorage.getItem("omnisvera_selected_character") || "");
  const [gmEditorChoice, setGmEditorChoice] = useState('');
  const [gmEditorId, setGmEditorId] = useState('');
  const gmEditorIdRef = useRef('');
  const [character, setCharacter] = useState<PlayableCharacter | null>(null);
  const [hemomancyChoice,setHemomancyChoice]=useState('arco');
  const [bloodBoost,setBloodBoost]=useState(0);
  const [ledger, setLedger] = useState<SessionLedgerEntry[]>([]);
  const [includeStateRecords, setIncludeStateRecords] = useState(false);
  const [actionReferenceOpen, setActionReferenceOpen] = useState(false);
  const [logActor, setLogActor] = useState('');
  const [logKind, setLogKind] = useState<'all' | 'actions'>('all');
  const [logQuery, setLogQuery] = useState('');
  const [logFiltersOpen, setLogFiltersOpen] = useState(false);
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot>({ table_mode: "digital", messages: [], presence: [], tokens: [], fog: DEFAULT_FOG });
  const [workspaceMaps, setWorkspaceMaps] = useState<WorkspaceMap[]>([]);
  const [message, setMessage] = useState("");
  const [condition, setCondition] = useState("");
  const [attackCountById, setAttackCountById] = useState<Record<string, number>>({});
  const [attackWeaponById, setAttackWeaponById] = useState<Record<string, string>>({});
  const [damageChoicePrompt, setDamageChoicePrompt] = useState<{attackId:string; targetId:string; automatic:boolean; damageType?:PhysicalDamageType; requiresTower?:boolean; towerProtectedSide?:boolean} | null>(null);
  const [techniqueModeById, setTechniqueModeById] = useState<Record<string, string>>({});
  const [sessionNotes, setSessionNotes] = useState("");
  const [mapTitle, setMapTitle] = useState("");
  const [mapFile, setMapFile] = useState<File | null>(null);
  const [mapVisibleToPlayers, setMapVisibleToPlayers] = useState(false);
  const [mapUploading,setMapUploading]=useState(false);
  const [mapUploadNotice,setMapUploadNotice]=useState('');
  const mapUploadingRef=useRef(false),mapFileInputRef=useRef<HTMLInputElement>(null);
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
  const [gmToolsOpen, setGmToolsOpen] = useState(false);
  const [assetPanelOpen, setAssetPanelOpen] = useState(false);
  const [fogLayer, setFogLayer] = useState<"exploration" | "battle">("exploration");
  const [fogTool, setFogTool] = useState<"add" | "remove">("add");
  const [fogEditing, setFogEditing] = useState(false);
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
  const [attackTargetById, setAttackTargetById] = useState<Record<string, string>>({});
  const [aimedAttackId, setAimedAttackId] = useState('');
  const [battleState, setBattleState] = useState<CombatEffectsState>({ round: 1, version: 0, effects: [] });
  const [gridDestination, setGridDestination] = useState<Cell | null>(null);
  const [targetConfirmation, setTargetConfirmation] = useState<{armId:string; targetId:string; name:string; repeat?:boolean; breath?:MonsterBreathPreview; contact?:MonsterContactPreview; rustChoice?:RustContactChoice | null;damageType?:PhysicalDamageType;towerProtectedSide?:boolean;dispel?:DispelPreview;dispelEffectId?:string} | null>(null);
  const areaAbilityRef = useRef<{armId:string; ability:SessionAbility} | null>(null);
  const [pendingGridCommand, setPendingGridCommand] = useState<{mapId:string; command:SpatialCommand} | null>(null);
  type TargetingState = {
    actionRef: string; actionLabel: string; attackerTokenId: string; mapId: string;
    ring: GridRing; selectedId: string | null; selectedIds:string[]; declaredM: string; approach: GridApproach | null; loading: boolean;
    armId: string; slot?: string;
  };
  const [targeting, setTargeting] = useState<TargetingState | null>(null);
  const targetingRef=useRef(targeting);targetingRef.current=targeting;
  const [multiOutcome,setMultiOutcome]=useState('');
  const [pcPending, setPcPending] = useState<null | { kind: "attack"; id: string; armId: string } | { kind: "ability"; ability: SessionAbility; armId: string }>(null);
  const pcPendingRef = useRef(pcPending);
  pcPendingRef.current = pcPending;
  const targetingArmRef = useRef('');
  useEffect(()=>{
    targetingArmRef.current='';pcPendingRef.current=null;areaAbilityRef.current=null;
    setPcPending(null);setTargeting(null);setTargetConfirmation(null);setDamageChoicePrompt(null);
  },[workspace.map?.id,selectedId]);
  const gridMovingRef = useRef(false);
  const gridClickSuppressRef = useRef(false);
  const [targetLine, setTargetLine] = useState<{ actorId?: string; targetId?: string }>({});
  const battleActive = Boolean(battleState.encounter?.active && battleState.encounter?.battle_mode);
  const battleCurrent = battleState.encounter?.participants?.[battleState.encounter.turn_index ?? 0];
  useEffect(() => {
    let alive = true;
    let pending = false;
    const load = async () => {
      if (!alive || pending) return;
      pending = true;
      try {
        const value = await getCombatEffects();
        if (alive) setBattleState(current => value.version >= current.version ? value : current);
      } catch { /* Keep the last confirmed effects; retry without clearing the sheet. */ }
      finally { pending = false; }
    };
    void load(); const timer = window.setInterval(load, 3000);
    window.addEventListener('omnisvera-session-changed', load);
    const aim = (event: Event) => setTargetLine((event as CustomEvent).detail || {});
    window.addEventListener('omnisvera-attack-target', aim);
    return () => { alive = false; window.clearInterval(timer); window.removeEventListener('omnisvera-session-changed', load); window.removeEventListener('omnisvera-attack-target', aim); };
  }, []);
  useEffect(() => {
    setTargetLine({}); setAttackTargetById({}); setAttackWeaponById({});
    if (battleActive && mode === 'gm' && combatPanelRef.current) combatPanelRef.current.open = true;
    if (battleActive) window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'table' }));
  }, [battleActive, battleState.encounter?.turn_sequence]);
  async function openTargeting(actionRef: string, actionLabel: string, attackerTokenId: string, rangeOverrideM?: number, tokens = workspace.tokens, map = workspace.map, extra?: { attackerCharacterId?: string; slot?: string; weaponItemPath?:string }, armId = "") {
    targetingArmRef.current=armId;
    const attacker = tokens.find(item => item.id === attackerTokenId);
    const mapId = attacker?.map_id || map?.id || "default";
setTargeting({ actionRef, actionLabel, attackerTokenId, mapId, ring: { gridded: false, declared: { mode: "?", label: "abrindo…" } }, selectedId: null, selectedIds:[], declaredM: rangeOverrideM != null ? String(rangeOverrideM) : "", approach: null, loading: true, armId, slot: extra?.slot });
    try {
      const ring = await getGridRange(actionRef, attackerTokenId, mapId, rangeOverrideM, extra);
      setTargeting(current => current && current.armId === armId ? { ...current, attackerTokenId: ring.origin?.token_id || current.attackerTokenId, ring, loading: false } : current);
      return ring;
    } catch (reason) {
      if(targetingArmRef.current===armId){setError(reason instanceof Error ? reason.message : "Não foi possível abrir o alcance.");setTargeting(null);}
      return null;
    }
  }
  useEffect(() => {
    const arm = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!detail.actionRef || (!detail.attackerTokenId && !detail.attackerCharacterId) || !detail.armId) return;
      window.dispatchEvent(new CustomEvent('omnisvera-open-workspace',{detail:'table'}));
      if (detail.pcAttack || detail.pcAbility) {
        setPcPending(detail.pcAttack
          ? { kind: "attack", id: detail.pcAttack, armId: detail.armId }
          : { kind: "ability", ability: detail.pcAbility, armId: detail.armId });
      }
      void openTargeting(detail.actionRef, detail.actionLabel || "Ação", detail.attackerTokenId || "",
        detail.rangeOverrideM, workspace.tokens, workspace.map,
        { attackerCharacterId: detail.attackerCharacterId, slot: detail.slot, weaponItemPath:detail.weaponItemPath }, detail.armId);
    };
    const clear = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (detail.armId) {
        if(targetingArmRef.current===detail.armId)targetingArmRef.current='';
        setPcPending(current => current && current.armId === detail.armId ? null : current);
        setTargeting(current => current && current.armId === detail.armId ? null : current);
        return;
      }
      setPcPending(null);
      setTargeting(null);
      targetingArmRef.current='';
    };
    const confirm = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!detail.targetId || !detail.armId) return;
      const current = pcPendingRef.current;
      if (!current || current.armId !== detail.armId) return;
      const token = attackTargetsRef.current.find(item => item.id === detail.targetId);
      if (!token) return;
      // State updaters may be replayed by React; commands must run outside them.
      pcPendingRef.current = null; setPcPending(null);
      if (current.kind === "attack") void resolveSelectedAttackRef.current(current.id, token, true, detail.damageType,detail.towerProtectedSide);
      else void useAbilityRef.current(current.ability, token, true,detail.towerProtectedSide);
    };
    window.addEventListener('omnisvera-targeting-arm', arm);
    window.addEventListener('omnisvera-targeting-clear', clear);
    window.addEventListener('omnisvera-targeting-confirm', confirm);
    return () => { window.removeEventListener('omnisvera-targeting-arm', arm); window.removeEventListener('omnisvera-targeting-clear', clear); window.removeEventListener('omnisvera-targeting-confirm', confirm); };
  }, [workspace.tokens, workspace.map]);
  function targetingRangeSpec(): { mode: string; range_m?: number; range_cells?: number } | null {
    const ring = targeting?.ring;
    if (!ring?.gridded) return null;
    if (ring.mode === "melee" || ring.mode === "touch") return { mode: ring.mode, range_cells: 1 };
    if (ring.range_m != null) return { mode: "ranged", range_m: ring.range_m };
    return null;
  }
  function confirmTargeting(targetId?: string) {
    const id = targetId || targeting?.selectedId;
    const area = areaAbilityRef.current;
    if(targetConfirmation?.dispel){
      const preview=targetConfirmation.dispel,effectId=targetConfirmation.dispelEffectId;
      if(!effectId)return;
      targetingRef.current=null;pcPendingRef.current=null;setPcPending(null);setTargetConfirmation(null);setTargeting(null);
      void castGridDispel(preview,effectId);return;
    }
    if (targeting?.actionRef==='technique:dorn7:relampago' && targeting.selectedIds.length) {
      const contract=targeting.ring.contract,mapId=targeting.mapId;
      const ids=[...targeting.selectedIds];targetingRef.current=null;pcPendingRef.current=null;setPcPending(null);
      setTargetConfirmation(null);setTargeting(null);void castGridLightning(ids,contract,mapId);return;
    }
    if (area && area.armId===targeting?.armId) {
      areaAbilityRef.current=null;setTargetConfirmation(null);setTargeting(null);
      void useAbilityRef.current(area.ability,undefined,true);return;
    }
    if (!id || !targeting || !targeting.ring.targets?.some(t => t.id === id && t.valid)) return;
    window.dispatchEvent(new CustomEvent('omnisvera-targeting-confirm', { detail: { targetId: id, range: targetingRangeSpec(), armId: targeting.armId,towerProtectedSide:targetConfirmation?.towerProtectedSide,damageType:targetConfirmation?.damageType,breath:targetConfirmation?.breath,contact:targetConfirmation?.contact,rustChoice:targetConfirmation?.rustChoice } }));
    setTargetConfirmation(null); setTargeting(null);
  }
  function chooseGridTarget(token:WorkspaceToken) {
    const current=targetingRef.current;
    if(!current?.ring.gridded)return;
    const entry=current.ring.targets?.find(t=>t.id===token.id);
    if(!entry)return;
    if(current.actionRef==='technique:dorn7:dissipar-magia'){
      if(!entry.valid||busy)return;
      const next={...current,selectedId:token.id,selectedIds:[token.id]};targetingRef.current=next;setTargeting(next);
      setBusy('dispel-preview');setError('');
      void getGridDispelPreview(token.id).then(preview=>{
        const latest=targetingRef.current;
        if(!latest||latest.armId!==current.armId||latest.selectedId!==token.id||latest.mapId!==preview.map_id)return;
        if(!preview.effects.length){setError('Este alvo não possui uma magia arcana dissipável no alcance. Nenhum uso foi gasto.');return;}
        setTargetConfirmation({armId:current.armId,targetId:token.id,name:token.name,dispel:preview,dispelEffectId:preview.effects.length===1?preview.effects[0].id:undefined});
      }).catch(reason=>setError(reason instanceof Error?reason.message:'Falha ao identificar as magias')).finally(()=>setBusy(''));
      return;
    }
    if(current.ring.native_contact){
      if(!entry.valid||busy)return;
      const binding=current.ring.native_contact;
      const next={...current,selectedId:token.id,selectedIds:[token.id]};targetingRef.current=next;setTargeting(next);
      setBusy('contact-preview');
      void getMonsterContactPreview(binding.token_id,token.id).then(preview=>{
        const latest=targetingRef.current;
        if(!latest||latest.armId!==current.armId||latest.selectedId!==token.id||latest.mapId!==preview.map_id)return;
        setTargetConfirmation({armId:current.armId,targetId:token.id,name:token.name,contact:preview,rustChoice:null});
      }).catch(reason=>setError(reason instanceof Error?reason.message:'Falha no contato')).finally(()=>setBusy(''));
      return;
    }
    if(current.ring.native_breath){
      if(!entry.valid||busy)return;
      const binding=current.ring.native_breath;
      const next={...current,selectedId:token.id,selectedIds:[token.id]};targetingRef.current=next;setTargeting(next);
      setBusy('breath-preview');
      void getMonsterBreathPreview(binding.token_id,binding.ability_name,token.id).then(preview=>{
        const latest=targetingRef.current;
        if(!latest||latest.armId!==current.armId||latest.selectedId!==token.id||latest.mapId!==preview.map_id)return;
        const updated={...latest,ring:{...latest.ring,area_cells:preview.contract.area_cells}};targetingRef.current=updated;setTargeting(updated);
        const names=preview.targets.map(t=>t.name).join(', ');
        const name=preview.contract.requires_eye_contact
          ? `${token.id===binding.token_id?'reflexo do próprio olhar':'contato visual direto'}: ${names}`
          : `toda a área, inclusive aliados: ${names}`;
        setTargetConfirmation({armId:current.armId,targetId:token.id,name,breath:preview});
      }).catch(reason=>setError(reason instanceof Error?reason.message:'Falha na área')).finally(()=>setBusy(''));
      return;
    }
    const chosenId=current.ring.contract ? selectionPinId(current.selectedIds,token.id,current.ring.targets || []) : token.id;
    const chosen=selectGridTarget(current.selectedIds,chosenId,entry.valid,current.ring.max_targets || 1);
    const next={...current,selectedId:chosenId,selectedIds:chosen.selected,approach:null};
    targetingRef.current=next;setTargeting(next);
    if(chosen.decision==='confirm')setTargetConfirmation({armId:current.armId,targetId:token.id,name:chosen.selected.map(id=>workspace.tokens.find(t=>t.id===id)?.name || id).join(', ')});
    if(chosen.decision==='repeat')setTargetConfirmation({armId:current.armId,targetId:chosenId,name:token.name,repeat:(current.ring.max_targets || 1)>1});
  }
  async function castGridDispel(preview:DispelPreview,effectId:string){
    if(mutationLock.current||busy)return;
    let command;try{command=gridDispelCommand(preview,effectId);}catch(reason){setError(reason instanceof Error?reason.message:'Magia inválida');return;}
    mutationLock.current=true;setBusy('dissipar-magia');setError('');let applied=false;
    const key=JSON.stringify(['grid-dispel',command.payload]);
    if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('grid-dispel')};
    try{await sendCombatEffectCommand({...command,request_id:techniqueRequestRef.current.id});applied=true;techniqueRequestRef.current=null;await refresh();}
    catch(reason){setError(applied?'Dissipação resolvida; atualize a tela para ver o registro. Não repita a ação.':reason instanceof Error?reason.message:'Falha ao dissipar');}
    finally{mutationLock.current=false;setBusy('');}
  }
  async function castGridLightning(ids:string[],contract:NativeActionContract|undefined,mapId:string) {
    if(mutationLock.current || busy)return;
    let command;
    try { command=configuredGridCommand(contract,mapId,ids); }
    catch(reason){setError(reason instanceof Error?reason.message:'Contrato de ação inválido');return;}
    mutationLock.current=true;setBusy('relampago');setError('');
    const {action,payload}=command;
    const key=JSON.stringify(['grid-lightning',payload]);
    if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('grid-lightning')};
    try {
      const response=await sendCombatEffectCommand({request_id:techniqueRequestRef.current.id,expected_version:battleState.version,action,payload});
      const result=response.protocol_result as unknown as {damage_roll:{individual_results:number[];total:number};results:{target:string;damage:number;hp_before:number;hp_after:number;saving_throw:{total:number;success:boolean}}[]};
      setMultiOutcome(`Relâmpago · dados ${result.damage_roll.individual_results.join(' + ')} = ${result.damage_roll.total}. ${result.results.map(r=>`${r.target}: JP ${r.saving_throw.total} (${r.saving_throw.success?'resistiu':'falhou'}), dano ${r.damage}, PV ${r.hp_before} → ${r.hp_after}`).join('; ')}`);
      techniqueRequestRef.current=null;await refresh();setBattleState(response);
    } catch(reason){setError(reason instanceof Error?reason.message:'Falha no Relâmpago');}
    finally{mutationLock.current=false;setBusy('');}
  }
  async function approachTarget() {
    if (!targeting?.ring.gridded || !targeting.selectedId) return;
    const ring = targeting.ring;
    const spec = targetingRangeSpec();
    if (!spec) return;
    setBusy("approach");
    try {
      const preview = await getGridApproach(targeting.mapId, targeting.attackerTokenId, targeting.selectedId, spec.mode, spec.range_m, spec.range_cells);
      setTargeting(current => current ? { ...current, approach: preview } : current);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível calcular a aproximação.");
    } finally { setBusy(""); }
  }
  async function confirmApproachMove() {
    const state = targeting;
    if (!state?.approach || state.approach.already_in_range) return;
    const grid = workspace.map?.grid;
    const attacker = workspace.tokens.find(item => item.id === state.attackerTokenId);
    const position = attacker?.grid_position;
    if (!grid || !attacker || !position || state.approach.path.length < 2) return;
    const active = Boolean(battleState.encounter?.active);
    await confirmGridMove(state.mapId, {
      request_id: crypto.randomUUID(), token_id: attacker.id,
      mode: active ? 'COMBAT_MOVE' : 'GM_REPOSITION',
      path: state.approach.path as Cell[],
      expected_position_version: position.version, expected_grid_version: grid.version,
      expected_combat_version: battleState.version,
    });
    await openTargeting(state.actionRef, state.actionLabel, state.attackerTokenId,
      state.declaredM.trim() ? Number(state.declaredM) : undefined);
  }
  useEffect(() => {
    setTargetLine({ actorId: selectedId, targetId: attackTargetById[aimedAttackId] });
  }, [attackTargetById, aimedAttackId, selectedId]);
  const [attackPhysicalD20ById, setAttackPhysicalD20ById] = useState<Record<string, string>>({});
  const [attackResolution, setAttackResolution] = useState<AttackResolution | null>(null);
  const [vampireOutcome, setVampireOutcome] = useState('');
  const vampireLock = useRef(false);
  const mutationLock = useRef(false);
  const abilityLock = useRef(false);
  const itemRequestRef = useRef<{ key: string; id: string } | null>(null);
  const attackRequestRef = useRef<{ key: string; id: string } | null>(null);
  const spellLockRef = useRef(false);
  const [dornSpell, setDornSpell] = useState('');
  const [necroSpell, setNecroSpell] = useState('');
  const spellRequestRef = useRef<{ key: string; id: string } | null>(null);
  const techniqueRequestRef = useRef<{ key: string; id: string } | null>(null);
  const [targetPickerAbilityId, setTargetPickerAbilityId] = useState<string | null>(null);
  useEffect(() => {
    if (!targetPickerAbilityId) return;
    const selector = document.getElementById(`ability-target-${targetPickerAbilityId}`);
    selector?.scrollIntoView({ block: 'nearest' });
    selector?.focus({ preventScroll: true });
    setTargetPickerAbilityId(null);
  }, [targetPickerAbilityId]);
  const [loadingTokenDetail, setLoadingTokenDetail] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [lootNotice,setLootNotice]=useState('');
  const [syncError, setSyncError] = useState("");
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedIdRef = useRef(selectedId);
  const attackTargetsRef = useRef<WorkspaceToken[]>([]);
  const resolveSelectedAttackRef = useRef<(attackId: string, target?: WorkspaceToken, automatic?:boolean, damageType?:PhysicalDamageType,towerProtectedSide?:boolean) => Promise<void>>(async () => {});
  const useAbilityRef = useRef<(ability: SessionAbility, target?: WorkspaceToken, automatic?:boolean,towerProtectedSide?:boolean) => Promise<void>>(async () => {});
  const gmToolsOpenRef = useRef(gmToolsOpen);
  const charactersRef = useRef<PlayableCharacterSummary[]>([]);
  const refreshingRef = useRef(false);
  const overviewRequestRef = useRef(0);
  const characterRequestRef = useRef(0);
  const currentModeRef = useRef(mode);
  currentModeRef.current = mode;
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
    const request = ++overviewRequestRef.current;
    const fogVersionAtRequest = fogMutationVersionRef.current;
    const fogSavePendingAtRequest = fogSavePendingRef.current;
    const shouldLoadAuxiliary = forceAuxiliary || !workspaceAuxLoadedRef.current;
    // A slow session log must not block the player's sheet.
    void listSessionLedger(150).then((entries) => {
      if (request !== overviewRequestRef.current || currentModeRef.current !== mode) return;
      ledgerLoadedRef.current = true;
      setLedger(entries);
    }).catch(() => { /* Preserve the log and retry with the next overview. */ });
    const [summaryItems, initialSnapshot, itemItems, mapItems, iconItems, lootItems, companionRoster] = await Promise.all([
      listPlayableCharacters(), getSessionWorkspace(mode === "player" ? playerMapIdRef.current || undefined : undefined), mode === "gm" && shouldLoadAuxiliary ? listSessionItems().catch(() => null) : Promise.resolve(null), mode === "player" || shouldLoadAuxiliary ? listWorkspaceMaps().catch(() => null) : Promise.resolve(null), mode === "gm" && shouldLoadAuxiliary ? listWorkspaceIcons().catch(() => null) : Promise.resolve(null), mode === "gm" && shouldLoadAuxiliary ? listWorkspaceLoot().catch(() => null) : Promise.resolve(null),
      mode === "gm" ? getCompanionRoster().catch(() => null) : Promise.resolve(null),
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
    if (request !== overviewRequestRef.current || currentModeRef.current !== mode) return;
    setError(current => /^Falha ao carregar (personagens|a mesa)(:|\.|$)/.test(current) ? '' : current);
    if (companionRoster) { setAllies(companionRoster.allies); setArchivedIds(companionRoster.archived_character_ids); }
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
    // A failed read is not an empty catalog: keep the confirmed data and retry.
    if (shouldLoadAuxiliary) workspaceAuxLoadedRef.current = mapItems !== null
      && (mode !== "gm" || (itemItems !== null && iconItems !== null && lootItems !== null));
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
    const request = ++characterRequestRef.current;
    if (mode === "gm" && gmToolsOpenRef.current && gmEditorIdRef.current !== selectedIdRef.current) {
      setCharacter(null);
      return;
    }
    const activeId = selectedIdRef.current;
    if (!activeId) return;
    const detail = await getPlayableCharacter(activeId);
    if (request !== characterRequestRef.current || selectedIdRef.current !== activeId || currentModeRef.current !== mode) return;
    setCharacter(detail);
    setSessionNotes(detail.state?.session_notes || "");
    setError(current => /^Falha ao carregar (ficha de jogo|o personagem)(:|\.|$)/.test(current) ? '' : current);
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
    let active = true;
    void heartbeatSessionWorkspace().catch(() => undefined);
    void loadOverview().catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar a mesa."); });
    const heartbeat = window.setInterval(() => void heartbeatSessionWorkspace().catch(() => undefined), 20_000);
    const leave = () => { if (mode === "player") void leaveSessionWorkspace().catch(() => undefined); };
    window.addEventListener("pagehide", leave);
    const refreshFromServer = () => {
      if (!active || refreshingRef.current || paintingFogRef.current || fogSavePendingRef.current || draggingTokenRef.current) return;
      refreshingRef.current = true;
      void loadOverview().then(() => { if (active) return loadCharacter(); }).then(() => { if (active) setSyncError(""); }).catch(() => { if (active) setSyncError("Conexão interrompida. Mantendo o último estado confirmado e tentando atualizar novamente."); }).finally(() => { refreshingRef.current = false; });
    };
    const refresh = window.setInterval(refreshFromServer, 15_000);
    window.addEventListener("online", refreshFromServer);
    return () => { active = false; overviewRequestRef.current++; characterRequestRef.current++; window.clearInterval(heartbeat); window.clearInterval(refresh); window.removeEventListener("online", refreshFromServer); window.removeEventListener("pagehide", leave); leave(); };
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
    let active = true;
    selectedIdRef.current = selectedId;
    setCharacter(null);
    void loadCharacter().catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar o personagem."); });
    return () => { active = false; characterRequestRef.current++; };
  }, [selectedId, mode, gmToolsOpen, gmEditorId]);

  useEffect(() => {
    let active = true;
    let disconnect: () => void = () => {};
    const refreshFromRealtime = () => {
      if (!active || refreshingRef.current || paintingFogRef.current || fogSavePendingRef.current || draggingTokenRef.current) return;
      refreshingRef.current = true;
      void loadOverview().then(() => { if (active) return loadCharacter(); }).then(() => { if (active) setSyncError(""); }).catch(() => { if (active) setSyncError("Conexão interrompida. Mantendo o último estado confirmado e tentando atualizar novamente."); }).finally(() => { refreshingRef.current = false; });
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
    if (!selectedId || busy || mutationLock.current) return;
    if (action === 'use_item') {
      const blocked = consumableActionBlock(battleState, selectedId, character?.state?.current_hp);
      if (blocked) { setError(blocked); return; }
    }
    mutationLock.current = true;
    const key = JSON.stringify([selectedId, action, payload, label]);
    if (itemRequestRef.current?.key !== key) itemRequestRef.current = { key, id: newDiceRequestId(action === 'use_item' ? 'item' : 'state') };
    setBusy(label); setError("");
    let applied = false;
    try {
      const result = await applyCharacterStateAction(selectedId, action, payload, label, itemRequestRef.current.id);
      applied = true;
      await refresh(result);
      if (action === 'equip_item' || action === 'unequip_item') {
        setOpenItem(current => current ? result.inventory.find(item => item.item_path === current.item_path) || null : null);
      }
      itemRequestRef.current = null;
    }
    catch (reason) { setError(applied ? 'Ação aplicada. A tela não sincronizou; não repita o uso. Aguarde a atualização.' : reason instanceof Error ? reason.message : "Não foi possível atualizar a ficha."); }
    finally { mutationLock.current = false; setBusy(""); }
  }

  async function restAllCharacters() {
    if (mode !== "gm" || busy || !characters.length) return;
    setBusy("rest-all"); setError("");
    try {
      const restRequest = newDiceRequestId('rest-all');
      await Promise.all(characters.filter(item => !archivedIds.includes(item.id)).map((item,index) => applyCharacterStateAction(
        item.id,
        "rest_at_inn",
        index===0 ? {reset_monsters:true} : {},
        "Descanso geral concedido pelo Mestre",
        `${restRequest}:${item.id}`,
      )));
      setBattleState(await getCombatEffects());
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
      // Players may only declare a difficulty in a private simulation (backend rule).
      const visibility = mode === "player" && targetValue != null ? "private" : "table";
      const createdRoll = await rollCharacterAction(selectedId, { request_id: newDiceRequestId("workspace"), roll_type: rollType, source_id: sourceId, target_value: targetValue, visibility });
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: createdRoll }));
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível realizar a ação."); }
    finally { setBusy(""); }
  }

  async function resolveSelectedAttack(attackId: string, selectedTarget?: WorkspaceToken, automatic = false, damageType?: PhysicalDamageType, towerProtectedSide?:boolean) {
    if (!selectedId || busy || mutationLock.current) return;
    const chosenWeapon=weaponForDamageChoice(attackId);
    const blocked = combatActionBlock(battleState, selectedId, character?.state?.current_hp, chosenWeapon?.item_path);
    if (blocked) { setError(blocked); return; }
    const target = selectedTarget || attackTargetFor(attackId);
    if (!target) {
      setError("Selecione um alvo antes de resolver o ataque.");
      return;
    }
    const rollMode = !automatic && workspace.table_mode === "physical" ? "physical" : "digital";
    const allowed = character?.definition.attacks?.find(a => a.id === attackId)?.attack_count || 1;
    const nativeRemaining=battleActive?Math.max(0,Math.min(allowed,battleState.encounter?.attack_limit??allowed)-(battleState.encounter?.attacks_used||0)):allowed;
    const remaining=nativeRemaining||(!combatActionBlock(battleState,selectedId,character?.state?.current_hp,chosenWeapon?.item_path)?1:0);
    const count = chosenWeapon?.mechanics?.special_attack==='vibranium'?Math.min(remaining,1):Math.min(remaining, attackCountById[attackId] || 1);
    if (count < 1) { setError("Nenhum ataque restante. Conclua e passe o turno."); return; }
    setTargetLine({ actorId: selectedId, targetId: target.id });
    const physicalValues = (attackPhysicalD20ById[attackId] || "").trim().split(/[ ,;]+/).map(Number);
    if (rollMode === "physical" && (physicalValues.length !== count || physicalValues.some(v => !Number.isInteger(v) || v < 1 || v > 20))) {
      setError(`Informe ${count} resultado(s) bruto(s) de d20, entre 1 e 20, separados por espaço.`);
      return;
    }
    if (weaponDamageChoices(weaponForDamageChoice(attackId)).length && !damageType) {
      setDamageChoicePrompt({attackId, targetId:target.id, automatic,towerProtectedSide}); return;
    }
    setBusy(`attack:${attackId}`); setError("");
    mutationLock.current = true;
    const boost=selectedId==='raziel'&&!['net','garrote'].includes(weaponForDamageChoice(attackId)?.mechanics?.special_attack||'')?Math.min(bloodBoost,character?.state?.resources.find(r=>r.key==='reserva_de_sangue')?.current||0):0;
    const key = `${selectedId}:${attackId}:${target.id}:${rollMode}:${count}:${attackWeaponById[attackId] || ''}:${boost}:${damageType || ''}:${String(towerProtectedSide)}:${rollMode === 'physical' ? physicalValues.join(',') : ''}`;
    if (attackRequestRef.current?.key !== key) attackRequestRef.current = { key, id: newDiceRequestId('attack') };
    try {
      const resolution = await resolveCharacterAttack(selectedId, {
        request_id: attackRequestRef.current.id,
        ...(damageType ? {damage_type:damageType} : {}),
        ...(typeof towerProtectedSide==='boolean'?{tower_protected_side:towerProtectedSide}:{}),
        attack_id: attackId,
        target_type: "token",
        target_id: target.id,
        roll_mode: rollMode,
        ...(automatic ? {grid_automatic:true} : {}),
        attack_count: count,
        ...(boost ? {blood_boost:boost}:{}),
        ...(rollMode === "physical" ? { d20s: physicalValues } : {}),
        ...(attackWeaponById[attackId] ? { weapon_item_path: attackWeaponById[attackId] } : {}),
      });
      setAttackResolution(resolution);
      attackRequestRef.current = null;
      setBattleState(current => !resolution.confirmed && current.encounter?.active && current.encounter.battle_mode
        ? { ...current, encounter: { ...current.encounter, pending_attack: resolution.resolution_id } } : current);
      if (resolution.confirmed) await refresh();
    } catch (reason) {
      if(reason instanceof Error && reason.message.includes('TOWER_SIDE_REQUIRED'))setDamageChoicePrompt({attackId,targetId:target.id,automatic,damageType,requiresTower:true});
      else setError(reason instanceof Error ? reason.message : "Não foi possível resolver o ataque.");
    } finally {
      mutationLock.current = false;
      setBusy("");
    }
  }

  async function confirmResolvedAttack() {
    if (!attackResolution || attackResolution.confirmed || busy || mutationLock.current) return;
    mutationLock.current = true;
    setBusy(`confirm:${attackResolution.resolution_id}`); setError("");
    let applied = false;
    try {
      const confirmed = await confirmCharacterAttack(attackResolution.resolution_id);
      setAttackResolution(confirmed);
      applied = true;
      setTargetLine({}); setAttackTargetById({});
      spellRequestRef.current = null;
      techniqueRequestRef.current = null;
      await refresh();
    } catch (reason) {
      setError(applied ? "Ataque confirmado. A atualização da ficha falhou; aguarde a sincronização, sem repetir o ataque." : reason instanceof Error ? reason.message : "Não foi possível confirmar o ataque.");
    } finally {
      mutationLock.current = false;
      setBusy("");
    }
  }

  useAbilityRef.current = useAbility;
  resolveSelectedAttackRef.current = resolveSelectedAttack;
  async function useAbility(ability: SessionAbility, target?: WorkspaceToken, automatic = false,towerProtectedSide?:boolean) {
    if (abilityLock.current || mutationLock.current || busy) return;
    abilityLock.current = true;
    try { await performAbility(ability, target, automatic,towerProtectedSide); }
    finally { abilityLock.current = false; }
  }

  async function performAbility(ability: SessionAbility, target?: WorkspaceToken, automatic = false,towerProtectedSide?:boolean) {
    const actionRollMode = automatic ? 'digital' : defaultAttackRollMode;
    const direction=typeof towerProtectedSide==='boolean'?{tower_protected_side:towerProtectedSide}:{};
    const useDirectedTechnique:typeof useCharacterTechnique=(profile,id,payload)=>useCharacterTechnique(profile,id,{...payload,...direction});
    async function showResolution(result: AttackResolution) {
      if (automatic && !result.confirmed) {
        try { setAttackResolution(await confirmCharacterAttack(result.resolution_id)); }
        catch (reason) { setAttackResolution(result); throw reason; }
      } else setAttackResolution(result);
    }
    if (character?.state?.animal_form && ability.id!=='forma-da-noite') { setError('Desative a forma animal para usar poderes humanoides.');return; }
    const blockedAction = ability.id === 'dorn-reparo'
      ? consumableActionBlock(battleState, selectedId, character?.state?.current_hp)
      : combatActionBlock(battleState, selectedId, character?.state?.current_hp);
    const endingCloning = ability.id==='clonagem' && (battleState.effects || []).some(e=>e.necro_spell==='clonagem');
    if (blockedAction && ability.active && !endingCloning && !['forma-da-noite','levantar-esqueleto','levantar-um-esqueleto','hemomancia-escudo'].includes(ability.id)) { setError(blockedAction); return; }
    if (ability.id.startsWith('hemomancia-')) {
      if (!selectedId || busy) return;
      const attacks = ability.requires_target;
      if (attacks && !target) {
        armPcAction({actionRef:`technique:${selectedId}:${ability.id}`,actionLabel:ability.name,pcAbility:ability});return;
      }
      const payload = {definition_revision:character?.definition.hemomancy?.revision,
        ...(attacks ? {target_type:'token' as const,target_id:target!.id,roll_mode:actionRollMode,
          ...(actionRollMode==='physical'?{d20:Number(attackPhysicalD20ById[ability.id])}:{})} : {})};
      const key=JSON.stringify([selectedId,ability.id,payload]);
      if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('hemomancy')};
      setBusy(`ability:${ability.id}`);setError('');
      try {
        const result=await useDirectedTechnique(selectedId,ability.id,{...payload,request_id:techniqueRequestRef.current.id});
        if(attacks)await showResolution(result as AttackResolution);
        await refresh();techniqueRequestRef.current=null;
      } catch(reason){setError(reason instanceof Error?reason.message:'Falha na Hemomancia');}
      finally{setBusy('');}
      return;
    }
    if (['arma-de-sangue', 'garras-predatorias', 'investida-predatoria', 'sangue-defensivo'].includes(ability.id)) {
      if (ability.blocked || !selectedId) { setError('Poder indisponível nesta ficha'); return; }
      const attacks = ability.id !== 'sangue-defensivo';
      if (attacks && !target) { setTargetPickerAbilityId(ability.id); return; }
      const blood = abilityResource(ability, character?.state?.resources || []);
      if (!blood || blood.current < (ability.uses?.cost || 1)) { setError('Reserva de Sangue insuficiente'); return; }
      const die = Number(attackPhysicalD20ById[ability.id]);
      if (attacks && actionRollMode === 'physical' && (!Number.isInteger(die) || die < 1 || die > 20)) {
        setError('Informe um d20 físico inteiro entre 1 e 20'); return;
      }
      const payload = attacks ? { target_type: 'token' as const, target_id: target!.id, roll_mode: actionRollMode,
        ...(actionRollMode === 'physical' ? { d20: die } : {}) } : {};
      const key = JSON.stringify([selectedId, ability.id, payload]);
      if (techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('blood-power') };
      setBusy(`ability:${ability.id}`); setError('');
      let accepted = false;
      try {
        const result = await useDirectedTechnique(selectedId, ability.id, { ...payload, request_id: techniqueRequestRef.current.id });
        accepted = true;
        if (attacks) await showResolution(result as AttackResolution);
        await refresh();
        techniqueRequestRef.current = null;
      } catch (reason) { setError(accepted ? 'Poder aceito. Aguarde a sincronização ou retome a prévia; não crie outra ação.' : reason instanceof Error ? reason.message : 'Falha no poder de sangue'); }
      finally { setBusy(''); }
      return;
    }
    if (ability.id === 'mordida' || ability.id === 'regeneracao-vampirica') {
      const blocked = combatActionBlock(battleState, selectedId);
      if (blocked) { setError(blocked); return; }
      if (ability.id === 'mordida' && !target) { setTargetPickerAbilityId(ability.id); return; }
      if (vampireLock.current || busy || !selectedId) return;
      vampireLock.current = true; setBusy(`ability:${ability.id}`); setError(''); setVampireOutcome('');
      const key = `${selectedId}:${ability.id}:${target?.id || ''}:${defaultAttackRollMode}:${attackPhysicalD20ById.mordida || ''}`;
      if (techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('vampire') };
      try {
        const result = await useDirectedTechnique(selectedId, ability.id, { request_id: techniqueRequestRef.current.id,
          ...(target ? { target_type: 'token', target_id: target.id, roll_mode: actionRollMode,
            ...(actionRollMode === 'physical' ? { d20: Number(attackPhysicalD20ById.mordida) } : {}) } : {}) });
        if (ability.id === 'mordida') { await showResolution(result as AttackResolution); if(automatic)await refresh(); }
        else {
          const healed = result as { hp_before: number; hp_after: number; heal_roll: number; blood_remaining: number };
          setVampireOutcome(`Regeneração: 1d4 = ${healed.heal_roll} · PV ${healed.hp_before} → ${healed.hp_after} · Sangue restante: ${healed.blood_remaining}`);
          await refresh();
        }
        techniqueRequestRef.current = null;
      } catch (reason) { setError(reason instanceof Error ? reason.message : 'Falha na habilidade vampírica'); }
      finally { vampireLock.current = false; setBusy(''); }
      return;
    }
    if (ability.id === 'animar-mortos') {
      const blocked = combatActionBlock(battleState, selectedId);
      if (blocked) { setError(blocked); return; }
    }
    if (ability.id === 'dorn-reparo') {
      if (!selectedId || busy || mode !== 'gm') return;
      setBusy('ability:dorn-reparo'); setError('');
      const key = `${selectedId}:dorn-reparo`;
      if (techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('repair') };
      try {
        await useDirectedTechnique(selectedId, ability.id, { request_id: techniqueRequestRef.current.id });
        techniqueRequestRef.current = null;
        await refresh();
      } catch (reason) { setError(reason instanceof Error ? reason.message : 'Falha no reparo'); }
      finally { setBusy(''); }
      return;
    }
    if (selectedId==='vezemir' && ['frenesi','provocacao'].includes(ability.id)) {
      if (busy) return;
      const key=`${selectedId}:${ability.id}`;
      if(techniqueRequestRef.current?.key!==key) techniqueRequestRef.current={key,id:newDiceRequestId('fighter-skill')};
      setBusy(`ability:${ability.id}`);setError('');
      try { await useDirectedTechnique(selectedId,ability.id,{request_id:techniqueRequestRef.current.id});techniqueRequestRef.current=null;await refresh(); }
      catch(reason){setError(reason instanceof Error?reason.message:'Falha na habilidade');}
      finally{setBusy('');}
      return;
    }
    if (selectedId === 'dorn7' && mode === 'gm' && ['levitacao', 'escuridao', 'relampago','reflexos','teia','forca-arcana','dissipar-magia'].includes(ability.id)) {
      if (ability.id==='relampago' && workspace.map?.grid) {
        armPcAction({actionRef:'technique:dorn7:relampago',actionLabel:'Relâmpago',slot:'ranged',pcAbility:ability});return;
      }
      if (['reflexos','teia','forca-arcana','dissipar-magia'].includes(ability.id)) {
        if(ability.id!=='reflexos' && !target){
          armPcAction({actionRef:`technique:dorn7:${ability.id}`,actionLabel:ability.name,slot:ability.id==='forca-arcana'?'touch':'ranged',pcAbility:ability});return;
        }
        const effects=ability.id==='dissipar-magia' && target ? battleState.effects.filter(e=>e.magic_type==='arcane' && e.spell_circle && e.caster_level && !e.environmental && (e.target_type==='token'?e.target_id===target.id:e.target_id===target.character_id)) : [];
        if(ability.id==='dissipar-magia' && effects.length!==1){
          if(!effects.length)setError('Este alvo não possui uma magia arcana dissipável cadastrada. Nenhum uso foi gasto.');
          else setDornSpell(ability.id); // Choose which magic when the same token has several effects.
          return;
        }
        const payload={spell_id:ability.id,...(ability.id==='dissipar-magia'?{effect_id:effects[0].id}:target?{targets:[{type:'token',id:target.id}]}:{})};
        const key=JSON.stringify(['dorn7',payload]);
        if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('dorn-spell')};
        setBusy(`ability:${ability.id}`);setError('');
        try{await sendCombatEffectCommand({request_id:techniqueRequestRef.current.id,expected_version:battleState.version,action:'dorn_spell_cast',payload});techniqueRequestRef.current=null;await refresh();}
        catch(reason){setError(reason instanceof Error?reason.message:'Falha na magia de Dorn');}
        finally{setBusy('');}return;
      }
      setDornSpell(ability.id); return;
    }
    if (selectedId === 'morthak' && ['toque-sombrio','aterrorizar','clonagem','magia-da-morte'].includes(ability.id)) {
      if (ability.id === 'toque-sombrio' && !target) {
        armPcAction({actionRef:`technique:morthak:${ability.id}`,actionLabel:ability.name,slot:'touch',pcAbility:ability}); return;
      }
      const activeClone=ability.id==='clonagem' && battleState.effects.some(e=>e.necro_spell==='clonagem');
      const payload = {mode:activeClone?'end':'automatic', ...(target && ability.id==='toque-sombrio' ? {target_type:'token' as const,target_id:target.id,roll_mode:'digital' as const}:{} )};
      const key=JSON.stringify([selectedId,ability.id,payload]);
      if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('necro')};
      setBusy(`ability:${ability.id}`);setError('');
      try {
        const result=await useDirectedTechnique(selectedId,ability.id,{...payload,request_id:techniqueRequestRef.current.id});
        if(ability.id==='toque-sombrio')await showResolution(result as AttackResolution);
        techniqueRequestRef.current=null;await refresh();
      } catch(reason){setError(reason instanceof Error?reason.message:'Falha na magia');}
      finally{setBusy('');} return;
    }
    if (ability.id === 'adaga-de-osso') {
      if (!target) { setTargetPickerAbilityId(ability.id); return; }
      if(automatic) await resolveSelectedAttack('adaga-de-osso', target, true);
      else await resolveSelectedAttack('adaga-de-osso', target);
      return;
    }
    if (ability.id === 'animar-mortos' && !target) { setTargetPickerAbilityId(ability.id); return; }
    if (ability.id === "misseis-magicos" && ["morthak", "dorn7"].includes(character?.definition.id || "")) {
      if (!automatic && workspace.table_mode === "physical") { setError("Use o alvo no grid para resolver automaticamente."); return; }
      if (!target) { setTargetPickerAbilityId(ability.id); return; }
      setTargetLine({ actorId: selectedId, targetId: target.id });
      if (spellLockRef.current || busy || !selectedId) return;
      spellLockRef.current = true;
      setBusy(`ability:${ability.id}`); setError("");
      const key = `${selectedId}:${ability.id}:${target.id}`;
      if (spellRequestRef.current?.key !== key) spellRequestRef.current = { key, id: newDiceRequestId("spell") };
      try {
        await showResolution(await resolveCharacterAttack(selectedId, { ...direction,request_id: spellRequestRef.current.id,
          attack_id: ability.id, target_type: "token", target_id: target.id, roll_mode: "digital", ...(automatic?{grid_automatic:true}:{}) }));
        if(automatic){spellRequestRef.current=null;await refresh();}
        // Resource and damage are applied together by the existing confirmation endpoint.
      } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao conferir a magia."); }
      finally { spellLockRef.current = false; setBusy(""); }
      return;
    }
    const resource = abilityResource(ability, character?.state?.resources || []);
    if (ability.requires_equipped_item && !requiredItemForAbility(ability)) {
      setError(`Equipe ${ability.requires_equipped_item} para usar ${ability.name}.`);
      return;
    }
    if (ability.blocked) {
      setError(`${ability.name} ainda está bloqueado.`);
      return;
    }
    if (ability.id === "lamina-de-sangue" || ability.id === "marca-rubra" || ability.id === "mordida" || ability.id === "forca-arcana" || ability.id === "velocidade" || ability.id === "animar-mortos" || ability.id === "levantar-esqueleto" || ability.id === 'levantar-um-esqueleto') {
      if (!selectedId || busy) return;
      setBusy(`ability:${ability.id}`); setError("");
      let summonCreated = false;
      try {
        if (ability.id === "lamina-de-sangue") {
          if (!target) { setTargetPickerAbilityId(ability.id); return; }
          const parts = (techniqueModeById[ability.id] || "1:ranged").split(":");
          const physicalD20 = Number(attackPhysicalD20ById[ability.id]);
          if (actionRollMode === 'physical' && (!Number.isInteger(physicalD20) || physicalD20 < 1 || physicalD20 > 20)) throw new Error('Informe o d20 físico da Lâmina de Sangue (1–20).');
          const key = `${selectedId}:${ability.id}:${target.id}:${parts.join(':')}:${defaultAttackRollMode}:${defaultAttackRollMode === 'physical' ? physicalD20 : ''}`;
          if (techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('blood-attack') };
          const resolution = await useDirectedTechnique(selectedId, ability.id, {
            request_id: techniqueRequestRef.current.id,
            charges: Math.max(1, Number(parts[0]) || 1),
            attack: parts[1] === "melee" ? "melee" : "ranged",
            target_type: "token", target_id: target.id, roll_mode: actionRollMode,
            ...(actionRollMode === 'physical' ? { d20: physicalD20 } : {}),
          }) as AttackResolution;
          await showResolution(resolution);
          if(automatic)techniqueRequestRef.current=null;
        } else if (ability.id === "forca-arcana" || ability.id === "velocidade" || ability.id === "animar-mortos" || ability.id === "levantar-esqueleto" || ability.id === 'levantar-um-esqueleto') {
          const skeleton = ['levantar-esqueleto','levantar-um-esqueleto'].includes(ability.id);
          const key = `${selectedId}:${ability.id}:${target?.id || ''}`;
          if (!skeleton && techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('technique') };
          const techniqueResult = skeleton
            ? await invokeSkeleton({ actor: selectedId, ability: ability.id, mapId: workspace.map?.id,
                pending: techniqueRequestRef, newId: () => newDiceRequestId('skeleton'),
                invoke: payload => useDirectedTechnique(selectedId, ability.id, payload),
                confirmReplacement: () => selectedIdRef.current === selectedId && window.confirm('Seu esqueleto ainda está ativo fora deste mapa. Dispensá-lo e invocar outro aqui? A nova invocação consome um uso e a ação normal do turno.') })
            : await useDirectedTechnique(selectedId, ability.id, { request_id: techniqueRequestRef.current!.id, map_id: workspace.map?.id,
                ...(target ? { target_type: 'token', target_id: target.id } : {}) });
          if (!techniqueResult || selectedIdRef.current !== selectedId) return;
          if (!skeleton) techniqueRequestRef.current = null;
          const summoned = (techniqueResult as { token?: WorkspaceToken }).token;
          if (summoned) {
            if ((techniqueResult as {existing?:boolean}).existing) {
              setReferenceToken(summoned);setOpenTokenId(summoned.id);setLoadingTokenDetail(false);setOpenCharacterDetail(null);
              setError('');await refresh();return;
            }
            summonCreated = true;
            setWorkspace(current => ({ ...current, tokens: [
              ...current.tokens.filter(item => item.id !== summoned.id && item.id !== (techniqueResult as { replaced_token_id?: string }).replaced_token_id).map(item => item.id === summoned.sheet?.summon?.corpse_id
                ? { ...item, sheet: { ...item.sheet, reanimated_by: summoned.id } } : item),
              summoned,
            ] }));
            setLoadingTokenDetail(false);
            setOpenCharacterDetail(null);
            setOpenTokenId(summoned.id);
          }
        } else if (ability.id === "marca-rubra") {
          if (!target) { setTargetPickerAbilityId(ability.id); return; }
          const key = `${selectedId}:${ability.id}:${target.id}`;
          if (techniqueRequestRef.current?.key !== key) techniqueRequestRef.current = { key, id: newDiceRequestId('blood-mark') };
          await useDirectedTechnique(selectedId, ability.id, { request_id: techniqueRequestRef.current.id, target_type: "token", target_id: target.id });
        }
        await refresh();
        if (ability.id === 'marca-rubra') techniqueRequestRef.current = null;
      } catch (reason) { setError(summonCreated
        ? "Invocação criada. A conexão falhou ao atualizar a tela; não invoque novamente. Aguarde a sincronização para abrir a ficha no pin."
        : reason instanceof Error ? reason.message : "Falha ao usar a técnica."); }
      finally { setBusy(""); }
      return;
    }
    if (ability.id === "caixao") {
      await stateAction("rest_in_coffin", {}, `${character?.definition.name || "Personagem"} descansou no Caixão`);
      return;
    }
    if (ability.id === 'forma-da-noite') {
      if (!resource || vampireLock.current || busy) return;
      vampireLock.current = true;
      const animal = techniqueModeById[ability.id] || 'corvo';
      try { await stateAction('consume_resource', { resource_key: resource.key, amount: 1, animal }, `Forma da Noite: ${animal}`); }
      finally { vampireLock.current = false; }
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
    if (mode !== "gm" || !mapFile || !mapTitle.trim() || mapUploadingRef.current) return;
    mapUploadingRef.current=true;setMapUploading(true);setMapUploadNotice('');
    try {
      const dataBase64 = await fileAsBase64(mapFile,10);
      const saved=await uploadWorkspaceMap({ title: mapTitle.trim(), filename: mapFile.name, content_type: mapFile.type || "application/octet-stream", data_base64: dataBase64, visible_to_players: mapVisibleToPlayers });
      setWorkspaceMaps(current=>[saved,...current.filter(item=>item.id!==saved.id)]);
      setMapFile(null); setMapTitle(""); setMapVisibleToPlayers(false);
      if(mapFileInputRef.current)mapFileInputRef.current.value='';
      setMapUploadNotice(`Imagem salva: ${saved.title}. Use Abrir na lista abaixo.`);
      await refreshMapWorkspace().catch(()=>setMapUploadNotice(`Imagem salva: ${saved.title}. Use Atualizar lista; não é necessário reenviar.`));
    } catch (reason) { setMapUploadNotice(reason instanceof Error ? reason.message : "Não foi possível enviar a imagem."); }
    finally { mapUploadingRef.current=false;setMapUploading(false); }
  }

  async function refreshMapWorkspace() {
    const request=++overviewRequestRef.current, fogVersion=fogMutationVersionRef.current;
    const [snapshot,maps]=await Promise.all([getSessionWorkspace(),listWorkspaceMaps()]);
    if(request!==overviewRequestRef.current || currentModeRef.current!==mode)return;
    setWorkspaceMaps(maps);
    setWorkspace(current=>({...snapshot,fog:fogSavePendingRef.current||paintingFogRef.current||fogVersion!==fogMutationVersionRef.current ? current.fog : snapshot.fog || DEFAULT_FOG}));
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
    if (mode !== "gm" || !mapId) return;
    if(busy)throw new Error('Aguarde a ação atual terminar antes de abrir outro mapa.');
    setBusy("map-select"); setError("");
    try { await selectWorkspaceMap(mapId); await refreshMapWorkspace(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível trocar o mapa."); throw reason; }
    finally { setBusy(""); }
  }

  async function browseWorkspaceMap(mapId: string) {
    if (battleActive && mapId !== battleState.encounter?.map_id) { setError('Encerre o combate antes de sair da arena.'); return; }
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
    try { await updateWorkspaceMapVisibility(mapId, visibleToPlayers); await refreshMapWorkspace(); }
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
      image_path: monsterImage ? current.image_path : monster.image_path || "",
      marker: marker.marker,
      role: monster.category || "Inimigo",
      level,
      armor_class: monster.armor_class ?? 10,
      description: [
        identity,
        monster.habitat ? `Habitat: ${monster.habitat}` : "",
        `DV ${monster.hit_dice || "—"} · PV ${monster.hit_points || "—"} · JP ${monster.saving_throw ?? "—"} · MO ${monster.morale ?? "—"} · MV ${monster.movement || "—"} · XP ${monster.experience_points ?? "—"}`,
      ].filter(Boolean).join("\n"),
      attacks: (monster.encounter_defaults?.attacks || monster.attacks).map((attack) => [attack.name, attack.damage, attack.bonus ?? "", attack.count ? `${attack.count}× · ${attack.raw}` : attack.raw].join(" | ")).join("\n"),
      abilities: (monster.encounter_defaults?.abilities || monster.abilities).map((ability) => `${ability.name}: ${ability.description}`).join("\n"),
      notes: [monster.encounter_defaults?.label, `Encontro ${monster.encounter || "—"} · Tesouro ${monster.treasure || "—"}`].filter(Boolean).join("\n"),
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
    const reanimated = token.sheet?.reanimated_by && workspace.tokens.find(item => item.id === token.sheet?.reanimated_by);
    if (reanimated) token = reanimated;
    if (token.token_type === 'character' && token.character_id) {
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

  async function removeCharacterPin(token: WorkspaceToken) {
    if (mode !== "gm" || busy) return;
    const inBattle = Boolean(battleActive && battleState.encounter?.participants?.some((p) => (p.target_type === "token" && p.target_id === token.id) || (p.target_type === "character" && token.character_id != null && p.target_id === token.character_id)));
    if (!window.confirm(`Remover o pin "${token.name}" do mapa?${inBattle ? " ATENÇÃO: está participando do combate ativo." : ""}`)) return;
    setBusy(`remove-pin:${token.id}`); setError("");
    try {
      await removeWorkspaceToken(token.id);
      setWorkspace((current) => ({ ...current, tokens: current.tokens.filter((item) => item.id !== token.id) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível remover o pin."); }
    finally { setBusy(""); }
  }

  async function refreshLoot() {
    const resolutions = await listWorkspaceLoot();
    setLootResolutions(resolutions);
    return resolutions;
  }

  async function collectMapLoot(token:WorkspaceToken) {
    if(busy)return;
    setBusy('collect:'+token.id);setError('');
    try {
      const receipt=await collectWorkspaceLoot(token.id);
      const shares=mode==='player'?receipt.shares.filter(s=>s.character_id===selectedIdRef.current):receipt.shares;
      const text=shares.map(s=>`${s.name}: ${s.rewards.map(r=>`${r.quantity}× ${r.name}`).join(', ')||'sem itens nesta divisão'}`).join('; ');
      setLootNotice(`Espólio de ${receipt.source_name} repartido. ${text}`);
      setWorkspace(current=>({...current,tokens:current.tokens.map(t=>t.id===token.id?{...t,sheet:{...t.sheet,loot_collected:true}}:t)}));
      void loadOverview().catch(()=>{});
    } catch(cause) {setError(cause instanceof Error?cause.message:'Falha ao recolher espólio');}
    finally {setBusy('');}
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
    if (workspace.map?.grid && token.token_type !== 'location') {
      if (gridMovingRef.current || pendingGridCommand || busy) return false;
      if (!battleState.encounter?.active) return mode === 'gm';
      if(battleState.effects.some(e=>e.immobilized&&((e.target_type==='token'&&e.target_id===token.id)||(e.target_type==='character'&&e.target_id===token.character_id))))return false;
      const isCurrent = token.character_id ? battleCurrent?.target_type === 'character' && battleCurrent.target_id === token.character_id : battleCurrent?.target_type === 'token' && battleCurrent.target_id === token.id;
      return Boolean(isCurrent && battleState.encounter?.map_id === workspace.map.id && (mode === 'gm' || token.character_id === selectedId || token.sheet?.summon?.caster === selectedId));
    }
    if (battleState.encounter?.active && token.token_type !== 'location') return false;
    return mode === "gm" || (mode === "player" && token.character_id === selectedId);
  }

  async function confirmGridMove(mapId: string, command: SpatialCommand) {
    if (gridMovingRef.current) return;
    gridMovingRef.current = true;
    setBusy(`move:${command.token_id}`);
    try {
      const result = await moveGridEntity(mapId, command);
      setPendingGridCommand(null);
      setWorkspace(current => current.map?.id !== mapId ? current : {...current,tokens:current.tokens.map(token => token.id !== command.token_id || (token.grid_position?.version || 0) > result.position.version ? token : {...token,grid_position:result.position,longitude:result.longitude,latitude:result.latitude})});
      setBattleState(current => current.version > result.combat_version ? current : {...current,version:result.combat_version,encounter:current.encounter ? {...current.encounter,...(result.movement ? {movement:result.movement} : {})} : current.encounter});
      await loadOverview().catch(() => setSyncError('Movimento confirmado; aguardando atualização da mesa.'));
    } catch(reason) {
      if (!(reason instanceof SpatialCommandError)) setPendingGridCommand({mapId,command});
      else setPendingGridCommand(null);
      setError(reason instanceof Error ? reason.message : 'Não foi possível confirmar o movimento.');
    } finally {gridMovingRef.current=false;setBusy('');setGridDestination(null);}
  }

  function gridMoveCommand(token: WorkspaceToken, end: Cell, grid: MapGrid, position: GridPosition, active=Boolean(battleState.encounter?.active), combatVersion=battleState.version): SpatialCommand {
    const start: Cell=[position.cell_x,position.cell_y];
    return {request_id:crypto.randomUUID(),token_id:token.id,mode:active?'COMBAT_MOVE':'GM_REPOSITION',path:active?simplePath(start,end,grid.distance_rule):[start,end],expected_position_version:position.version,expected_grid_version:grid.version,expected_combat_version:combatVersion};
  }

  function previewTokenMove(event: ReactPointerEvent<HTMLDivElement>) {
    const dragging = draggingTokenRef.current;
    if (!dragging) return;
    const coordinates = tokenCoordinates(event);
    if (!coordinates) return;
    dragging.latest = coordinates;
    if (dragging.grid) {setGridDestination(cellAt(dragging.grid,coordinates.longitude,coordinates.latitude));return;}
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
    if (dragging.grid && dragging.position) {
      setGridDestination(null);
      if (event.type === 'pointercancel') return;
      const end=cellAt(dragging.grid,coordinates.longitude,coordinates.latitude);
      if(end[0]===dragging.position.cell_x && end[1]===dragging.position.cell_y) return;
      gridClickSuppressRef.current=true;
      setTimeout(()=>{gridClickSuppressRef.current=false;},300);
      const token=workspace.tokens.find(item=>item.id===dragging.id);
      if(token) await confirmGridMove(dragging.grid.map_id,gridMoveCommand(token,end,dragging.grid,dragging.position,dragging.combatActive,dragging.combatVersion));
      return;
    }
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
    if (!fogEditing) return;
    if (mode !== "gm" || view !== "maps" || !workspace.map?.id) return;
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
  const canOperate = character?.access_level !== "public" && (!battleActive || mode === 'gm' || (battleCurrent?.target_id === selectedId && !battleState.encounter?.action_committed));
  const [hpDraft, setHpDraft] = useState<number | "">(state?.current_hp ?? "");
  const boostEffect=battleState.effects.find(e=>'hemomancy_kind' in e&&e.hemomancy_kind==='boost') as {multiplier?:number;turns_remaining?:number}|undefined;
  const reinforcementMultiplier=Number(boostEffect?.multiplier)||1;
  async function reinforceBlood(factor:number){
    if(selectedId!=='raziel'||busy)return;
    const key=`raziel:reforco:x${factor}`;
    if(techniqueRequestRef.current?.key!==key)techniqueRequestRef.current={key,id:newDiceRequestId('blood-multiplier')};
    setBusy('reforco');setError('');
    try{await useCharacterTechnique('raziel','reforco',{request_id:techniqueRequestRef.current.id,mode:`x${factor}`});techniqueRequestRef.current=null;await refresh();}
    catch(reason){setError(reason instanceof Error?reason.message:'Falha no reforço');}finally{setBusy('');}
  }
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
  const abilities = (definition?.session_abilities || []).filter((item) => item.id !== "hemomancia" && item.id !== "grimorio-de-mago" && !item.id.startsWith('dorn_') && !(definition?.id === 'dorn7' && ['levitacao', 'escuridao'].includes(item.id)));
  const spells = abilities.filter((item) => item.kind === "spell" || item.id === 'adaga-de-osso');
  const hemomancyIds=new Set(['lamina-de-sangue','arma-de-sangue','garras-predatorias','investida-predatoria','sangue-defensivo']);
  const basicAbilities = razielSheetAbilities(definition?.id, abilities, definition?.hemomancy).filter((item) => item.id !== 'dorn-reparo' && !(definition?.id==='raziel'&&hemomancyIds.has(item.id)) && !["spell", "resource", "attack"].includes(item.kind))
    .sort((left, right) => definition?.id === "raziel"
      ? Number((right.group || "Habilidades") === "Habilidades") - Number((left.group || "Habilidades") === "Habilidades") : 0);
  const groupedAbilities = basicAbilities.reduce<Record<string, SessionAbility[]>>((groups, ability) => {
    const group = ability.group || "Habilidades";
    (groups[group] ||= []).push(ability);
    return groups;
  }, {});
  const basicAttacks = abilities.filter((item) => item.kind === "attack" && item.id !== 'adaga-de-osso');
  const equipmentAttacks = basicAttacks.filter(ability => !definition?.attacks?.some(attack => attack.id === ability.id));
  const catalogResourceKeys = new Set(
    abilities
      .filter((item) => Boolean(item.uses) && item.kind !== "resource")
      .map((item) => abilityResource(item, state?.resources || [])?.key)
      .filter((key): key is string => Boolean(key)),
  );
  const standaloneResources = (state?.resources || []).filter((resource) => !(definition?.id === 'dorn7' && ['dorn_levitacao', 'dorn_escuridao', 'dorn_guard'].includes(resource.key)) && (resource.key === "reserva_de_sangue" || (!catalogResourceKeys.has(resource.key) && !resource.label.toLocaleLowerCase("pt-BR").startsWith("magias de "))));
  const resourceItem = (item: PlayableCharacter['inventory'][number]) => isConsumable(item) || (definition?.id === 'vezemir' && item.item_title === 'Pulseira de Vinhas') || (definition?.id === 'dorn7' && item.item_title === 'Kit de Reparo');
  const consumables = character?.inventory.filter(resourceItem).filter(item => item.item_title !== 'Pulseira de Vinhas' || item.equipped) || [];
  const carriedItems = character?.inventory.filter((item) => item.item_title === 'Pulseira de Vinhas' || !resourceItem(item)) || [];
  const equippedItems = carriedItems.filter((item) => item.equipped);
  const equippedCombatItems = equippedItems.filter((item) => Boolean(item.damage_formula) || ['net','garrote'].includes(item.mechanics?.special_attack || '') || itemLooksLikeShield(item));
  const equippedWeapons = equippedCombatItems.filter((item) => (Boolean(item.damage_formula) || ['net','garrote','vibranium'].includes(item.mechanics?.special_attack || '')) && (!itemLooksLikeShield(item)||item.mechanics?.special_attack==='vibranium'));
  const meleeSlotWeapons = equippedWeapons.filter((item) => item.mechanics?.special_attack!=="vibranium" && normalizedName(item.equipment_slot || "").includes("corpo a corpo"));
  const legacyMeleeWeapons = equippedWeapons.filter((item) => item.mechanics?.special_attack!=="vibranium" && !item.equipment_slot && !itemLooksLikeRangedWeapon(item));
  const equippedMeleeWeapon = definition?.id === "vezemir"
    ? meleeSlotWeapons.find((item) => normalizedName(item.item_title).includes("grisalma")) || meleeSlotWeapons[0] || legacyMeleeWeapons.find((item) => normalizedName(item.item_title).includes("grisalma")) || legacyMeleeWeapons[0]
    : meleeSlotWeapons[0] || legacyMeleeWeapons[0];
  const equippedRangedWeapon = equippedWeapons.find((item) => normalizedName(item.equipment_slot || "").includes("distancia"))
    || equippedWeapons.find((item) => !item.equipment_slot && itemLooksLikeRangedWeapon(item));
  const rangedSlotWeapons = equippedWeapons.filter((item) => normalizedName(item.equipment_slot || "").includes("distancia"));
  const legacyRangedWeapons = equippedWeapons.filter((item) => !item.equipment_slot && itemLooksLikeRangedWeapon(item));
  const attackWeaponCandidates = (attackId: string) => {
    // Mesma exceção do backend: Adagas de Espectro Fantasma podem ser arremessadas.
    const throwingRelic = attackId === "ranged"
      ? equippedWeapons.filter((item) => !item.equipment_slot && item.item_path.replace("\\", "/") === "Items/Adagas de Espectro Fantasma.md")
      : [];
    const approvedModes = equippedWeapons.filter(item => item.mechanics?.attack_modes?.some(mode => mode === attackId));
    const ordered = (attackId === "ranged" ? [...rangedSlotWeapons, ...approvedModes, ...throwingRelic, ...legacyRangedWeapons] : [...meleeSlotWeapons, ...approvedModes, ...legacyMeleeWeapons]).filter(item=>attackId==="ranged"||item.mechanics?.special_attack!=="vibranium");
    const seen = new Set<string>(); const unique: typeof ordered = [];
    for (const item of ordered) { if (!seen.has(item.item_path)) { seen.add(item.item_path); unique.push(item); } }
    return unique;
  };
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
  const openToken = openTokenId ? workspace.tokens.find((token) => token.id === openTokenId) || (referenceToken?.id === openTokenId && (mode === 'gm' || referenceToken.sheet?.summon?.caster===selectedId) ? referenceToken : null) : null;

  const availableMapTokens = workspace.tokens.filter(token => !token.sheet?.combat_retired);
  const battleMapTokens = battleActive ? availableMapTokens.filter(token => token.sheet?.statless || token.sheet?.source?.monster_id==='morcego' || battleState.encounter?.participants?.some(p => p.target_type === 'token' ? p.target_id === token.id : token.token_type === 'character' && (p.token_id ? p.token_id === token.id : p.target_id === token.character_id))) : availableMapTokens;
  const merchantParentIds=new Set(workspace.tokens.map(token=>token.id));
  const merchantCombatIds=new Set(battleActive ? (battleState.encounter?.participants || []).filter(p=>p.target_type==='token').map(p=>p.target_id) : []);
  const renderedMapTokens=[...battleMapTokens.filter(token=>!token.sheet?.corpse),...workspace.tokens.filter(token=>token.sheet?.corpse&&!token.sheet?.reanimated_by)].filter(token=>showMerchantMapToken(token,merchantParentIds,merchantCombatIds));
  const attackTargets = battleMapTokens.filter((token) => !token.sheet?.statless && token.token_type !== "location" && (mode === "gm" || token.character_id !== selectedId));
  attackTargetsRef.current = workspace.tokens.filter(token=>token.token_type!=='location'&&!token.sheet?.statless);
  const defaultAttackRollMode: "digital" | "physical" = workspace.table_mode === "physical" ? "physical" : "digital";
  const griddedCombat = Boolean(workspace.map?.grid);
  const characterTokenId = workspace.tokens.find((token) => token.character_id === selectedId)?.id || "";
  function weaponForDamageChoice(attackId: string) {
    const attack = definition?.attacks?.find(item => item.id === attackId);
    return character?.inventory?.find(item => item.item_path === (attackWeaponById[attackId] || attack?.weapon_item_path));
  }
  const confirmingTower=Boolean(targeting?.ring.targets?.find(t=>t.id===targetConfirmation?.targetId)?.requires_tower_side_confirmation);
  const confirmingDamageChoices = weaponDamageChoices(pcPending?.kind === 'attack' ? weaponForDamageChoice(pcPending.id) : undefined);
  function armPcAction(detail: { actionRef: string; actionLabel: string; slot?: string; pcAttack?: string; pcAbility?: SessionAbility }) {
    if (!characterTokenId && !selectedId) return;
    const armId = crypto.randomUUID();
    if (detail.pcAttack) setPcPending({ kind: "attack", id: detail.pcAttack, armId });
    else if (detail.pcAbility) setPcPending({ kind: "ability", ability: detail.pcAbility, armId });
    window.dispatchEvent(new CustomEvent('omnisvera-targeting-arm', { detail: {
      actionRef: detail.actionRef, actionLabel: detail.actionLabel, attackerTokenId: characterTokenId,
      attackerCharacterId: selectedId, slot: detail.slot, armId,
      weaponItemPath:detail.pcAttack?weaponForDamageChoice(detail.pcAttack)?.item_path:undefined,
      ...(detail.pcAttack ? { pcAttack: detail.pcAttack } : { pcAbility: detail.pcAbility }),
    } }));
  }
  async function armAreaAbility(ability:SessionAbility) {
    if(ability.id==='clonagem' && battleState.effects.some(e=>e.necro_spell==='clonagem')){await useAbility(ability);return;}
    const armId=crypto.randomUUID();
    window.dispatchEvent(new CustomEvent('omnisvera-open-workspace',{detail:'table'}));
    const ring=await openTargeting(`technique:${selectedId}:${ability.id}`,ability.name,characterTokenId,undefined,workspace.tokens,workspace.map,{attackerCharacterId:selectedId},armId);
    if(!ring?.gridded)return;
    areaAbilityRef.current={armId,ability};
    setTargetConfirmation({armId,targetId:characterTokenId,name:ability.id==='magia-da-morte'?'a área indicada (inclusive aliados elegíveis; perde 90% dos PV atuais)':ability.id==='clonagem'?'si mesmo (consome um fragmento de cristal)':'os inimigos elegíveis na área indicada'});
  }
  function necroCardBlocked(ability:SessionAbility) {
    if (busy || ability.blocked) return true;
    if (ability.id==='clonagem' && (battleState.effects || []).some(e=>e.necro_spell==='clonagem')) return false;
    if (combatActionBlock(battleState,selectedId,state?.current_hp)) return true;
    if (['clonagem','magia-da-morte'].includes(ability.id)) {
      const resource=abilityResource(ability,state?.resources || []);
      if (!resource || resource.current<=0) return true;
    }
    return ability.id==='clonagem' && !character?.inventory.some(item=>item.item_title.toLocaleLowerCase()==='fragmento de cristal arcano' && item.quantity>0);
  }
  const attackTargetFor = (attackId: string) => attackTargets.find((token) => token.id === attackTargetById[attackId]);
  const attackTargetControl = (attackId: string) => {
    return <TargetSelect label={`Alvo de ${definition?.attacks?.find(attack => attack.id === attackId)?.name || attackId}`} targets={attackTargets} value={attackTargetById[attackId] || ''} disabled={Boolean(busy)} onChange={id => { setAimedAttackId(attackId); setAttackTargetById(current => ({ ...current, [attackId]: id })); }} rangeQuery={{ profileId: selectedId, attackId, slot: attackId === "melee" ? "melee" : "ranged" }} />;
  };
  const abilitySlotById: Record<string, string | undefined> = {
    "lamina-de-sangue": (techniqueModeById["lamina-de-sangue"] || "1:ranged").split(":")[1],
    "mordida": "melee", "garras-predatorias": "melee", "investida-predatoria": "melee",
    "arma-de-sangue": "melee", "toque-sombrio": "touch", "marca-rubra": "ranged", "misseis-magicos": "ranged",
  };
  const requiredItemForAbility = (ability: SessionAbility) => {
    if (!ability.requires_equipped_item) return null;
    const wanted = normalizedName(ability.requires_equipped_item);
    return character?.inventory.find((item) => item.equipped && normalizedName(item.item_title).includes(wanted)) || null;
  };
  const abilityTargetControl = (ability: SessionAbility) => {
    const resource = abilityResource(ability, state?.resources || []);
    const targets = ability.id === 'animar-mortos'
      ? workspace.tokens.filter(token => token.sheet?.corpse && token.current_hp === 0 && !token.sheet?.summon && !token.sheet?.reanimated_by)
      : attackTargets;
    const target = targets.find(token => token.id === attackTargetById[ability.id]);
    const disabled = Boolean(busy) || Boolean(ability.blocked) || Boolean(resource && resource.current <= 0) || Boolean(ability.id === 'dorn-reparo' ? consumableActionBlock(battleState, selectedId, character?.state?.current_hp) : combatActionBlock(battleState, selectedId, character?.state?.current_hp));
    if (griddedCombat) return <div className="workspace-target-actions">
      {ability.id==='lamina-de-sangue' && <>
        <label>Lâminas<select aria-label="Lâminas declaradas" value={(techniqueModeById[ability.id] || '1:ranged').split(':')[0]} onChange={event=>setTechniqueModeById(current=>({...current,[ability.id]:`${event.target.value}:${(current[ability.id] || '1:ranged').split(':')[1]}`}))}>{Array.from({length:state?.resources.find(r=>r.key==='reserva_de_sangue')?.current || 0},(_,i)=><option key={i+1} value={i+1}>{i+1} ({i+1}d4)</option>)}</select></label>
        <label>Modo<select aria-label="Modo da Lâmina de Sangue" value={(techniqueModeById[ability.id] || '1:ranged').split(':')[1]} onChange={event=>setTechniqueModeById(current=>({...current,[ability.id]:`${(current[ability.id] || '1:ranged').split(':')[0]}:${event.target.value}`}))}><option value="ranged">À distância</option><option value="melee">Corpo a corpo</option></select></label>
      </>}
      <button data-card-command disabled={disabled} onClick={() => armPcAction({ actionRef: `technique:${selectedId}:${ability.id}`, actionLabel: `${character?.definition.name || selectedId} · ${ability.name}`, slot: abilitySlotById[ability.id], pcAbility: ability })}>Usar</button>
    </div>;
    return <div className="workspace-target-actions">
      {ability.id === 'lamina-de-sangue' && <>
        <label>Lâminas<select aria-label="Lâminas declaradas" value={(techniqueModeById[ability.id] || '1:ranged').split(':')[0]} onChange={event => setTechniqueModeById(current => ({ ...current, [ability.id]: `${event.target.value}:${(current[ability.id] || '1:ranged').split(':')[1]}` }))}>{Array.from({length:state?.resources.find(r=>r.key==='reserva_de_sangue')?.current||0},(_,i)=>i+1).map(count => <option key={count} value={count}>{count} ({count}d4)</option>)}</select></label>
        <label>Modo<select aria-label="Modo da Lâmina de Sangue" value={(techniqueModeById[ability.id] || '1:ranged').split(':')[1]} onChange={event => setTechniqueModeById(current => ({ ...current, [ability.id]: `${(current[ability.id] || '1:ranged').split(':')[0]}:${event.target.value}` }))}><option value="ranged">À distância</option><option value="melee">Corpo a corpo</option></select></label>
      </>}
      <TargetSelect id={`ability-target-${ability.id}`} label={`Alvo de ${ability.name}`} targets={targets.map(token => ({ ...token, disabled: ability.id === 'animar-mortos' && !token.sheet?.reanimation_allowed, name: token.name + (ability.id === 'animar-mortos' && !token.sheet?.reanimation_allowed ? ' · aguarda autorização do Mestre' : '') }))} value={target?.id || ''} disabled={disabled} onChange={id => { setAimedAttackId(ability.id); setAttackTargetById(current => ({ ...current, [ability.id]: id })); }} rangeQuery={abilitySlotById[ability.id] ? { profileId: selectedId, attackId: ability.id, slot: abilitySlotById[ability.id] } : undefined} />
      {(['adaga-de-osso', 'mordida', 'lamina-de-sangue'].includes(ability.id) || ['arma-de-sangue', 'garras-predatorias', 'investida-predatoria'].includes(ability.id)) && defaultAttackRollMode === 'physical' && <label>d20 físico<input aria-label={`d20 físico de ${ability.name}`} type="number" min={1} max={20} value={attackPhysicalD20ById[ability.id] || ''} onChange={event => setAttackPhysicalD20ById(current => ({ ...current, [ability.id]: event.target.value }))} /></label>}
      <button data-card-command disabled={disabled || !target || (ability.id === 'animar-mortos' && !target.sheet?.reanimation_allowed)} onClick={() => { if (target && !disabled && (ability.id !== 'animar-mortos' || target.sheet?.reanimation_allowed)) void useAbility(ability, target); }}>Usar</button>
    </div>;
  };

  const attackSection = <section ref={attackCatalogRef} className="workspace-action-catalog workspace-attack-catalog">
    <header><span>ATAQUES</span><small>{(definition?.attacks?.filter(attack => attack.id !== 'adaga-de-osso').length || 0) + equipmentAttacks.length}</small></header>
    {definition?.id==='raziel'&&<BloodReinforcement multiplier={reinforcementMultiplier} turns={boostEffect?.turns_remaining||0} blood={state?.resources.find(r=>r.key==='reserva_de_sangue')?.current||0} disabled={Boolean(busy)||Boolean(state?.animal_form)} onActivate={factor=>void reinforceBlood(factor)}/>}
    {combatActionBlock(battleState, selectedId, state?.current_hp) && <p role="status">{combatActionBlock(battleState, selectedId, state?.current_hp)}</p>}
    {definition?.attacks?.filter(attack => attack.id !== 'adaga-de-osso').map((baseAttack) => {
      const attack=definition.id==='raziel'?{...baseAttack,attack_bonus:baseAttack.attack_bonus==null?baseAttack.attack_bonus:baseAttack.attack_bonus*reinforcementMultiplier}:baseAttack;
      const held=definition.id==='raziel'?battleState.effects.find(e=>'hemomancy_kind' in e&&e.hemomancy_kind==='weapon'&&e.target_id==='raziel'):undefined;
      const heldSpec=held&&'weapon' in held?definition.hemomancy?.weapons.find(w=>w.weapon===held.weapon):undefined;
      if(heldSpec&&attack.id===(heldSpec.weapon==='arco'?'ranged':'melee')){
        const ability=hemomancySelection(definition.hemomancy,heldSpec.weapon,false)!;
        return <SpellCard key={attack.id} heading={<><HemomancyWeaponIcon weapon={heldSpec.weapon}/><span>{attack.name}</span></>} summary={<><small>{heldSpec.name} · {heldSpec.damage}{reinforcementMultiplier>1?` ×${reinforcementMultiplier}`:''}</small><b>+{((attack.base_attack_bonus||0)+(attack.effect_attack_bonus||0))*reinforcementMultiplier}</b></>}>
          <button data-card-command disabled={!canOperate||Boolean(busy)||Boolean(combatActionBlock(battleState,selectedId,state?.current_hp))} onClick={()=>void useAbility(ability)}>Usar</button>
        </SpellCard>;
      }
      const fallbackWeapon = attack.id === "ranged" ? equippedRangedWeapon : attack.id === "melee" ? equippedMeleeWeapon : null;
      const weaponPath = attack.weapon_item_path;
      const candidates = (attack.id === "melee" || attack.id === "ranged") ? attackWeaponCandidates(attack.id) : [];
      const chosenPath = attackWeaponById[attack.id] || weaponPath;
      const weapon = chosenPath ? ((attack.id === 'melee' || attack.id === 'ranged') ? candidates : character?.inventory)?.find((item) => item.item_path === chosenPath) || fallbackWeapon : fallbackWeapon;
      const attackEquipment = weapon && weapon.item_path !== attack.weapon_item_path ? [{...weapon,role:"weapon" as const},...(attack.equipment||[]).filter(item=>item.role!=="weapon")] : attack.equipment?.length ? attack.equipment : weapon ? [{ ...weapon, role: "weapon" as const }] : [];
      const damage = (weapon?.mechanics?.special_attack === 'garrote' ? 'Aperto' : weapon?.mechanics?.special_attack === 'net' ? 'Constrição' : weapon?.mechanics?.special_attack === 'vibranium' ? '1d6 + FOR' : attackDamage(definition?.id, attack, weapon?.damage_formula))+(definition.id==='raziel'&&reinforcementMultiplier>1?` ×${reinforcementMultiplier}`:'');
      const attackBlock=combatActionBlock(battleState,selectedId,state?.current_hp,weapon?.item_path);
      const nativeRemaining=battleActive?Math.max(0,Math.min(attack.attack_count||1,battleState.encounter?.attack_limit??(attack.attack_count||1))-(battleState.encounter?.attacks_used||0)):attack.attack_count||1;
      const remainingAttacks=nativeRemaining||(!attackBlock?1:0);
      const weaponTitle = attackEquipment.find((item) => item.role === "weapon")?.item_title || weapon?.item_title;
      const attackArt = mediaUrlFromVaultPath(abilities.find(ability => ability.id === attack.id)?.image_path);
      return <article tabIndex={0} key={attack.id}>
        <div className="workspace-catalog-card-heading workspace-attack-card-heading">{attackEquipment.length > 0 && <span className="workspace-attack-equipment-icons">{attackEquipment.map((item) => { const icon = mediaUrlFromVaultPath(item.thumbnail || item.cover || iconPathForItem(item.item_title, item.item_type)); return icon ? <SheetDetail key={item.item_path} title={cleanItemDisplayName(item.item_title)} icon={icon} showIcon={false} description={item.item_title}><img src={imagePreviewUrl(icon)} alt={cleanItemDisplayName(item.item_title)} loading="lazy" decoding="async" /></SheetDetail> : null; })}</span>}
<SheetDetail title={attack.name} showIcon={Boolean(attackArt)} icon={attackArt || (weapon ? mediaUrlFromVaultPath(weapon.thumbnail || weapon.cover || iconPathForItem(weapon.item_title, weapon.item_type)) : undefined)} description={`${weapon?.description || weaponTitle || attack.name}\nDano: ${damage}\nAtaque: ${attack.attack_bonus ?? '—'}${attack.range ? `\nAlcance: ${attack.range}` : ''}`} /></div>
        <div className="workspace-catalog-card-summary">{attack.id === "ranged" && !weaponPath ? <small>Arma não equipada</small> : <><small>{damage}{attack.range ? ` · ${attack.range}` : ""}{weaponTitle ? ` · ${cleanItemDisplayName(weaponTitle)}` : ""}</small><b>{attack.attack_bonus == null ? "—" : `${attack.attack_bonus >= 0 ? "+" : ""}${attack.attack_bonus}`}</b></>}</div>
        {attack.id !== "ranged" && (!weaponPath || !attack.damage) && <small className="workspace-attack-pending">{attack.id === "ranged" ? "Arma não equipada" : "Ataque sem arma/dano configurado na ficha."}</small>}
        {canOperate && weaponPath && attack.damage && <div className="workspace-inline-actions">
          {griddedCombat
            ? <><button data-card-command type="button" title="Abre o alcance no grid; clique no alvo e confirme Sim ou Não." disabled={Boolean(busy) || remainingAttacks < 1 || Boolean(attackBlock)} onClick={() => armPcAction({ actionRef: `character:${selectedId}:attack:${attack.id}`, actionLabel: `${character?.definition.name || selectedId} · ${attack.name}`, pcAttack: attack.id })}>Usar</button></>
            : <>{attackTargetControl(attack.id)}</>}
          {candidates.length > 1 && <label>Arma<select aria-label={`Arma de ${attack.name}`} value={chosenPath || ""} onChange={(e) => setAttackWeaponById((current) => ({ ...current, [attack.id]: e.target.value }))}>{candidates.map((item) => <option key={item.item_path} value={item.item_path}>{cleanItemDisplayName(item.item_title)}{item.damage_formula ? ` · ${item.damage_formula}` : ""}</option>)}</select></label>}
          {(attack.attack_count || 1) > 1 && weapon?.mechanics?.special_attack!=='vibranium' && <label>Ataques nesta ação<select aria-label={`Quantidade de ataques de ${attack.name}`} value={Math.min(remainingAttacks, attackCountById[attack.id] || 1)} onChange={e => setAttackCountById(current => ({ ...current, [attack.id]: Number(e.target.value) }))}>{Array.from({ length: remainingAttacks }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}</select><small>{remainingAttacks} restante(s). Use 1 para escolher outro alvo no próximo golpe.</small></label>}
          {!griddedCombat && defaultAttackRollMode === "physical" && <input aria-label={`Resultado físico de ${attack.name}`} type="text" inputMode="text" value={attackPhysicalD20ById[attack.id] || ""} onChange={(event) => setAttackPhysicalD20ById((current) => ({ ...current, [attack.id]: event.target.value }))} placeholder={(attackCountById[attack.id] || 1) > 1 ? "d20 de cada golpe · ex.: 15 8" : "d20 físico"} />}
          {!griddedCombat && <button data-card-command type="button" title={attackBlock || "Usa o bônus e dano da ficha; calcula acerto e dano automaticamente."} disabled={Boolean(busy) || !attackTargetFor(attack.id) || remainingAttacks < 1 || Boolean(attackBlock)} onClick={() => void resolveSelectedAttack(attack.id)}>Atacar</button>}
        </div>}
      </article>;
    })}
    {equipmentAttacks.map((attack) => {
      const damage = attackDamage(definition?.id, attack);
      return <article key={attack.id}><div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{attack.name}</strong></div><div className="workspace-catalog-card-summary"><small>{damage}</small></div><small className="workspace-attack-pending" title="Resolução automática ainda não configurada; selecionar alvo não aplica dano.">Resolução manual</small></article>;
    })}
  </section>;

  const hemomancyAbility=hemomancySelection(definition?.hemomancy,hemomancyChoice,false);
  const heldBloodWeapon=battleState.effects.find(effect=>'hemomancy_kind' in effect&&effect.hemomancy_kind==='weapon');
  const heldBloodWeaponId=heldBloodWeapon&&'weapon' in heldBloodWeapon?String(heldBloodWeapon.weapon):'';
  const hemomancyCost=hemomancyBloodCost(definition?.hemomancy,hemomancyChoice,false,heldBloodWeaponId);
  const bloodAvailable=state?.resources.find(r=>r.key==='reserva_de_sangue')?.current||0;
  const hemomancyCard=<HemomancyCard blood={bloodAvailable} animal={state?.animal_form} value={hemomancyChoice}
    activeWeapon={definition?.hemomancy?.weapons.find(w=>w.weapon===heldBloodWeaponId)}
    options={(definition?.hemomancy?.weapons||[]).map(w=>({id:w.weapon,label:w.name+(w.weapon===heldBloodWeaponId?' · ativa':'')}))}
    onChange={setHemomancyChoice}>
    {hemomancyAbility&&<>
      <AbilityName ability={hemomancyAbility} icon={mediaUrlFromVaultPath(hemomancyAbility.image_path)||undefined}/>
      <button data-card-command type="button" disabled={!canOperate||Boolean(busy)||hemomancyCost==null||Boolean(hemomancyAbility.requires_target&&!workspace.map?.grid)||bloodAvailable<(hemomancyCost||0)||Boolean(hemomancyAbility.requires_target&&combatActionBlock(battleState,selectedId,state?.current_hp))} onClick={()=>void useAbility(hemomancyAbility)}>Usar</button>
    </>}
  </HemomancyCard>;

  const timeline = useMemo(() => {
    // Character state events retain the complete before/after payload for audit and
    // rollback, but every player-facing mutation also records a readable action.
    // Showing both duplicates the action and leaks implementation JSON into the
    // session narrative, so the workspace timeline only renders narrative events.
    const entries: TimelineEntry[] = ledger.filter((item) => item.event_kind !== "state" || (mode === 'gm' && includeStateRecords)).map((item) => {
      const detail = item.detail || {};
      let detailText = "";
      let summaryText: string | undefined;
      if (item.event_kind === "roll") {
        const results = Array.isArray(detail.results) ? detail.results.join(", ") : "";
        detailText = `${String(detail.formula || "")}: [${results}] = ${String(detail.total ?? "")}`;
      }
      if (item.source_type === "combat_action") {
        const text = attackOutcomeText(detail as Partial<AttackResolution>);
        summaryText = text.summary;
        detailText = text.details;
      }
      if(item.source_type==='monster_breath'){
        const text=monsterBreathOutcomeText(detail);
        summaryText=text.summary;detailText=text.details;
      }
      return {
      id: `ledger-${item.id}`,
      timestamp: item.created_at,
      actor: nameById.get(item.character_id || "") || item.actor_name || item.actor_id,
      actorId: item.character_id,
      kind: (["roll", "action", "state", "message"].includes(item.event_kind) ? item.event_kind : "event") as TimelineEntry["kind"],
      title: item.title,
      cards: item.action_cards,
      detail: detailText || undefined,
      summary: summaryText,
    }; });
    return entries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [ledger, nameById, includeStateRecords, mode]);
  const visibleTimeline = filterActivity(timeline, { actor: logActor, kind: logKind, query: logQuery });
  const logActors = [...new Map(timeline.map(entry => [entry.actorId || entry.actor, entry.actor])).entries()];

  useEffect(() => { if (timelineRef.current) timelineRef.current.scrollTop = 0; }, [timeline.length, logActor, logKind, logQuery]);

  function openNpcLibrary() {
    setNpcLibraryOpen(true); setNpcSheetOpen(false); setGmToolsOpen(false);
    window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'npcs' }));
  }
  const npcLibraryToggle = <button className="workspace-action-card workspace-npc-toggle" type="button" aria-expanded={npcLibraryOpen} onClick={openNpcLibrary}><MasterToolHeading icon="♟" title="NPCs do Mestre" description="Consultar todos os NPCs, fichas e criaturas" /></button>;
  const reservedCharacters = characters.filter(item => archivedIds.includes(item.id));
  const npcReference = mode === "gm" ? <MasterNpcLibrary
    characters={characters} reservedIds={reservedCharacters.map(item => item.id)} allies={allies} mapId={workspace.map?.id || "default"}
    onBack={() => { setNpcLibraryOpen(false); setNpcSheetOpen(false); window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'table' })); }}
    onOpenCharacter={id => { setSelectedAllyId(""); setNpcLibraryOpen(false); setNpcSheetOpen(true); setGmToolsOpen(false); selectedIdRef.current = id; setSelectedId(id); localStorage.setItem("omnisvera_selected_character", id); window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'sheet' })); }}
    onOpenToken={token => { setReferenceToken(token); void openTokenDetails(token); }}
  /> : null;

  function renderGmWorkspaceTools(section: "master" | "maps" | "npcs" = "master") {
    if (mode !== "gm" || (section === "master" && !gmToolsOpen)) return null;
    return <section className="workspace-gm-drawer">
      {section === 'master' && npcLibraryToggle}
      {section === "master" && <details className="workspace-gm-section" open={assetPanelOpen} onToggle={event => { if (event.target === event.currentTarget) setAssetPanelOpen(event.currentTarget.open); }}><summary className="workspace-action-card"><MasterToolHeading icon="▧" title="Assets IA" description="Gerar, revisar e aprovar imagens" /></summary>{assetPanelOpen && <MasterAssetPanel onApproved={() => { void listWorkspaceIcons().then(setUploadedIcons); }} />}</details>}
      {section === "maps" && <header className="workspace-gm-drawer-heading"><div><small>MAPAS</small><strong>Controles do mapa</strong></div></header>}
      {section === "maps" && <>
      <details open className="workspace-gm-section workspace-fog-section">
        <summary><span>FOG DO MAPA</span><small>pintar e revelar o mapa</small></summary>
        <section className="workspace-fog-tools">
          <fieldset disabled={Boolean(busy) || !workspace.map?.id} aria-label="Editar fog do mapa atual">
          <header><small>pinte o mapa e revele apenas o necessário aos jogadores</small><label><input type="checkbox" checked={fog[fogLayer].enabled} onChange={(event) => void toggleFog(event.target.checked)} /> Ativa</label></header>
          <div className="workspace-fog-toolbar">
<button type="button" aria-pressed={!fogEditing} onClick={()=>setFogEditing(false)}>Interagir com pins</button>
<button type="button" className={fogLayer === "exploration" ? "active" : ""} onClick={() => setFogLayer("exploration")}>Exploração</button><button type="button" className={fogLayer === "battle" ? "active" : ""} onClick={() => setFogLayer("battle")}>Batalha</button><span className="workspace-fog-divider" /><button type="button" className={fogEditing && fogTool === "add" ? "active" : ""} onClick={() => {setFogTool("add");setFogEditing(true);}}>Pintar névoa</button><button type="button" className={fogEditing && fogTool === "remove" ? "active" : ""} onClick={() => {setFogTool("remove");setFogEditing(true);}}>Apagar névoa</button><label>Densidade <input type="range" min={0.01} max={1} step={0.01} value={fogDensity} onChange={(event) => setFogDensity(Number(event.target.value))} /><output>{Math.round(fogDensity * 100)}%</output></label><label>Pincel redondo <input type="range" min={0.5} max={6} step={0.25} value={fogBrush} onChange={(event) => setFogBrush(Number(event.target.value))} /><output>{fogBrush.toLocaleString("pt-BR")} células</output></label><button type="button" onClick={() => void setAllFog(false)}>Limpar névoa</button><button type="button" onClick={() => void setAllFog(true)}>Preencher névoa</button></div>
          </fieldset>
        </section>
      </details>
      </>}
      {section === 'npcs' && <>
      <details open className="workspace-gm-section">
        <summary><span>CONTROLES DE NPCs E PINS</span><small>personagens, monstros e NPCs</small></summary>
        <section className="workspace-map-tools workspace-pin-controls">
          <section className="workspace-monster-catalog"><header><strong>BESTIÁRIO OFICIAL OD2</strong><small>{monsterCatalog ? `${filteredCatalogMonsters.length} exibidos · ${monsterCatalog.image_count} com arte · ${monsterCatalog.total} fichas` : "Carregando biblioteca…"}</small></header><input value={monsterCatalogSearch} onChange={(event) => setMonsterCatalogSearch(event.target.value)} placeholder="Buscar por nome, tipo ou habitat" /><div><select aria-label="Monstro do bestiário" value={selectedCatalogMonsterId} onChange={(event) => setSelectedCatalogMonsterId(event.target.value)}><option value="">Selecione uma ficha…</option>{filteredCatalogMonsters.map((monster) => <option key={monster.id} value={monster.id}>{monster.image_path ? "▣ " : ""}{monster.name} · DV {monster.hit_dice || "—"} · CA {monster.armor_class ?? "—"}</option>)}</select><button type="button" disabled={!selectedCatalogMonsterId} onClick={applyCatalogMonster}>Carregar no formulário</button></div>{selectedCatalogMonster && <article className="workspace-monster-catalog-preview">{selectedCatalogMonster.image_path ? <img src={mediaUrlFromVaultPath(selectedCatalogMonster.image_path)} alt={`Ilustração de ${selectedCatalogMonster.name}`} /> : <span aria-hidden="true">{markerForMonster(selectedCatalogMonster).marker}</span>}<div><strong>{selectedCatalogMonster.name}</strong><small>{selectedCatalogMonster.category || "Criatura"} · DV {selectedCatalogMonster.hit_dice || "—"} · CA {selectedCatalogMonster.armor_class ?? "—"}</small><small>{selectedCatalogMonster.image_attribution ? `Arte: ${selectedCatalogMonster.image_attribution} · ${selectedCatalogMonster.image_license}` : "Sem correspondência segura no pacote; você ainda pode escolher uma imagem."}</small></div></article>}{monsterDraft.source_monster_id && <small>Base carregada: {monsterDraft.name} · SRD OD2 · CC BY-SA 4.0. A imagem própria do Mestre sempre tem prioridade.{monsterDraft.notes.startsWith("Configuração da campanha") && " Equipamento e repertório: escolhas editáveis da campanha."}</small>}</section>
          <div><header><span>PERSONAGENS NO MAPA</span><small>arraste os avatares para posicionar</small></header><div>{characters.map((item) => { const pinned = workspace.tokens.some((token) => token.character_id === item.id); return <button type="button" key={item.id} disabled={pinned || Boolean(busy)} style={{ color: characterColor(item.id) }} onClick={() => void pinCharacter(item.id)}>{pinned ? "✓" : "+"} {item.name}</button>; })}</div><div className="workspace-pin-list">{workspace.tokens.map((token) => <div key={token.id}><span><strong style={{ color: token.color }}>{token.name}</strong><small>{token.token_type === "monster" ? "Monstro/NPC" : token.token_type === "location" ? "Local" : "Personagem"} · {token.latitude.toFixed(1)}, {token.longitude.toFixed(1)}</small></span><button type="button" onClick={() => void openTokenDetails(token)}>{token.character_id ? "Selecionar" : token.token_type === "location" ? "Detalhes" : "Ficha"}</button>{mode === "gm" && token.token_type === "character" && <button type="button" disabled={Boolean(busy)} onClick={() => void removeCharacterPin(token)}>Remover</button>}</div>)}</div><section className="workspace-monster-manager"><header><span>MONSTROS E NPCS NO MAPA</span><small>gerencie os marcadores criados</small></header>{workspace.tokens.filter((token) => token.token_type === "monster").map((token) => <div className="workspace-monster-row" key={token.id}><span><strong style={{ color: token.color }}>{token.sheet?.marker || "⚔"} {token.name}</strong><small>{token.current_hp ?? "—"}/{token.maximum_hp ?? "—"} PV · {token.visible_to_players ? "visível" : "oculto"} · Tesouro {token.sheet?.treasure || "—"}</small></span><button type="button" disabled={Boolean(busy)} onClick={() => void toggleMonsterVisibility(token)}>{token.visible_to_players ? "Ocultar" : "Revelar"}</button><button type="button" disabled={Boolean(busy)} onClick={() => void openTokenDetails(token)}>Ficha</button><button type="button" disabled={Boolean(busy)} onClick={() => editMonster(token)}>Editar</button>{token.current_hp === 0 && !token.sheet?.summon && treasureHasCarried(token.sheet?.treasure) && <button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "carried")}>Gerar espólio</button>}{token.current_hp === 0 && !token.sheet?.summon && treasureHasLair(token.sheet?.treasure) && <button type="button" disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, "lair")}>Gerar covil</button>}<button type="button" disabled={Boolean(busy)} onClick={() => void removeMonster(token)}>Remover</button></div>)}{!workspace.tokens.some((token) => token.token_type === "monster") && <p className="workspace-empty-monsters">Nenhum monstro ou NPC criado.</p>}</section></div>
          <form className="workspace-monster-form" onSubmit={createMonster}><header><span>{editingMonsterId ? "EDITAR MONSTRO / NPC" : "CRIAR E PINAR RAPIDAMENTE"}</span><small>nome, PV e CA bastam; imagem e ficha completa são opcionais</small></header><div className="workspace-monster-quick-presets">{CREATURE_MARKERS.map((preset) => <button type="button" key={preset.label} onClick={() => setMonsterDraft((current) => ({ ...current, marker: preset.marker, role: preset.role, color: preset.color }))}><span>{preset.marker}</span>{preset.label}</button>)}</div><input value={monsterDraft.name} onChange={(event) => setMonsterDraft({ ...monsterDraft, name: event.target.value })} placeholder="Nome do monstro ou NPC" /><div className="workspace-monster-hp"><label><span>PV atual</span><input type="number" min={0} max={99999} inputMode="numeric" aria-label="PV atual restante" value={monsterDraft.current_hp} onChange={(event) => setMonsterDraft({ ...monsterDraft, current_hp: event.target.value === "" ? 0 : Number(event.target.value) })} /></label><label><span>PV máximo</span><input type="number" min={1} max={99999} inputMode="numeric" aria-label="PV máximo" value={monsterDraft.maximum_hp} onChange={(event) => setMonsterDraft({ ...monsterDraft, maximum_hp: event.target.value === "" ? 1 : Number(event.target.value) })} /></label></div><div className="workspace-monster-sheet-grid"><input value={monsterDraft.role} onChange={(event) => setMonsterDraft({ ...monsterDraft, role: event.target.value })} placeholder="Tipo / função" /><select aria-label="Símbolo do marcador" value={monsterDraft.marker} onChange={(event) => setMonsterDraft({ ...monsterDraft, marker: event.target.value })}>{CREATURE_MARKERS.map((preset) => <option key={preset.marker} value={preset.marker}>{preset.marker} {preset.label}</option>)}</select><input type="number" min={0} max={99} value={monsterDraft.armor_class} onChange={(event) => setMonsterDraft({ ...monsterDraft, armor_class: Number(event.target.value) })} placeholder="CA" /><input type="number" min={-30} max={30} value={monsterDraft.initiative} onChange={(event) => setMonsterDraft({ ...monsterDraft, initiative: Number(event.target.value) })} placeholder="Iniciativa" /></div><label className="workspace-monster-visibility"><input type="checkbox" checked={monsterDraft.visible_to_players} onChange={(event) => setMonsterDraft({ ...monsterDraft, visible_to_players: event.target.checked })} /><span>{monsterDraft.visible_to_players ? "Mostrar aos jogadores ao criar" : "Preparar oculto e revelar depois"}</span></label><details className="workspace-monster-advanced"><summary>Ficha avançada opcional</summary><input type="number" min={1} max={30} value={monsterDraft.level} onChange={(event) => setMonsterDraft({ ...monsterDraft, level: Number(event.target.value) })} placeholder="Nível" /><input value={monsterDraft.conditions} onChange={(event) => setMonsterDraft({ ...monsterDraft, conditions: event.target.value })} placeholder="Status separados por vírgula" /><textarea value={monsterDraft.description} onChange={(event) => setMonsterDraft({ ...monsterDraft, description: event.target.value })} placeholder="Descrição da ficha" /><textarea value={monsterDraft.attacks} onChange={(event) => setMonsterDraft({ ...monsterDraft, attacks: event.target.value })} placeholder="Ataques: nome | dano | bônus | observações (um por linha)" /><textarea value={monsterDraft.abilities} onChange={(event) => setMonsterDraft({ ...monsterDraft, abilities: event.target.value })} placeholder="Habilidades (uma por linha)" /><textarea value={monsterDraft.notes} onChange={(event) => setMonsterDraft({ ...monsterDraft, notes: event.target.value })} placeholder="Notas do Mestre" /></details><input type="color" value={monsterDraft.color} onChange={(event) => setMonsterDraft({ ...monsterDraft, color: event.target.value })} title="Cor do marcador" /><label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMonsterImage(event.target.files?.[0] || null)} /><span>{monsterImage?.name || (monsterDraft.image_path ? "Imagem atual selecionada" : `${monsterDraft.marker} Usar símbolo agora ou escolher imagem`)}</span></label><button disabled={!monsterDraft.name.trim() || Boolean(busy)}>{editingMonsterId ? "Salvar ficha" : monsterDraft.visible_to_players ? "Criar, pinar e mostrar" : "Criar pin oculto"}</button>{editingMonsterId && <button type="button" onClick={() => { setEditingMonsterId(null); setMonsterDraft(EMPTY_MONSTER_DRAFT); }}>Cancelar</button>}</form>
        </section>
      </details>
      <details className="workspace-gm-section">
        <summary><span>GRIMÓRIO E COMPÊNDIOS</span><small>magias, habilidades e itens</small></summary>
        <CompendiumPanel characters={characters} tokens={workspace.tokens} />
      </details>
      <details className="workspace-gm-section">
        <summary><span>MERCADORES</span><small>compra, venda e pechincha</small></summary>
        <MerchantPanel characters={characters} />
      </details>
      </>}
      {section === 'maps' && <>
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
        <details className="workspace-gm-section workspace-table-summary"><summary className="workspace-action-card"><MasterToolHeading icon="☷" title="Resumo da mesa" description={`${characters.filter(item => !archivedIds.includes(item.id)).length} jogadores · ${allies.length} aliado(s) do Mestre · ${workspace.presence.filter(item => item.online && item.actor_role === 'player').length} online`} /></summary>
        <p className="workspace-current-map">Mapa: {workspace.map?.title || 'Sem mapa ativo'}</p>
        <section className={`workspace-table-mode workspace-table-mode-${workspace.table_mode}`}>
          <div><small>MODO DA MESA</small><strong>{workspace.table_mode === "digital" ? "Digital" : workspace.table_mode === "physical" ? "Física" : "Teste"}</strong><p>{workspace.table_mode === "digital" ? "O Companion faz as rolagens por padrão." : workspace.table_mode === "physical" ? "Ataques pedem o valor bruto do dado físico por padrão." : "Simula sozinho a visão dos jogadores. As alterações continuam reais."}</p></div>
          <div role="group" aria-label="Modo operacional da mesa"><button type="button" className={workspace.table_mode === "digital" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("digital")}>Digital</button><button type="button" className={workspace.table_mode === "physical" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("physical")}>Física</button><button type="button" className={workspace.table_mode === "test" ? "active" : ""} disabled={Boolean(busy)} onClick={() => void changeTableMode("test")}>Teste</button></div>
        </section>
        </details>
        <nav className="workspace-master-shortcuts" aria-label="Atalhos do Mestre">
          <button className="workspace-action-card" type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray", { detail: { panel: "request", characterId: selectedId } }))}><MasterToolHeading icon="⚄" title="Pedir rolagem" description="Escolher jogador e teste" /></button>
          <button className="workspace-action-card" type="button" disabled={Boolean(busy) || !characters.length} onClick={() => void restAllCharacters()}><MasterToolHeading icon="☾" title="Descanso geral" description="Restaurar jogadores ativos · não altera NPCs reservados" /></button>
        </nav>
        <details className="workspace-gm-section" open={actionReferenceOpen} onToggle={event => setActionReferenceOpen(event.currentTarget.open)}>
          <summary className="workspace-action-card"><MasterToolHeading icon="▤" title="Cola de ações" description="Consultar habilidades, magias, ataques e itens por personagem" /></summary>
          {actionReferenceOpen && <CharacterActionReference characters={characters} initialId={selectedId} />}
        </details>
        <details ref={combatPanelRef} open={battleActive || undefined} className="workspace-gm-section"><summary className="workspace-action-card"><MasterToolHeading icon="⚔" title="Combate" description="Iniciativa, efeitos e multiataque" /></summary><CombatEncounterPanel ledger={ledger} confirmedState={battleState || undefined} mode={mode} tableMode={workspace.table_mode} mapId={workspace.map?.id || "default"} characters={characters} tokens={workspace.tokens} onChange={refresh} gridded={Boolean(workspace.map?.grid)} onPins={() => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "maps" }))} />
          <NecromancerEffects combat={battleState} onChange={refresh} />
          {workspace.tokens.some(token => token.token_type === 'monster' && token.current_hp === 0 && !token.sheet?.summon && token.sheet?.treasure && token.sheet.treasure !== '-') && <section className="workspace-monster-manager"><header><span>ESPÓLIOS DO ENCONTRO</span><small>Carregado e covil são tabelas distintas; covil exige acesso ao local.</small></header>
            {workspace.tokens.filter(token => token.token_type === 'monster' && token.current_hp === 0 && !token.sheet?.summon && token.sheet?.treasure && token.sheet.treasure !== '-').map(token => <div className="workspace-monster-row" key={`aftermath:${token.id}`}><strong>{token.name}</strong>
              {treasureHasCarried(token.sheet?.treasure) && <button disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, 'carried')}>Sortear espólio carregado</button>}
              {treasureHasLair(token.sheet?.treasure) && <button disabled={Boolean(busy)} onClick={() => void generateTokenLoot(token, 'lair')}>Sortear tesouro do covil</button>}
            </div>)}
          </section>}
        </details>
      </section>}
      {section === "master" && <details ref={itemToolsRef} className="workspace-gm-section">
        <summary className="workspace-action-card"><MasterToolHeading icon="◇" title="Itens e loot" description="Criar, editar e distribuir espólios" /></summary>
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
        <summary className="workspace-action-card"><MasterToolHeading icon="✎" title="Edição do Mestre" description="Selecionar e ajustar as fichas dos personagens" /></summary>
        <section className="workspace-gm-tools">
          <div className="workspace-gm-character-picker">
            <label>Ficha do personagem<select aria-label="Ficha para edição do Mestre" value={gmEditorChoice || selectedId} disabled={Boolean(busy)} onChange={event => setGmEditorChoice(event.target.value)}><option value="">Selecione um personagem</option>{characters.map(item => <option key={item.id} value={item.id}>{item.name}{archivedIds.includes(item.id) ? ' · NPC reservado' : ''}</option>)}</select></label>
            <button type="button" disabled={Boolean(busy) || !(gmEditorChoice || selectedId)} onClick={() => { const id = gmEditorChoice || selectedId; gmEditorIdRef.current = id; selectedIdRef.current = id; setGmEditorId(id); setSelectedId(id); localStorage.setItem('omnisvera_selected_character', id); }}>Carregar ficha</button>
          </div>
          {character && character.definition.id === gmEditorId && character.definition.id === selectedId ? <details open className="workspace-gm-subsection">
            <summary>Editar ficha de {definition?.name || "personagem selecionado"}</summary>
        <div className="workspace-gm-numbers"><NumericEditor label="PV atual" value={state?.current_hp} max={state?.maximum_hp || 999} onSave={(value) => stateAction("set_hp", { value }, "PV ajustado pelo Mestre")} /><NumericEditor label="PV máximo" value={state?.maximum_hp} min={1} onSave={(value) => definitionAction({ maximum_hp: value })} /><NumericEditor label="Nível" value={definition?.level} min={1} max={20} onSave={(value) => definitionAction({ level: value })} /><NumericEditor label="Classe de Armadura base" value={definition?.defenses?.base_armor_class ?? definition?.defenses?.armor_class} onSave={(value) => definitionAction({ armor_class: value })} /><NumericEditor label="Iniciativa" value={definition?.defenses?.initiative} min={-30} max={30} onSave={(value) => definitionAction({ initiative: value })} />{ATTRIBUTES.map(([key, label]) => <NumericEditor key={key} label={label} value={definition?.base_attributes?.[key] ?? definition?.attributes?.[key]} min={1} max={30} onSave={(value) => definitionAction({ attributes: { [key]: value } })} />)}</div>
        {character && <SpecializationSection key={character.definition.id} character={character} canOperate={canOperate} onApplied={refresh} />}
        <form onSubmit={(event) => { event.preventDefault(); if (condition.trim()) { void stateAction("add_condition", { condition: condition.trim() }, `Adicionou ${condition.trim()}`); setCondition(""); } }}><input value={condition} onChange={(event) => setCondition(event.target.value)} placeholder="Nova condição" /><button disabled={!condition.trim() || Boolean(busy)}>Adicionar status</button></form>
        <label className="workspace-session-notes"><span>Notas da sessão do Mestre</span><textarea value={sessionNotes} onChange={(event) => setSessionNotes(event.target.value)} /><button disabled={Boolean(busy) || sessionNotes === (state?.session_notes || "")} onClick={() => void stateAction("set_session_notes", { value: sessionNotes }, "Atualizou notas da sessão")}>Salvar notas</button></label>

        <button className="workspace-rest-button" disabled={Boolean(busy)} onClick={() => void stateAction("rest_at_inn", {}, "Descanso completo no INN")}>Descanso completo · restaurar vida, status, magias e habilidades</button>
          </details> : <p className="workspace-current-map">Selecione um personagem e carregue a ficha para editar.</p>}
        </section>
      </details>}
    </section>;
  }

  return <section className={`session-workspace unified-workspace workspace-view-${view}`} onClickCapture={activateCard} onKeyDownCapture={activateCard}>
    <header className="party-status-header">
      {mode === "gm" ? <button type="button" className={`party-status-title party-master-summary ${gmToolsOpen ? "active" : ""}`} onClick={() => setGmToolsOpen(true)} aria-label="Abrir painel do Mestre"><span>PAINEL DO MESTRE</span><strong>Omnisvera</strong><small>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} online · abrir resumo</small></button> : <div className="party-status-title"><span>MESA ÚNICA</span><strong>Omnisvera</strong><small>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} online</small></div>}
      <div className="party-status-list">{characters.filter(item => !archivedIds.includes(item.id)).map((item) => {
        const online = Boolean(presenceByCharacter.get(item.id));
        const selectable = mode === "gm" || item.access_level === "owner";
        return <button key={item.id} type="button" data-character={item.id} disabled={!selectable} aria-label={selectable ? `Abrir ficha de ${item.name}` : `${item.name} no grupo`} className={!gmToolsOpen && !selectedAllyId && !npcLibraryOpen && selectedId === item.id ? "active" : ""} onClick={() => { if (!selectable) return; setSelectedAllyId(""); setNpcLibraryOpen(false); setGmToolsOpen(false); selectedIdRef.current = item.id; setSelectedId(item.id); localStorage.setItem("omnisvera_selected_character", item.id); }}>
          <span className="workspace-avatar"><CharacterPortrait character={item} /><i className={online ? "online" : "offline"} title={online ? "Online" : "Offline"} /></span>
          <PartyMemberSummary name={item.name} className={item.class_name||'Personagem'} level={item.level} color={characterColor(item.id)} hp={item.current_hp} maximumHp={item.maximum_hp}/>
        </button>;
      })}{mode === "gm" && allies.map(ally => <button key={ally.id} type="button" aria-label={`Abrir ficha de ${ally.name}`} className={!gmToolsOpen && !npcLibraryOpen && selectedAllyId === ally.id ? "active" : ""} onClick={() => { setSelectedAllyId(ally.id); setNpcLibraryOpen(false); setGmToolsOpen(false); }}>
        <span className="workspace-avatar">{ally.image_path ? <img src={mediaUrlFromVaultPath(ally.image_path)} alt={ally.name} /> : <span>◆</span>}</span>
        <PartyMemberSummary name={ally.name} className={ally.sheet?.role||'Aliado'} level={ally.sheet?.level} color={ally.color} hp={ally.current_hp} maximumHp={ally.maximum_hp}/>
      </button>)}</div>
    </header>
    {mode === "player" && <div className={`workspace-table-mode-banner workspace-table-mode-${workspace.table_mode}`}>Mesa {workspace.table_mode === "digital" ? "digital" : workspace.table_mode === "physical" ? "física" : "em teste"}</div>}

    {error && <p className="workspace-error">{error}</p>}
    {syncError && <p className="workspace-error" role="status">{syncError}</p>}
    {attackResolution?.confirmed && <AttackOutcome resolution={attackResolution} />}
    <div className="session-workspace-grid">
      {(view === "table" || view === "sheet") && <aside className={`workspace-character-panel ${gmToolsOpen ? "gm-tools-active" : ""}`}>
        <PendingAttacks onOpen={setAttackResolution} refreshKey={`${attackResolution?.resolution_id}:${attackResolution?.confirmed}`} />
        {mode === "gm" && npcSheetOpen && <div className="workspace-reference-actions"><button type="button" onClick={openNpcLibrary}>Voltar para NPCs</button><button type="button" onClick={() => { setNpcSheetOpen(false); window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'maps' })); }}>Mapas</button></div>}
        {mode === "gm" && gmToolsOpen ? renderGmWorkspaceTools() : mode === "gm" && npcLibraryOpen ? npcReference : mode === "gm" && selectedAllyId ? (allies.find(ally => ally.id === selectedAllyId) ? <><button type="button" className="workspace-reference-back" onClick={openNpcLibrary}>Voltar para NPCs</button><CompanionAllySheet token={allies.find(ally => ally.id === selectedAllyId)!} characters={characters.filter(item => !archivedIds.includes(item.id))} targets={workspace.tokens} physical={workspace.table_mode === "physical"} onChange={async () => { await loadOverview(); }} /></> : <p>Ficha do aliado indisponível. Tentando atualizar novamente.</p>) : character ? <>
          <header className="workspace-character-identity">
            {mediaUrlFromVaultPath(definition?.portrait) ? <img src={mediaUrlFromVaultPath(definition?.portrait, 128)} alt={`Retrato de ${definition?.name}`} /> : <span>{definition?.name.slice(0, 1)}</span>}
            <CharacterLevel characterId={character.definition.id} onApplied={refresh} key={character.definition.id} level={definition?.level ?? null} experience={definition?.progression?.experience ?? null} canEdit={mode === "gm"} onSave={async (fields) => { await refresh(await updateCharacterDefinition(character.definition.id, fields, "Edição de nível e XP")); }} />
          {definition?.id === 'dorn7' && mode === 'gm' && definition.progression?.approved_build !== 'dorn-mage3-approved-2026-10-07' && <button disabled={Boolean(busy)} onClick={async () => {
            if (busy) return; setBusy('dorn-build'); setError('');
            try { await refresh(await applyDornApprovedBuild()); }
            catch (reason) { setError(reason instanceof Error ? reason.message : 'Falha na ficha aprovada'); }
            finally { setBusy(''); }
          }}>Aplicar ficha aprovada de Dorn · nível 3 / PV 20</button>}
            <div className="workspace-character-copy"><small>PERSONAGEM</small><h2 style={{ color: characterColor(definition?.id) }}>{definition?.name}</h2>{definition?.epithet && <p>{definition.epithet}</p>}<div className="workspace-identity-tags"><SheetDetail compactImage title={definition?.race || 'Raça'} description={definition?.identity_cards?.race.description || definition?.abilities?.racial || 'Sem regras raciais cadastradas.'} icon={mediaUrlFromVaultPath(definition?.identity_cards?.race.image_path)} showIcon={false}><b>{definition?.race || 'Raça'}</b></SheetDetail><SheetDetail compactImage title={definition?.class_name || 'Classe'} description={definition?.identity_cards?.class.description || definition?.abilities?.class || 'Sem regras de classe cadastradas.'} icon={mediaUrlFromVaultPath(definition?.identity_cards?.class.image_path)} showIcon={false}><b>{definition?.class_name || 'Classe'}</b></SheetDetail><SpecializationBadge key={character.definition.id} character={character} /></div></div>
          </header>

          <PendingLevelRolls character={character} canOperate={canOperate} onApplied={async () => { await refresh(); }} />

          {state?.animal_form&&<p className="workspace-animal-sheet" role="status">Forma animal · 1 PV · CA 14 · JP 4 · voo 9 m. Sem ataques nem fala. Forma normal: {state.normal_current_hp}/{state.normal_maximum_hp} PV.</p>}
          <div className="workspace-vitals-and-controls">
          <section className="workspace-vitals"><div className="workspace-hp-heading"><span><small>VIDA</small><strong>{state?.current_hp ?? "—"}<em>/ {state?.maximum_hp ?? "—"}</em></strong></span><span className="workspace-armor-class"><small>CA</small><strong><ArmorClassValue defenses={definition?.defenses} inventory={character.inventory} /></strong></span></div><div className="workspace-hp-track"><i style={{ width: `${state?.maximum_hp ? Math.max(0, Math.min(100, Number(state.current_hp || 0) / state.maximum_hp * 100)) : 0}%` }} /></div></section>
          {definition?.id !== 'vezemir' && ATTRIBUTES.some(([key]) => itemEffectBreakdown.some((entry) => entry.kind === "attribute_bonus" && entry.target === key && entry.active)) && <div className="workspace-attribute-effect-details">{ATTRIBUTES.filter(([key]) => itemEffectBreakdown.some((entry) => entry.kind === "attribute_bonus" && entry.target === key && entry.active)).map(([key, label]) => <button type="button" key={key} onClick={() => setEffectBreakdownOpen(key)}>Detalhar {label}</button>)}</div>}
          <div className="workspace-hp-quick-controls" aria-label="Ajuste rápido de vida">
            <button type="button" disabled={!canOperate||Boolean(busy)} onClick={()=>setHpDraft(Math.max(selectedId==='vezemir'?-10:0,Number(hpDraft===''?state?.current_hp??0:hpDraft)-1))}>−</button>
            <input type="number" min={selectedId==='vezemir'?-10:0} max={state?.maximum_hp||99999} value={hpDraft} onChange={event=>setHpDraft(event.target.value===''?'':Number(event.target.value))} aria-label="PV"/>
            <button type="button" disabled={!canOperate||Boolean(busy)} onClick={()=>setHpDraft(Math.min(state?.maximum_hp||99999,Number(hpDraft===''?state?.current_hp??0:hpDraft)+1))}>+</button>
            <button type="button" aria-label="Confirmar PV" title="Confirmar PV" disabled={!canOperate||Boolean(busy)||hpDraft===''} onClick={()=>void stateAction('set_hp',{value:Number(hpDraft)},'PV ajustado')}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg></button>
          </div></div>

          <section className="workspace-conditions workspace-status-under-vitals" aria-label="Status"><ActiveEffectIcons state={battleState} targetId={character.definition.id} /><ParasiteControl state={battleState} targetId={character.definition.id} onChange={refresh} />{state?.conditions.length ? <div className="workspace-condition-list">{state.conditions.map((item) => <span key={item}>{item}{mode === "gm" && <button onClick={() => void stateAction("remove_condition", { condition: item }, `Removeu ${item}`)}>×</button>}</span>)}</div> : <p>{battleState.active_effect_icons?.some(e=>e.target_type==='character' && e.target_id===character.definition.id) ? 'STATUS' : 'STATUS - Nenhum'}</p>}</section>
          <CombatEncounterPanel compact ledger={ledger} confirmedState={battleState || undefined} mode={mode} tableMode={workspace.table_mode} mapId={workspace.map?.id || "default"} characters={characters} tokens={workspace.tokens} onChange={refresh} gridded={Boolean(workspace.map?.grid)} onFollowMap={id => void browseWorkspaceMap(id)} />

          {(Object.keys(definition?.item_effects?.skill_modifiers || {}).length > 0 || (definition?.item_effects?.resistances.length || 0) > 0 || (definition?.item_effects?.immunities.length || 0) > 0 || (definition?.item_effects?.vulnerabilities.length || 0) > 0) && <SheetSection title="Efeitos de itens"><section className="workspace-item-traits"><header><span>EFEITOS DE ITENS</span></header><div>{Object.entries(definition?.item_effects?.skill_modifiers || {}).map(([skill, bonus]) => <button type="button" key={`skill:${skill}`} disabled={!canOperate || Boolean(busy)} onClick={() => void roll("skill", skill)}><strong>{skill}</strong><small>{bonus >= 0 ? "+" : ""}{bonus} · jogar perícia</small></button>)}{definition?.item_effects?.resistances.map((target) => <span key={`resistance:${target}`}><strong>Resistência</strong><small>{target}</small></span>)}{definition?.item_effects?.immunities.map((target) => <span key={`immunity:${target}`}><strong>Imunidade</strong><small>{target}</small></span>)}{definition?.item_effects?.vulnerabilities.map((target) => <span key={`vulnerability:${target}`}><strong>Vulnerabilidade</strong><small>{target}</small></span>)}</div></section></SheetSection>}

          <section className="workspace-attributes"><header><span>ATRIBUTOS E TESTES</span><div className="workspace-attribute-tools" role="group" aria-label="Proteção e dados"><button className="workspace-save-roll" aria-label="Jogar proteção" title="Jogada de proteção" disabled={!canOperate || Boolean(busy)} onClick={() => void roll("saving_throw")}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 21 6v6c0 5-9 10-9 10S3 17 3 12V6Z" fill="none" stroke="currentColor" strokeWidth="2"/></svg><span>JP</span></button><button className="workspace-dice-tray-button" aria-label="Bandeja de dados" title="Bandeja de dados" type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray"))}>{diceIcon ? <img src={diceIcon} alt="" /> : <span>⚄</span>}</button>{character.access_level !== "public" && <CharacterNotes key={`notes:${character.definition.id}`} characterId={character.definition.id} compact />}</div></header><div>{ATTRIBUTES.map(([key, label]) => { const itemBonus = Number(definition?.attributes?.[key] || 0) - Number(definition?.base_attributes?.[key] ?? definition?.attributes?.[key] ?? 0); return <button key={key} disabled={!canOperate || Boolean(busy)} onClick={() => void roll("attribute", key)}><span>{label}</span><strong>{definition?.attributes?.[key] ?? "—"}</strong><small>{definition?.attribute_modifiers?.[key] == null ? "N/C" : `${Number(definition.attribute_modifiers[key]) >= 0 ? "+" : ""}${definition.attribute_modifiers[key]}`}{itemBonus !== 0 ? ` · item ${itemBonus > 0 ? "+" : ""}${itemBonus}` : ""}</small></button>; })}</div></section>
          <EquipmentLoadout inventory={character.inventory} cover={character.definition.cover} portrait={character.definition.portrait} onInspect={setOpenItem} />

          {(standaloneResources.length > 0 || consumables.length > 0) && <section className="workspace-action-catalog workspace-resource-catalog">
<header>
<span>RECURSOS</span>
</header>{standaloneResources.map((resource) => <article tabIndex={0} key={resource.key}>
<span>
<SheetDetail title={resource.label}
icon={mediaUrlFromVaultPath(abilities.find(a => a.kind === 'resource' && a.uses?.resource_key === resource.key)?.image_path)}
description={`${abilities.find(a => a.kind === 'resource' && a.uses?.resource_key === resource.key)?.description || resource.label}\nDisponível: ${resource.current}/${resource.maximum}`} />
</span>
<b>{resource.current}/{resource.maximum}</b>{canOperate && resource.key !== "reserva_de_sangue" && <button data-card-command disabled={Boolean(busy) || resource.current <= 0} onClick={() => void stateAction("consume_resource", { resource_key: resource.key, amount: 1 }, `Usou ${resource.label}`)}>Usar</button>}</article>)}{consumables.map((item) => { if (item.item_title === 'Pulseira de Vinhas') return <VineBraceletControl remaining={Number(item.charges_current ?? item.charges_max ?? 2)} maximum={Number(item.charges_max || 2)} key={item.item_path} icon={item.thumbnail} equipped={item.equipped} disabled={!canOperate || Boolean(busy) || !battleActive} tokens={battleMapTokens} onChange={async () => { await refresh(); setBattleState(await getCombatEffects()); }} />; const repair = definition?.id === 'dorn7' && item.item_title === 'Kit de Reparo'; const title = repair ? 'Reparo' : cleanItemDisplayName(item.item_title); const executesRules = item.effect_rules?.some((rule) => rule.trigger === "on_use"); const available = item.charges_max ? Number(item.charges_current ?? item.charges_max) : item.quantity; return <article tabIndex={0} key={item.item_path}>
<span>
<SheetDetail title={title} description={item.description || title} icon={mediaUrlFromVaultPath(item.thumbnail || item.cover || iconPathForItem(item.item_title, item.item_type))} />
</span>
<b>{item.charges_max ? `${available}/${item.charges_max} cargas` : item.quantity}</b>{canOperate && <button data-card-command title={consumableActionBlock(battleState, selectedId, state?.current_hp) || 'Um consumível por turno; ainda pode atacar.'} disabled={Boolean(busy) || available <= 0 || Boolean(consumableActionBlock(battleState, selectedId, state?.current_hp))} onClick={() => { const ability = repair ? abilities.find(a => a.id === 'dorn-reparo') : undefined; if (ability) { void useAbility(ability); return; } if (repair) { setError('Reparo não está disponível na ficha aprovada'); return; } void stateAction(executesRules ? "use_item" : "change_quantity", executesRules ? { item_path: item.item_path } : { item_path: item.item_path, quantity: Math.max(0, item.quantity - 1) }, `Usou ${title}`); }}>Usar</button>}</article>; })}{battleActive && <small role="status">{consumableActionBlock(battleState, selectedId, state?.current_hp) || 'Um consumível por turno; ainda pode atacar.'}</small>}</section>}

          {attackSection}
          {definition?.id === 'raziel' && hemomancyCard}
          {vampireOutcome && <p role="status">{vampireOutcome}</p>}
          {spells.length > 0 && <SheetSection title="Magias" autoOpen={battleActive} key={`spells:${selectedId}`}><section className="workspace-action-catalog"><header><span>MAGIAS</span><small>{spells.length}</small></header>{spells.map((ability) => {
            const resource = abilityResource(ability, state?.resources || []);
            const requiredItem = requiredItemForAbility(ability);
            const requirementMissing = Boolean(ability.requires_equipped_item && !requiredItem);
            const requiredIcon = mediaUrlFromVaultPath(ability.image_path) || (requiredItem ? mediaUrlFromVaultPath(requiredItem.thumbnail || requiredItem.cover || iconPathForItem(requiredItem.item_title, requiredItem.item_type)) : "");
            if (['levantar-esqueleto','levantar-um-esqueleto'].includes(ability.id)) {
              return <SpellCard key={ability.id} heading={<AbilityName ability={ability} icon={requiredIcon}/>} summary={<b>{resource?.current || 0}/{resource?.maximum || 0}</b>}><button data-card-command disabled={!character || character.access_level === 'public' || Boolean(busy) || Boolean(ability.blocked)} onClick={()=>void useAbility(ability)}>Usar</button></SpellCard>;
            }
            if (ability.id === 'animar-mortos') return <SpellCard key={ability.id} heading={<AbilityName ability={ability} icon={requiredIcon} />} summary={<>{resource && <b>{resource.current}/{resource.maximum}</b>}</>}>{canOperate && <div className="workspace-inline-actions">{abilityTargetControl(ability)}</div>}</SpellCard>;
            if (ability.id === 'adaga-de-osso') return <SpellCard key={ability.id} heading={<AbilityName ability={ability} icon={requiredIcon} />} summary={<b>—</b>}>{canOperate && <div className="workspace-inline-actions">{abilityTargetControl(ability)}</div>}</SpellCard>;
if (canOperate && ['toque-sombrio','aterrorizar','clonagem','magia-da-morte'].includes(ability.id)) return <SpellCard key={ability.id} heading={<AbilityName ability={ability} icon={requiredIcon} />} summary={<>{resource && <b>{resource.current}/{resource.maximum}</b>}</>}><button data-card-command disabled={necroCardBlocked(ability)} onClick={()=>void (ability.id==='toque-sombrio'?useAbility(ability):armAreaAbility(ability))}>{ability.id==='clonagem' && (battleState.effects || []).some(e=>e.necro_spell==='clonagem')?'Encerrar concentração':'Usar'}</button></SpellCard>;
            if (canOperate && ability.id === "misseis-magicos") return <SpellTargetControl key={ability.id}
              heading={<AbilityName ability={ability} icon={requiredIcon} />}
              summary={<>{resource && <b>{resource.current}/{resource.maximum}</b>}</>}
              targets={attackTargets} targetId={attackTargetById[ability.id] || ""}
              disabled={Boolean(busy) || Boolean(resource && resource.current <= 0) || Boolean(ability.blocked) || requirementMissing || Boolean(combatActionBlock(battleState, selectedId, character?.state?.current_hp))}
              onSelect={id => { setAimedAttackId(ability.id); setAttackTargetById(current => ({ ...current, [ability.id]: id })); }}
              onUse={(target,automatic) => void useAbility(ability, target, automatic)}
              gridded={griddedCombat} actionRef={`technique:${selectedId}:${ability.id}`}
              attackerTokenId={characterTokenId} attackerCharacterId={selectedId} />;
            return <SpellCard key={ability.id} heading={<AbilityName ability={ability} icon={requiredIcon} />} summary={<>{resource && <b>{resource.current}/{resource.maximum}</b>}</>}>{canOperate && <button data-card-command disabled={Boolean(busy) || Boolean(resource && resource.current <= 0) || Boolean(ability.blocked) || requirementMissing} onClick={() => void useAbility(ability)}>{ability.blocked ? "Bloqueado" : requirementMissing ? "Equipar item" : "Usar"}</button>}</SpellCard>;
          })}</section></SheetSection>}
          {definition?.id === 'morthak' && canOperate && necroSpell && <NecromancerSpellControls key={necroSpell} spell={necroSpell} ability={abilities.find(a=>a.id===necroSpell)} mode={mode} targets={attackTargets} resources={state?.resources || []} combat={battleState} hp={state?.current_hp || 0} rollMode={defaultAttackRollMode} gridded={griddedCombat} attackerTokenId={attackTargets.find(token => token.character_id === selectedId)?.id || ""} attackerCharacterId={selectedId} onResolved={setAttackResolution} onChange={refresh} onClose={()=>setNecroSpell('')} />}

{definition?.id === 'dorn7' && mode === 'gm' && <>{dornSpell && battleState && <DornSpellControls key={dornSpell} spell={dornSpell} ability={abilities.find(a=>a.id===dornSpell)} tokens={workspace.tokens} combat={battleState} onChange={refresh} onClose={() => setDornSpell('')} />}<SheetSection title="Ações / protocolos" autoOpen={battleActive}><section className="workspace-action-catalog"><header><span>AÇÕES / PROTOCOLOS</span></header><DornProtocolControls combat={battleState} tokens={workspace.tokens} gridded={griddedCombat} remaining={state?.resources.find(r=>r.key==='dorn_guard')?.current ?? 1} onChange={async snapshot => { setBattleState(snapshot); await refresh(); }} /></section></SheetSection><DornConstructDetails character={character} combat={battleState} /></>}

          {Object.entries(groupedAbilities).map(([group, groupEntries]) => { const medal = definition?.id === "vezemir" && normalizedName(group) === "poderes" ? character?.inventory.find((item) => normalizedName(item.item_title).includes("medalhao")) : null; const medalIcon = medal ? mediaUrlFromVaultPath(medal.thumbnail || medal.cover || iconPathForItem(medal.item_title, medal.item_type)) : ""; return <SheetSection key={`${selectedId}:${group}`} title={group} autoOpen={battleActive && groupEntries.some(ability => ability.active)}><section className="workspace-action-catalog">
<header>
<span className="workspace-group-title">{medalIcon && <img src={medalIcon} alt="" />}{group.toUpperCase()}</span>
<small>{groupEntries.length}</small>
</header>{groupEntries.map((ability) => { const resource = abilityResource(ability, state?.resources || []); const requiredItem = requiredItemForAbility(ability); const requirementMissing = Boolean(ability.requires_equipped_item && !requiredItem); const nightArt = ability.id === 'forma-da-noite' ? NIGHT_FORMS.find(form => form.id === (state?.animal_form || techniqueModeById[ability.id] || 'corvo'))?.image : undefined; const requiredIcon = ability.id==='forma-da-noite'?"":mediaUrlFromVaultPath(ability.image_path || nightArt) || (requiredItem ? mediaUrlFromVaultPath(requiredItem.thumbnail || requiredItem.cover || iconPathForItem(requiredItem.item_title, requiredItem.item_type)) : "");
const bloodSkill = ability.active && definition?.id==='raziel' ? definition.hemomancy?.weapons.find(weapon=>hemomancySelection(definition.hemomancy,weapon.weapon,true)?.id===ability.id) : undefined;
if (bloodSkill) {
  const cost=hemomancyBloodCost(definition?.hemomancy,bloodSkill.weapon,true,heldBloodWeaponId);
  return <SpellCard key={ability.id} className="workspace-hemomancy-skill" heading={<AbilityName ability={ability} icon={requiredIcon}/>} summary={<b>{cost} sangue</b>}>
    {canOperate&&<button data-card-command disabled={Boolean(busy)||Boolean(state?.animal_form)||cost==null||bloodAvailable<(cost||0)||Boolean(ability.requires_target&&(!workspace.map?.grid||combatActionBlock(battleState,selectedId,state?.current_hp)))} onClick={()=>{setHemomancyChoice(bloodSkill.weapon);void useAbility(ability);}}>Usar</button>}
  </SpellCard>;
}
return <article tabIndex={0} key={ability.id}
className={ability.id === 'forma-da-noite' ? 'workspace-night-form-card' : undefined}>
<span>
<AbilityName ability={ability} icon={requiredIcon} />{!ability.active && <small>Passiva</small>}</span>
{resource && !['regeneracao-vampirica', 'lamina-de-sangue'].includes(ability.id) && <b>{resource.current}/{resource.maximum}</b>}
{ability.active && canOperate && (ability.requires_target ? <div className="workspace-inline-actions">{abilityTargetControl(ability)}</div> : <>{ability.id === "forma-da-noite" && <NightFormControl animal={state?.animal_form} busy={Boolean(busy)} canActivate={!Boolean(resource && resource.current <= 0) && !Boolean(ability.blocked) && !requirementMissing} onActivate={() => void useAbility(ability)} onDeactivate={() => void stateAction('end_night_form', {}, 'Desativar Forma da Noite')} selector={<NightFormSelector value={techniqueModeById[ability.id] || "corvo"} onChange={animal => setTechniqueModeById(current => ({ ...current, [ability.id]: animal }))} />} />}{ability.id === "lamina-de-sangue" && <>
<label>Lâminas<select aria-label="Lâminas declaradas" value={(techniqueModeById[ability.id] || "1:ranged").split(":")[0]} onChange={(e) => setTechniqueModeById((current) => ({ ...current, [ability.id]: `${e.target.value}:${(current[ability.id] || "1:ranged").split(":")[1] || "ranged"}` }))}>{[1, 2, 3, 4, 5].map((n) => <option key={n} value={String(n)}>{n} ({n}d4)</option>)}</select>
</label>
<label>Modo<select aria-label="Modo da Lâmina de Sangue" value={(techniqueModeById[ability.id] || "1:ranged").split(":")[1] || "ranged"} onChange={(e) => setTechniqueModeById((current) => ({ ...current, [ability.id]: `${(current[ability.id] || "1:ranged").split(":")[0] || "1"}:${e.target.value}` }))}>
<option value="ranged">À distância</option>
<option value="melee">Corpo a corpo</option>
</select>
</label>
</>}{ability.id !== "forma-da-noite" && <button data-card-command disabled={Boolean(busy) || Boolean(resource && resource.current <= 0) || Boolean(ability.blocked) || requirementMissing} onClick={() => void useAbility(ability)}>{ability.blocked ? "Bloqueado" : requirementMissing ? "Equipar item" : "Usar"}</button>}
</>)}</article>; })}</section></SheetSection>; })}


          <CurrencyCounters key={`wallet:${character.definition.id}`} character={character} onChange={refresh} summaryOnly />
          <section className="workspace-action-catalog workspace-inventory-catalog"><header><span>INVENTÁRIO</span><small>{carriedItems.length}</small></header>{carriedItems.map(item => <article key={item.item_path}><InventoryItemIcon item={item} onInspect={() => setOpenItem(item)} /></article>)}</section>


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

      {view === 'npcs' && mode === 'gm' && <aside className="workspace-character-panel workspace-map-controls-panel" aria-label="Controles de NPCs">{npcReference}<details className="workspace-gm-section"><summary>Criar, editar ou revelar pins no mapa atual</summary>{renderGmWorkspaceTools('npcs')}</details></aside>}
      {view === "maps" && <aside className="workspace-character-panel workspace-map-controls-panel">
        {renderGmWorkspaceTools("maps")}
        {mode === 'gm' && <section className="workspace-map-management" aria-label="Gerenciamento de mapas">
          <h2>Gerenciamento de mapas</h2>
          <p>Os seis mapas da Sessão 7 já têm grid pronto. Na Mesa, basta abrir a cena e mover os tokens.</p>
          <form className="workspace-map-upload" onSubmit={submitMap}>
            <input aria-label="Nome da imagem" value={mapTitle} disabled={mapUploading} onChange={event=>setMapTitle(event.target.value)} placeholder="Nome da imagem" maxLength={160}/>
            <label><input ref={mapFileInputRef} type="file" accept="image/png,image/jpeg,image/webp" disabled={mapUploading} onChange={event=>{const file=event.target.files?.[0]||null;setMapFile(file);setMapUploadNotice('');if(file&&!mapTitle.trim())setMapTitle(file.name.replace(/\.[^.]+$/,''));}}/><span>{mapFile?.name || "Escolher imagem · até 10 MB"}</span></label>
            <label className="workspace-map-public-toggle"><input type="checkbox" checked={mapVisibleToPlayers} disabled={mapUploading} onChange={event=>setMapVisibleToPlayers(event.target.checked)}/><span>Disponível para os jogadores</span></label>
            <button disabled={!mapTitle.trim() || !mapFile || mapUploading}>{mapUploading?'Enviando imagem…':'Salvar na biblioteca'}</button>
          </form>
          {mapUploadNotice&&<p role="status">{mapUploadNotice}</p>}
          <WorkspaceMapLibrary maps={workspaceMaps} activeId={workspace.map?.id} onChange={refreshMapWorkspace} onSelect={changeWorkspaceMap} selectionDisabled={Boolean(battleState.encounter?.active)}/>
          {workspace.map?.id && <label className="workspace-map-public-toggle"><input type="checkbox" checked={Boolean(workspace.map.visible_to_players)} disabled={Boolean(busy)} onChange={event=>void changeMapVisibility(String(workspace.map?.id),event.target.checked)}/><span>Mapa atual disponível aos jogadores</span></label>}
          {workspace.map && <GridConfiguration key={workspace.map.id} mapId={workspace.map.id} grid={workspace.map.grid} disabled={Boolean(battleState.encounter?.active || busy)} onChange={refreshMapWorkspace}/>}
        </section>}
        {mode === "gm" && <details className="workspace-gm-section" onToggle={event=>setSpriteStudioOpen(event.currentTarget.open)}><summary>Sprite Studio</summary>{spriteStudioOpen && <SpriteStudio entities={[...characters.map(c=>({entity_type:"character" as const,id:c.id,name:c.name})),...workspace.tokens.filter(t=>t.token_type!=="character").map(t=>({entity_type:"token" as const,id:t.id,name:t.name}))]} onChange={refreshMapWorkspace}/>}</details>}
        {mode === "gm" && <LocationQuickPin mapId={workspace.map?.id || "default"} tokens={workspace.tokens} onChange={refresh} />}
      </aside>}

      {view !== "sheet" && <main className="workspace-map-panel">
        {lootNotice && <div className="workspace-map-loot-receipt" role="status"><span>{lootNotice}</span><button type="button" aria-label="Fechar resultado do espólio" onClick={()=>setLootNotice('')}>×</button></div>}
        {battleActive && <div className="workspace-battle-banner" role="status" aria-live="polite"><strong>COMBATE · Rodada {battleState.round}</strong><span>{battleCurrent?.target_id === selectedId && mode === 'player' ? 'É o seu turno' : `${mode === 'gm' && battleCurrent?.target_type === 'token' ? 'Mestre, sua vez' : 'Turno'}: ${battleCurrent?.name || 'participante oculto'}`}</span>{battleState.encounter?.action_committed && <small>Ação confirmada · conclua e passe o turno</small>}</div>}
        <header>
          <div>
            {(mode!=='gm' || !workspaceMaps.length || view==='memory') && <h2>{mapTitleShown}</h2>}
            {mode === 'gm' && view !== 'memory' && workspaceMaps.length > 0 && <label className="workspace-active-map-select">
              <select aria-label="Mapa ativo" value={workspace.map?.id || ''} disabled={Boolean(busy || battleState.encounter?.active)} onChange={event=>void changeWorkspaceMap(event.target.value).catch(()=>{})}>
                {workspaceMaps.map(item=><option key={item.id} value={item.id}>{item.title}{!item.visible_to_players ? ' · privado' : ''}</option>)}
              </select>
              {battleState.encounter?.active && <small>Encerre o combate para trocar a arena.</small>}
            </label>}
            {mode === 'player' && workspaceMaps.length > 0 && <label className="workspace-map-select">
              Explorar mapa
              <select value={playerMapId} onChange={event=>void browseWorkspaceMap(event.target.value)}>
                {workspaceMaps.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}
              </select>
            </label>}
          </div>
          <div className="workspace-map-zoom" aria-label="Zoom do mapa"><button type="button" disabled={mapZoom <= 1} onClick={() => changeMapZoom(mapZoom - .1)} aria-label="Diminuir zoom">−</button><output>{Math.round(mapZoom * 100)}%</output><button type="button" disabled={mapZoom >= 3} onClick={() => changeMapZoom(mapZoom + .1)} aria-label="Aumentar zoom">+</button><button type="button" disabled={mapZoom === 1} onClick={() => changeMapZoom(1)}>Ajustar</button></div>
        </header>
        {pendingGridCommand && <button type="button" disabled={Boolean(busy)} onClick={()=>void confirmGridMove(pendingGridCommand.mapId,pendingGridCommand.command)}>Reenviar movimento pendente</button>}
        {targeting && (() => {
          const ring = targeting.ring;
          const selected = ring.targets?.find(item => item.id === targeting.selectedId) || null;
          const validCount = ring.targets?.filter(item => item.valid).length || 0;
          return <div className="targeting-bar" role="group" aria-label="Mira no grid">
            <strong>{targeting.actionLabel}</strong>
            {targeting.loading ? <small>Abrindo alcance…</small> : ring.gridded ? <>
              <small>{ring.mode === "melee" || ring.mode === "touch" ? "corpo a corpo" : ring.range_m==null ? 'Alcance não cadastrado · seleção no mapa' : `${ring.range_m} m`} · {validCount} alvos válidos</small>
              {(ring.max_targets || 1)>1 && <small>{targeting.selectedIds.length}/{ring.max_targets} selecionados · repita um alvo para remover ou concluir</small>}
              {selected && <small>{selected.name} · {selected.cells} células · {selected.meters.toFixed(1)} m{selected.valid ? "" : ` · FORA (${selected.reason})`}</small>}
              {selected && !selected.valid && <button type="button" disabled={Boolean(busy)} onClick={() => void approachTarget()}>Mover até o alcance</button>}
              {targeting.approach && !targeting.approach.already_in_range && <small>
                {targeting.approach.lands_in_range
                  ? `Caminho: ${targeting.approach.path.length - 1} células · ${targeting.approach.cost_m} m${targeting.approach.remaining_m != null ? ` (resta ${targeting.approach.remaining_m} m)` : ""}`
                  : `Não alcança: faltam ${(targeting.approach.meters - (targeting.approach.cost_m + (targeting.approach.remaining_m || 0))).toFixed(1)} m mesmo andando tudo`}
                <button type="button" disabled={Boolean(busy) || targeting.approach.path.length < 2} onClick={() => void confirmApproachMove()}>Confirmar movimento</button>
              </small>}
            </> : <>
              <small>{ring.reason || ring.declared?.label}</small>
              {ring.declared?.mode === "unknown" && <>
                <input value={targeting.declaredM} onChange={(event) => setTargeting(current => current ? { ...current, declaredM: event.target.value } : current)} placeholder="metros (Mestre declara)" />
                <button type="button" disabled={!targeting.declaredM.trim()} onClick={() => void openTargeting(targeting.actionRef, targeting.actionLabel, targeting.attackerTokenId, Number(targeting.declaredM))}>Abrir anel</button>
              </>}
            </>}
            <button type="button" onClick={() => setTargeting(null)}>Cancelar mira</button>
          </div>;
        })()}
        <div ref={mapViewportRef} className={`workspace-map-canvas ${mode === "gm" ? "editable" : "locked"}`} onScroll={() => queueWorkspaceViewSave()} onPointerMove={previewTokenMove} onPointerUp={(event) => void finishTokenMove(event)} onPointerCancel={(event) => void finishTokenMove(event)} onPointerLeave={(event) => { if (draggingTokenRef.current && event.buttons === 0) void finishTokenMove(event); }}>
          <div ref={mapCanvasRef} className={`workspace-map-stage ${mode === "gm" && view === "maps" && fogEditing ? "fog-editing" : ""}`} style={{ width: `${mapZoom * 100}%`, height: `${mapZoom * 100}%` }}>
            <AttackTargetLine tokens={battleMapTokens} {...(targeting ? {actorId:targeting.attackerTokenId,targetIds:targeting.selectedIds} : targetLine.targetId ? targetLine : sharedAttackTarget(battleState, ledger))} />
            {mapImagePath ? <img src={mediaUrlFromVaultPath(mapImagePath)} alt={mapTitleShown} draggable={false} /> : <p className="workspace-map-empty">O Mestre ainda não disponibilizou mapas para os jogadores.</p>}
            {workspace.map?.grid ? <LogicalGrid grid={workspace.map.grid} destination={gridDestination}/> : <div className="workspace-map-grid" aria-hidden="true" />}
            <MapSpellEffects effects={'map_spell_effects' in battleState?battleState.map_spell_effects as typeof battleState.effects:battleState.effects} mapId={workspace.map?.id||''} grid={workspace.map?.grid} tokens={renderedMapTokens} characters={characters}/>
            {targeting?.ring.gridded && workspace.map?.grid && targeting.ring.origin && targeting.ring.range_cells != null && (() => {
              const grid = workspace.map!.grid!;
              const pathCells: [number, number][] | undefined = targeting.approach && !targeting.approach.already_in_range
                ? targeting.approach.path.map((cell) => [cell[0], cell[1]] as [number, number]) : undefined;
              const center=targeting.actionRef==='technique:raziel:marca-rubra' ? renderedMapTokens.find(t=>t.id===targeting.selectedIds[0])?.grid_position : null;
              const areaCells: [number,number][] | undefined=center ? [[0,0],[1,0],[-1,0],[0,1],[0,-1]].map(([dx,dy])=>[center.cell_x+dx,center.cell_y+dy] as [number,number]).filter(([x,y])=>x>=0&&y>=0&&x<grid.cols&&y<grid.rows) : undefined;
              return <TargetingOverlay grid={grid} ring={{ origin: targeting.ring.origin, rangeCells: targeting.ring.range_cells, path: pathCells,areaCells:targeting.ring.area_cells || areaCells }} />;
            })()}
            {(mode === "gm" || fogLayers.length > 0) && <div className={`workspace-map-fog ${mode === "gm" && view === "maps" && fogEditing ? "editor" : ""}`} style={{ gridTemplateColumns: `repeat(${fogColumns}, 1fr)`, gridTemplateRows: `repeat(${fogRows}, 1fr)` }} onPointerDown={beginFogPaint} onPointerMove={paintFog} onPointerUp={(event) => void finishFogPaint(event)} onPointerCancel={(event) => void finishFogPaint(event)} onLostPointerCapture={() => void finishFogPaint()}>
              {fogCells.map((cell) => { const density = mistDensityByCell[cell] || 0; return <div key={cell} className={`workspace-fog-cell ${fogIsRevealed(cell) ? "revealed" : "hidden"} ${density > 0 ? "mist-active" : ""}`} style={density > 0 ? { backgroundColor: `rgba(210,220,226,${Math.min(.42, density * .34)})` } : undefined} aria-hidden="true" />; })}
            </div>}
            {Object.keys(mistDensityByCell).length > 0 && <MistParticleOverlay densityByCell={mistDensityByCell} columns={fogColumns} rows={fogRows} />}
            {renderedMapTokens.map((token) => { const summary = token.token_type === "character" && token.character_id ? characterById.get(token.character_id) : undefined; const image = token.sheet?.corpse ? '' : mediaUrlFromVaultPath(token.image_path || summary?.portrait); const hpCurrent = summary?.current_hp ?? token.current_hp; const hpMaximum = summary?.maximum_hp ?? token.maximum_hp; const conditions = summary?.conditions || token.conditions;
              const visual=tokenProjection(workspace.map?.grid,token.grid_position,token);
              const grid=workspace.map?.grid;
              const gridSize=grid && token.grid_position ? { width: `${(100-grid.origin_x)/grid.cols*token.grid_position.footprint_w}%`, height: `${(100-grid.origin_y)/grid.rows*token.grid_position.footprint_h}%` } : {};
return <button type="button" key={token.id} data-grid-token={token.id} data-grid-sized={Boolean(grid && token.grid_position)} className={`workspace-map-token ${token.token_type} ${canMoveToken(token) ? "movable" : ""} ${token.sheet?.summon?.technique === "animar-mortos" ? "reanimated" : ""}${targeting?.ring.gridded && targeting.ring.targets?.some(item => item.id === token.id && item.valid) ? " target-valid" : ""}${targeting?.ring.gridded && targeting.ring.targets?.some(item => item.id === token.id && !item.valid) ? " target-invalid" : ""}${targeting?.selectedIds.includes(token.id) ? " target-selected" : ""}`} style={{ left: `${visual.longitude}%`, top: `${visual.latitude}%`, borderColor: token.color, color: token.color, ...gridSize }}
                onPointerDown={(event) => { if (!targeting && canMoveToken(token)) { event.preventDefault(); event.stopPropagation(); event.currentTarget.setPointerCapture?.(event.pointerId); draggingTokenRef.current = { id: token.id, element: event.currentTarget, pointerId: event.pointerId, original: { latitude: token.latitude, longitude: token.longitude }, latest: { latitude: token.latitude, longitude: token.longitude },grid:token.grid_position?workspace.map?.grid:undefined,position:token.grid_position,combatActive:Boolean(battleState.encounter?.active),combatVersion:battleState.version }; } }}
                onClick={() => {
                  if (targeting) {
                    if (targeting.ring.gridded && targeting.ring.targets?.some(item => item.id === token.id)) chooseGridTarget(token);
                    return;
                  }
                  if(!gridClickSuppressRef.current) void openTokenDetails(token);
                }}
                title={`${token.name}${token.grid_position ? ` · célula ${token.grid_position.cell_x}, ${token.grid_position.cell_y}` : ` · latitude ${token.latitude.toFixed(2)} · longitude ${token.longitude.toFixed(2)}`}${conditions.length ? ` · ${conditions.join(", ")}` : ""}`}>
              {token.sprite ? <AnimatedSprite asset={token.sprite} point={{...visual,map_id:token.map_id}} fallback={image ? <img src={image} alt="" draggable={false}/> : <i>{token.name.slice(0,1)}</i>}/> : image ? <img src={image} alt="" draggable={false} /> : <i>{token.sheet?.marker || token.name.slice(0, 1).toUpperCase()}</i>}{hpMaximum != null && hpMaximum > 0 ? <span className="workspace-pin-health"><span className="workspace-pin-health-track" role="progressbar" aria-label={`Vida de ${token.name}`} aria-valuenow={hpCurrent ?? 0} aria-valuemin={0} aria-valuemax={hpMaximum}><span style={{ width: `${Math.max(0, Math.min(100, Number(hpCurrent || 0) / hpMaximum * 100))}%` }} /></span><span className="workspace-pin-health-number">{hpCurrent ?? "—"}/{hpMaximum}</span></span> : <strong>{token.name}</strong>}
              {token.tactical_attack_bonus ? <small className="workspace-pin-diagonal-bonus" title="+2 nos ataques por aliados em diagonal ou flanqueamento; não acumula">+{token.tactical_attack_bonus}</small> : null}
              <ActiveEffectIcons state={battleState} targetId={token.character_id || token.id} targetType={token.character_id ? 'character' : 'token'} interactive={false} />
              {token.sheet?.corpse && <small className="workspace-pin-corpse-label">Cadáver</small>}
            </button>; })}
            {renderedMapTokens.map(token=>{const point=tokenProjection(workspace.map?.grid,token.grid_position,token);return <MapLootChest key={'loot:'+token.id} token={token} left={point.longitude} top={point.latitude} disabled={Boolean(busy||targeting||(mode==='gm'&&view==='maps'&&fogEditing))} onCollect={()=>void collectMapLoot(token)}/>;})}
          </div>
        </div>
        <footer><span><i className="online" /> Mesa sincronizada</span><span>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} jogadores online</span><span>{visibleTimeline.length} eventos exibidos · {ledger.length} carregados</span>{mode === 'gm' && <button onClick={() => setIncludeStateRecords(value => !value)} aria-pressed={includeStateRecords}>{includeStateRecords ? 'Ocultar estados' : 'Incluir estados'}</button>}</footer>
      </main>}

      {(view === "table" || view === "maps") && <aside className="workspace-timeline-panel">
        <header><div><small>{view === "maps" ? "REGISTRO DO MAPA" : "REGISTRO DA SESSÃO"}</small><h2>{view === "maps" ? "Ações no mapa" : "Ações e conversa"}</h2></div><div className="workspace-log-tools"><button type="button" aria-label="Filtros do registro" aria-expanded={logFiltersOpen} aria-controls="workspace-log-filters" data-active={Boolean(logActor || logQuery || logKind !== 'all')} onClick={() => setLogFiltersOpen(value => !value)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h18l-7 8v7l-4 2v-9Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /></svg></button><span title="Eventos exibidos / registros carregados; não é o total do banco.">{visibleTimeline.length}/{ledger.length}</span></div></header>
        {logFiltersOpen && <section id="workspace-log-filters" className="workspace-log-filters" aria-label="Filtros do registro">
          <select aria-label="Filtrar registro por personagem" value={logActor} onChange={event => setLogActor(event.target.value)}><option value="">Todos os personagens</option>{logActors.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select>
          <select aria-label="Tipo de registro" value={logKind} onChange={event => setLogKind(event.target.value as 'all' | 'actions')}><option value="all">Ações e conversa</option><option value="actions">Só ações e rolagens</option></select>
          <input type="search" aria-label="Buscar no registro" placeholder="Buscar ação, magia ou resultado…" value={logQuery} onChange={event => setLogQuery(event.target.value)} />
          <button type="button" onClick={() => { setLogActor(''); setLogKind('all'); setLogQuery(''); }}>Limpar filtros</button>
        </section>}
        <form className="workspace-log-composer" onSubmit={submitMessage}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder={view === "maps" ? "Registrar observação do mapa…" : "Escreva sua mensagem…"} /><button disabled={!message.trim() || Boolean(busy)}>Enviar</button></form>
<div className="workspace-timeline" ref={timelineRef}>{visibleTimeline.length ? visibleTimeline.map((entry) => <article key={entry.id} className={entry.kind}><div><i>{entry.kind === "roll" ? "◈" : entry.kind === "message" ? "✦" : entry.kind === "state" ? "±" : "→"}</i><time>{formatClock(entry.timestamp)}</time></div><section><header><strong style={{ color: characterColor(entry.actorId) }}>{entry.actor}</strong><small>{entry.kind === "roll" ? "rolagem" : entry.kind === "message" ? "mensagem" : entry.kind === "state" ? "estado" : "ação"}</small></header><p><ActionTitle title={entry.title} cards={entry.cards} /></p>{entry.summary && <p>{entry.summary}</p>}{entry.detail && !['action', 'roll'].includes(entry.kind) && <pre>{entry.detail}</pre>}{['action', 'roll'].includes(entry.kind) && <SheetDetail title={`Resultado: ${entry.title}`} description={[`${entry.actor} · ${formatClock(entry.timestamp)}`, entry.title, entry.detail].filter(Boolean).join('\n\n')} showIcon={false}>Ver resultado</SheetDetail>}</section></article>) : <p className="workspace-empty-log">{timeline.length ? 'Nenhum registro corresponde aos filtros.' : 'O registro da sessão começará com a primeira ação ou mensagem.'}</p>}</div>
      </aside>}
    </div>
    {attackResolution && !attackResolution.confirmed && !attackResolution.breakdown.automatic_hit && <div className="workspace-combat-result-dock" role="presentation" onClick={() => { if (attackResolution.confirmed) setAttackResolution(null); }}><section className="workspace-item-modal" role="dialog" aria-modal="false" aria-label="Resolução do ataque" onClick={(event) => event.stopPropagation()}><header><div><small>RESOLUÇÃO DO ATAQUE</small><h2>{attackResolution.actor_name} → {attackResolution.target_name}</h2></div><button type="button" onClick={() => setAttackResolution(null)} aria-label="Fechar resolução">×</button></header>{!attackResolution.confirmed && <p role="status"><strong>Dano ainda não aplicado.</strong> Confirme abaixo para atualizar a vida do alvo.</p>}<div className="workspace-token-modal-meta"><span>{attackResolution.roll_mode === "physical" ? "Dado físico" : "Rolagem digital"}: {attackResolution.d20}</span><span>Bônus: {attackResolution.attack_bonus >= 0 ? "+" : ""}{attackResolution.attack_bonus}</span><span>Total: {attackResolution.attack_total}</span><span>CA: {attackResolution.target_ac}</span></div><div className="workspace-item-modal-meta"><strong>{attackResolution.result === "hit" ? "ACERTO" : "ERRO"}</strong><span>Dano: {attackResolution.damage_total} ({attackResolution.damage_formula})</span>{attackResolution.confirmed && <span>HP: {attackResolution.hp_before} → {attackResolution.hp_after}</span>}</div>{attackResolution.breakdown.life_drain && <p role="status">{attackResolution.breakdown.drain_result ? `Drenagem: ${attackResolution.breakdown.drain_result.drained} PV · Raziel: ${attackResolution.breakdown.drain_result.hp_before} → ${attackResolution.breakdown.drain_result.hp_after} (+${attackResolution.breakdown.drain_result.healed})` : "Ao confirmar, a cura será limitada ao dano efetivamente drenado e aos PV máximos de Raziel."}</p>}{attackResolution.breakdown.strikes?.map((strike, index) => <p key={index}>Golpe {index + 1}: d20 {strike.d20} + {attackResolution.attack_bonus} = {strike.attack_total} · {strike.result === "hit" ? "Acerto" : "Erro"} · dano {strike.damage_total}</p>)}<p>Base {attackResolution.breakdown.attack?.base_bonus ?? 0} · equipamento {Number(attackResolution.breakdown.attack?.equipment_bonus || 0) >= 0 ? "+" : ""}{attackResolution.breakdown.attack?.equipment_bonus ?? 0} · efeitos {Number(attackResolution.breakdown.attack?.effect_bonus || 0) >= 0 ? "+" : ""}{attackResolution.breakdown.attack?.effect_bonus ?? 0}{attackResolution.breakdown.equipment?.length ? ` · ${attackResolution.breakdown.equipment.map((item) => item.item_title).join(" + ")}` : ""}</p>{attackResolution.confirmed ? <button type="button" onClick={() => setAttackResolution(null)}>Concluído</button> : <button type="button" disabled={Boolean(busy)} onClick={() => void confirmResolvedAttack()}>{busy.startsWith("confirm:") ? "Aplicando…" : "Confirmar resultado e aplicar dano"}</button>}</section></div>}
    {damageChoicePrompt && <TargetConfirmation action="Ataque" target={workspace.tokens.find(t=>t.id===damageChoicePrompt.targetId)?.name || 'Alvo'} busy={Boolean(busy)} confirmDisabled={(weaponDamageChoices(weaponForDamageChoice(damageChoicePrompt.attackId)).length>0&&!damageChoicePrompt.damageType)||Boolean(damageChoicePrompt.requiresTower&&typeof damageChoicePrompt.towerProtectedSide!=='boolean')} onNo={()=>setDamageChoicePrompt(null)} onYes={()=>{const prompt=damageChoicePrompt;setDamageChoicePrompt(null);const target=workspace.tokens.find(t=>t.id===prompt.targetId);if(target)void resolveSelectedAttack(prompt.attackId,target,prompt.automatic,prompt.damageType,prompt.towerProtectedSide);else setError('Alvo indisponível; selecione novamente.');}}><AttackDirectionChoice required={Boolean(damageChoicePrompt.requiresTower)} value={damageChoicePrompt.towerProtectedSide} onChange={towerProtectedSide=>setDamageChoicePrompt(current=>current?{...current,towerProtectedSide}:null)}/><WeaponDamageChoice choices={weaponDamageChoices(weaponForDamageChoice(damageChoicePrompt.attackId))} value={damageChoicePrompt.damageType} onChange={damageType=>setDamageChoicePrompt(current=>current?{...current,damageType}:null)}/></TargetConfirmation>}
    {targetConfirmation && targeting?.armId===targetConfirmation.armId && <TargetConfirmation key={`${targetConfirmation.armId}:${targetConfirmation.targetId}:${Boolean(targetConfirmation.repeat)}`} action={targeting.actionLabel} target={targetConfirmation.name} busy={Boolean(busy)} message={targetConfirmation.dispel?'Confirmar a tentativa de dissipação? O teste será rolado e o efeito encerrado em caso de sucesso.':targetConfirmation.contact?.kind==='disintegration'?'Confirmar contato? O alvo será desintegrado sem ataque nem JP.':targetConfirmation.contact?.kind==='rust'?'Escolha o equipamento que recebe o contato. Acerto e corrosão serão resolvidos automaticamente.':undefined} confirmDisabled={(confirmingTower && typeof targetConfirmation.towerProtectedSide!=='boolean')||(confirmingDamageChoices.length > 0 && !targetConfirmation.damageType)||(targetConfirmation.contact?.kind==='rust'&&!targetConfirmation.rustChoice)||Boolean(targetConfirmation.dispel&&!targetConfirmation.dispelEffectId)} onYes={()=>confirmTargeting(targetConfirmation.targetId)} onRemove={targetConfirmation.repeat ? ()=>{const current=targetingRef.current;if(current){const next={...current,selectedIds:current.selectedIds.filter(id=>id!==targetConfirmation.targetId),selectedId:null};targetingRef.current=next;setTargeting(next);}setTargetConfirmation(null);} : undefined} onNo={()=>{setTargetConfirmation(null);if(!targetConfirmation.repeat){targetingRef.current=null;window.dispatchEvent(new CustomEvent("omnisvera-targeting-clear",{detail:{armId:targetConfirmation.armId}}));}}} ><AttackDirectionChoice required={confirmingTower} value={targetConfirmation.towerProtectedSide} onChange={towerProtectedSide=>setTargetConfirmation(current=>current?{...current,towerProtectedSide}:null)}/><WeaponDamageChoice choices={confirmingDamageChoices} value={targetConfirmation.damageType} onChange={damageType=>setTargetConfirmation(current=>current?{...current,damageType}:null)}/>{targetConfirmation.dispel&&<DispelEffectOptions effects={targetConfirmation.dispel.effects} selected={targetConfirmation.dispelEffectId} onChange={dispelEffectId=>setTargetConfirmation(previous=>previous?{...previous,dispelEffectId}:previous)} />}{targetConfirmation.contact?.kind==='rust'&&<RustContactOptions items={targetConfirmation.contact.inventory} disabled={Boolean(busy)} onChange={rustChoice=>setTargetConfirmation(previous=>previous?{...previous,rustChoice}:previous)} />}</TargetConfirmation>}
    {attackResolution && !attackResolution.confirmed && attackResolution.breakdown.automatic_hit && <SpellResolution resolution={attackResolution} busy={Boolean(busy)} onConfirm={() => void confirmResolvedAttack()} onClose={() => setAttackResolution(null)} />}
    {effectBreakdownOpen && <EffectBreakdownModal title={effectBreakdownOpen === "armor" ? "Classe de Armadura" : ATTRIBUTES.find(([key]) => key === effectBreakdownOpen)?.[1] || effectBreakdownOpen} base={effectBreakdownOpen === "armor" ? definition?.defenses?.unmodified_armor_class ?? definition?.defenses?.base_armor_class : definition?.base_attributes?.[effectBreakdownOpen]} effective={effectBreakdownOpen === "armor" ? definition?.defenses?.armor_class : definition?.attributes?.[effectBreakdownOpen]} entries={openBreakdownEntries} onClose={() => setEffectBreakdownOpen(null)} onRoll={effectBreakdownOpen !== "armor" ? () => { const key = effectBreakdownOpen; setEffectBreakdownOpen(null); void roll("attribute", key); } : undefined} />}
{openToken?.token_type === "location" && <div className="workspace-token-modal-backdrop" onClick={() => setOpenTokenId(null)}><section className="workspace-token-modal" role="dialog" aria-label={`Local ${openToken.name}`} onClick={e => e.stopPropagation()}><header><h2>{openToken.name}</h2><button onClick={() => setOpenTokenId(null)}>Fechar local</button></header>{openToken.image_path && <img src={mediaUrlFromVaultPath(openToken.image_path)} alt="" width={96} />}<p>{openToken.sheet?.description}</p>
<MapCommerce key={openToken.id} tokenId={openToken.id} tokenName={openToken.name} characterId={character?.access_level !== "public" ? selectedId : ""} mode={mode} onChange={async()=>{await loadOverview();await loadCharacter();}} onInspectNpc={id=>setOpenTokenId(id)}/>
<small>{openToken.latitude.toFixed(1)}, {openToken.longitude.toFixed(1)}</small></section></div>}
    {openToken && openToken.token_type !== "location" && <div className="workspace-token-modal-backdrop" style={{display:targeting?"none":undefined}} role="presentation" onClick={() => setOpenTokenId(null)}><section className={`workspace-token-modal ${openToken.sheet?.summon?.technique === "animar-mortos" ? "reanimated" : ""}`} role="dialog" aria-modal="true" aria-label={`Ficha de ${openToken.name}`} onClick={(event) => event.stopPropagation()}><header><div><small>{openToken.token_type === "monster" ? "MONSTRO / NPC" : "PERSONAGEM"}</small><h2 style={{ color: openToken.color }}>{openToken.name}</h2></div><button type="button" onClick={() => setOpenTokenId(null)} aria-label="Fechar ficha">×</button></header>{mode === "gm" && referenceToken?.id === openToken.id && <div className="workspace-reference-actions"><button type="button" onClick={() => setOpenTokenId(null)}>Voltar para NPCs</button><button type="button" disabled={Boolean(busy || battleState.encounter?.active)} onClick={() => { void changeWorkspaceMap(openToken.map_id || "default").then(() => { setOpenTokenId(null); window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "maps" })); }).catch(() => {}); }}>Abrir mapa deste NPC</button></div>}
{mode==='gm'&&openToken.sheet?.embedded_in_location&&<div className="workspace-reference-actions"><small>{openToken.sheet.rank&&`Rank ${openToken.sheet.rank} · `}Nv. {openToken.sheet.level}</small><button type="button" onClick={()=>setOpenTokenId(openToken.sheet!.embedded_in_location!)}>Voltar ao Conclave</button></div>}
{!openToken.sheet?.embedded_in_location&&<MapCommerce key={openToken.id} tokenId={openToken.id} tokenName={openToken.name} characterId={character?.access_level !== "public" ? selectedId : ""} mode={mode} onChange={async()=>{await loadOverview();await loadCharacter();}} />}
{mode==='gm'&&(Boolean(openToken.sheet?.spell_repertoire?.length)||['esfera-da-aniquilacao','monstro-ferrugem','flagelo-da-podridao','morcego'].includes(openToken.sheet?.source?.monster_id||''))&&<MonsterAttackPanel key={`special:${openToken.id}`} token={openToken} characters={characters} targets={workspace.tokens} physical={workspace.table_mode === "physical"} combat={battleState} gridded={Boolean(openToken.grid_position)} onChange={refresh} />}<SkeletonReward token={openToken} />{(workspace.tokens.some(token => token.id === openToken.id) || openToken.sheet?.summon?.caster===selectedId) && <SummonControls token={openToken} mode={mode} characters={characters} tokens={workspace.tokens} state={battleState} physical={workspace.table_mode === "physical"} onChange={async () => { await loadOverview(); setBattleState(await getCombatEffects()); }} />}<TokenVitals key={`${openToken.id}:${openToken.current_hp}:${openToken.maximum_hp}`} token={openToken} editable={mode === "gm" && workspace.tokens.some(token => token.id === openToken.id)} onChange={async () => { await loadOverview(); }} />{loadingTokenDetail ? <p>Carregando ficha…</p> : <><div className="workspace-token-modal-vitals"><strong>VIDA {openCharacterDetail?.state?.current_hp ?? openToken.current_hp ?? "—"} / {openCharacterDetail?.state?.maximum_hp ?? openToken.maximum_hp ?? "—"}</strong><span>{(openCharacterDetail?.state?.conditions || openToken.conditions).length ? (openCharacterDetail?.state?.conditions || openToken.conditions).join(" · ") : "STATUS - Nenhum"}</span></div><div className="workspace-token-modal-meta"><span>Mapa: {openToken.map_id || "default"}</span><span>Latitude: {openToken.latitude.toFixed(2)}</span><span>Longitude: {openToken.longitude.toFixed(2)}</span>{openCharacterDetail ? <><span>Classe: {openCharacterDetail.definition.class_name}</span><span>Nível: {openCharacterDetail.definition.level}</span><span>CA: <ArmorClassValue defenses={openCharacterDetail.definition.defenses} inventory={openCharacterDetail.inventory} /></span></> : <><span>Função: {openToken.sheet?.role || "Inimigo"}</span><span>Nível: {openToken.sheet?.level ?? "—"}</span><span>CA: {openToken.sheet?.armor_class ?? "—"}</span><span>Iniciativa: {openToken.sheet?.initiative ?? "—"}</span></>}</div>{openCharacterDetail ? <div className="workspace-token-modal-body"><p>{openCharacterDetail.definition.epithet || openCharacterDetail.definition.race}</p><h3>Ataques</h3>{openCharacterDetail.definition.attacks?.map((attack) => <p key={attack.id}>{attack.name} · {attack.damage || "dano não configurado"}</p>)}</div> : <div className="workspace-token-modal-body">{openToken.sheet?.description && <p>{openToken.sheet.description}</p>}{(openToken.sheet?.attacks || []).length > 0 && <><h3>Ataques</h3>{openToken.sheet?.attacks?.map((attack, index) => <p key={`${attack.name}-${index}`}>{attack.name} · {attack.damage || "dano não configurado"}{attack.bonus ? ` · ${attack.bonus}` : ""}{attack.notes ? ` · ${attack.notes}` : ""}</p>)}</>}{(openToken.sheet?.abilities || []).length > 0 && <><h3>Habilidades</h3>{openToken.sheet?.abilities?.map((ability) => <p key={ability}>{ability}</p>)}</>}{openToken.sheet?.notes && <><h3>Notas</h3><p>{openToken.sheet.notes}</p></>}</div>}</>}</section></div>}
    {openItem && <div className="workspace-item-modal-backdrop" role="presentation" onClick={() => setOpenItem(null)}><section className="workspace-item-modal" role="dialog" aria-modal="true" aria-label={`Informações de ${cleanItemDisplayName(openItem.item_title)}`} onClick={(event) => event.stopPropagation()}><header><div>{mediaUrlFromVaultPath(openItem.thumbnail || openItem.cover || iconPathForItem(openItem.item_title, openItem.item_type)) && <img src={mediaUrlFromVaultPath(openItem.thumbnail || openItem.cover || iconPathForItem(openItem.item_title, openItem.item_type))} alt="" />}<div><small>{openItem.item_type || "Item"}</small><h2>{cleanItemDisplayName(openItem.item_title)}</h2></div></div><button type="button" onClick={() => setOpenItem(null)} aria-label="Fechar informações do item">×</button></header><div className="workspace-item-modal-meta"><span>{openItem.equipped ? `Equipado${openItem.equipment_slot ? ` · ${openItem.equipment_slot}` : ""}` : "Guardado"}</span><span>Quantidade: {inventoryQuantity(openItem)}</span>{openItem.damage_formula && <span>Dano: {openItem.damage_formula}</span>}</div>{carriedItems.some(item => item.item_path === openItem.item_path) && canOperate && <div className="workspace-item-modal-equipment">{(character?.inventory.find(item => item.item_path === openItem.item_path) || openItem).equipped ? <button disabled={Boolean(busy)} onClick={() => void stateAction("unequip_item", {item_path:openItem.item_path}, `Guardou ${cleanItemDisplayName(openItem.item_title)}`)}>Guardar</button> : <div className="workspace-equip-menu">{possibleEquipmentSlots(openItem).map(slot => <button type="button" key={slot} disabled={Boolean(busy)} onClick={() => void stateAction("equip_item", {item_path:openItem.item_path,equipment_slot:slot}, `Equipou ${cleanItemDisplayName(openItem.item_title)} · ${slot}`)}>Equipar em {slot}</button>)}</div>}</div>}{error && <p role="alert">{error}</p>}{openItem.description && <p>{openItem.description}</p>}{(openItem.effects || []).length > 0 && <div><h3>Efeitos</h3>{openItem.effects?.map((effect) => <p key={effect}>{effect}</p>)}</div>}{(openItem.effect_rules || []).length > 0 && <div><h3>Efeitos automáticos</h3>{openItem.effect_rules?.map((rule) => <p key={rule.id}>{describeItemRule(rule)}</p>)}</div>}{openItem.notes && <div><h3>Notas</h3><p>{openItem.notes}</p></div>}</section></div>}
    <DiceTray mode={mode} triggerHidden targetTokens={workspace.tokens} />
  </section>;
}
