import { useEffect, useMemo, useState } from "react";
import {
  getPlayerProfile,
  listNotes,
  listPlayerActions,
  listPlayerDiscoveries,
  listPlayerFeed,
  listPlayerQuests,
  markPlayerFeedRead,
  mediaUrlFromVaultPath,
  NoteSummary,
  PlayerAction,
  PlayerActionType,
  PlayerDiscovery,
  PlayerEvent,
  PlayerProfile,
  PlayerQuest,
  playerDashboard,
  PlayerDashboard,
  submitPlayerAction,
} from "../api";

const SECTION_ICONS: Record<string, string> = {
  diary: "✦",
  characters: "♟",
  quests: "!",
  rumors: "?",
  places: "⌖",
  maps: "◇",
};

const SECTION_LABELS: Record<string, string> = {
  diary: "Diário",
  characters: "Grupo",
  quests: "Missão",
  rumors: "Rumor",
  places: "Lugar",
  maps: "Mapa",
};

type PlayerActionKey = PlayerActionType;

function ActionIcon({ type }: { type: PlayerActionType }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {type === "investigate" && <><circle {...common} cx="10.5" cy="10.5" r="5.5" /><path {...common} d="m15 15 5 5M8 10.5l1.5 1.5 3-3.5" /></>}
      {type === "talk" && <><path {...common} d="M4 5.5h11a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H9l-4 3v-3H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2Z" /><path {...common} d="M9 18h6l4 3v-4a2 2 0 0 0 2-2V10" /></>}
      {type === "mission" && <><path {...common} d="M6 3h10a2 2 0 0 1 2 2v16l-5-3-5 3V5a2 2 0 0 1 2-2Z" /><path {...common} d="m9.5 10 1.7 1.7 3.5-4" /></>}
      {type === "rumor" && <><path {...common} d="M12 4a6 6 0 0 0-6 6c0 4 3 4.5 3 7a3 3 0 0 0 6 0" /><path {...common} d="M10 10a2 2 0 0 1 4 0c0 2-2 2-2 4M17.5 6.5c1 1 1.5 2.2 1.5 3.5" /></>}
      {type === "destination" && <><circle {...common} cx="12" cy="12" r="9" /><path {...common} d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8 4.8-2.2Z" /></>}
      {type === "theory" && <><circle {...common} cx="5" cy="12" r="2.5" /><circle {...common} cx="18" cy="6" r="2.5" /><circle {...common} cx="18" cy="18" r="2.5" /><path {...common} d="m7.3 11 8.4-4M7.3 13l8.4 4" /></>}
    </svg>
  );
}

const ACTION_LABELS: Record<PlayerActionType, string> = {
  investigate: "Investigar pista",
  talk: "Falar com alguém",
  mission: "Seguir missão",
  rumor: "Procurar rumores",
  destination: "Escolher destino",
  theory: "Montar teoria",
};

const ACTION_STATUS: Record<PlayerAction["status"], string> = {
  submitted: "Enviada",
  in_review: "Em análise",
  answered: "Respondida",
  canonized: "Canonizada pelo Mestre",
  rejected: "Não realizada",
};

const QUEST_STATUS: Record<PlayerQuest["status"], string> = {
  available: "Disponível",
  accepted: "Aceita",
  in_progress: "Em andamento",
  completed: "Concluída",
  failed: "Falhou",
  archived: "Arquivada",
};

function profileValue(value?: string | number | null) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value)
    .replace(/^['"]|['"]$/g, "")
    .replace(/^\[\[/, "")
    .replace(/\]\]$/, "")
    .split("|")
    .at(-1) || "—";
}

const PLAYER_ACTIONS: Array<{
  key: PlayerActionKey;
  label: string;
  description: string;
  noteTypes: string[];
}> = [
  {
    key: "investigate",
    label: "Investigar pista",
    description: "Escolha uma missão ou rumor e transforme a informação conhecida em linhas de investigação.",
    noteTypes: ["quest", "rumor"],
  },
  {
    key: "talk",
    label: "Falar com alguém",
    description: "Escolha uma pessoa ou facção conhecida e prepare uma abordagem antes da conversa.",
    noteTypes: ["character", "faction"],
  },
  {
    key: "mission",
    label: "Seguir missão",
    description: "Escolha uma missão liberada e organize objetivo, recursos e primeiro movimento.",
    noteTypes: ["quest"],
  },
  {
    key: "rumor",
    label: "Procurar rumores",
    description: "Escolha um boato e descubra como verificá-lo sem tratá-lo como verdade.",
    noteTypes: ["rumor"],
  },
  {
    key: "destination",
    label: "Escolher destino",
    description: "Escolha um lugar conhecido e revise rota, motivo e preparação para a viagem.",
    noteTypes: ["location", "territory", "map"],
  },
  {
    key: "theory",
    label: "Montar teoria",
    description: "Escolha um mistério liberado e separe fatos, conexões possíveis e lacunas.",
    noteTypes: ["rumor", "quest", "lore", "story"],
  },
];

function actionPrompt(action: PlayerActionKey, note: NoteSummary) {
  const target = note.title;
  const prompts: Record<PlayerActionKey, string> = {
    investigate: `Ação — Investigar pista: ${target}. Resuma o que já foi confirmado e ajude a escolher uma abordagem de investigação sem revelar a solução.`,
    talk: `Ação — Falar com alguém: ${target}. O que já sabemos, o que faria sentido perguntar e como preparar uma abordagem sem afirmar que a conversa já aconteceu?`,
    mission: `Ação — Seguir missão: ${target}. Qual é o objetivo público, o que o grupo deve preparar e qual pode ser o primeiro passo?`,
    rumor: `Ação — Procurar rumores: ${target}. O que foi revelado e como o grupo pode verificar esse boato sem assumi-lo como verdade?`,
    destination: `Ação — Escolher destino: ${target}. O que sabemos sobre o lugar, por que ir até lá e que preparação pública faz sentido?`,
    theory: `Ação — Montar teoria: ${target}. Separe fatos confirmados, conexões possíveis e o que ainda falta descobrir.`,
  };
  return prompts[action];
}

function NoteTile({
  note,
  sectionKind,
  onOpenNote,
}: {
  note: NoteSummary;
  sectionKind?: string | null;
  onOpenNote: (id: number) => void;
}) {
  const image = mediaUrlFromVaultPath(note.thumbnail || note.cover);
  const label = SECTION_LABELS[sectionKind || ""] || note.type || "Nota";

  return (
    <button className={`play-card ${image ? "has-image" : ""} card-${sectionKind || "default"}`} onClick={() => onOpenNote(note.id)}>
      {image && <img src={image} alt="" loading="lazy" />}
      <span className="play-card-overlay" />
      <span className="play-card-content">
        <span className="card-kicker">{label}</span>
        <strong>{note.title}</strong>
        <small>
          {note.status || note.type || "nota"} · {note.visibility || "liberado"}
        </small>
        {note.description && <em>{note.description}</em>}
      </span>
    </button>
  );
}

export default function PlayerPanel({
  onOpenNote,
  onAskPrompt,
}: {
  onOpenNote: (id: number) => void;
  onAskPrompt: (prompt: string) => void;
}) {
  const [dashboard, setDashboard] = useState<PlayerDashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [knownNotes, setKnownNotes] = useState<NoteSummary[]>([]);
  const [actions, setActions] = useState<PlayerAction[]>([]);
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [discoveries, setDiscoveries] = useState<PlayerDiscovery[]>([]);
  const [feed, setFeed] = useState<PlayerEvent[]>([]);
  const [personalQuests, setPersonalQuests] = useState<PlayerQuest[]>([]);
  const [selectedAction, setSelectedAction] = useState<PlayerActionKey | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [selectedCharacterId, setSelectedCharacterId] = useState("");
  const [actionIntent, setActionIntent] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionFeedback, setActionFeedback] = useState("");

  useEffect(() => {
    let active = true;

    async function refresh(initial = false) {
      if (initial) {
        setLoading(true);
        setError("");
      }
      try {
        const [dashboardData, notesData, actionData, profileData, discoveryData, feedData, questData] = await Promise.all([
          playerDashboard(),
          listNotes(),
          listPlayerActions(),
          getPlayerProfile(),
          listPlayerDiscoveries(),
          listPlayerFeed(),
          listPlayerQuests(),
        ]);
        if (!active) return;
        setDashboard(dashboardData);
        setKnownNotes(notesData);
        setActions(actionData);
        setProfile(profileData);
        setDiscoveries(discoveryData);
        setFeed(feedData);
        setPersonalQuests(questData);
        setError("");
      } catch {
        if (!active || !initial) return;
        setDashboard(null);
        setKnownNotes([]);
        setError("Não consegui carregar o painel dos jogadores. Confira o modo e o token.");
      } finally {
        if (active && initial) setLoading(false);
      }
    }

    void refresh(true);
    const timer = window.setInterval(() => void refresh(false), 15_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const sections = dashboard?.sections || [];
  const counts = {
    quests: sections.find((section) => section.kind === "quests")?.items.length ?? null,
    rumors: sections.find((section) => section.kind === "rumors")?.items.length ?? null,
    characters: sections.find((section) => section.kind === "characters")?.items.length ?? null,
    places: sections.find((section) => section.kind === "places")?.items.length ?? null,
  };
  const actionDefinition = PLAYER_ACTIONS.find((item) => item.key === selectedAction) || null;
  const actionOptions = useMemo(() => {
    if (!actionDefinition) return [];
    return knownNotes
      .filter((note) => actionDefinition.noteTypes.includes(String(note.type || "").toLowerCase()))
      .filter((note) => !note.path.includes("INDICE_") && !note.title.toLowerCase().startsWith("índice"))
      .sort((left, right) => left.title.localeCompare(right.title, "pt-BR"))
      .slice(0, 40);
  }, [actionDefinition, knownNotes]);
  const selectedTarget = actionOptions.find((note) => String(note.id) === selectedTargetId) || null;
  const unreadEvents = feed.filter((event) => !event.read_at);
  const playerCharacters = useMemo(
    () => knownNotes
      .filter((note) => note.type === "character")
      .filter((note) =>
        note.tags.some((tag) => ["jogador", "player", "personagem-jogador"].includes(tag.toLowerCase()))
        || ["Vezemir", "Varkh Nimalis", "Raziel", "Morthak"].includes(note.title),
      )
      .filter((note) => !profile?.character_path || note.path === profile.character_path)
      .sort((left, right) => left.title.localeCompare(right.title, "pt-BR")),
    [knownNotes, profile],
  );

  useEffect(() => {
    if (!profile?.character_path) return;
    const ownCharacter = knownNotes.find((note) => note.path === profile.character_path);
    if (ownCharacter) setSelectedCharacterId(String(ownCharacter.id));
  }, [knownNotes, profile]);

  async function sendAction() {
    if (!selectedAction || !selectedTarget || !selectedCharacterId || actionIntent.trim().length < 3) return;
    setSubmittingAction(true);
    setActionFeedback("");
    try {
      const created = await submitPlayerAction({
        character_note_id: Number(selectedCharacterId),
        action_type: selectedAction,
        target_note_id: selectedTarget.id,
        intent: actionIntent.trim(),
      });
      setActions((current) => [created, ...current]);
      setActionIntent("");
      setActionFeedback("Ação enviada ao Mestre. Ela ainda não aconteceu no cânone.");
    } catch (error) {
      setActionFeedback(error instanceof Error ? error.message : "Não foi possível enviar a ação.");
    } finally {
      setSubmittingAction(false);
    }
  }

  async function markAllRead() {
    if (!unreadEvents.length) return;
    try {
      await markPlayerFeedRead(unreadEvents.map((event) => event.id));
      const now = new Date().toISOString();
      setFeed((current) => current.map((event) => ({ ...event, read_at: event.read_at || now })));
    } catch {
      setActionFeedback("Não foi possível marcar as novidades como lidas.");
    }
  }

  return (
    <section className="panel player-home">
      <div className="player-hero">
        <div className="player-hero-main">
          <p className="eyebrow">Modo Jogador</p>
          {profile?.character_title && (
            <button
              className="player-profile-card"
              disabled={!profile.character_note_id}
              onClick={() => profile.character_note_id && onOpenNote(profile.character_note_id)}
            >
              {(profile.thumbnail || profile.cover) && (
                <img src={mediaUrlFromVaultPath(profile.thumbnail || profile.cover)} alt="" />
              )}
              <span className="player-profile-info">
                <small>Você joga como</small>
                <strong>{profile.character_title}</strong>
                <em>{profileValue(profile.race)} · {profileValue(profile.character_class)} · nível {profileValue(profile.level)}</em>
                <span className="player-profile-stats">
                  <b>{profileValue(profile.status)}</b>
                  <b>{profileValue(profile.location)}</b>
                  {profile.faction && <b>{profileValue(profile.faction)}</b>}
                </span>
              </span>
            </button>
          )}
          <span className="version-pill">Home Jogável v4 · player-safe</span>
          <h2>Omnisvera em jogo</h2>
          <div className="player-stats" aria-label="Resumo do painel dos jogadores">
            <span><strong>{loading || counts.quests === null ? "…" : counts.quests}</strong><em>missões</em></span>
            <span><strong>{loading || counts.rumors === null ? "…" : counts.rumors}</strong><em>rumores</em></span>
            <span><strong>{loading || counts.characters === null ? "…" : counts.characters}</strong><em>personagens</em></span>
            <span><strong>{loading || counts.places === null ? "…" : counts.places}</strong><em>lugares</em></span>
          </div>
        </div>
      </div>

      <div className="player-prompts">
        <span>Perguntas rápidas:</span>
        {[
          "Quais rumores estão ativos?",
          "Quais missões estão ativas?",
          "O que sabemos sobre Nimalis?",
          "Quem são os personagens jogadores?",
        ].map((prompt) => (
          <button key={prompt} onClick={() => onAskPrompt(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <section className="player-live-state">
        <div className="player-news-panel">
          <div className="live-panel-heading">
            <div>
              <p className="eyebrow">Novidades</p>
              <h3>O que mudou para você</h3>
            </div>
            {unreadEvents.length > 0 && <span className="unread-badge">{unreadEvents.length}</span>}
            {unreadEvents.length > 0 && <button onClick={() => void markAllRead()}>Marcar como lidas</button>}
          </div>
          <div className="player-timeline">
            {feed.slice(0, 8).map((event) => {
              const note = knownNotes.find((item) => item.path === event.note_path);
              return (
                <button
                  key={event.id}
                  className={event.read_at ? "timeline-event" : "timeline-event unread"}
                  disabled={!note}
                  onClick={() => note && onOpenNote(note.id)}
                >
                  <span className="timeline-dot" />
                  <span><strong>{event.title}</strong><small>{event.message}</small></span>
                </button>
              );
            })}
            {feed.length === 0 && <p className="muted">Nenhuma novidade pessoal ainda.</p>}
          </div>
        </div>

        <div className="player-quest-progress">
          <div className="live-panel-heading">
            <div>
              <p className="eyebrow">Jornada</p>
              <h3>Suas missões</h3>
            </div>
          </div>
          <div className="personal-quest-list">
            {personalQuests.filter((quest) => quest.status !== "archived").slice(0, 6).map((quest) => {
              const note = knownNotes.find((item) => item.path === quest.note_path);
              return (
                <button key={quest.id} disabled={!note} onClick={() => note && onOpenNote(note.id)}>
                  <span><strong>{quest.note_title}</strong><small>{quest.progress || "Sem nova orientação."}</small></span>
                  <b className={`quest-status status-${quest.status}`}>{QUEST_STATUS[quest.status]}</b>
                </button>
              );
            })}
            {personalQuests.length === 0 && <p className="muted">Nenhuma missão foi vinculada ao seu perfil.</p>}
          </div>
        </div>
      </section>

      <div className="player-actions">
        <div>
          <p className="eyebrow">Ações do jogador</p>
          <h3>O que você quer fazer agora?</h3>
          <p>Escolha o próximo movimento do seu personagem.</p>
        </div>
        <div className="action-grid">
          {PLAYER_ACTIONS.map((action) => (
            <button
              key={action.key}
              className={selectedAction === action.key ? "active" : ""}
              onClick={() => {
                setSelectedAction(action.key);
                setSelectedTargetId("");
                setActionIntent("");
                setActionFeedback("");
              }}
            >
              <span className={`action-icon action-icon-${action.key}`}><ActionIcon type={action.key} /></span>
              <span className="action-card-copy">
                <strong>{action.label}</strong>
                <small>{action.description.split(" e ")[0].replace(/[.,;:]$/, "")}.</small>
              </span>
              <span className="action-arrow">›</span>
            </button>
          ))}
        </div>
        {actionDefinition && (
          <div className="action-builder">
            <div className="action-builder-heading">
              <div>
                <strong>{actionDefinition.label}</strong>
                <p>{actionDefinition.description}</p>
              </div>
              <button className="secondary-button" onClick={() => setSelectedAction(null)}>Fechar</button>
            </div>
            <label>
              Quem age
              <select
                value={selectedCharacterId}
                disabled={Boolean(profile?.character_path)}
                onChange={(event) => setSelectedCharacterId(event.target.value)}
              >
                <option value="">Escolha seu personagem...</option>
                {playerCharacters.map((character) => (
                  <option key={character.id} value={character.id}>{character.title}</option>
                ))}
              </select>
            </label>
            <label>
              Foco da ação
              <select value={selectedTargetId} onChange={(event) => setSelectedTargetId(event.target.value)}>
                <option value="">Escolha uma opção liberada...</option>
                {actionOptions.map((note) => (
                  <option key={note.id} value={note.id}>{note.title}</option>
                ))}
              </select>
            </label>
            {selectedTarget?.description && <p className="action-target-preview">{selectedTarget.description}</p>}
            <label>
              O que você pretende fazer?
              <textarea
                value={actionIntent}
                maxLength={1200}
                placeholder="Descreva a intenção, abordagem ou pergunta do personagem."
                onChange={(event) => setActionIntent(event.target.value)}
              />
            </label>
            <div className="action-submit-row">
              <button
                className="secondary-button"
                disabled={!selectedTarget}
                onClick={() => selectedTarget && onAskPrompt(actionPrompt(actionDefinition.key, selectedTarget))}
              >
                Consultar o Arquivo
              </button>
              <button
                className="action-launch"
                disabled={!selectedTarget || !selectedCharacterId || actionIntent.trim().length < 3 || submittingAction}
                onClick={() => void sendAction()}
              >
                {submittingAction ? "Enviando..." : "Enviar ao Mestre"}
              </button>
            </div>
            {actionFeedback && <p className="action-feedback">{actionFeedback}</p>}
            <small>A intenção fica pendente até o Mestre responder. Nada é canonizado automaticamente.</small>
          </div>
        )}
      </div>

      {profile?.profile_id && (
        <div className="player-discoveries">
          <div className="section-heading">
            <span>✧</span>
            <div>
              <h3>Suas descobertas</h3>
              <p>Pistas e registros revelados especificamente para {profile.character_title}.</p>
            </div>
          </div>
          <div className="discovery-grid">
            {discoveries.map((discovery) => {
              const note = knownNotes.find((item) => item.path === discovery.note_path);
              return (
                <button key={discovery.id} disabled={!note} onClick={() => note && onOpenNote(note.id)}>
                  <strong>{discovery.note_title}</strong>
                  <small>Descoberta pessoal</small>
                </button>
              );
            })}
            {discoveries.length === 0 && <p className="muted">O Mestre ainda não revelou descobertas individuais.</p>}
          </div>
        </div>
      )}

      <div className="player-action-history">
        <div className="section-heading">
          <span>✎</span>
          <div>
            <h3>Ações enviadas</h3>
            <p>Intenções do grupo e respostas recebidas do Mestre.</p>
          </div>
        </div>
        <div className="action-history-list">
          {actions.slice(0, 12).map((action) => (
            <article key={action.id} className={`action-history-card status-${action.status}`}>
              <header>
                <strong>{action.character_title} · {ACTION_LABELS[action.action_type]}</strong>
                <span>{ACTION_STATUS[action.status]}</span>
              </header>
              <small>Alvo: {action.target_title}</small>
              <p>{action.intent}</p>
              {action.gm_response && <blockquote>{action.gm_response}</blockquote>}
            </article>
          ))}
          {actions.length === 0 && <p className="muted">Nenhuma ação foi enviada ainda.</p>}
        </div>
      </div>

      {error && <p className="warning-text">{error}</p>}
      {loading && <p className="muted">Carregando painel dos jogadores...</p>}

      {!loading && sections.map((section) => {
        const sectionCover = mediaUrlFromVaultPath(section.cover);

        return (
        <div key={section.title} className={`dashboard-section section-${section.kind || "default"}`}>
          {sectionCover && (
            <div className="section-cover">
              <img src={sectionCover} alt="" loading="lazy" />
              <span />
            </div>
          )}
          <div className="section-heading">
            <span>{SECTION_ICONS[section.kind || ""] || "•"}</span>
            <div>
              <h3>{section.title}</h3>
              {section.description && <p>{section.description}</p>}
            </div>
            {section.prompt && <button onClick={() => onAskPrompt(section.prompt || "")}>Perguntar</button>}
          </div>

          <div className="play-grid">
            {section.items.map((note) => (
              <NoteTile key={note.id} note={note} sectionKind={section.kind} onOpenNote={onOpenNote} />
            ))}
            {section.items.length === 0 && <p className="muted">Nada liberado nesta seção ainda.</p>}
          </div>
        </div>
        );
      })}
    </section>
  );
}
