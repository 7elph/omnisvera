import { useEffect, useMemo, useState } from "react";
import {
  applyCharacterStateAction,
  CharacterEvent,
  getPlayableCharacter,
  InventoryItem,
  listCharacterEvents,
  listNotes,
  listPlayableCharacters,
  mediaUrlFromVaultPath,
  NoteSummary,
  PlayableCharacter,
  PlayableCharacterDefinition,
  PlayableCharacterSummary,
  revertCharacterEvent,
  updateCharacterDefinition,
} from "../api";
import CharacterSheetBuilder from "./CharacterSheetBuilder";

type CharacterTab = "summary" | "mechanics" | "combat" | "inventory" | "abilities" | "story" | "gm";

const TAB_LABELS: Array<{ key: CharacterTab; icon: string; label: string }> = [
  { key: "summary", icon: "✦", label: "Resumo" },
  { key: "mechanics", icon: "⚙", label: "Mecânicas" },
  { key: "combat", icon: "⚔", label: "Combate" },
  { key: "inventory", icon: "◈", label: "Inventário" },
  { key: "abilities", icon: "✧", label: "Habilidades e Magias" },
  { key: "story", icon: "⌘", label: "História e Relações" },
  { key: "gm", icon: "♛", label: "Mestre" },
];

const ATTRIBUTE_LABELS: Record<string, string> = {
  strength: "FOR",
  dexterity: "DES",
  constitution: "CON",
  intelligence: "INT",
  wisdom: "SAB",
  charisma: "CAR",
};

const EVENT_LABELS: Record<string, string> = {
  damage: "Dano aplicado",
  heal: "Cura aplicada",
  set_hp: "PV definido",
  add_condition: "Condição adicionada",
  remove_condition: "Condição removida",
  consume_resource: "Recurso consumido",
  restore_resource: "Recurso restaurado",
  equip_item: "Item equipado",
  unequip_item: "Item desequipado",
  change_quantity: "Quantidade alterada",
  grant_item: "Item concedido",
  remove_item: "Item removido",
  set_location: "Localização atualizada",
  set_session_notes: "Observação de sessão atualizada",
  definition_update: "Definição atualizada",
};

function shown(value: unknown, fallback = "Não informado") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function signed(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value >= 0 ? `+${value}` : String(value);
}

function Portrait({ character, compact = false }: { character: PlayableCharacterDefinition | PlayableCharacterSummary; compact?: boolean }) {
  const [failed, setFailed] = useState(false);
  const src = mediaUrlFromVaultPath(character.portrait);
  return (
    <div className={`playable-portrait ${compact ? "compact" : ""} ${failed || !src ? "fallback" : ""}`}>
      {!failed && src ? <img src={src} alt={`Retrato de ${character.name}`} onError={() => setFailed(true)} /> : <span aria-label="Retrato não disponível">♙</span>}
    </div>
  );
}

function TextBlock({ value, empty = "Ainda não informado." }: { value?: string | null; empty?: string }) {
  if (!value?.trim()) return <p className="sheet-empty">{empty}</p>;
  const normalized = value
    .replace(/\r/g, "")
    .replace(/^\s*---\s*$/gm, "")
    .replace(/^\s*#{1,6}\s*/gm, "")
    .replace(/\s+\*\*([^*]+):\*\*\s*/g, "\n$1: ")
    .replace(/\*\*|__/g, "")
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
    .replace(/\[\[([^\]]+)\]\]/g, (_match, target: string) => target.split("/").pop() || target)
    .replace(/\s+-\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])/g, "\n- ")
    .trim();
  const lines = normalized.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const blocks: Array<{ kind: "list" | "paragraph"; values: string[] }> = [];
  for (const line of lines) {
    const isList = /^[-*]\s+/.test(line);
    const clean = line.replace(/^[-*]\s+/, "").trim();
    const current = blocks.at(-1);
    if (isList && current?.kind === "list") current.values.push(clean);
    else if (!isList && current?.kind === "paragraph" && !/^[^:]{1,40}:\s/.test(clean) && !/^[^:]{1,40}:\s/.test(current.values[0])) current.values[0] += ` ${clean}`;
    else blocks.push({ kind: isList ? "list" : "paragraph", values: [clean] });
  }
  return <div className="playable-text-block">{blocks.map((block, index) => block.kind === "list"
    ? <ul key={`list-${index}`}>{block.values.map((item) => <li key={item}>{item}</li>)}</ul>
    : <p key={`paragraph-${index}`}>{block.values[0]}</p>)}</div>;
}

function QuickStat({ label, value, accent = false }: { label: string; value: unknown; accent?: boolean }) {
  return <span className={accent ? "accent" : ""}><small>{label}</small><strong>{shown(value, "—")}</strong></span>;
}

function SummaryTab({ character }: { character: PlayableCharacter }) {
  const { definition, state } = character;
  return <div className="playable-tab-grid summary-tab">
    <section className="sheet-card span-2"><h3>Quem é</h3><TextBlock value={definition.public_description} /></section>
    <section className="sheet-card"><h3>Estado atual</h3><dl className="definition-list">
      <div><dt>Local</dt><dd>{shown(state?.location || definition.location)}</dd></div>
      <div><dt>Situação</dt><dd>{shown(definition.current_status)}</dd></div>
      <div><dt>Cânone</dt><dd>{shown(definition.canonical_state)}</dd></div>
      <div><dt>Campanha</dt><dd>{shown(definition.campaign)}</dd></div>
    </dl></section>
    <section className="sheet-card"><h3>Condições</h3>{state?.conditions.length ? <div className="condition-cloud">{state.conditions.map((condition) => <span key={condition}>{condition}</span>)}</div> : <p className="sheet-empty">Nenhuma condição ativa.</p>}</section>
    <section className="sheet-card span-2"><h3>Objetivos</h3><TextBlock value={definition.goals} /></section>
  </div>;
}

function MechanicsTab({ character }: { character: PlayableCharacter }) {
  const { definition } = character;
  const attributes = definition.attributes || {};
  return <div className="playable-tab-grid">
    <section className="sheet-card span-2"><h3>Atributos</h3><div className="attribute-grid">
      {Object.entries(ATTRIBUTE_LABELS).map(([key, label]) => <article key={key}><small>{label}</small><strong>{shown(attributes[key], "—")}</strong><em>{signed(definition.attribute_modifiers?.[key])}</em></article>)}
    </div></section>
    <section className="sheet-card"><h3>Defesas</h3><dl className="definition-list">
      <div><dt>Classe de Armadura</dt><dd>{shown(definition.defenses?.armor_class)}</dd></div>
      <div><dt>Jogada de Proteção</dt><dd>{shown(definition.defenses?.saving_throw)}</dd></div>
      <div><dt>Iniciativa</dt><dd>{definition.defenses?.initiative_configured ? signed(definition.defenses.initiative) : "Não configurada"}</dd></div>
    </dl></section>
    <section className="sheet-card"><h3>Progressão</h3><dl className="definition-list">
      <div><dt>Nível</dt><dd>{shown(definition.level)}</dd></div>
      <div><dt>Experiência</dt><dd>{shown(definition.progression?.experience)}</dd></div>
      <div><dt>Base de Ataque</dt><dd>{signed(definition.progression?.base_attack)}</dd></div>
      <div><dt>Deslocamento</dt><dd>{shown(definition.movement)}</dd></div>
    </dl></section>
    <section className="sheet-card span-2"><h3>Descrição física</h3><TextBlock value={definition.physical_description} /></section>
  </div>;
}

function CombatTab({ character, mode, onAction }: { character: PlayableCharacter; mode: "player" | "gm"; onAction: (action: string, payload: Record<string, unknown>) => Promise<void> }) {
  const [amount, setAmount] = useState(1);
  const [condition, setCondition] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const state = character.state;

  async function act(action: string, payload: Record<string, unknown>) {
    setBusy(true); setError("");
    try { await onAction(action, payload); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível atualizar."); }
    finally { setBusy(false); }
  }

  return <div className="playable-tab-grid">
    <section className="sheet-card hp-control-card">
      <h3>Pontos de Vida</h3>
      <div className="hp-display"><strong>{shown(state?.current_hp, "—")}</strong><span>/ {shown(state?.maximum_hp, "—")}</span>{state?.temporary_hp ? <em>+{state.temporary_hp} temp.</em> : null}</div>
      {character.permissions.edit_state && <><label>Valor<input aria-label="Valor de PV" type="number" min="0" value={amount} onChange={(event) => setAmount(Math.max(0, Number(event.target.value)))} /></label><div className="compact-actions"><button disabled={busy} className="danger-button" onClick={() => void act("damage", { amount })}>Aplicar dano</button><button disabled={busy} onClick={() => void act("heal", { amount })}>Curar</button><button disabled={busy} className="secondary-button" onClick={() => void act("set_hp", { value: amount })}>Definir PV</button></div></>}
    </section>
    <section className="sheet-card"><h3>Condições</h3><div className="condition-cloud">{state?.conditions.map((item) => <button title="Remover condição" key={item} disabled={busy} onClick={() => void act("remove_condition", { condition: item })}>{item} ×</button>)}</div>{character.permissions.edit_state && <div className="inline-control"><input aria-label="Nova condição" value={condition} placeholder="Ex.: Caído" onChange={(event) => setCondition(event.target.value)} /><button disabled={!condition.trim() || busy} onClick={() => { void act("add_condition", { condition }); setCondition(""); }}>Adicionar</button></div>}</section>
    <section className="sheet-card span-2"><h3>Recursos</h3>{state?.resources.length ? <div className="resource-grid">{state.resources.map((resource) => <article key={resource.key}><span><strong>{resource.label}</strong><small>{resource.current} / {resource.maximum}</small></span><div><button disabled={busy || resource.current <= 0} onClick={() => void act("consume_resource", { resource_key: resource.key, amount: 1 })}>− Usar</button>{mode === "gm" && <button disabled={busy || resource.current >= resource.maximum} onClick={() => void act("restore_resource", { resource_key: resource.key, amount: 1 })}>+ Restaurar</button>}</div></article>)}</div> : <p className="sheet-empty">Nenhum recurso consumível confirmado para esta ficha.</p>}</section>
    <section className="sheet-card span-2"><h3>Ataques</h3>{character.definition.attacks?.length ? <div className="attack-grid">{character.definition.attacks.map((attack) => <article key={attack.id}><span><strong>{attack.name}</strong><em>{signed(attack.attack_bonus)}</em></span><dl><div><dt>Dano</dt><dd>{shown(attack.damage, "Não configurado")}</dd></div><div><dt>Alcance</dt><dd>{shown(attack.range, "Não configurado")}</dd></div></dl><small>{attack.notes}</small></article>)}</div> : <p className="sheet-empty">Ataques ainda não configurados.</p>}<TextBlock value={character.definition.attack_notes} /></section>
    {error && <p className="warning-text span-2">{error}</p>}
  </div>;
}

function InventoryCard({ item, canEdit, isGm, busy, onAction }: { item: InventoryItem; canEdit: boolean; isGm: boolean; busy: boolean; onAction: (action: string, payload: Record<string, unknown>) => Promise<void> }) {
  const [quantity, setQuantity] = useState(item.quantity);
  useEffect(() => setQuantity(item.quantity), [item.quantity]);
  const image = mediaUrlFromVaultPath(item.thumbnail || item.cover);
  return <article className={`sheet-inventory-card ${item.equipped ? "equipped" : ""}`}>
    {image ? <img src={image} alt={item.item_title} /> : <span className="inventory-item-placeholder" aria-hidden="true">◈</span>}
    <div><strong>{item.item_title}</strong><small>{item.equipped ? "Equipado" : "Guardado"}</small>{item.notes && <p>{item.notes}</p>}</div>
    {canEdit && <div className="inventory-card-actions"><button disabled={busy} onClick={() => void onAction(item.equipped ? "unequip_item" : "equip_item", { item_path: item.item_path })}>{item.equipped ? "Desequipar" : "Equipar"}</button><label>Qtd.<input type="number" min="0" max="999" value={quantity} onChange={(event) => setQuantity(Math.max(0, Number(event.target.value)))} /></label><button disabled={busy || quantity === item.quantity} className="secondary-button" onClick={() => void onAction("change_quantity", { item_path: item.item_path, quantity })}>Salvar</button>{isGm && <button disabled={busy} className="danger-button subtle" onClick={() => void onAction("remove_item", { item_path: item.item_path })}>Remover</button>}</div>}
  </article>;
}

function InventoryTab({ character, mode, availableItems, onAction }: { character: PlayableCharacter; mode: "player" | "gm"; availableItems: NoteSummary[]; onAction: (action: string, payload: Record<string, unknown>) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [noteId, setNoteId] = useState("");
  const [quantity, setQuantity] = useState(1);
  async function act(action: string, payload: Record<string, unknown>) { setBusy(true); setError(""); try { await onAction(action, payload); } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível atualizar o inventário."); } finally { setBusy(false); } }
  return <div className="inventory-tab">
    <section className="sheet-card"><h3>Recursos carregados</h3><dl className="definition-list"><div><dt>Moedas</dt><dd>{shown(character.state?.coins)}</dd></div></dl>{character.definition.base_equipment?.length ? <><h4>Equipamento-base confirmado</h4><div className="condition-cloud">{character.definition.base_equipment.map((item) => <span key={item}>{item}</span>)}</div></> : <p className="sheet-empty">Equipamento-base ainda não informado.</p>}</section>
    {mode === "gm" && <section className="sheet-card grant-item-form"><div><h3>Conceder item</h3><p>Adiciona ao estado do Companion sem editar a nota do personagem.</p></div><select aria-label="Item para conceder" value={noteId} onChange={(event) => setNoteId(event.target.value)}><option value="">Escolha um item...</option>{availableItems.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select><input aria-label="Quantidade do item" type="number" min="1" max="999" value={quantity} onChange={(event) => setQuantity(Math.max(1, Number(event.target.value)))} /><button disabled={!noteId || busy} onClick={() => void act("grant_item", { note_id: Number(noteId), quantity })}>Conceder</button></section>}
    <div className="sheet-inventory-grid">{character.inventory.length ? character.inventory.map((item) => <InventoryCard key={item.id} item={item} canEdit={character.permissions.edit_state} isGm={mode === "gm"} busy={busy} onAction={act} />) : <p className="sheet-empty">Inventário vazio.</p>}</div>
    {error && <p className="warning-text">{error}</p>}
  </div>;
}

function AbilitiesTab({ character }: { character: PlayableCharacter }) {
  const abilities = character.definition.abilities || {};
  return <div className="playable-tab-grid"><section className="sheet-card"><h3>Habilidades raciais</h3><TextBlock value={abilities.racial} /></section><section className="sheet-card"><h3>Habilidades de classe</h3><TextBlock value={abilities.class} /></section><section className="sheet-card span-2"><h3>Magias, fórmulas ou técnicas</h3><TextBlock value={abilities.magic} empty="Nenhuma magia ou técnica confirmada nesta ficha." />{abilities.magic_notes && <aside className="rule-note">{abilities.magic_notes}</aside>}</section></div>;
}

function StoryTab({ character }: { character: PlayableCharacter }) {
  return <div className="playable-tab-grid"><section className="sheet-card span-2"><h3>História</h3><TextBlock value={character.definition.history} /></section><section className="sheet-card"><h3>Personalidade</h3><TextBlock value={character.definition.personality} /></section><section className="sheet-card"><h3>Relações</h3><TextBlock value={character.definition.relationships} /></section></div>;
}

function GmTab({ character, events, onDefinition, onAction, onRevert }: { character: PlayableCharacter; events: CharacterEvent[]; onDefinition: (fields: Record<string, unknown>) => Promise<void>; onAction: (action: string, payload: Record<string, unknown>) => Promise<void>; onRevert: (eventId: number) => Promise<void> }) {
  const definition = character.definition;
  const [draft, setDraft] = useState({
    epithet: definition.epithet || "", player_name: definition.player_name || "", campaign: definition.campaign || "Omnisvera",
    race: definition.race || "", class_name: definition.class_name || "", level: definition.level || 1,
    maximum_hp: definition.progression?.maximum_hp ?? "", armor_class: definition.defenses?.armor_class ?? "", initiative: definition.defenses?.initiative ?? "",
    movement: definition.movement || "", location: character.state?.location || definition.location || "", current_status: definition.current_status || "",
    notes: definition.gm_fields?.notes || "", private_state: definition.gm_fields?.private_state || "",
    strength: definition.attributes?.strength ?? "", dexterity: definition.attributes?.dexterity ?? "", constitution: definition.attributes?.constitution ?? "", intelligence: definition.attributes?.intelligence ?? "", wisdom: definition.attributes?.wisdom ?? "", charisma: definition.attributes?.charisma ?? "",
  });
  const [sessionNotes, setSessionNotes] = useState(character.state?.session_notes || "");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  useEffect(() => setSessionNotes(character.state?.session_notes || ""), [character.state?.session_notes]);

  async function saveDefinition() {
    setBusy(true); setFeedback("");
    try {
      await onDefinition({
        epithet: draft.epithet, player_name: draft.player_name, campaign: draft.campaign, race: draft.race,
        class_name: draft.class_name, level: Number(draft.level), maximum_hp: draft.maximum_hp === "" ? null : Number(draft.maximum_hp),
        armor_class: draft.armor_class === "" ? null : Number(draft.armor_class), initiative: draft.initiative === "" ? null : Number(draft.initiative),
        movement: draft.movement, location: draft.location, current_status: draft.current_status,
        attributes: Object.fromEntries(Object.keys(ATTRIBUTE_LABELS).map((key) => [key, Number(draft[key as keyof typeof draft])]).filter(([, value]) => Number.isFinite(value) && value > 0)),
        gm_fields: { notes: draft.notes, private_state: draft.private_state },
      });
      setFeedback("Definição local atualizada. O Vault não foi alterado.");
    } catch (reason) { setFeedback(reason instanceof Error ? reason.message : "Falha ao salvar definição."); }
    finally { setBusy(false); }
  }

  return <div className="gm-character-tab">
    <section className="sheet-card"><h3>Definição da ficha</h3><p className="rule-note">Sobrescritas locais para a mesa. Nenhum campo é escrito automaticamente no Vault.</p><div className="definition-editor-grid">
      {([['epithet','Alcunha'],['player_name','Jogador'],['campaign','Campanha'],['race','Raça'],['class_name','Classe'],['level','Nível'],['maximum_hp','PV máximo'],['armor_class','CA'],['initiative','Iniciativa'],['movement','Deslocamento'],['location','Localização'],['current_status','Estado atual']] as const).map(([key,label]) => <label key={key}>{label}<input type={['level','maximum_hp','armor_class','initiative'].includes(key) ? 'number' : 'text'} value={draft[key]} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} /></label>)}
    </div><h4>Atributos-base</h4><div className="attribute-editor">{Object.entries(ATTRIBUTE_LABELS).map(([key,label]) => <label key={key}>{label}<input type="number" min="1" max="30" value={draft[key as keyof typeof draft]} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} /></label>)}</div><label>Notas privadas do Mestre<textarea rows={5} value={draft.notes} onChange={(event) => setDraft({ ...draft, notes: event.target.value })} /></label><label>Estado privado<textarea rows={3} value={draft.private_state} onChange={(event) => setDraft({ ...draft, private_state: event.target.value })} /></label><button disabled={busy} onClick={() => void saveDefinition()}>Salvar definição local</button>{feedback && <p className="action-feedback">{feedback}</p>}</section>
    <section className="sheet-card"><h3>Observações de sessão</h3><textarea rows={6} value={sessionNotes} onChange={(event) => setSessionNotes(event.target.value)} /><button disabled={busy || sessionNotes === character.state?.session_notes} onClick={() => void onAction("set_session_notes", { value: sessionNotes })}>Salvar observações</button></section>
    <section className="sheet-card"><h3>Histórico auditável</h3>{events.length ? <div className="character-event-list">{events.map((event) => <article key={event.id}><span><strong>{EVENT_LABELS[event.event_type] || event.event_type}</strong><small>{new Date(event.created_at).toLocaleString("pt-BR")} · {event.actor_role}</small></span>{event.reason && <p>{event.reason}</p>}{event.reverted_at ? <em>Revertido</em> : <button disabled={busy} className="secondary-button" onClick={() => void onRevert(event.id)}>Reverter</button>}</article>)}</div> : <p className="sheet-empty">Nenhuma alteração registrada.</p>}</section>
  </div>;
}

export default function PlayableCharacterSheet({ mode }: { mode: "player" | "gm" }) {
  const [view, setView] = useState<"play" | "creation">("play");
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [selectedId, setSelectedId] = useState(localStorage.getItem("omnisvera_selected_character") || "");
  const [character, setCharacter] = useState<PlayableCharacter | null>(null);
  const [events, setEvents] = useState<CharacterEvent[]>([]);
  const [availableItems, setAvailableItems] = useState<NoteSummary[]>([]);
  const [tab, setTab] = useState<CharacterTab>("summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    listPlayableCharacters().then((items) => {
      const ordered = [...items].sort((a, b) => Number(b.access_level === "owner") - Number(a.access_level === "owner"));
      setCharacters(ordered);
      const fallback = ordered.find((item) => item.access_level === "owner")?.id
        || ordered.find((item) => item.id === "vezemir")?.id
        || ordered[0]?.id
        || "";
      const preferred = ordered.some((item) => item.id === selectedId) ? selectedId : fallback;
      setSelectedId(preferred);
      if (preferred) localStorage.setItem("omnisvera_selected_character", preferred);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Não foi possível carregar as fichas.")).finally(() => setLoading(false));
  }, [mode]);

  useEffect(() => {
    if (!selectedId || view !== "play") return;
    setLoading(true); setError("");
    getPlayableCharacter(selectedId).then(setCharacter).catch((reason) => setError(reason instanceof Error ? reason.message : "Não foi possível abrir a ficha.")).finally(() => setLoading(false));
    if (mode === "gm") {
      listCharacterEvents(selectedId).then(setEvents).catch(() => setEvents([]));
      listNotes().then((notes) => setAvailableItems(notes.filter((note) => note.type === "item"))).catch(() => setAvailableItems([]));
    }
  }, [selectedId, mode, view]);

  async function refresh(updated?: PlayableCharacter) {
    const next = updated || await getPlayableCharacter(selectedId);
    setCharacter(next);
    const summaries = await listPlayableCharacters();
    setCharacters(summaries.sort((a, b) => Number(b.access_level === "owner") - Number(a.access_level === "owner")));
    if (mode === "gm") setEvents(await listCharacterEvents(selectedId));
    window.dispatchEvent(new CustomEvent("omnisvera-character-state"));
  }
  async function action(actionName: string, payload: Record<string, unknown>) { await refresh(await applyCharacterStateAction(selectedId, actionName, payload)); }
  async function updateDefinition(fields: Record<string, unknown>) { await refresh(await updateCharacterDefinition(selectedId, fields, "Ajuste pela ficha de jogo")); }
  async function revert(eventId: number) { if (!window.confirm("Reverter esta alteração?")) return; await refresh(await revertCharacterEvent(selectedId, eventId)); }

  const visibleTabs = useMemo(() => TAB_LABELS.filter((item) => item.key !== "gm" || mode === "gm"), [mode]);

  if (view === "creation") return <section className="playable-sheet-page"><div className="sheet-mode-switch"><button onClick={() => setView("play")}>Ficha de jogo</button><button className="active">Criação em 10 passos</button></div><CharacterSheetBuilder mode={mode} /></section>;
  return <section className="panel playable-sheet-page">
    <div className="sheet-mode-switch"><button className="active">Ficha de jogo</button><button onClick={() => setView("creation")}>Criação em 10 passos</button></div>
    <header className="playable-roster-header"><div><p className="eyebrow">Personagens da campanha</p><h2>Ficha de jogo</h2><p>Definição vem do Vault; estado de mesa e histórico ficam no Companion.</p></div>{characters.length > 1 && <label>Personagem<select value={selectedId} onChange={(event) => { setSelectedId(event.target.value); localStorage.setItem("omnisvera_selected_character", event.target.value); setTab("summary"); }}>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}{item.access_level === "owner" ? " · sua ficha" : ""}</option>)}</select></label>}</header>
    {loading && <p className="muted">Preparando ficha...</p>}
    {error && <p className="warning-text">{error}</p>}
    {!loading && character && <>
      <header className="character-identity-card"><Portrait character={character.definition} /><div className="character-identity-copy"><p className="eyebrow">{character.definition.campaign || "Omnisvera"}</p><h2>{character.definition.name}</h2>{character.definition.epithet && <h3>{character.definition.epithet}</h3>}<div className="identity-tags"><span>{shown(character.definition.race)}</span><span>{shown(character.definition.class_name)}</span><span>Nível {shown(character.definition.level)}</span>{character.definition.player_name && <span>Jogador: {character.definition.player_name}</span>}</div><p>{shown(character.state?.location || character.definition.location, "Localização não informada")} · {shown(character.definition.current_status, "Estado não informado")}</p></div><div className="always-visible-stats"><QuickStat label="PV" value={character.state?.maximum_hp === null || character.state?.maximum_hp === undefined ? "—" : `${character.state.current_hp}/${character.state.maximum_hp}`} accent /><QuickStat label="CA" value={character.definition.defenses?.armor_class} /><QuickStat label="Iniciativa" value={character.definition.defenses?.initiative_configured ? signed(character.definition.defenses?.initiative) : "N/C"} /><QuickStat label="Desloc." value={character.definition.movement} /></div></header>
      {character.access_level === "public" ? <section className="sheet-card public-character-view"><h3>O que você conhece</h3><TextBlock value={character.definition.public_description} empty="Este personagem ainda não revelou mais informações a você." /></section> : <>
        <nav className="character-tabs" aria-label="Seções da ficha">{visibleTabs.map((item) => <button key={item.key} className={tab === item.key ? "active" : ""} onClick={() => setTab(item.key)}><span>{item.icon}</span><small>{item.label}</small></button>)}</nav>
        <div className="playable-tab-content">
          {tab === "summary" && <SummaryTab character={character} />}
          {tab === "mechanics" && <MechanicsTab character={character} />}
          {tab === "combat" && <CombatTab character={character} mode={mode} onAction={action} />}
          {tab === "inventory" && <InventoryTab character={character} mode={mode} availableItems={availableItems} onAction={action} />}
          {tab === "abilities" && <AbilitiesTab character={character} />}
          {tab === "story" && <StoryTab character={character} />}
          {tab === "gm" && mode === "gm" && <GmTab character={character} events={events} onDefinition={updateDefinition} onAction={action} onRevert={revert} />}
        </div>
      </>}
    </>}
  </section>;
}
