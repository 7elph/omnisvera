import { useEffect, useState } from "react";
import {
  listGmDiscoveries,
  listGmQuests,
  listNotes,
  listPlayerActions,
  mediaUrlFromVaultPath,
  PlayerAction,
  PlayerActionStatus,
  PlayerDiscovery,
  PlayerQuest,
  PlayerQuestStatus,
  NoteSummary,
  revealPlayerDiscovery,
  revokePlayerDiscovery,
  updatePlayerQuest,
  searchNotes,
  SearchResult,
  updatePlayerAction,
} from "../api";

const PLAYER_PROFILES = [
  { id: "group", title: "Todo o grupo" },
  { id: "vezemir", title: "Vezemir" },
  { id: "varkh", title: "Varkh Nimalis" },
  { id: "raziel", title: "Raziel" },
  { id: "morthak", title: "Morthak" },
];

const QUICK_SEARCHES = [
  "Sessão 01 Roteiro de Mesa",
  "01 Ecos do Mundo Perdido",
  "Estado da Campanha",
  "Varkh Nimalis",
  "Vezemir",
  "Raziel",
  "Morthak",
  "Unidade DORN-7",
  "Remédios Falsos",
  "O Frasco Afogado",
  "Guarda Real de Nimalia",
  "Nimalis",
];

const GM_PROMPTS = [
  "O que preciso preparar para a próxima sessão?",
  "Quais segredos não devo revelar aos jogadores?",
  "Quais NPCs entram na sessão 01?",
  "Quais pistas apontam para remédios falsos?",
];

const ACTION_LABELS: Record<PlayerAction["action_type"], string> = {
  investigate: "Investigar pista",
  talk: "Falar com alguém",
  mission: "Seguir missão",
  rumor: "Procurar rumores",
  destination: "Escolher destino",
  theory: "Montar teoria",
};

const ACTION_STATUS: Record<PlayerActionStatus, string> = {
  submitted: "Enviada",
  in_review: "Em análise",
  answered: "Respondida",
  canonized: "Canonizada",
  rejected: "Rejeitada",
};

function SessionCard({ note, onOpenNote }: { note: SearchResult; onOpenNote: (id: number) => void }) {
  const image = mediaUrlFromVaultPath(note.thumbnail || note.cover);

  return (
    <button className={`note-card result-card ${image ? "has-image" : ""}`} onClick={() => onOpenNote(note.id)}>
      {image && <img src={image} alt="" loading="lazy" />}
      <strong>{note.title}</strong>
      <small>{note.type || "nota"} · {note.visibility || "sem visibilidade"}</small>
      <span>{note.path}</span>
    </button>
  );
}

export default function SessionPanel({
  onOpenNote,
  onAskPrompt,
}: {
  onOpenNote: (id: number) => void;
  onAskPrompt: (prompt: string) => void;
}) {
  const [items, setItems] = useState<SearchResult[]>([]);
  const [actions, setActions] = useState<PlayerAction[]>([]);
  const [responseDrafts, setResponseDrafts] = useState<Record<number, string>>({});
  const [actionError, setActionError] = useState("");
  const [updatingAction, setUpdatingAction] = useState<number | null>(null);
  const [discoveries, setDiscoveries] = useState<PlayerDiscovery[]>([]);
  const [availableNotes, setAvailableNotes] = useState<NoteSummary[]>([]);
  const [discoveryProfile, setDiscoveryProfile] = useState("vezemir");
  const [discoveryNoteId, setDiscoveryNoteId] = useState("");
  const [discoveryFeedback, setDiscoveryFeedback] = useState("");
  const [questProgress, setQuestProgress] = useState<PlayerQuest[]>([]);
  const [questProfile, setQuestProfile] = useState("group");
  const [questNoteId, setQuestNoteId] = useState("");
  const [questStatus, setQuestStatus] = useState<PlayerQuestStatus>("available");
  const [questSummary, setQuestSummary] = useState("");
  const [questFeedback, setQuestFeedback] = useState("");

  useEffect(() => {
    Promise.all(QUICK_SEARCHES.map((query) => searchNotes(query, 1))).then((groups) => {
      const seen = new Set<number>();
      const flattened = groups.flat().filter((note) => {
        if (seen.has(note.id)) return false;
        seen.add(note.id);
        return true;
      });
      setItems(flattened);
    });
  }, []);

  useEffect(() => {
    Promise.all([listGmDiscoveries(), listGmQuests(), listNotes()])
      .then(([discoveryData, questData, noteData]) => {
        setDiscoveries(discoveryData);
        setQuestProgress(questData);
        setAvailableNotes(
          noteData
            .filter((note) => ["Jogadores", "Público"].includes(String(note.visibility || "")))
            .sort((left, right) => left.title.localeCompare(right.title, "pt-BR")),
        );
      })
      .catch(() => setDiscoveryFeedback("Não foi possível carregar as descobertas."));
  }, []);

  async function revealDiscovery() {
    if (!discoveryNoteId) return;
    setDiscoveryFeedback("");
    try {
      const created = await revealPlayerDiscovery(discoveryProfile, Number(discoveryNoteId));
      setDiscoveries((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setDiscoveryFeedback("Descoberta revelada ao jogador.");
    } catch (error) {
      setDiscoveryFeedback(error instanceof Error ? error.message : "Não foi possível revelar a descoberta.");
    }
  }

  async function revokeDiscovery(id: number) {
    try {
      await revokePlayerDiscovery(id);
      setDiscoveries((current) => current.filter((item) => item.id !== id));
    } catch {
      setDiscoveryFeedback("Não foi possível revogar a descoberta.");
    }
  }

  async function saveQuestProgress() {
    if (!questNoteId) return;
    setQuestFeedback("");
    try {
      const updated = await updatePlayerQuest({
        profile_id: questProfile,
        note_id: Number(questNoteId),
        status: questStatus,
        progress: questSummary,
      });
      setQuestProgress((current) => [updated, ...current.filter((item) => item.id !== updated.id)]);
      setQuestFeedback("Progresso salvo e enviado para a timeline do jogador.");
    } catch (error) {
      setQuestFeedback(error instanceof Error ? error.message : "Não foi possível atualizar a missão.");
    }
  }

  useEffect(() => {
    let active = true;
    async function refreshActions() {
      try {
        const current = await listPlayerActions();
        if (active) setActions(current);
      } catch {
        if (active) setActionError("Não foi possível carregar as ações dos jogadores.");
      }
    }
    void refreshActions();
    const timer = window.setInterval(() => void refreshActions(), 10_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  async function reviewAction(action: PlayerAction, status: PlayerActionStatus) {
    setUpdatingAction(action.id);
    setActionError("");
    try {
      const updated = await updatePlayerAction(action.id, {
        status,
        gm_response: responseDrafts[action.id] ?? action.gm_response ?? "",
      });
      setActions((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setResponseDrafts((current) => ({ ...current, [updated.id]: updated.gm_response || "" }));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Não foi possível atualizar a ação.");
    } finally {
      setUpdatingAction(null);
    }
  }

  return (
    <section className="panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Painel do Mestre</p>
          <h2>Preparação de sessão</h2>
          <p>Atalhos rápidos para abrir mesa, consultar P0 e perguntar ao vault sem caçar arquivo.</p>
        </div>
      </div>

      <div className="prompt-chips">
        {GM_PROMPTS.map((prompt) => (
          <button key={prompt} onClick={() => onAskPrompt(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <section className="gm-action-inbox">
        <div className="section-heading">
          <span>✉</span>
          <div>
            <p className="eyebrow">Central de Ações</p>
            <h3>Intenções dos jogadores</h3>
            <p>Responder aqui não altera o vault. Canonizar apenas registra sua decisão no Companion.</p>
          </div>
        </div>
        {actionError && <p className="warning-text">{actionError}</p>}
        <div className="gm-action-list">
          {actions.map((action) => (
            <article key={action.id} className={`gm-action-card status-${action.status}`}>
              <header>
                <div>
                  <strong>{action.character_title} · {ACTION_LABELS[action.action_type]}</strong>
                  <small>Alvo: {action.target_title}</small>
                </div>
                <span>{ACTION_STATUS[action.status]}</span>
              </header>
              <p>{action.intent}</p>
              <textarea
                value={responseDrafts[action.id] ?? action.gm_response ?? ""}
                maxLength={2400}
                placeholder="Resposta, consequência ou orientação do Mestre..."
                onChange={(event) => setResponseDrafts((current) => ({ ...current, [action.id]: event.target.value }))}
              />
              <div className="gm-action-controls">
                <button disabled={updatingAction === action.id} onClick={() => void reviewAction(action, "in_review")}>Analisar</button>
                <button disabled={updatingAction === action.id} onClick={() => void reviewAction(action, "answered")}>Responder</button>
                <button disabled={updatingAction === action.id} onClick={() => void reviewAction(action, "canonized")}>Canonizar</button>
                <button className="danger-button" disabled={updatingAction === action.id} onClick={() => void reviewAction(action, "rejected")}>Rejeitar</button>
              </div>
            </article>
          ))}
          {actions.length === 0 && <p className="muted">Nenhuma ação aguardando o Mestre.</p>}
        </div>
      </section>

      <section className="gm-discovery-panel">
        <div className="section-heading">
          <span>✧</span>
          <div>
            <p className="eyebrow">Conhecimento individual</p>
            <h3>Revelar descoberta</h3>
            <p>Libera uma nota já player-safe somente no painel pessoal escolhido.</p>
          </div>
        </div>
        <div className="discovery-controls">
          <select value={discoveryProfile} onChange={(event) => setDiscoveryProfile(event.target.value)}>
            {PLAYER_PROFILES.filter((profile) => profile.id !== "group").map((profile) => <option key={profile.id} value={profile.id}>{profile.title}</option>)}
          </select>
          <select value={discoveryNoteId} onChange={(event) => setDiscoveryNoteId(event.target.value)}>
            <option value="">Escolha uma nota liberada...</option>
            {availableNotes.map((note) => <option key={note.id} value={note.id}>{note.title}</option>)}
          </select>
          <button disabled={!discoveryNoteId} onClick={() => void revealDiscovery()}>Revelar</button>
        </div>
        {discoveryFeedback && <p className="action-feedback">{discoveryFeedback}</p>}
        <div className="gm-discovery-list">
          {discoveries.map((discovery) => (
            <article key={discovery.id}>
              <span><strong>{discovery.note_title}</strong><small>{discovery.profile_id}</small></span>
              <button className="danger-button" onClick={() => void revokeDiscovery(discovery.id)}>Revogar</button>
            </article>
          ))}
          {discoveries.length === 0 && <p className="muted">Nenhuma descoberta individual revelada.</p>}
        </div>
      </section>

      <section className="gm-quest-panel">
        <div className="section-heading">
          <span>⚑</span>
          <div>
            <p className="eyebrow">Progresso de campanha</p>
            <h3>Atualizar missão</h3>
            <p>Vincula uma missão pública ao grupo ou a um personagem e registra a mudança na timeline.</p>
          </div>
        </div>
        <div className="quest-progress-controls">
          <select value={questProfile} onChange={(event) => setQuestProfile(event.target.value)}>
            {PLAYER_PROFILES.map((profile) => <option key={profile.id} value={profile.id}>{profile.title}</option>)}
          </select>
          <select value={questNoteId} onChange={(event) => setQuestNoteId(event.target.value)}>
            <option value="">Escolha uma missão...</option>
            {availableNotes.filter((note) => note.type === "quest").map((note) => (
              <option key={note.id} value={note.id}>{note.title}</option>
            ))}
          </select>
          <select value={questStatus} onChange={(event) => setQuestStatus(event.target.value as PlayerQuestStatus)}>
            <option value="available">Disponível</option>
            <option value="accepted">Aceita</option>
            <option value="in_progress">Em andamento</option>
            <option value="completed">Concluída</option>
            <option value="failed">Falhou</option>
            <option value="archived">Arquivada</option>
          </select>
          <textarea
            value={questSummary}
            maxLength={1200}
            placeholder="Objetivo conhecido, avanço ou orientação do Mestre..."
            onChange={(event) => setQuestSummary(event.target.value)}
          />
          <button disabled={!questNoteId} onClick={() => void saveQuestProgress()}>Salvar progresso</button>
        </div>
        {questFeedback && <p className="action-feedback">{questFeedback}</p>}
        <div className="gm-quest-list">
          {questProgress.map((quest) => (
            <article key={quest.id}>
              <span><strong>{quest.note_title}</strong><small>{quest.profile_id} · {quest.status}</small></span>
              <p>{quest.progress || "Sem resumo."}</p>
            </article>
          ))}
          {questProgress.length === 0 && <p className="muted">Nenhum progresso personalizado registrado.</p>}
        </div>
      </section>

      <div className="cards">
        {items.map((note) => (
          <SessionCard key={note.id} note={note} onOpenNote={onOpenNote} />
        ))}
      </div>
    </section>
  );
}
