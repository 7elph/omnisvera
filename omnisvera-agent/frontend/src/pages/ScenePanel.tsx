import { useEffect, useMemo, useState } from "react";
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
  listGameSessions,
  listPlayableCharacters,
  listNpcs,
  listScenes,
  mediaUrlFromVaultPath,
  newSceneRequestId,
  PlayableCharacterSummary,
  NpcRecord,
  newNpcRequestId,
  recordNpcEncounter,
  rejectSceneAction,
  requestSceneActionRoll,
  resolveSceneAction,
  revealSceneElement,
  updateGameSessionStatus,
  updateSceneStatus,
} from "../api";

const ACTIONS = [
  ["talk", "Conversar", "☷"], ["investigate", "Investigar", "⌕"], ["observe", "Observar", "◉"],
  ["move", "Mover-se", "➜"], ["use_item", "Usar item", "◇"], ["interact", "Interagir", "✋"],
  ["attack", "Atacar", "⚔"], ["other", "Outra ação", "+"],
];

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
  </article>;
}

export default function ScenePanel({ mode }: { mode: "gm" | "player" }) {
  const [scene, setScene] = useState<GameScene | null>(null);
  const [scenes, setScenes] = useState<GameScene[]>([]);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [npcs, setNpcs] = useState<NpcRecord[]>([]);
  const [sessions, setSessions] = useState<Array<{ id: number; title: string; status: string }>>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [createDraft, setCreateDraft] = useState({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", session_id: "" });
  const [sessionTitle, setSessionTitle] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [npcId, setNpcId] = useState("");
  const [elementDraft, setElementDraft] = useState({ element_type: "clue", title: "", public_description: "", private_description: "" });
  const [actionType, setActionType] = useState("investigate");
  const [actionText, setActionText] = useState("");
  const [actionTarget, setActionTarget] = useState("");
  const [resolution, setResolution] = useState<Record<number, string>>({});

  async function refresh(preferredId?: number | null) {
    try {
      const [active, all] = await Promise.all([getActiveScene(), listScenes()]);
      setScenes(all);
      if (mode === "gm") setSessions(await listGameSessions());
      const wanted = preferredId ?? selectedId ?? storedSceneId() ?? active?.id ?? all[0]?.id ?? null;
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

  async function run(operation: () => Promise<unknown>, message: string, preferredId?: number) {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try { await operation(); setNotice(message); await refresh(preferredId); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "A operação não pôde ser concluída."); }
    finally { setBusy(false); }
  }

  async function submitScene() {
    await run(async () => {
      const created = await createScene({ request_id: newSceneRequestId("scene"), ...createDraft, session_id: createDraft.session_id ? Number(createDraft.session_id) : undefined, visibility: "table" });
      setCreateDraft({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", session_id: "" });
      setSelectedId(created.id);
    }, "Cena criada.");
  }

  async function declare() {
    if (!scene || !actionText.trim()) return;
    await run(() => declareSceneAction(scene.id, { request_id: newSceneRequestId("action"), action_type: actionType, description: actionText, target_label: actionTarget || undefined, visibility: "table" }), "Ação declarada.", scene.id);
    setActionText(""); setActionTarget("");
  }

  const activeParticipants = useMemo(() => scene?.participants.filter((item) => !item.left_at) || [], [scene]);

  if (loading) return <section className="panel scene-page"><p className="muted">Preparando painel de cena...</p></section>;
  if (!scene) return <section className="panel scene-page scene-empty"><div className="scene-empty-icon" aria-hidden="true">◌</div><h2>Nenhuma cena ativa</h2><p>{mode === "gm" ? "Crie uma cena para reunir participantes, ações, pistas e rolagens da mesa." : "O mestre ainda não iniciou uma cena."}</p>{notice && <p className="success-text" role="status">{notice}</p>}{error && <p className="warning-text" role="alert">{error}</p>}{mode === "gm" && <div className="scene-create-form"><label>Título<input value={createDraft.title} onChange={(event) => setCreateDraft({ ...createDraft, title: event.target.value })} /></label><label>Local<input value={createDraft.location_name} onChange={(event) => setCreateDraft({ ...createDraft, location_name: event.target.value })} /></label><label>Objetivo<input value={createDraft.objective} onChange={(event) => setCreateDraft({ ...createDraft, objective: event.target.value })} /></label><button disabled={busy || !createDraft.title || !createDraft.location_name} onClick={() => void submitScene()}>Criar cena</button></div>}</section>;

  return <section className="panel scene-page">
    <header className="scene-hero"><div><p className="eyebrow">Cena atual · {statusLabel(scene.status)}</p><h2>{scene.title}</h2><p className="scene-location">⌖ {scene.location_name}</p><p>{scene.public_description}</p></div><div className="scene-objective"><small>Objetivo</small><strong>{scene.objective || "Não informado"}</strong></div></header>
    <div className="scene-toolbar"><button onClick={() => void refresh(scene.id)}>Atualizar</button>{scenes.length > 1 && <select aria-label="Abrir outra cena" value={scene.id} onChange={(event) => { const id = Number(event.target.value); localStorage.setItem("omnisvera_selected_scene", String(id)); setSelectedId(id); void refresh(id); }}>{scenes.map((item) => <option key={item.id} value={item.id}>{item.title} · {statusLabel(item.status)}</option>)}</select>}{mode === "gm" && <>{scene.status !== "active" && scene.status !== "resolved" && <button onClick={() => void run(() => updateSceneStatus(scene.id, "active"), "Cena iniciada.", scene.id)}>Ativar</button>}{scene.status === "active" && <button onClick={() => void run(() => updateSceneStatus(scene.id, "paused"), "Cena pausada.", scene.id)}>Pausar</button>}{!(["resolved", "abandoned"].includes(scene.status)) && <button className="danger-button subtle" onClick={() => void run(() => updateSceneStatus(scene.id, "resolved", "Cena encerrada pelo Mestre."), "Cena encerrada.", scene.id)}>Encerrar</button>}</>}</div>
    {!!scene.contract_links?.length && <section className="scene-contract-links" aria-label="Contratos vinculados">
      {scene.contract_links.map((link) => <button key={link.id} onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-contract", { detail: link.contract_id }))}>
        <strong>{link.contract_title || `Contrato ${link.contract_id}`}</strong>
        <small>{link.objective_title ? `Objetivo: ${link.objective_title}` : "Contrato vinculado"}</small>
      </button>)}
    </section>}
    {notice && <p className="success-text" role="status">{notice}</p>}{error && <p className="warning-text" role="alert">{error}</p>}

    {mode === "gm" && <section className="scene-section scene-npc-picker"><header><div><small>Continuidade</small><h3>Adicionar NPC existente</h3></div></header><div className="scene-inline-form"><select aria-label="NPC participante" value={npcId} onChange={(event) => setNpcId(event.target.value)}><option value="">Selecionar NPC...</option>{npcs.map((npc) => <option key={npc.id} value={npc.id}>{npc.name}</option>)}</select><button disabled={!npcId || busy} onClick={() => { const npc = npcs.find((item) => item.id === Number(npcId)); if (npc) void run(() => addSceneParticipant(scene.id, { participant_type: "npc", npc_name: npc.name, npc_source: `npc:${npc.id}`, public_label: npc.name, public_status: npc.public_status || "Presente", visible_to_players: npc.visible_to_players }), "NPC adicionado à cena.", scene.id); }}>Adicionar NPC</button></div></section>}

    <div className="scene-layout">
      <div className="scene-main-column">
        <section className="scene-section"><header><div><small>Elenco em cena</small><h3>Participantes</h3></div><b>{activeParticipants.length}</b></header><div className="scene-participant-grid">{activeParticipants.map((participant) => <ParticipantCard key={participant.id} participant={participant} mode={mode} sceneId={scene.id} onRefresh={() => refresh(scene.id)} />)}</div>{mode === "gm" && <div className="scene-inline-form"><select aria-label="Personagem participante" value={participantId} onChange={(event) => setParticipantId(event.target.value)}><option value="">Adicionar personagem...</option>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><button disabled={!participantId || busy} onClick={() => { const character = characters.find((item) => item.id === participantId); if (character) void run(() => addSceneParticipant(scene.id, { participant_type: "player_character", character_id: character.id, public_label: character.name, public_status: "Ativo", visible_to_players: true }), "Participante adicionado.", scene.id); }}>Adicionar</button></div>}</section>

        <section className="scene-section"><header><div><small>O que está em jogo</small><h3>Pistas, ameaças e caminhos</h3></div></header><div className="scene-elements">{scene.elements.length ? scene.elements.map((element) => <article key={element.id} className={`scene-element ${element.element_type}`}><span aria-hidden="true">{element.element_type === "clue" ? "⌕" : element.element_type === "threat" ? "⚠" : "◇"}</span><div><strong>{element.title}</strong><small>{statusLabel(element.status)}</small><p>{element.public_description || (mode === "gm" ? element.private_description : "")}</p></div>{mode === "gm" && element.visibility !== "table" && <button disabled={busy} onClick={() => void run(() => revealSceneElement(element.id), "Elemento revelado.", scene.id)}>Revelar</button>}</article>) : <p className="sheet-empty">Nenhum elemento revelado.</p>}</div>{mode === "gm" && <details className="scene-admin-details"><summary>Criar pista ou ameaça</summary><div className="scene-create-form"><select value={elementDraft.element_type} onChange={(event) => setElementDraft({ ...elementDraft, element_type: event.target.value })}><option value="clue">Pista</option><option value="threat">Ameaça</option><option value="objective">Objetivo</option><option value="object">Objeto</option><option value="exit">Saída</option><option value="environmental_effect">Efeito ambiental</option></select><input aria-label="Título do elemento" placeholder="Título" value={elementDraft.title} onChange={(event) => setElementDraft({ ...elementDraft, title: event.target.value })} /><textarea aria-label="Descrição pública do elemento" placeholder="Descrição pública" value={elementDraft.public_description} onChange={(event) => setElementDraft({ ...elementDraft, public_description: event.target.value })} /><textarea aria-label="Descrição privada do elemento" placeholder="Notas do Mestre" value={elementDraft.private_description} onChange={(event) => setElementDraft({ ...elementDraft, private_description: event.target.value })} /><button disabled={!elementDraft.title || busy} onClick={() => void run(() => createSceneElement(scene.id, { request_id: newSceneRequestId("element"), ...elementDraft, status: "hidden", visibility: "gm" }), "Elemento criado.", scene.id)}>Criar oculto</button></div></details>}</section>

        <section className="scene-section scene-actions-section"><header><div><small>Intenções da mesa</small><h3>Ações declaradas</h3></div></header>{scene.status === "active" ? <div className="scene-action-composer"><div className="scene-action-types">{ACTIONS.map(([key, label, icon]) => <button key={key} className={actionType === key ? "active" : ""} onClick={() => setActionType(key)}><span>{icon}</span><small>{label}</small></button>)}</div><textarea aria-label="Descrição da ação" maxLength={600} placeholder="Descreva o que seu personagem tenta fazer..." value={actionText} onChange={(event) => setActionText(event.target.value)} /><input aria-label="Alvo da ação" maxLength={180} placeholder="Alvo opcional" value={actionTarget} onChange={(event) => setActionTarget(event.target.value)} /><button disabled={busy || !actionText.trim()} onClick={() => void declare()}>Declarar ação</button></div> : <p className="sheet-empty">A cena não aceita novas ações.</p>}
        <div className="scene-action-list">{scene.actions.map((action) => <article key={action.id} className={`scene-action-card ${action.status}`}><header><strong>{ACTIONS.find(([key]) => key === action.action_type)?.[1] || "Ação"}</strong><span>{statusLabel(action.status)}</span></header><p>{action.description}</p>{action.target_label && <small>Alvo: {action.target_label}</small>}{action.resolution && <blockquote>{action.resolution}</blockquote>}{action.rejection_reason && <blockquote>{action.rejection_reason}</blockquote>}{mode === "gm" && ["declared", "awaiting_roll"].includes(action.status) && <div className="scene-resolution-controls"><input aria-label={`Resolução da ação ${action.id}`} placeholder="Resolução ou motivo" value={resolution[action.id] || ""} onChange={(event) => setResolution({ ...resolution, [action.id]: event.target.value })} />{action.status === "declared" && <button onClick={() => void run(() => requestSceneActionRoll(action.id, { request_id: newSceneRequestId("scene-roll"), roll_type: "attribute", source_id: "strength", visibility: "owner", label: "Teste solicitado pela cena" }), "Rolagem solicitada.", scene.id)}>Solicitar FOR</button>}<button onClick={() => void run(() => resolveSceneAction(action.id, resolution[action.id]), "Ação resolvida.", scene.id)}>Resolver</button><button className="danger-button subtle" disabled={!resolution[action.id]} onClick={() => void run(() => rejectSceneAction(action.id, resolution[action.id]), "Ação rejeitada.", scene.id)}>Rejeitar</button></div>}</article>)}</div></section>
      </div>

      <aside className="scene-history"><header><small>Registro persistente</small><h3>Histórico da cena</h3></header>{scene.events.length ? scene.events.map((event) => <article key={event.id} className={event.voided ? "voided" : ""}><span aria-hidden="true">{event.roll ? "⚄" : event.event_type.includes("clue") || event.event_type.includes("element") ? "⌕" : "•"}</span><div><strong>{event.title}</strong><p>{event.public_text || (mode === "gm" ? event.private_text : "")}</p>{event.roll && <em>{event.roll.dice}: {event.roll.individual_results.join(" + ")}{event.roll.modifier ? ` ${event.roll.modifier > 0 ? "+" : "−"} ${Math.abs(event.roll.modifier)}` : ""} = {event.roll.total}</em>}<small>{time(event.created_at)} · {event.visibility === "table" ? "Mesa" : "Reservado"}</small></div></article>) : <p className="sheet-empty">A cena ainda não possui eventos.</p>}</aside>
    </div>

    {mode === "gm" && <details className="scene-admin-details scene-create-another"><summary>Administração de sessão e nova cena</summary><div className="scene-create-form"><label>Nova sessão<input value={sessionTitle} onChange={(event) => setSessionTitle(event.target.value)} /></label><button disabled={!sessionTitle || busy} onClick={() => void run(async () => { const session = await createGameSession({ request_id: newSceneRequestId("session"), title: sessionTitle }); await updateGameSessionStatus(session.id, "active"); setSessionTitle(""); }, "Sessão criada.", scene.id)}>Criar sessão</button><label>Título da cena<input value={createDraft.title} onChange={(event) => setCreateDraft({ ...createDraft, title: event.target.value })} /></label><label>Local<input value={createDraft.location_name} onChange={(event) => setCreateDraft({ ...createDraft, location_name: event.target.value })} /></label><label>Objetivo<input value={createDraft.objective} onChange={(event) => setCreateDraft({ ...createDraft, objective: event.target.value })} /></label><label>Sessão<select value={createDraft.session_id} onChange={(event) => setCreateDraft({ ...createDraft, session_id: event.target.value })}><option value="">Sem sessão</option>{sessions.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><button disabled={busy || !createDraft.title || !createDraft.location_name} onClick={() => void submitScene()}>Criar outra cena</button></div></details>}
  </section>;
}
