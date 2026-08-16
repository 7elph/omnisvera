import { FormEvent, PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  applyCharacterStateAction,
  connectSessionRealtime,
  createWorkspaceToken,
  getPlayableCharacter,
  getSessionWorkspace,
  heartbeatSessionWorkspace,
  listPlayableCharacters,
  listSessionLedger,
  listSessionItems,
  mediaUrlFromVaultPath,
  moveWorkspaceToken,
  newDiceRequestId,
  PlayableCharacter,
  PlayableCharacterSummary,
  rollCharacterAction,
  grantSessionItem,
  saveSessionItem,
  sendWorkspaceMessage,
  SessionAbility,
  SessionItem,
  SessionLedgerEntry,
  updateCharacterDefinition,
  uploadWorkspaceMap,
  WorkspaceSnapshot,
  WorkspaceToken,
} from "../api";
import DiceTray from "../components/DiceTray";

type Props = { mode: "gm" | "player" };

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

function characterColor(characterId?: string | null) {
  return CHARACTER_COLORS[String(characterId || "").toLocaleLowerCase("pt-BR")] || "#d6a858";
}

function isConsumable(item: PlayableCharacter["inventory"][number]) {
  const type = String(item.item_type || "").toLocaleLowerCase("pt-BR");
  return Boolean(item.usable || type.includes("consum") || type.includes("poção") || type.includes("potion"));
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

function abilityResource(ability: SessionAbility, resources: NonNullable<PlayableCharacter["state"]>["resources"]) {
  if (ability.uses?.resource_key) {
    const wanted = ability.uses.resource_key.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    return resources.find((item) => item.key === wanted) || null;
  }
  if (ability.circle) return resources.find((item) => item.label.toLocaleLowerCase("pt-BR").includes(`${ability.circle}º círculo`)) || null;
  return null;
}

function fileAsBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Não foi possível ler a imagem."));
    reader.onload = () => resolve(String(reader.result || "").split(",", 2)[1] || "");
    reader.readAsDataURL(file);
  });
}

export default function SessionWorkspace({ mode }: Props) {
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [selectedId, setSelectedId] = useState(localStorage.getItem("omnisvera_selected_character") || "");
  const [character, setCharacter] = useState<PlayableCharacter | null>(null);
  const [ledger, setLedger] = useState<SessionLedgerEntry[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot>({ messages: [], presence: [], tokens: [] });
  const [message, setMessage] = useState("");
  const [condition, setCondition] = useState("");
  const [sessionNotes, setSessionNotes] = useState("");
  const [mapTitle, setMapTitle] = useState("");
  const [mapFile, setMapFile] = useState<File | null>(null);
  const [mapZoom, setMapZoom] = useState(() => {
    const saved = Number(localStorage.getItem("omnisvera_session_map_zoom") || 1);
    return Number.isFinite(saved) ? Math.max(1, Math.min(3, saved)) : 1;
  });
  const [sessionItems, setSessionItems] = useState<SessionItem[]>([]);
  const [itemDraft, setItemDraft] = useState({ id: 0, name: "", item_type: "consumível", description: "", effects: "", usable: true });
  const [grantDraft, setGrantDraft] = useState({ item_id: 0, character_id: "", quantity: 1 });
  const [monsterDraft, setMonsterDraft] = useState({ name: "", maximum_hp: 10, color: "#b94c4c" });
  const [monsterImage, setMonsterImage] = useState<File | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedIdRef = useRef(selectedId);
  const charactersRef = useRef<PlayableCharacterSummary[]>([]);
  const refreshingRef = useRef(false);
  const mapViewportRef = useRef<HTMLDivElement>(null);
  const mapCanvasRef = useRef<HTMLDivElement>(null);
  const draggingTokenRef = useRef<string | null>(null);
  const ledgerLoadedRef = useRef(false);
  const knownRollIdsRef = useRef(new Set<string>());
  const rollLedgerInitializedRef = useRef(false);

  async function loadOverview() {
    const [summaryItems, snapshot, itemItems, ledgerItems] = await Promise.all([
      listPlayableCharacters(), getSessionWorkspace(), mode === "gm" ? listSessionItems().catch(() => []) : Promise.resolve([]), listSessionLedger(500),
    ]);
    const ordered = [...summaryItems].sort((a, b) => Number(b.access_level === "owner") - Number(a.access_level === "owner"));
    const currentSelection = selectedIdRef.current;
    const preferred = ordered.some((item) => item.id === currentSelection)
      ? currentSelection
      : ordered.find((item) => item.access_level === "owner")?.id || ordered[0]?.id || "";
    charactersRef.current = ordered;
    setCharacters(ordered);
    setWorkspace(snapshot);
    setSessionItems(itemItems);
    ledgerLoadedRef.current = true;
    setLedger(ledgerItems);
    if (preferred && preferred !== currentSelection) {
      selectedIdRef.current = preferred;
      setSelectedId(preferred);
      localStorage.setItem("omnisvera_selected_character", preferred);
    }
  }

  async function loadCharacter() {
    const activeId = selectedIdRef.current;
    if (!activeId) return;
    const detail = await getPlayableCharacter(activeId);
    setCharacter(detail);
    setSessionNotes(detail.state?.session_notes || "");
  }

  useEffect(() => {
    void heartbeatSessionWorkspace().catch(() => undefined);
    void loadOverview().catch((reason) => setError(reason instanceof Error ? reason.message : "Falha ao carregar a mesa."));
    const heartbeat = window.setInterval(() => void heartbeatSessionWorkspace().catch(() => undefined), 20_000);
    const refresh = window.setInterval(() => {
      if (refreshingRef.current) return;
      refreshingRef.current = true;
      void loadOverview().then(loadCharacter).catch(() => undefined).finally(() => { refreshingRef.current = false; });
    }, 15_000);
    return () => { window.clearInterval(heartbeat); window.clearInterval(refresh); };
  }, [mode]);

  useEffect(() => {
    selectedIdRef.current = selectedId;
    setCharacter(null);
    void loadCharacter().catch((reason) => setError(reason instanceof Error ? reason.message : "Falha ao carregar o personagem."));
  }, [selectedId, mode]);

  useEffect(() => {
    let active = true;
    let disconnect: () => void = () => {};
    const refreshFromRealtime = () => {
      if (!active || refreshingRef.current) return;
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

  async function definitionAction(fields: Record<string, unknown>) {
    if (mode !== "gm" || !selectedId || busy) return;
    setBusy("definition"); setError("");
    try { await refresh(await updateCharacterDefinition(selectedId, fields, "Ajuste manual do Mestre")); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o modificador."); }
    finally { setBusy(""); }
  }

  async function roll(rollType: string, sourceId?: string) {
    if (!selectedId || busy) return;
    setBusy(`roll:${rollType}:${sourceId || ""}`); setError("");
    try {
      const createdRoll = await rollCharacterAction(selectedId, { request_id: newDiceRequestId("workspace"), roll_type: rollType, source_id: sourceId, visibility: "table" });
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: createdRoll }));
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível realizar a ação."); }
    finally { setBusy(""); }
  }

  async function useAbility(ability: SessionAbility) {
    const resource = abilityResource(ability, character?.state?.resources || []);
    if (resource) {
      await stateAction("consume_resource", { resource_key: resource.key, amount: 1 }, `Usou ${ability.name}`);
      return;
    }
    setBusy(`ability:${ability.id}`);
    try {
      await sendWorkspaceMessage(`${character?.definition.name || "Personagem"} usou ${ability.name}.`, "action");
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
      await uploadWorkspaceMap({ title: mapTitle.trim(), filename: mapFile.name, content_type: mapFile.type || "application/octet-stream", data_base64: dataBase64 });
      setMapFile(null); setMapTitle(""); await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível trocar a imagem."); }
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
        color: characterColor(characterId), latitude: 50, longitude: 50,
      });
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível posicionar o personagem."); }
    finally { setBusy(""); }
  }

  async function createMonster(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !monsterDraft.name.trim() || busy) return;
    setBusy("monster"); setError("");
    try {
      const imageData = monsterImage ? await fileAsBase64(monsterImage) : undefined;
      await createWorkspaceToken({
        token_type: "monster", name: monsterDraft.name.trim(), color: monsterDraft.color,
        maximum_hp: monsterDraft.maximum_hp, current_hp: monsterDraft.maximum_hp,
        latitude: 50, longitude: 50, image_filename: monsterImage?.name, image_data_base64: imageData,
      });
      setMonsterDraft({ name: "", maximum_hp: 10, color: "#b94c4c" }); setMonsterImage(null);
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível criar o monstro."); }
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
    });
  }

  function zoomMapWithWheel(event: ReactWheelEvent<HTMLDivElement>) {
    event.preventDefault();
    changeMapZoom(mapZoom + (event.deltaY < 0 ? .1 : -.1), event.clientX, event.clientY);
  }

  function previewTokenMove(event: ReactPointerEvent<HTMLDivElement>) {
    const tokenId = draggingTokenRef.current;
    if (mode !== "gm" || !tokenId) return;
    const coordinates = tokenCoordinates(event);
    if (!coordinates) return;
    setWorkspace((current) => ({ ...current, tokens: current.tokens.map((item) => item.id === tokenId ? { ...item, ...coordinates } : item) }));
  }

  async function finishTokenMove(event: ReactPointerEvent<HTMLDivElement>) {
    const tokenId = draggingTokenRef.current;
    draggingTokenRef.current = null;
    if (mode !== "gm" || !tokenId) return;
    const coordinates = tokenCoordinates(event);
    if (!coordinates) return;
    setBusy(`move:${tokenId}`);
    try { await moveWorkspaceToken(tokenId, coordinates.latitude, coordinates.longitude); await loadOverview(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar a posição."); await loadOverview(); }
    finally { setBusy(""); }
  }

  async function saveItem(event: FormEvent) {
    event.preventDefault();
    if (mode !== "gm" || !itemDraft.name.trim() || busy) return;
    setBusy("item"); setError("");
    try {
      await saveSessionItem({
        name: itemDraft.name.trim(), item_type: itemDraft.item_type.trim() || "item",
        description: itemDraft.description.trim(), effects: itemDraft.effects.split("\n").map((item) => item.trim()).filter(Boolean),
        usable: itemDraft.usable,
      }, itemDraft.id || undefined);
      setItemDraft({ id: 0, name: "", item_type: "consumível", description: "", effects: "", usable: true });
      await loadOverview();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o item."); }
    finally { setBusy(""); }
  }

  async function grantItem(event: FormEvent) {
    event.preventDefault();
    const characterId = grantDraft.character_id || selectedId;
    if (mode !== "gm" || !characterId || !grantDraft.item_id || busy) return;
    setBusy("grant"); setError("");
    try {
      await grantSessionItem({ character_id: characterId, item_id: grantDraft.item_id, quantity: grantDraft.quantity });
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível conceder o item."); }
    finally { setBusy(""); }
  }

  const definition = character?.definition;
  const state = character?.state;
  const canOperate = character?.access_level !== "public";
  const mapTitleShown = workspace.map?.title || "Mapa de Nimalis";
  const mapImagePath = workspace.map?.image_path || "zz_media/maps/mapa_de_nimalis.png";
  const presenceByCharacter = useMemo(() => new Map(workspace.presence.filter((item) => item.character_id).map((item) => [item.character_id as string, item.online])), [workspace.presence]);
  const nameById = useMemo(() => new Map(characters.map((item) => [item.id, item.name])), [characters]);
  const characterById = useMemo(() => new Map(characters.map((item) => [item.id, item])), [characters]);
  const abilities = definition?.session_abilities || [];
  const spells = abilities.filter((item) => item.kind === "spell" && item.id !== "misseis-magicos");
  const basicAbilities = abilities.filter((item) => !["spell", "resource", "attack"].includes(item.kind));
  const basicAttacks = abilities.filter((item) => item.kind === "attack");
  const catalogResourceKeys = new Set(
    abilities
      .filter((item) => Boolean(item.uses) && item.kind !== "resource" && item.id !== "misseis-magicos")
      .map((item) => abilityResource(item, state?.resources || [])?.key)
      .filter((key): key is string => Boolean(key)),
  );
  const standaloneResources = (state?.resources || []).filter((resource) => !catalogResourceKeys.has(resource.key));
  const consumables = character?.inventory.filter(isConsumable) || [];
  const carriedItems = character?.inventory.filter((item) => !isConsumable(item)) || [];

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
      return {
      id: `ledger-${item.id}`,
      timestamp: item.created_at,
      actor: nameById.get(item.character_id || "") || item.actor_name || item.actor_id,
      actorId: item.character_id,
      kind: (["roll", "action", "state", "message"].includes(item.event_kind) ? item.event_kind : "event") as TimelineEntry["kind"],
      title: item.title,
      detail: detailText || undefined,
    }; });
    return entries.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()).slice(-250);
  }, [ledger, nameById]);

  useEffect(() => { if (timelineRef.current) timelineRef.current.scrollTop = timelineRef.current.scrollHeight; }, [timeline.length]);

  return <section className="session-workspace unified-workspace">
    <header className="party-status-header">
      <div className="party-status-title"><span>MESA ÚNICA</span><strong>Omnisvera</strong><small>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} online</small></div>
      <div className="party-status-list">{characters.map((item) => {
        const hpPercent = item.maximum_hp ? Math.max(0, Math.min(100, Number(item.current_hp || 0) / item.maximum_hp * 100)) : 0;
        const online = Boolean(presenceByCharacter.get(item.id));
        return <button key={item.id} data-character={item.id} className={selectedId === item.id ? "active" : ""} onClick={() => { selectedIdRef.current = item.id; setSelectedId(item.id); localStorage.setItem("omnisvera_selected_character", item.id); }}>
          <span className="workspace-avatar"><CharacterPortrait character={item} /><i className={online ? "online" : "offline"} title={online ? "Online" : "Offline"} /></span>
          <span><strong style={{ color: characterColor(item.id) }}>{item.name}</strong><small>{item.conditions.length ? item.conditions.join(" · ") : `${item.class_name || "Personagem"} · Nv. ${item.level || 1}`}</small><i><b style={{ width: `${hpPercent}%` }} /></i></span>
          <em>{item.current_hp ?? "—"}/{item.maximum_hp ?? "—"}</em>
        </button>;
      })}</div>
    </header>

    {error && <p className="workspace-error">{error}</p>}
    <div className="session-workspace-grid">
      <aside className="workspace-character-panel">
        {character ? <>
          <header className="workspace-character-identity">
            {mediaUrlFromVaultPath(definition?.portrait) ? <img src={mediaUrlFromVaultPath(definition?.portrait)} alt={`Retrato de ${definition?.name}`} /> : <span>{definition?.name.slice(0, 1)}</span>}
            <div><small>PERSONAGEM ATIVO</small><h2 style={{ color: characterColor(definition?.id) }}>{definition?.name}</h2>{definition?.epithet && <p>{definition.epithet}</p>}<div><b>{definition?.race || "Raça"}</b><b>{definition?.class_name || "Classe"}</b><b>Nível {definition?.level || 1}</b></div></div>
          </header>

          <section className="workspace-vitals"><div className="workspace-hp-heading"><span><small>VIDA</small><strong>{state?.current_hp ?? "—"}<em>/ {state?.maximum_hp ?? "—"}</em></strong></span><span><small>CA</small><strong>{definition?.defenses?.armor_class ?? "—"}</strong></span></div><div className="workspace-hp-track"><i style={{ width: `${state?.maximum_hp ? Math.max(0, Math.min(100, Number(state.current_hp || 0) / state.maximum_hp * 100)) : 0}%` }} /></div></section>

          <section className="workspace-attributes"><header><span>ATRIBUTOS E TESTES</span></header><div>{ATTRIBUTES.map(([key, label]) => <button key={key} disabled={!canOperate || Boolean(busy)} onClick={() => void roll("attribute", key)}><span>{label}</span><strong>{definition?.attributes?.[key] ?? "—"}</strong><small>{definition?.attribute_modifiers?.[key] == null ? "N/C" : `${Number(definition.attribute_modifiers[key]) >= 0 ? "+" : ""}${definition.attribute_modifiers[key]}`}</small></button>)}</div><button className="workspace-save-roll" disabled={!canOperate || Boolean(busy)} onClick={() => void roll("saving_throw")}>Jogar proteção</button><button className="workspace-dice-tray-button" type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray"))}><span>⚄</span> Bandeja de dados</button></section>

          <section className="workspace-resources"><header><span>USOS DISPONÍVEIS</span><small>atual / máximo</small></header>{standaloneResources.map((resource) => <div key={resource.key}><span><strong>{resource.label}</strong><small>recupera no descanso completo</small></span><b>{resource.current}/{resource.maximum}</b>{canOperate && <button disabled={Boolean(busy) || resource.current <= 0} onClick={() => void stateAction("consume_resource", { resource_key: resource.key, amount: 1 }, `Usou ${resource.label}`)}>Usar</button>}</div>)}{consumables.map((item) => <div key={item.item_path} className="consumable-counter"><span><strong>{item.item_title}</strong><small>consumível · inventário</small></span><b>{item.quantity}</b>{canOperate && <button disabled={Boolean(busy) || item.quantity <= 0} onClick={() => void stateAction("change_quantity", { item_path: item.item_path, quantity: Math.max(0, item.quantity - 1) }, `Usou ${item.item_title}`)}>Usar</button>}</div>)}{!standaloneResources.length && !consumables.length && <p>Nenhum uso limitado ou consumível.</p>}</section>

          <section className="workspace-action-catalog"><header><span>MAGIAS</span><small>{spells.length}</small></header>{spells.map((ability) => { const resource = abilityResource(ability, state?.resources || []); return <details key={ability.id}><summary><span><strong>{ability.name}</strong><small>{ability.circle ? `${ability.circle}º círculo` : "magia"}</small></span>{resource && <b>{resource.current}/{resource.maximum}</b>}</summary><p>{ability.description || "Sem descrição adicional."}</p>{canOperate && <button disabled={Boolean(busy) || Boolean(resource && resource.current <= 0)} onClick={() => void useAbility(ability)}>Usar magia</button>}</details>; })}{!spells.length && <p>Nenhuma magia cadastrada.</p>}</section>

          <section className="workspace-action-catalog"><header><span>HABILIDADES</span><small>{basicAbilities.length}</small></header>{basicAbilities.map((ability) => { const resource = abilityResource(ability, state?.resources || []); return <details key={ability.id}><summary><span><strong>{ability.name}</strong><small>{ability.group}</small></span>{resource && <b>{resource.current}/{resource.maximum}</b>}</summary><p>{ability.description || "Sem descrição adicional."}</p>{canOperate && <button disabled={Boolean(busy) || Boolean(resource && resource.current <= 0)} onClick={() => void useAbility(ability)}>Usar habilidade</button>}</details>; })}</section>

          <section className="workspace-action-catalog"><header><span>ATAQUES</span><small>{(definition?.attacks?.length || 0) + basicAttacks.length}</small></header>{definition?.attacks?.map((attack) => <article key={attack.id}><span><strong>{attack.name}</strong><small>{attack.damage || "Dano não configurado"}{attack.range ? ` · ${attack.range}` : ""}</small></span><b>{attack.attack_bonus == null ? "—" : `${attack.attack_bonus >= 0 ? "+" : ""}${attack.attack_bonus}`}</b>{canOperate && <button disabled={Boolean(busy)} onClick={() => void roll("attack", attack.id)}>Atacar</button>}</article>)}{basicAttacks.map((attack) => <article key={attack.id}><span><strong>{attack.name}</strong><small>Ataque básico · uso normal</small></span><b>∞</b>{canOperate && <button disabled={Boolean(busy)} onClick={() => void useAbility(attack)}>Atacar</button>}</article>)}</section>

          <section className="workspace-action-catalog"><header><span>INVENTÁRIO</span><small>{carriedItems.length}</small></header>{carriedItems.length ? carriedItems.map((item) => <article key={item.item_path}><span><strong>{item.item_title}</strong><small>{item.equipped ? "Equipado" : "Guardado"}</small></span><b>{item.quantity}</b>{canOperate && <button disabled={Boolean(busy)} onClick={() => void stateAction(item.equipped ? "unequip_item" : "equip_item", { item_path: item.item_path }, `${item.equipped ? "Guardou" : "Equipou"} ${item.item_title}`)}>{item.equipped ? "Guardar" : "Equipar"}</button>}</article>) : <p>Nenhum item não consumível registrado.</p>}</section>

          <section className="workspace-conditions"><header><span>ALTERAÇÕES DE STATUS</span><small>{state?.conditions.length || 0} ativas</small></header>{state?.conditions.length ? <div className="workspace-condition-list">{state.conditions.map((item) => <span key={item}>{item}{mode === "gm" && <button onClick={() => void stateAction("remove_condition", { condition: item }, `Removeu ${item}`)}>×</button>}</span>)}</div> : <p>Nenhuma condição ativa.</p>}</section>

          {mode === "gm" && <section className="workspace-gm-tools">
            <header><span>FERRAMENTAS DO MESTRE</span><small>edição completa</small></header>
            <div className="workspace-gm-numbers"><NumericEditor label="PV atual" value={state?.current_hp} max={state?.maximum_hp || 999} onSave={(value) => stateAction("set_hp", { value }, "PV ajustado pelo Mestre")} /><NumericEditor label="PV máximo" value={state?.maximum_hp} min={1} onSave={(value) => definitionAction({ maximum_hp: value })} /><NumericEditor label="Nível" value={definition?.level} min={1} max={20} onSave={(value) => definitionAction({ level: value })} /><NumericEditor label="Classe de Armadura" value={definition?.defenses?.armor_class} onSave={(value) => definitionAction({ armor_class: value })} /><NumericEditor label="Iniciativa" value={definition?.defenses?.initiative} min={-30} max={30} onSave={(value) => definitionAction({ initiative: value })} />{ATTRIBUTES.map(([key, label]) => <NumericEditor key={key} label={label} value={definition?.attributes?.[key]} min={1} max={30} onSave={(value) => definitionAction({ attributes: { [key]: value } })} />)}</div>
            <form onSubmit={(event) => { event.preventDefault(); if (condition.trim()) { void stateAction("add_condition", { condition: condition.trim() }, `Adicionou ${condition.trim()}`); setCondition(""); } }}><input value={condition} onChange={(event) => setCondition(event.target.value)} placeholder="Nova condição" /><button disabled={!condition.trim() || Boolean(busy)}>Adicionar status</button></form>
            <label className="workspace-session-notes"><span>Notas da sessão do Mestre</span><textarea value={sessionNotes} onChange={(event) => setSessionNotes(event.target.value)} /><button disabled={Boolean(busy) || sessionNotes === (state?.session_notes || "")} onClick={() => void stateAction("set_session_notes", { value: sessionNotes }, "Atualizou notas da sessão")}>Salvar notas</button></label>
            <section className="workspace-item-studio">
              <header><span>CRIAR E EDITAR ITENS</span><button type="button" onClick={() => setItemDraft({ id: 0, name: "", item_type: "consumível", description: "", effects: "", usable: true })}>Novo</button></header>
              <form onSubmit={saveItem}><input value={itemDraft.name} onChange={(event) => setItemDraft({ ...itemDraft, name: event.target.value })} placeholder="Nome do item" /><input value={itemDraft.item_type} onChange={(event) => setItemDraft({ ...itemDraft, item_type: event.target.value })} placeholder="Tipo" /><textarea value={itemDraft.description} onChange={(event) => setItemDraft({ ...itemDraft, description: event.target.value })} placeholder="Descrição" /><textarea value={itemDraft.effects} onChange={(event) => setItemDraft({ ...itemDraft, effects: event.target.value })} placeholder="Um efeito por linha" /><label><input type="checkbox" checked={itemDraft.usable} onChange={(event) => setItemDraft({ ...itemDraft, usable: event.target.checked })} /> Consumível / utilizável</label><button disabled={!itemDraft.name.trim() || Boolean(busy)}>{itemDraft.id ? "Salvar item" : "Criar item"}</button></form>
              <div className="workspace-item-list">{sessionItems.map((item) => <button type="button" key={item.id} onClick={() => setItemDraft({ id: item.id, name: item.name, item_type: item.item_type, description: item.description || "", effects: item.effects.join("\n"), usable: item.usable })}><strong>{item.name}</strong><small>{item.item_type}</small></button>)}</div>
              <form className="workspace-grant-item" onSubmit={grantItem}><select value={grantDraft.item_id} onChange={(event) => setGrantDraft({ ...grantDraft, item_id: Number(event.target.value) })}><option value={0}>Escolha um item</option>{sessionItems.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select value={grantDraft.character_id || selectedId} onChange={(event) => setGrantDraft({ ...grantDraft, character_id: event.target.value })}>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><input type="number" min={1} max={999} value={grantDraft.quantity} onChange={(event) => setGrantDraft({ ...grantDraft, quantity: Number(event.target.value) })} /><button disabled={!grantDraft.item_id || Boolean(busy)}>Dar ao personagem</button></form>
            </section>
            <button className="workspace-rest-button" disabled={Boolean(busy)} onClick={() => void stateAction("rest_at_inn", {}, "Descanso completo no INN")}>Descanso completo · restaurar vida, status, magias e habilidades</button>
          </section>}
        </> : <p className="workspace-loading">Carregando personagem…</p>}
      </aside>

      <main className="workspace-map-panel">
        <header><div><small>IMAGEM DA SESSÃO</small><h2>{mapTitleShown}</h2></div><div className="workspace-map-zoom" aria-label="Zoom do mapa"><button type="button" disabled={mapZoom <= 1} onClick={() => changeMapZoom(mapZoom - .1)} aria-label="Diminuir zoom">−</button><output>{Math.round(mapZoom * 100)}%</output><button type="button" disabled={mapZoom >= 3} onClick={() => changeMapZoom(mapZoom + .1)} aria-label="Aumentar zoom">+</button><button type="button" disabled={mapZoom === 1} onClick={() => changeMapZoom(1)}>Ajustar</button></div>{mode === "gm" && <form className="workspace-map-upload" onSubmit={submitMap}><input value={mapTitle} onChange={(event) => setMapTitle(event.target.value)} placeholder="Nome da imagem" /><label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMapFile(event.target.files?.[0] || null)} /><span>{mapFile?.name || "Escolher imagem"}</span></label><button disabled={!mapTitle.trim() || !mapFile || Boolean(busy)}>Carregar</button></form>}</header>
        <div ref={mapViewportRef} className={`workspace-map-canvas ${mode === "gm" ? "editable" : ""}`} onWheel={zoomMapWithWheel} onPointerMove={previewTokenMove} onPointerUp={(event) => void finishTokenMove(event)} onPointerLeave={(event) => { if (draggingTokenRef.current && event.buttons === 0) void finishTokenMove(event); }}>
          <div ref={mapCanvasRef} className="workspace-map-stage" style={{ width: `${mapZoom * 100}%`, height: `${mapZoom * 100}%` }}>
            <img src={mediaUrlFromVaultPath(mapImagePath)} alt={mapTitleShown} draggable={false} />
            <div className="workspace-map-grid" aria-hidden="true" />
            {workspace.tokens.map((token) => { const summary = token.character_id ? characterById.get(token.character_id) : undefined; const image = mediaUrlFromVaultPath(token.image_path || summary?.portrait); const hpCurrent = summary?.current_hp ?? token.current_hp; const hpMaximum = summary?.maximum_hp ?? token.maximum_hp; const conditions = summary?.conditions || token.conditions; return <button type="button" key={token.id} className={`workspace-map-token ${token.token_type}`} style={{ left: `${token.longitude}%`, top: `${token.latitude}%`, borderColor: token.color, color: token.color }} onPointerDown={(event) => { if (mode === "gm") { event.preventDefault(); draggingTokenRef.current = token.id; } }} onClick={() => { if (token.character_id) { selectedIdRef.current = token.character_id; setSelectedId(token.character_id); } }} title={`${token.name} · latitude ${token.latitude.toFixed(2)} · longitude ${token.longitude.toFixed(2)}${conditions.length ? ` · ${conditions.join(", ")}` : ""}`}>
              {image ? <img src={image} alt="" draggable={false} /> : <i>{token.name.slice(0, 1).toUpperCase()}</i>}<strong>{token.name}</strong>{hpMaximum != null && <small>{hpCurrent ?? "—"}/{hpMaximum} PV</small>}
            </button>; })}
          </div>
        </div>
        {mode === "gm" && <section className="workspace-map-tools">
          <div><header><span>PERSONAGENS NO MAPA</span><small>arraste os avatares para posicionar</small></header><div>{characters.map((item) => { const pinned = workspace.tokens.some((token) => token.character_id === item.id); return <button type="button" key={item.id} disabled={pinned || Boolean(busy)} style={{ color: characterColor(item.id) }} onClick={() => void pinCharacter(item.id)}>{pinned ? "✓" : "+"} {item.name}</button>; })}</div></div>
          <form onSubmit={createMonster}><header><span>CRIAR MONSTRO</span><small>novo marcador tático</small></header><input value={monsterDraft.name} onChange={(event) => setMonsterDraft({ ...monsterDraft, name: event.target.value })} placeholder="Nome do monstro" /><div className="workspace-monster-hp"><span>PV</span><input type="number" min={1} max={99999} value={monsterDraft.maximum_hp} onChange={(event) => setMonsterDraft({ ...monsterDraft, maximum_hp: Number(event.target.value) })} title="PV máximo" /></div><input type="color" value={monsterDraft.color} onChange={(event) => setMonsterDraft({ ...monsterDraft, color: event.target.value })} title="Cor" /><label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMonsterImage(event.target.files?.[0] || null)} /><span>{monsterImage?.name || "Imagem opcional"}</span></label><button disabled={!monsterDraft.name.trim() || Boolean(busy)}>Criar e pinar</button></form>
        </section>}
        <footer><span><i className="online" /> Mesa sincronizada</span><span>{workspace.presence.filter((item) => item.online && item.actor_role === "player").length} jogadores online</span><span>{timeline.length} registros</span></footer>
      </main>

      <aside className="workspace-timeline-panel">
        <header><div><small>REGISTRO DA SESSÃO</small><h2>Ações e conversa</h2></div><span>{timeline.length}</span></header>
        <div className="workspace-timeline" ref={timelineRef}>{timeline.length ? timeline.map((entry) => <article key={entry.id} className={entry.kind}><div><i>{entry.kind === "roll" ? "◈" : entry.kind === "message" ? "✦" : entry.kind === "state" ? "±" : "→"}</i><time>{formatClock(entry.timestamp)}</time></div><section><header><strong style={{ color: characterColor(entry.actorId) }}>{entry.actor}</strong><small>{entry.kind === "roll" ? "rolagem" : entry.kind === "message" ? "mensagem" : entry.kind === "state" ? "estado" : "ação"}</small></header><p>{entry.title}</p>{entry.detail && <pre>{entry.detail}</pre>}</section></article>) : <p className="workspace-empty-log">O registro da sessão começará com a primeira ação ou mensagem.</p>}</div>
        <form className="workspace-log-composer" onSubmit={submitMessage}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Escreva sua mensagem…" /><button disabled={!message.trim() || Boolean(busy)}>Enviar</button></form>
      </aside>
    </div>
    <DiceTray mode={mode} triggerHidden />
  </section>;
}
