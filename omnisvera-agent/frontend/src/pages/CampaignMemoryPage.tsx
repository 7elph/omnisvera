import { useEffect, useMemo, useState } from "react";
import {
  CampaignNarrativeEntry,
  CampaignSession,
  ContractRecord,
  GameScene,
  getCurrentOperationalContract,
  getActiveScene,
  listCampaignSessions,
  listContracts,
  listPlayableCharacters,
  mediaUrlFromVaultPath,
  PlayableCharacterSummary,
  updateGameSessionMetadata,
  uploadGameSessionImage,
} from "../api";
import ConclaveHub from "./ConclaveHub";
import MasterAssetPanel from "./MasterAssetPanel";

type Props = {
  mode: "gm" | "player";
  view: "history" | "missions";
  onViewChange: (view: "history" | "missions") => void;
};

type SessionMemory = {
  key: string;
  session: CampaignSession;
  number?: number | null;
  title: string;
  status: string;
  date?: string | null;
  participants: Array<{ id?: string | null; name: string; portrait?: string | null }>;
  summary: string;
  chronicle: string;
  image?: string | null;
  tags: string[];
  discoveries: CampaignNarrativeEntry[];
  consequences: CampaignNarrativeEntry[];
  rewards: CampaignNarrativeEntry[];
  items: CampaignNarrativeEntry[];
  openThreads: CampaignNarrativeEntry[];
};

function dateLabel(value?: string | null) {
  if (!value) return "Data não registrada";
  return new Date(value).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
}

function buildMemories(sessions: CampaignSession[], characters: PlayableCharacterSummary[]): SessionMemory[] {
  const characterById = new Map(characters.map((character) => [character.id, character]));
  return sessions.map((session) => {
    const narrative = session.narrative || {
      participants: [], locations: [], missions: [], discoveries: [], rewards: [], items_acquired: [],
      world_events: [], character_events: [], open_threads: [], tags: [],
    };
    return {
      key: `session:${session.id}`,
      session,
      number: session.session_number,
      title: session.title,
      status: session.status,
      // The import timestamp is provenance, not the date when the table met.
      // Historical sessions without an evidenced date must stay explicitly undated.
      date: session.ended_at || session.started_at,
      participants: narrative.participants.map((participant) => {
        const character = participant.character_id ? characterById.get(participant.character_id) : undefined;
        return { id: participant.character_id, name: participant.name, portrait: participant.portrait || character?.portrait };
      }),
      summary: session.public_summary || "Esta sessão ainda não possui um resumo narrativo público.",
      chronicle: session.public_chronicle || session.public_summary || "A crônica desta sessão ainda não foi registrada pelo Mestre.",
      image: session.image_path,
      tags: narrative.tags || [],
      discoveries: narrative.discoveries || [],
      consequences: narrative.world_events || [],
      rewards: narrative.rewards || [],
      items: narrative.items_acquired || [],
      openThreads: narrative.open_threads || [],
    };
  });
}

function entryText(entry: CampaignNarrativeEntry) {
  return entry.description || entry.status || "Registro da sessão.";
}

export default function CampaignMemoryPage({ mode, view, onViewChange }: Props) {
  const [sessions, setSessions] = useState<CampaignSession[]>([]);
  const [activeScene, setActiveScene] = useState<GameScene | null>(null);
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sessionDate, setSessionDate] = useState("");
  const [sessionImage, setSessionImage] = useState<File | null>(null);
  const [sessionEditBusy, setSessionEditBusy] = useState(false);
  const [sessionEditNotice, setSessionEditNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async (initial = false) => {
      if (initial) setLoading(true);
      try {
        const [sessionRows, active, contractRows, roster] = await Promise.all([
          listCampaignSessions(),
          getActiveScene(),
          listContracts(),
          listPlayableCharacters(),
        ]);
        if (cancelled) return;
        setSessions(sessionRows);
        setActiveScene(active);
        setContracts(contractRows);
        setCharacters(roster);
        setError("");
      } catch (cause) {
        if (!cancelled && initial) setError(cause instanceof Error ? cause.message : "Não foi possível carregar a memória da campanha.");
      } finally {
        if (!cancelled && initial) setLoading(false);
      }
    };
    const refresh = () => void load(false);
    const refreshWhenVisible = () => { if (document.visibilityState === "visible") refresh(); };
    void load(true);
    const timer = window.setInterval(refresh, 10_000);
    window.addEventListener("omnisvera-scene-updated", refresh);
    window.addEventListener("omnisvera-session-changed", refresh);
    window.addEventListener("online", refresh);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener("omnisvera-scene-updated", refresh);
      window.removeEventListener("omnisvera-session-changed", refresh);
      window.removeEventListener("online", refresh);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, [mode]);

  const memories = useMemo(() => buildMemories(sessions, characters), [sessions, characters]);
  const selected = memories.find((memory) => memory.key === selectedKey) || null;

  useEffect(() => {
    setSessionDate(selected?.date ? selected.date.slice(0, 10) : "");
    setSessionImage(null);
    setSessionEditNotice("");
  }, [selected?.key]);

  async function saveSessionMetadata() {
    if (!selected || mode !== "gm" || sessionEditBusy) return;
    setSessionEditBusy(true);
    setSessionEditNotice("");
    setError("");
    try {
      let updated = selected.session;
      if (sessionImage) updated = await uploadGameSessionImage(selected.session.id, sessionImage);
      updated = await updateGameSessionMetadata(selected.session.id, { played_on: sessionDate || null });
      setSessions((current) => current.map((session) => session.id === updated.id ? updated : session));
      setSessionImage(null);
      setSessionEditNotice("Data e imagem da sessão salvas.");
    } catch (cause) {
      setSessionEditNotice(cause instanceof Error ? cause.message : "Não foi possível salvar a sessão.");
    } finally {
      setSessionEditBusy(false);
    }
  }
  const activeContract = getCurrentOperationalContract(contracts);
  const activeSession = sessions.find((session) => session.status === "active") || null;
  // A scene is live only inside an operational session. This also protects the
  // player UI from legacy/orphaned active-scene rows left by older builds.
  const liveScene = activeSession ? activeScene : null;
  const currentTitle = liveScene?.title || activeContract?.title || activeSession?.title || "A próxima aventura ainda não começou";
  const currentSummary = liveScene?.public_description || liveScene?.objective || activeContract?.public_briefing || activeContract?.public_summary || activeSession?.public_summary || "Quando o Mestre abrir a próxima etapa, o ponto atual da campanha aparecerá aqui.";
  const currentLocation = liveScene?.location_name || activeContract?.location_name || "Local ainda não definido";
  const currentParticipants = liveScene?.participants || [];
  const ownerCharacterId = characters.find((character) => character.access_level === "owner")?.id || null;
  const canOpenTable = mode === "gm" || Boolean(activeSession);
  const latest = memories.slice(0, 4);
  const recap = [...latest].reverse().map((memory) => memory.summary).filter((text) => !text.startsWith("Esta sessão ainda")).join("\n\n");
  const stories = [
    ...contracts.filter((contract) => ["published", "accepted", "active"].includes(contract.status)).map((contract) => ({ key: `contract:${contract.id}`, title: contract.title, text: contract.public_summary || contract.public_briefing })),
    ...latest.flatMap((memory) => memory.openThreads.map((thread, index) => ({ key: `${memory.key}:thread:${index}`, title: thread.title || "Mistério", text: thread.description || "Esta história continua em aberto." }))),
  ].filter((story, index, all) => all.findIndex((candidate) => candidate.title === story.title) === index);

  if (loading) return <section className="campaign-memory-layout campaign-memory-loading"><p>Recuperando a memória da campanha…</p></section>;
  if (error) return <section className="campaign-memory-layout campaign-memory-loading"><p className="error">{error}</p></section>;

  return <section className="campaign-memory-layout">
    <header className="party-status-header campaign-memory-party-header">
      <div className="party-status-title"><span>AGORA</span><strong>{currentTitle}</strong><small>{activeContract?.risk_label || "Campanha em andamento"}</small></div>
      <div className="campaign-memory-now-bar">
        <p>{currentSummary}</p>
        <div className="campaign-now-meta"><div className="campaign-view-switch" aria-label="Conteúdo da sessão"><button type="button" className={view === "history" ? "active" : ""} onClick={() => onViewChange("history")}>Histórico</button><button type="button" className={view === "missions" ? "active" : ""} onClick={() => onViewChange("missions")}>Missões</button></div><button type="button">📍 {currentLocation}</button><span>👥 {currentParticipants.length ? currentParticipants.map((item) => item.public_label).join(" • ") : "Grupo ainda não definido"}</span>{mode === "player" && <button type="button" disabled={!canOpenTable} onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "table" }))}>Minha ficha</button>}<button type="button" className="campaign-continue" disabled={!canOpenTable} onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: "table" }))}>{canOpenTable ? "Continuar sessão" : "Aguardando Mestre"}</button></div>
      </div>
    </header>

    {view === "missions" ? <section className="campaign-missions-panel">
      <ConclaveHub mode={mode} embedded onOpenScene={(sceneId) => window.dispatchEvent(new CustomEvent("omnisvera-open-workspace", { detail: sceneId ? "scenes" : "table" }))} />
    </section> : <>
    <aside className="workspace-character-panel campaign-memory-current">
        <section className="campaign-section campaign-stories-panel"><header><small>HISTÓRIAS EM ANDAMENTO</small><span>{stories.length}</span></header><div className="campaign-story-list">{stories.length ? stories.map((story) => <article key={story.key}><h3>{story.title}</h3><p>{story.text || "Esta história continua em aberto."}</p></article>) : <p>Nenhuma história pública está marcada como ativa.</p>}</div></section>
        {mode === "gm" && <details className="campaign-gm-layer"><summary>Modo Mestre</summary><div><article><small>FOCO ATUAL</small><strong>{currentTitle}</strong><p>{liveScene?.private_notes || activeContract?.private_briefing || "Sem notas privadas para o foco atual."}</p></article><article><small>MEMÓRIA HISTÓRICA</small><strong>{sessions.length} sessões consolidadas</strong><p>Feedback técnico e proveniência permanecem visíveis somente para o Mestre.</p></article><MasterAssetPanel /></div></details>}
    </aside>

    <aside className="workspace-timeline-panel campaign-memory-timeline">
        <header><div><small>MEMÓRIA DA CAMPANHA</small><h2>{selected ? selected.title : "Anteriormente em Omnisvera"}</h2></div><span>{selected?.number || latest.length}</span></header>
        <div className="campaign-memory-scroll">{selected ? <>
          <button type="button" className="campaign-back" onClick={() => setSelectedKey(null)}>← Voltar para a campanha</button>
          <header className="campaign-detail-hero">{selected.image && <img src={mediaUrlFromVaultPath(selected.image)} alt="" />}<div><small>{selected.number ? `SESSÃO ${selected.number}` : "MEMÓRIA DA CAMPANHA"}</small><h1>{selected.title}</h1><time>{dateLabel(selected.date)}</time></div></header>
          <section className="campaign-chronicle"><small>CRÔNICA</small>{selected.chronicle.split("\n\n").map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>
          <section className="campaign-detail-section"><small>PARTICIPANTES</small><div className="campaign-character-grid">{selected.participants.length ? selected.participants.map((participant) => {
            const canOpenCharacter = mode === "gm" || Boolean(participant.id && participant.id === ownerCharacterId);
            return <button key={participant.name} type="button" disabled={!canOpenCharacter} title={canOpenCharacter ? `Abrir ficha de ${participant.name}` : "Apenas sua própria ficha pode ser aberta"} onClick={() => canOpenCharacter && participant.id && window.dispatchEvent(new CustomEvent("omnisvera-view-character", { detail: participant.id }))}>{participant.portrait ? <img src={mediaUrlFromVaultPath(participant.portrait)} alt="" /> : <i>{participant.name.slice(0, 1)}</i>}<span>{participant.name}</span></button>;
          }) : <p>Participantes não registrados.</p>}</div></section>
          {selected.discoveries.length > 0 && <section className="campaign-detail-section"><small>DESCOBERTAS</small><div className="campaign-discovery-list">{selected.discoveries.map((item, index) => <article key={`${item.title}-${index}`}><strong>{item.title}</strong><p>{entryText(item)}</p></article>)}</div></section>}
          {(selected.rewards.length > 0 || selected.items.length > 0) && <section className="campaign-detail-section"><small>RECOMPENSAS E ITENS</small><div className="campaign-reward-grid">{[...selected.rewards, ...selected.items].map((item, index) => <article key={`${item.title || item.name}-${index}`}><strong>{item.name || item.title}</strong>{item.quantity != null && <span>×{item.quantity}</span>}<p>{entryText(item)}</p></article>)}</div></section>}
          {selected.consequences.length > 0 && <section className="campaign-detail-section"><small>CONSEQUÊNCIAS</small><div className="campaign-consequences">{selected.consequences.map((item, index) => <blockquote key={`${item.title}-${index}`}><strong>{item.title}</strong><p>{entryText(item)}</p></blockquote>)}</div></section>}
          {mode === "gm" && <details className="campaign-session-editor"><summary>Editar data e imagem</summary><div><label>Data da sessão<input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} /></label><label>Imagem da sessão<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setSessionImage(event.target.files?.[0] || null)} /></label><button type="button" disabled={sessionEditBusy} onClick={() => void saveSessionMetadata()}>{sessionEditBusy ? "Salvando…" : "Salvar sessão"}</button>{sessionEditNotice && <p role="status">{sessionEditNotice}</p>}</div></details>}
          {mode === "gm" && (selected.session.gm_summary || selected.session.gm_analysis) && <details className="campaign-gm-layer"><summary>Notas de consolidação do Mestre</summary><div><article><p>{selected.session.gm_summary}</p></article>{selected.session.gm_analysis?.companion_feedback?.map((item, index) => <article key={`${item.title}-${index}`}><strong>{item.title}</strong><p>{entryText(item)}</p></article>)}</div></details>}
        </> : <>
          <section className="campaign-previously"><small>ANTERIORMENTE EM OMNISVERA…</small>{recap ? recap.split("\n\n").map((paragraph) => <p key={paragraph}>{paragraph}</p>) : <p>A memória narrativa começará a aparecer quando o Mestre consolidar uma sessão.</p>}</section>
          <section className="campaign-section campaign-recent-panel"><header><small>SESSÕES RECENTES</small><span>{latest.length}</span></header><div className="campaign-session-grid">{latest.map((memory) => <article key={memory.key}><div className="campaign-session-image">{memory.image ? <img src={mediaUrlFromVaultPath(memory.image)} alt="" /> : <i>✦</i>}</div><div><small>{memory.number ? `SESSÃO ${memory.number}` : "MEMÓRIA"}</small><h3>{memory.title}</h3><p>{memory.summary}</p><div className="campaign-card-tags">{memory.tags.map((tag) => <span key={tag}>{tag}</span>)}</div><footer><span>{memory.participants.map((item) => item.name).join(" • ") || "Participantes não registrados"}</span><time>{dateLabel(memory.date)}</time></footer><button type="button" onClick={() => setSelectedKey(memory.key)}>Ver sessão</button></div></article>)}</div>{latest.length === 0 && <p className="campaign-empty">Ainda não existem sessões públicas consolidadas.</p>}</section>
        </>}</div>
    </aside>
    </>}
  </section>;
}
