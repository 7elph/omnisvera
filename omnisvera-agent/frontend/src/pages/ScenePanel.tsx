import { useEffect, useMemo, useRef, useState } from "react";
import {
  addSceneParticipant,
  applySceneConsequence,
  createGameSession,
  createScene,
  createSceneElement,
  declareSceneAction,
  GameScene,
  getActiveScene,
  getScene,
  getSessionWorkspace,
  listGameSessions,
  listPlayableCharacters,
  listNpcs,
  listPlayerFeed,
  listScenes,
  listWorkspaceMaps,
  markPlayerFeedRead,
  mediaUrlFromVaultPath,
  newSceneRequestId,
  PlayableCharacterSummary,
  NpcRecord,
  newNpcRequestId,
  openSceneOnTable,
  publishScene,
  recordNpcEncounter,
  recordRuntimeEvent,
  rejectSceneAction,
  requestSceneActionRoll,
  resolveSceneAction,
  revealSceneElement,
  sendPlayerNotification,
  updateSceneParticipant,
  updateScene,
  updateGameSessionStatus,
  updateSceneStatus,
  WorkspaceToken,
} from "../api";

const ACTIONS = [
  ["talk", "Conversar", "☷"], ["investigate", "Investigar", "⌕"], ["observe", "Observar", "◉"],
  ["move", "Mover-se", "➜"], ["use_item", "Usar item", "◇"], ["interact", "Interagir", "✋"],
  ["attack", "Atacar", "⚔"], ["other", "Outra ação", "+"],
];

const SCENE_CHECKLIST = [
  ["identity", "Nome, local e objetivo"], ["map", "Mapa da cena"], ["opening", "Abertura pública"],
  ["public_image", "Imagem para os jogadores"], ["characters", "Personagens presentes"], ["npcs", "NPCs"],
  ["creatures", "Criaturas e inimigos"], ["scenery", "Cenário interativo"], ["pins", "Pins posicionados"],
  ["fog", "Névoa e áreas reveladas"], ["clues", "Pistas e descobertas"], ["treasure", "Tesouros e loot"],
  ["interactive_items", "Itens utilizáveis"], ["initial_states", "Estados iniciais"], ["private_notes", "Notas privadas"],
  ["transitions", "Saídas e transições"], ["player_preview", "Prévia dos jogadores"],
] as const;

const EMPTY_CHECKLIST = Object.fromEntries(SCENE_CHECKLIST.map(([key]) => [key, false])) as Record<string, boolean>;

function time(value?: string | null) {
  return value ? new Date(value).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
}

function statusLabel(value: string) {
  return ({ draft: "Rascunho", active: "Ativa", paused: "Pausada", resolved: "Encerrada", abandoned: "Abandonada", declared: "Declarada", awaiting_roll: "Aguardando rolagem", rejected: "Rejeitada", cancelled: "Cancelada" } as Record<string, string>)[value] || value;
}

function storedSceneId() {
  const stored = Number(localStorage.getItem("omnisvera_selected_scene") || "");
  return Number.isFinite(stored) && stored > 0 ? stored : null;
}

function ParticipantCard({ participant, mode, sceneId, onRefresh }: { participant: GameScene["participants"][number]; mode: "gm" | "player"; sceneId: number; onRefresh: () => Promise<void> }) {
  const character = participant.character;
  const npc = participant.npc;
  const portrait = mediaUrlFromVaultPath(character?.portrait || npc?.portrait_path);
  async function consequence(action: string, payload: Record<string, unknown>, title: string) {
    if (!participant.character_id) return;
    await applySceneConsequence(sceneId, { character_id: participant.character_id, action, payload, title, public_text: title, visibility: "table" });
    window.dispatchEvent(new CustomEvent("omnisvera-character-state"));
    await onRefresh();
  }
  async function registerEncounter() {
    if (!npc) return;
    await recordNpcEncounter(npc.id, { request_id: newNpcRequestId("scene-npc-encounter"), scene_id: sceneId, title: `Encontro em cena: ${participant.public_label}`, public_summary: `${participant.public_label} participou desta cena.` });
    await onRefresh();
  }
  return <article className="scene-participant-card">
    <button className="scene-character-link" disabled={!participant.character_id && !npc} onClick={() => participant.character_id ? window.dispatchEvent(new CustomEvent("omnisvera-open-character", { detail: participant.character_id })) : npc && window.dispatchEvent(new CustomEvent("omnisvera-open-npc", { detail: npc.id }))}>
      {portrait ? <img src={portrait} alt={`Retrato de ${participant.public_label}`} /> : <span aria-hidden="true">♟</span>}
      <div><strong>{participant.public_label}</strong><small>{participant.public_status || "Presente"}</small></div>
    </button>
    {character && <div className="scene-participant-stats"><span>PV <b>{character.current_hp ?? "—"}/{character.maximum_hp ?? "—"}</b></span><span>CA <b>{character.armor_class ?? "—"}</b></span>{character.conditions.map((item) => <em key={item}>{item}</em>)}</div>}
    {mode === "gm" && participant.character_id && <div className="scene-participant-actions">
      <button onClick={() => void consequence("damage", { amount: 1 }, `${participant.public_label} sofre 1 de dano`)}>−1 PV</button>
      <button onClick={() => void consequence("heal", { amount: 1 }, `${participant.public_label} recupera 1 PV`)}>+1 PV</button>
      <button onClick={() => void consequence("add_condition", { condition: "Abalado" }, `${participant.public_label} fica Abalado`)}>+ Abalado</button>
      {character?.conditions.map((condition) => <button key={`remove-${condition}`} aria-label={`Remover condição ${condition} de ${participant.public_label}`} onClick={() => void consequence("remove_condition", { condition }, `${participant.public_label} não está mais ${condition}`)}>− {condition}</button>)}
    </div>}
    {mode === "gm" && npc && <div className="scene-participant-actions"><button onClick={() => void registerEncounter()}>Registrar encontro</button><button onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-npc", { detail: npc.id }))}>Memória e relações</button></div>}
    {mode === "gm" && !participant.visible_to_players && <button onClick={() => void updateSceneParticipant(participant.id, { visible_to_players: true, public_status: "Presente" }).then(onRefresh)}>Revelar aos jogadores</button>}
  </article>;
}

export default function ScenePanel({ mode, surface = "admin", viewerMode = mode }: { mode: "gm" | "player"; surface?: "live" | "admin"; viewerMode?: "gm" | "player" }) {
  const [scene, setScene] = useState<GameScene | null>(null);
  const [scenes, setScenes] = useState<GameScene[]>([]);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [npcs, setNpcs] = useState<NpcRecord[]>([]);
  const [sessions, setSessions] = useState<Array<{ id: number; title: string; status: string }>>([]);
  const [workspaceMaps, setWorkspaceMaps] = useState<Array<{ id: string; title: string; image_path: string }>>([]);
  const [mapMonsters, setMapMonsters] = useState<WorkspaceToken[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [createDraft, setCreateDraft] = useState({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", image_path: "", map_id: "", checklist: { ...EMPTY_CHECKLIST }, session_id: "" });
  const [sessionTitle, setSessionTitle] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [npcId, setNpcId] = useState("");
  const [monsterTokenId, setMonsterTokenId] = useState("");
  const [elementDraft, setElementDraft] = useState({ element_type: "clue", title: "", public_description: "", private_description: "" });
  const [actionType, setActionType] = useState("investigate");
  const [actionText, setActionText] = useState("");
  const [actionTarget, setActionTarget] = useState("");
  const [resolution, setResolution] = useState<Record<number, string>>({});
  const [notifications, setNotifications] = useState<Array<{ id: number; title: string; message: string; read_at?: string | null }>>([]);
  const [notificationDraft, setNotificationDraft] = useState({ profile_id: "group", title: "Mensagem do Mestre", message: "" });
  const [touchLocked, setTouchLocked] = useState(false);
  const [workspaceView, setWorkspaceView] = useState({ zoom: 1, scroll_left: 0, scroll_top: 0 });
  const [preparation, setPreparation] = useState({ map_id: "", map_zoom: 1, map_scroll_left: 0, map_scroll_top: 0, checklist: { ...EMPTY_CHECKLIST } as Record<string, boolean> });
  const [sceneDraft, setSceneDraft] = useState({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", image_path: "" });
  const [preparationElement, setPreparationElement] = useState({ title: "", public_description: "", private_description: "" });
  const [previewPlayers, setPreviewPlayers] = useState(false);
  const [publicationDraft, setPublicationDraft] = useState({ publication_type: "opening", title: "", public_text: "", private_text: "" });
  const notificationInitializedRef = useRef(false);

  async function refresh(preferredId?: number | null) {
    try {
      const [active, all] = await Promise.all([getActiveScene(), listScenes()]);
      setScenes(all);
      if (mode === "gm") {
        setSessions(await listGameSessions());
        setWorkspaceMaps(await listWorkspaceMaps().catch(() => []));
        const workspace = await getSessionWorkspace().catch(() => null);
        setMapMonsters((workspace?.tokens || []).filter((token) => token.token_type === "monster"));
        if (workspace?.view) setWorkspaceView(workspace.view);
      }
      const wanted = surface === "live" && viewerMode === "player"
        ? active?.id ?? null
        : preferredId ?? selectedId ?? storedSceneId() ?? active?.id ?? all[0]?.id ?? null;
      setSelectedId(wanted);
      if (wanted) localStorage.setItem("omnisvera_selected_scene", String(wanted));
      setScene(wanted ? await getScene(wanted) : active);
      window.dispatchEvent(new CustomEvent("omnisvera-scene-updated"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar a cena."); }
    finally { setLoading(false); }
  }

  useEffect(() => { void refresh(storedSceneId()); }, []);
  useEffect(() => {
    let cancelled = false;
    void listPlayableCharacters()
      .then((roster) => { if (!cancelled) setCharacters(roster); })
      .catch((cause) => { if (!cancelled && mode === "gm") setError(cause instanceof Error ? cause.message : "Não foi possível carregar os personagens."); });
    return () => { cancelled = true; };
  }, [mode]);
  useEffect(() => {
    if (!scene) return;
    setPreparation({
      map_id: scene.map_id || "",
      map_zoom: scene.map_zoom || 1,
      map_scroll_left: scene.map_scroll_left || 0,
      map_scroll_top: scene.map_scroll_top || 0,
      checklist: { ...EMPTY_CHECKLIST, ...(scene.checklist || {}) },
    });
    setSceneDraft({
      title: scene.title,
      location_name: scene.location_name,
      objective: scene.objective || "",
      public_description: scene.public_description || "",
      private_notes: scene.private_notes || "",
      image_path: scene.image_path || "",
    });
  }, [scene?.id, scene?.version]);
  useEffect(() => {
    let cancelled = false;
    void listNpcs().then((rows) => { if (!cancelled) setNpcs(rows); }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [mode]);
  useEffect(() => {
    const update = () => void refresh();
    const openScene = (event: Event) => {
      const sceneId = Number((event as CustomEvent<number>).detail);
      if (!Number.isFinite(sceneId) || sceneId <= 0) return;
      localStorage.setItem("omnisvera_selected_scene", String(sceneId));
      setSelectedId(sceneId);
      void refresh(sceneId);
    };
    window.addEventListener("omnisvera-roll-created", update);
    window.addEventListener("omnisvera-open-scene", openScene);
    return () => {
      window.removeEventListener("omnisvera-roll-created", update);
      window.removeEventListener("omnisvera-open-scene", openScene);
    };
  }, [selectedId]);

  useEffect(() => {
    if (surface !== "live") return;
    const timer = window.setInterval(() => void refresh(selectedId), 10_000);
    return () => window.clearInterval(timer);
  }, [surface, selectedId]);

  useEffect(() => {
    if (surface !== "live" || viewerMode !== "player") return;
    const load = async () => {
      const feed = await listPlayerFeed();
      const unread = feed.filter((item) => !item.read_at);
      setNotifications(unread);
      if (notificationInitializedRef.current && Notification.permission === "granted") {
        for (const item of unread.filter((entry) => !notifications.some((known) => known.id === entry.id))) {
          new Notification(item.title, { body: item.message, tag: `omnisvera-${item.id}` });
        }
      }
      notificationInitializedRef.current = true;
    };
    void load().catch(() => undefined);
    const timer = window.setInterval(() => void load().catch(() => undefined), 12_000);
    return () => window.clearInterval(timer);
  }, [surface, viewerMode, notifications.length]);

  async function run(operation: () => Promise<unknown>, message: string, preferredId?: number) {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try { await operation(); setNotice(message); await refresh(preferredId); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "A operação não pôde ser concluída."); }
    finally { setBusy(false); }
  }

  async function submitScene() {
    await run(async () => {
      const created = await createScene({ request_id: newSceneRequestId("scene"), ...createDraft, checklist: { ...createDraft.checklist, identity: true }, session_id: createDraft.session_id ? Number(createDraft.session_id) : undefined, visibility: "table" });
      setCreateDraft({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", image_path: "", map_id: "", checklist: { ...EMPTY_CHECKLIST }, session_id: "" });
      setSelectedId(created.id);
    }, "Cena criada.");
  }

  async function declare() {
    if (!scene || !actionText.trim()) return;
    await run(() => declareSceneAction(scene.id, { request_id: newSceneRequestId("action"), action_type: actionType, description: actionText, target_label: actionTarget || undefined, visibility: "table" }), "Ação declarada.", scene.id);
    setActionText(""); setActionTarget("");
  }

  async function moveParticipant(index: number, direction: -1 | 1) {
    const target = activeParticipants[index];
    const other = activeParticipants[index + direction];
    if (!target || !other) return;
    await run(async () => {
      await Promise.all([
        updateSceneParticipant(target.id, { order_index: other.order_index }),
        updateSceneParticipant(other.id, { order_index: target.order_index }),
      ]);
    }, "Ordem da cena atualizada.", scene?.id);
  }

  async function setCurrentParticipant(participantId: number) {
    await run(async () => {
      await Promise.all(activeParticipants.map((participant) => updateSceneParticipant(participant.id, {
        public_status: participant.id === participantId ? "Agindo agora" : participant.public_status === "Agindo agora" ? "Presente" : participant.public_status,
      })));
    }, "Vez atualizada.", scene?.id);
  }

  async function sendNotification() {
    if (!notificationDraft.message.trim()) return;
    await run(() => sendPlayerNotification({ ...notificationDraft, message: notificationDraft.message.trim() }), "Notificação enviada.", scene?.id);
    setNotificationDraft((current) => ({ ...current, message: "" }));
  }

  async function setStepDone(key: string, done: boolean, fields: Record<string, unknown> = {}) {
    if (!scene) return;
    await run(
      () => updateScene(scene.id, scene.version, { ...fields, checklist: { ...preparation.checklist, [key]: done } }),
      done ? "Etapa concluída." : "Etapa reaberta.",
      scene.id,
    );
  }

  async function addParticipantAndComplete(kind: "characters" | "npcs" | "creatures") {
    if (!scene) return;
    await run(async () => {
      if (kind === "characters") {
        const character = characters.find((item) => item.id === participantId);
        if (!character) throw new Error("Selecione um personagem.");
        await addSceneParticipant(scene.id, { participant_type: "player_character", character_id: character.id, public_label: character.name, public_status: "Presente", visible_to_players: true });
      } else if (kind === "npcs") {
        const npc = npcs.find((item) => item.id === Number(npcId));
        if (!npc) throw new Error("Selecione um NPC.");
        await addSceneParticipant(scene.id, { participant_type: "npc", npc_name: npc.name, npc_source: `npc:${npc.id}`, public_label: npc.name, public_status: npc.public_status || "Presente", visible_to_players: npc.visible_to_players });
      } else {
        const token = preparedMapMonsters.find((item) => item.id === monsterTokenId);
        if (!token) throw new Error("Selecione uma criatura do mapa preparado.");
        await addSceneParticipant(scene.id, { participant_type: "creature", npc_name: token.name, npc_source: `map-token:${token.id}`, public_label: token.name, public_status: "Oculto", private_status: `${token.current_hp ?? "—"}/${token.maximum_hp ?? "—"} PV`, visible_to_players: false });
      }
      await updateScene(scene.id, scene.version, { checklist: { ...preparation.checklist, [kind]: true } });
    }, "Participante preparado e etapa concluída.", scene.id);
  }

  async function createElementAndComplete(key: string, elementType: string) {
    if (!scene || !preparationElement.title.trim()) return;
    await run(async () => {
      await createSceneElement(scene.id, {
        request_id: newSceneRequestId(`prepare-${key}`),
        element_type: elementType,
        title: preparationElement.title.trim(),
        public_description: preparationElement.public_description.trim() || undefined,
        private_description: preparationElement.private_description.trim() || undefined,
        status: "hidden",
        visibility: "gm",
      });
      await updateScene(scene.id, scene.version, { checklist: { ...preparation.checklist, [key]: true } });
    }, "Elemento preparado e etapa concluída.", scene.id);
    setPreparationElement({ title: "", public_description: "", private_description: "" });
  }

  async function publishToTable() {
    if (!scene || !publicationDraft.title.trim()) return;
    await run(
      () => publishScene(scene.id, { request_id: newSceneRequestId("scene-publication"), ...publicationDraft, title: publicationDraft.title.trim(), public_text: publicationDraft.public_text.trim() || undefined, private_text: publicationDraft.private_text.trim() || undefined }),
      "Informação publicada no registro da Mesa.",
      scene.id,
    );
    setPublicationDraft({ publication_type: "opening", title: "", public_text: "", private_text: "" });
  }

  const activeParticipants = useMemo(() => scene?.participants.filter((item) => !item.left_at) || [], [scene]);
  const preparedMapMonsters = useMemo(() => mapMonsters.filter((token) => !scene?.map_id || token.map_id === scene.map_id), [mapMonsters, scene?.map_id]);
  const checklistDone = useMemo(() => SCENE_CHECKLIST.filter(([key]) => preparation.checklist[key]).length, [preparation.checklist]);
  const sceneLocked = Boolean(scene && ["resolved", "abandoned"].includes(scene.status));
  const openWorkspace = (view: "maps" | "tools" | "table") => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: view }));
  const elementSolution = (key: string, elementType: string, noun: string) => <div className="scene-step-form">
    <p>Prepare {noun} como elemento oculto. Ele só aparece aos jogadores quando você revelar.</p>
    <input aria-label={`Título de ${noun}`} placeholder="Título" value={preparationElement.title} onChange={(event) => setPreparationElement({ ...preparationElement, title: event.target.value })} />
    <textarea aria-label={`Descrição pública de ${noun}`} placeholder="Descrição que poderá ser revelada" value={preparationElement.public_description} onChange={(event) => setPreparationElement({ ...preparationElement, public_description: event.target.value })} />
    <textarea aria-label={`Nota privada de ${noun}`} placeholder="Notas apenas do Mestre" value={preparationElement.private_description} onChange={(event) => setPreparationElement({ ...preparationElement, private_description: event.target.value })} />
    <button disabled={busy || sceneLocked || !preparationElement.title.trim()} onClick={() => void createElementAndComplete(key, elementType)}>Criar oculto e concluir</button>
  </div>;

  function renderPreparationSolution(key: string) {
    if (!scene) return null;
    if (key === "identity") return <div className="scene-step-form scene-step-grid">
      <label>Título<input value={sceneDraft.title} onChange={(event) => setSceneDraft({ ...sceneDraft, title: event.target.value })} /></label>
      <label>Local<input value={sceneDraft.location_name} onChange={(event) => setSceneDraft({ ...sceneDraft, location_name: event.target.value })} /></label>
      <label className="wide">Objetivo<textarea value={sceneDraft.objective} onChange={(event) => setSceneDraft({ ...sceneDraft, objective: event.target.value })} /></label>
      <button disabled={busy || sceneLocked || !sceneDraft.title.trim() || !sceneDraft.location_name.trim()} onClick={() => void setStepDone("identity", true, { title: sceneDraft.title, location_name: sceneDraft.location_name, objective: sceneDraft.objective })}>Salvar identidade e concluir</button>
    </div>;
    if (key === "map") return <div className="scene-step-form scene-step-grid">
      <label className="wide">Mapa<select value={preparation.map_id} onChange={(event) => setPreparation({ ...preparation, map_id: event.target.value })}><option value="">Selecione o mapa da cena</option>{workspaceMaps.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label>
      <label>Zoom<input type="number" min="1" max="3" step="0.1" value={preparation.map_zoom} onChange={(event) => setPreparation({ ...preparation, map_zoom: Number(event.target.value) })} /></label>
      <button className="secondary-button" onClick={() => setPreparation({ ...preparation, map_zoom: workspaceView.zoom, map_scroll_left: workspaceView.scroll_left, map_scroll_top: workspaceView.scroll_top })}>Usar enquadramento atual</button>
      <button disabled={busy || sceneLocked || !preparation.map_id} onClick={() => { const selected = workspaceMaps.find((item) => item.id === preparation.map_id); void setStepDone("map", true, { map_id: preparation.map_id, map_zoom: preparation.map_zoom, map_scroll_left: preparation.map_scroll_left, map_scroll_top: preparation.map_scroll_top, image_path: selected?.image_path || scene.image_path || null }); }}>Salvar mapa e concluir</button>
    </div>;
    if (key === "opening") return <div className="scene-step-form"><p>Escreva o texto que será apresentado quando a cena for aberta na Mesa.</p><textarea value={sceneDraft.public_description} onChange={(event) => setSceneDraft({ ...sceneDraft, public_description: event.target.value })} placeholder="O que os jogadores percebem ao entrar na cena" /><button disabled={busy || sceneLocked || !sceneDraft.public_description.trim()} onClick={() => void setStepDone("opening", true, { public_description: sceneDraft.public_description })}>Salvar abertura e concluir</button></div>;
    if (key === "public_image") return <div className="scene-step-form"><p>Escolha a imagem teatral da cena. Ela pode usar a imagem de qualquer mapa carregado.</p><select value={sceneDraft.image_path} onChange={(event) => setSceneDraft({ ...sceneDraft, image_path: event.target.value })}><option value="">Sem imagem pública</option>{workspaceMaps.map((item) => <option key={item.id} value={item.image_path}>{item.title}</option>)}</select><button disabled={busy || sceneLocked || !sceneDraft.image_path} onClick={() => void setStepDone("public_image", true, { image_path: sceneDraft.image_path })}>Salvar imagem e concluir</button></div>;
    if (key === "characters") return <div className="scene-step-form"><p>Escolha quais personagens dos jogadores começam na cena.</p><div className="scene-inline-form"><select value={participantId} onChange={(event) => setParticipantId(event.target.value)}><option value="">Selecionar personagem...</option>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><button disabled={busy || sceneLocked || !participantId} onClick={() => void addParticipantAndComplete("characters")}>Adicionar e concluir</button></div></div>;
    if (key === "npcs") return <div className="scene-step-form"><p>Adicione um NPC já cadastrado e determine depois se ele será revelado.</p><div className="scene-inline-form"><select value={npcId} onChange={(event) => setNpcId(event.target.value)}><option value="">Selecionar NPC...</option>{npcs.map((npc) => <option key={npc.id} value={npc.id}>{npc.name}</option>)}</select><button disabled={busy || sceneLocked || !npcId} onClick={() => void addParticipantAndComplete("npcs")}>Adicionar e concluir</button></div><button className="secondary-button" onClick={() => openWorkspace("tools")}>Criar ou editar NPC</button></div>;
    if (key === "creatures") return <div className="scene-step-form"><p>As criaturas abaixo são os pins do mapa preparado.</p><div className="scene-inline-form"><select value={monsterTokenId} onChange={(event) => setMonsterTokenId(event.target.value)}><option value="">Selecionar criatura...</option>{preparedMapMonsters.map((token) => <option key={token.id} value={token.id}>{token.name}</option>)}</select><button disabled={busy || sceneLocked || !monsterTokenId} onClick={() => void addParticipantAndComplete("creatures")}>Preparar oculta e concluir</button></div><button className="secondary-button" onClick={() => openWorkspace("maps")}>Criar criatura no mapa</button></div>;
    if (key === "scenery") return elementSolution(key, "environmental_effect", "um elemento de cenário interativo");
    if (key === "clues") return elementSolution(key, "clue", "uma pista ou descoberta");
    if (key === "treasure") return elementSolution(key, "object", "um tesouro ou loot");
    if (key === "transitions") return elementSolution(key, "exit", "uma saída ou transição");
    if (key === "pins") return <div className="scene-step-form"><p>Abra o mapa preparado, posicione os pins e defina quais estarão visíveis aos jogadores.</p><button onClick={() => openWorkspace("maps")}>Abrir editor de pins</button></div>;
    if (key === "fog") return <div className="scene-step-form"><p>Configure as camadas de exploração e batalha diretamente sobre o mapa da cena.</p><button onClick={() => openWorkspace("maps")}>Abrir ferramentas de névoa</button></div>;
    if (key === "interactive_items") return <div className="scene-step-form"><p>Crie ou edite o item na Mesa do Mestre. Depois, volte para vinculá-lo como elemento ou loot da cena.</p><button onClick={() => openWorkspace("tools")}>Abrir criação de itens</button></div>;
    if (key === "initial_states") return <div className="scene-step-form"><p>Revise PV, condições e estado público dos participantes preparados.</p><div className="scene-step-review-list">{activeParticipants.length ? activeParticipants.map((item) => <span key={item.id}><strong>{item.public_label}</strong><small>{item.public_status || "Sem estado"}{item.character ? ` · ${item.character.current_hp ?? "—"}/${item.character.maximum_hp ?? "—"} PV` : item.private_status ? ` · ${item.private_status}` : ""}</small></span>) : <em>Nenhum participante preparado.</em>}</div></div>;
    if (key === "private_notes") return <div className="scene-step-form"><p>Registre segredos, gatilhos e informações que não devem aparecer aos jogadores.</p><textarea value={sceneDraft.private_notes} onChange={(event) => setSceneDraft({ ...sceneDraft, private_notes: event.target.value })} placeholder="Notas privadas do Mestre" /><button disabled={busy || sceneLocked || !sceneDraft.private_notes.trim()} onClick={() => void setStepDone("private_notes", true, { private_notes: sceneDraft.private_notes })}>Salvar notas e concluir</button></div>;
    if (key === "player_preview") return <div className="scene-step-form"><p>Confira exatamente a versão pública antes de abrir a cena.</p><button onClick={() => setPreviewPlayers((current) => !current)}>{previewPlayers ? "Fechar prévia" : "Visualizar como jogadores"}</button>{previewPlayers && <article className="scene-player-preview">{sceneDraft.image_path && <img src={mediaUrlFromVaultPath(sceneDraft.image_path)} alt="" />}<small>{scene.location_name}</small><h4>{scene.title}</h4><p>{scene.public_description || "Sem texto público."}</p><strong>Participantes visíveis</strong><p>{activeParticipants.filter((item) => item.visible_to_players).map((item) => item.public_label).join(" · ") || "Nenhum"}</p><strong>Elementos revelados</strong><p>{scene.elements.filter((item) => item.visibility === "table" && item.status !== "hidden").map((item) => item.title).join(" · ") || "Nenhum"}</p></article>}</div>;
    return null;
  }
  const renderSceneCreateForm = (includeSession = false) => <div className="scene-create-form">
    <label>Título<input value={createDraft.title} onChange={(event) => setCreateDraft({ ...createDraft, title: event.target.value })} /></label>
    <label>Local<input value={createDraft.location_name} onChange={(event) => setCreateDraft({ ...createDraft, location_name: event.target.value })} /></label>
    <label>Objetivo<input value={createDraft.objective} onChange={(event) => setCreateDraft({ ...createDraft, objective: event.target.value })} /></label>
    <label>Mapa da cena<select value={createDraft.map_id} onChange={(event) => { const selected = workspaceMaps.find((item) => item.id === event.target.value); setCreateDraft({ ...createDraft, map_id: event.target.value, image_path: selected?.image_path || "", checklist: { ...createDraft.checklist, map: Boolean(event.target.value), public_image: Boolean(selected?.image_path) } }); }}><option value="">Sem mapa</option>{workspaceMaps.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
    <label>Introdução pública<textarea value={createDraft.public_description} onChange={(event) => setCreateDraft({ ...createDraft, public_description: event.target.value, checklist: { ...createDraft.checklist, opening: Boolean(event.target.value.trim()) } })} /></label>
    <label>Preparação privada<textarea value={createDraft.private_notes} onChange={(event) => setCreateDraft({ ...createDraft, private_notes: event.target.value, checklist: { ...createDraft.checklist, private_notes: Boolean(event.target.value.trim()) } })} /></label>
    {includeSession && <label>Sessão<select value={createDraft.session_id} onChange={(event) => setCreateDraft({ ...createDraft, session_id: event.target.value })}><option value="">Sem sessão</option>{sessions.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label>}
    <p className="muted">A identidade será concluída ao criar. As demais etapas terão suas ferramentas dentro da cena.</p>
    <button disabled={busy || !createDraft.title || !createDraft.location_name} onClick={() => void submitScene()}>{includeSession ? "Criar outra cena" : "Criar cena"}</button>
  </div>;

  if (loading) return <section className="panel scene-page"><p className="muted">Preparando painel de cena...</p></section>;
  if (!scene) return <section className="panel scene-page scene-empty"><div className="scene-empty-icon" aria-hidden="true">◌</div><h2>Nenhuma cena ativa</h2><p>{mode === "gm" ? "Crie uma cena e prepare mapa, pins e revelações antes de abri-la para a Mesa." : "O mestre ainda não iniciou uma cena."}</p>{notice && <p className="success-text" role="status">{notice}</p>}{error && <p className="warning-text" role="alert">{error}</p>}{mode === "gm" && renderSceneCreateForm()}</section>;

  return <section className={`panel scene-page ${surface === "live" ? "live-session-page" : "scene-admin-page"} ${touchLocked ? "touch-locked" : ""}`}>
    {surface === "live" && <div className="live-session-toolbar"><strong>Sessão em andamento</strong><button type="button" onClick={() => void document.documentElement.requestFullscreen?.()}>Modo TV</button><button type="button" onClick={() => setTouchLocked((current) => !current)}>{touchLocked ? "Desbloquear toque" : "Bloquear toque"}</button>{viewerMode === "player" && typeof Notification !== "undefined" && Notification.permission !== "granted" && <button type="button" onClick={() => void Notification.requestPermission()}>Ativar notificações</button>}</div>}
    {touchLocked && <button type="button" className="touch-unlock-button" onClick={() => setTouchLocked(false)}>Desbloquear toque</button>}
    {surface === "live" && viewerMode === "player" && notifications.slice(0, 1).map((item) => <button type="button" className="live-notification" key={item.id} onClick={() => { void markPlayerFeedRead([item.id]); void recordRuntimeEvent("notification_opened", { label: item.title, notification_id: item.id, device: window.innerWidth <= 720 ? "celular" : "desktop" }).catch(() => undefined); setNotifications((current) => current.filter((entry) => entry.id !== item.id)); }}><span>Mensagem do Mestre</span><strong>{item.title}</strong><p>{item.message}</p><small>Toque para marcar como lida</small></button>)}
    <header className="party-status-header campaign-memory-party-header">
      <div className="party-status-title"><span>Cena atual · {statusLabel(scene.status)}</span><strong>{scene.title || "Ruinas Novas"}</strong><small>⌖ {scene.location_name || "Ruinas Novas"}</small></div>
      <div className="campaign-memory-now-bar">
        <p>{scene.objective || scene.public_description || "Descobrir mais sobre as ruínas"}</p>
        <div className="campaign-now-meta">
          <button type="button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-map"))}>Abrir mapa e viagens</button>
          <span>📍 {scene.location_name || "Local ainda não definido"}</span>
          <span>👥 Grupo ainda não definido</span>
          <button type="button" className="campaign-continue" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "table" }))}>Continuar sessão</button>
        </div>
      </div>
    </header>
    <aside className={surface === "admin" ? "scene-workspace-left" : "scene-live-controls"}>
    <div className="scene-toolbar"><button onClick={() => void refresh(scene.id)}>Atualizar</button>{scenes.length > 1 && <select aria-label="Abrir outra cena" value={scene.id} onChange={(event) => { const id = Number(event.target.value); localStorage.setItem("omnisvera_selected_scene", String(id)); setSelectedId(id); void refresh(id); }}>{scenes.map((item) => <option key={item.id} value={item.id}>{item.title} · {statusLabel(item.status)}</option>)}</select>}{mode === "gm" && <>{scene.status !== "active" && scene.status !== "resolved" && <button onClick={() => void run(() => updateSceneStatus(scene.id, "active"), "Cena iniciada.", scene.id)}>Ativar</button>}{scene.status === "active" && <button onClick={() => void run(() => updateSceneStatus(scene.id, "paused"), "Cena pausada.", scene.id)}>Pausar</button>}{!(["resolved", "abandoned"].includes(scene.status)) && <button className="danger-button subtle" onClick={() => void run(() => updateSceneStatus(scene.id, "resolved", "Cena encerrada pelo Mestre."), "Cena encerrada.", scene.id)}>Encerrar</button>}</>}</div>
    {!!scene.contract_links?.length && <section className="scene-contract-links" aria-label="Contratos vinculados">
      {scene.contract_links.map((link) => <button key={link.id} onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-contract", { detail: link.contract_id }))}>
        <strong>{link.contract_title || `Contrato ${link.contract_id}`}</strong>
        <small>{link.objective_title ? `Objetivo: ${link.objective_title}` : "Contrato vinculado"}</small>
      </button>)}
    </section>}
    {notice && <p className="success-text" role="status">{notice}</p>}{error && <p className="warning-text" role="alert">{error}</p>}
    {mode === "gm" && <section className="scene-section scene-preparation-control">
      <header><div><small>Preparação privada</small><h3>Checklist da cena</h3></div><b>{checklistDone}/{SCENE_CHECKLIST.length}</b></header>
      <p className="muted">Abra uma etapa, use a ferramenta correspondente e marque-a como feita quando a preparação estiver pronta.</p>
      <div className="scene-preparation-steps">
        {SCENE_CHECKLIST.map(([key, label], index) => <details className={`scene-preparation-step ${preparation.checklist[key] ? "done" : "pending"}`} key={key} open={index === 0 && !preparation.checklist[key]}>
          <summary><span aria-hidden="true">{preparation.checklist[key] ? "✓" : index + 1}</span><strong>{label}</strong><small>{preparation.checklist[key] ? "Feito" : "Pendente"}</small></summary>
          <div className="scene-preparation-solution">
            {renderPreparationSolution(key)}
            <footer><button className={preparation.checklist[key] ? "secondary-button" : ""} disabled={busy || sceneLocked} onClick={() => void setStepDone(key, !preparation.checklist[key])}>{preparation.checklist[key] ? "Reabrir etapa" : "Marcar como feito"}</button></footer>
          </div>
        </details>)}
      </div>
      <div className="scene-preparation-actions"><button disabled={busy || sceneLocked || checklistDone < SCENE_CHECKLIST.length} onClick={() => void run(() => openSceneOnTable(scene.id, newSceneRequestId("scene-open")), "Cena aberta na Mesa; mapa e registro publicados.", scene.id)}>Abrir cena preparada na Mesa</button></div>
      <p className="muted">Abrir na Mesa ativa o mapa e seus pins. Somente pins marcados como visíveis aparecem para os jogadores.</p>
    </section>}
    {mode === "gm" && <section className="scene-section scene-publication-composer">
      <header><div><small>Versão teatral</small><h3>Publicar no registro da Mesa</h3></div></header>
      <div className="scene-create-form">
        <select aria-label="Tipo de publicação" value={publicationDraft.publication_type} onChange={(event) => setPublicationDraft({ ...publicationDraft, publication_type: event.target.value })}><option value="opening">Abertura</option><option value="npc">NPC</option><option value="creature">Criatura</option><option value="clue">Descoberta ou pista</option><option value="treasure">Tesouro ou loot</option><option value="state">Estado público</option><option value="environment">Ambiente</option><option value="image">Imagem</option><option value="other">Outro</option></select>
        <input aria-label="Título público" placeholder="Título que os jogadores verão" value={publicationDraft.title} onChange={(event) => setPublicationDraft({ ...publicationDraft, title: event.target.value })} />
        <textarea aria-label="Texto público" placeholder="O que entrou em cena ou foi descoberto" value={publicationDraft.public_text} onChange={(event) => setPublicationDraft({ ...publicationDraft, public_text: event.target.value })} />
        <textarea aria-label="Nota privada da publicação" placeholder="Nota privada opcional; não vai para os jogadores" value={publicationDraft.private_text} onChange={(event) => setPublicationDraft({ ...publicationDraft, private_text: event.target.value })} />
        <button disabled={busy || !publicationDraft.title.trim()} onClick={() => void publishToTable()}>Publicar para jogadores</button>
      </div>
    </section>}
    {surface === "admin" && mode === "gm" && <details className="scene-admin-details scene-notification-composer"><summary>Enviar notificação para celular</summary><div className="scene-create-form"><select value={notificationDraft.profile_id} onChange={(event) => setNotificationDraft({ ...notificationDraft, profile_id: event.target.value })}><option value="group">Todos os jogadores</option>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><input value={notificationDraft.title} onChange={(event) => setNotificationDraft({ ...notificationDraft, title: event.target.value })} placeholder="Título" /><textarea value={notificationDraft.message} onChange={(event) => setNotificationDraft({ ...notificationDraft, message: event.target.value })} placeholder="Mensagem para o jogador" /><button disabled={busy || !notificationDraft.title.trim() || !notificationDraft.message.trim()} onClick={() => void sendNotification()}>Enviar notificação</button></div></details>}
    {mode === "gm" && scene.private_notes && <section className="scene-section scene-private-prep"><header><div><small>Somente Mestre</small><h3>Preparação da cena</h3></div></header><p>{scene.private_notes}</p></section>}

    {mode === "gm" && <section className="scene-section scene-npc-picker"><header><div><small>Preparação</small><h3>NPCs e inimigos</h3></div></header><div className="scene-inline-form"><select aria-label="NPC participante" value={npcId} onChange={(event) => setNpcId(event.target.value)}><option value="">Selecionar NPC...</option>{npcs.map((npc) => <option key={npc.id} value={npc.id}>{npc.name}</option>)}</select><button disabled={!npcId || busy} onClick={() => { const npc = npcs.find((item) => item.id === Number(npcId)); if (npc) void run(() => addSceneParticipant(scene.id, { participant_type: "npc", npc_name: npc.name, npc_source: `npc:${npc.id}`, public_label: npc.name, public_status: npc.public_status || "Presente", visible_to_players: npc.visible_to_players }), "NPC adicionado à cena.", scene.id); }}>Adicionar NPC</button></div><div className="scene-inline-form"><select aria-label="Inimigo preparado" value={monsterTokenId} onChange={(event) => setMonsterTokenId(event.target.value)}><option value="">Inimigo do mapa preparado...</option>{preparedMapMonsters.map((token) => <option key={token.id} value={token.id}>{token.name}</option>)}</select><button disabled={!monsterTokenId || busy} onClick={() => { const token = preparedMapMonsters.find((item) => item.id === monsterTokenId); if (token) void run(() => addSceneParticipant(scene.id, { participant_type: "creature", npc_name: token.name, npc_source: `map-token:${token.id}`, public_label: token.name, public_status: "Oculto", private_status: `${token.current_hp ?? "—"}/${token.maximum_hp ?? "—"} PV`, visible_to_players: false }), "Inimigo preparado e oculto.", scene.id); }}>Preparar oculto</button></div></section>}
    {mode === "gm" && <details className="scene-admin-details scene-create-another"><summary>Administração de sessão e nova cena</summary><div className="scene-create-form"><label>Nova sessão<input value={sessionTitle} onChange={(event) => setSessionTitle(event.target.value)} /></label><button disabled={!sessionTitle || busy} onClick={() => void run(async () => { const session = await createGameSession({ request_id: newSceneRequestId("session"), title: sessionTitle }); await updateGameSessionStatus(session.id, "active"); setSessionTitle(""); }, "Sessão criada.", scene.id)}>Criar sessão</button></div>{renderSceneCreateForm(true)}</details>}
    </aside>

    <div className="scene-layout">
      <div className="scene-main-column">
        <section className="scene-section"><header><div><small>Elenco em cena</small><h3>Ordem definida pelo Mestre</h3></div><b>{activeParticipants.length}</b></header><div className="scene-participant-grid">{activeParticipants.map((participant, index) => <div className={`scene-ordered-participant ${participant.public_status === "Agindo agora" ? "current" : ""}`} key={participant.id}><ParticipantCard participant={participant} mode={mode} sceneId={scene.id} onRefresh={() => refresh(scene.id)} />{mode === "gm" && <div className="scene-order-controls"><button disabled={busy || index === 0} onClick={() => void moveParticipant(index, -1)}>Subir</button><button disabled={busy || index === activeParticipants.length - 1} onClick={() => void moveParticipant(index, 1)}>Descer</button><button disabled={busy || participant.public_status === "Agindo agora"} onClick={() => void setCurrentParticipant(participant.id)}>É a vez</button></div>}</div>)}</div>{mode === "gm" && <div className="scene-inline-form"><select aria-label="Personagem participante" value={participantId} onChange={(event) => setParticipantId(event.target.value)}><option value="">Adicionar personagem...</option>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><button disabled={!participantId || busy} onClick={() => { const character = characters.find((item) => item.id === participantId); if (character) void run(() => addSceneParticipant(scene.id, { participant_type: "player_character", character_id: character.id, public_label: character.name, public_status: "Presente", visible_to_players: true }), "Participante adicionado.", scene.id); }}>Adicionar</button></div>}</section>

        <section className="scene-section"><header><div><small>O que está em jogo</small><h3>Pistas, ameaças e caminhos</h3></div></header><div className="scene-elements">{scene.elements.length ? scene.elements.map((element) => <article key={element.id} className={`scene-element ${element.element_type}`}><span aria-hidden="true">{element.element_type === "clue" ? "⌕" : element.element_type === "threat" ? "⚠" : "◇"}</span><div><strong>{element.title}</strong><small>{statusLabel(element.status)}</small><p>{element.public_description || (mode === "gm" ? element.private_description : "")}</p></div>{mode === "gm" && element.visibility !== "table" && <button disabled={busy} onClick={() => void run(() => revealSceneElement(element.id), "Elemento revelado.", scene.id)}>Revelar</button>}</article>) : <p className="sheet-empty">Nenhum elemento revelado.</p>}</div>{mode === "gm" && <details className="scene-admin-details"><summary>Criar pista ou ameaça</summary><div className="scene-create-form"><select value={elementDraft.element_type} onChange={(event) => setElementDraft({ ...elementDraft, element_type: event.target.value })}><option value="clue">Pista</option><option value="threat">Ameaça</option><option value="objective">Objetivo</option><option value="object">Objeto</option><option value="exit">Saída</option><option value="environmental_effect">Efeito ambiental</option></select><input aria-label="Título do elemento" placeholder="Título" value={elementDraft.title} onChange={(event) => setElementDraft({ ...elementDraft, title: event.target.value })} /><textarea aria-label="Descrição pública do elemento" placeholder="Descrição pública" value={elementDraft.public_description} onChange={(event) => setElementDraft({ ...elementDraft, public_description: event.target.value })} /><textarea aria-label="Descrição privada do elemento" placeholder="Notas do Mestre" value={elementDraft.private_description} onChange={(event) => setElementDraft({ ...elementDraft, private_description: event.target.value })} /><button disabled={!elementDraft.title || busy} onClick={() => void run(() => createSceneElement(scene.id, { request_id: newSceneRequestId("element"), ...elementDraft, status: "hidden", visibility: "gm" }), "Elemento criado.", scene.id)}>Criar oculto</button></div></details>}</section>

        <section className="scene-section scene-actions-section"><header><div><small>Intenções da mesa</small><h3>Ações declaradas</h3></div></header>{scene.status === "active" ? <div className="scene-action-composer"><div className="scene-action-types">{ACTIONS.map(([key, label, icon]) => <button key={key} className={actionType === key ? "active" : ""} onClick={() => setActionType(key)}><span>{icon}</span><small>{label}</small></button>)}</div><textarea aria-label="Descrição da ação" maxLength={600} placeholder="Descreva o que seu personagem tenta fazer..." value={actionText} onChange={(event) => setActionText(event.target.value)} /><input aria-label="Alvo da ação" maxLength={180} placeholder="Alvo opcional" value={actionTarget} onChange={(event) => setActionTarget(event.target.value)} /><button disabled={busy || !actionText.trim()} onClick={() => void declare()}>Declarar ação</button></div> : <p className="sheet-empty">A cena não aceita novas ações.</p>}
        <div className="scene-action-list">{scene.actions.map((action) => <article key={action.id} className={`scene-action-card ${action.status}`}><header><strong>{ACTIONS.find(([key]) => key === action.action_type)?.[1] || "Ação"}</strong><span>{statusLabel(action.status)}</span></header><p>{action.description}</p>{action.target_label && <small>Alvo: {action.target_label}</small>}{action.resolution && <blockquote>{action.resolution}</blockquote>}{action.rejection_reason && <blockquote>{action.rejection_reason}</blockquote>}{mode === "gm" && ["declared", "awaiting_roll"].includes(action.status) && <div className="scene-resolution-controls"><input aria-label={`Resolução da ação ${action.id}`} placeholder="Resolução ou motivo" value={resolution[action.id] || ""} onChange={(event) => setResolution({ ...resolution, [action.id]: event.target.value })} />{action.status === "declared" && <button onClick={() => void run(() => requestSceneActionRoll(action.id, { request_id: newSceneRequestId("scene-roll"), roll_type: "attribute", source_id: "strength", visibility: "owner", label: "Teste solicitado pela cena" }), "Rolagem solicitada.", scene.id)}>Solicitar FOR</button>}<button onClick={() => void run(() => resolveSceneAction(action.id, resolution[action.id]), "Ação resolvida.", scene.id)}>Resolver</button><button className="danger-button subtle" disabled={!resolution[action.id]} onClick={() => void run(() => rejectSceneAction(action.id, resolution[action.id]), "Ação rejeitada.", scene.id)}>Rejeitar</button></div>}</article>)}</div></section>
      </div>

      <aside className="scene-history"><header><small>Registro persistente</small><h3>Histórico da cena</h3></header>{scene.events.length ? scene.events.map((event) => <article key={event.id} className={event.voided ? "voided" : ""}><span aria-hidden="true">{event.roll ? "⚄" : event.event_type.includes("clue") || event.event_type.includes("element") ? "⌕" : "•"}</span><div><strong>{event.title}</strong><p>{event.public_text || (mode === "gm" ? event.private_text : "")}</p>{event.roll && <em>{event.roll.dice}: {event.roll.individual_results.join(" + ")}{event.roll.modifier ? ` ${event.roll.modifier > 0 ? "+" : "−"} ${Math.abs(event.roll.modifier)}` : ""} = {event.roll.total}</em>}<small>{time(event.created_at)} · {event.visibility === "table" ? "Mesa" : "Reservado"}</small></div></article>) : <p className="sheet-empty">A cena ainda não possui eventos.</p>}</aside>
    </div>

  </section>;
}
