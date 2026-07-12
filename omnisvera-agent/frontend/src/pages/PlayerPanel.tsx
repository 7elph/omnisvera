import { useEffect, useMemo, useState } from "react";
import { listNotes, mediaUrlFromVaultPath, NoteSummary, playerDashboard, PlayerDashboard } from "../api";

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

type PlayerActionKey = "investigate" | "talk" | "mission" | "rumor" | "destination" | "theory";

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
  const [selectedAction, setSelectedAction] = useState<PlayerActionKey | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    playerDashboard()
      .then((data) => {
        setDashboard(data);
        setError("");
      })
      .catch(() => {
        setDashboard(null);
        setError("Não consegui carregar o painel dos jogadores. Confira o modo e o token.");
      })
      .finally(() => setLoading(false));
    listNotes().then(setKnownNotes).catch(() => setKnownNotes([]));
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

  return (
    <section className="panel player-home">
      <div className="player-hero">
        <div className="player-hero-main">
          <p className="eyebrow">Modo Jogador</p>
          <span className="version-pill">Home Jogável v4 · player-safe</span>
          <h2>Omnisvera em jogo</h2>
          <p>Missões, rumores, personagens e lugares liberados — sem abrir bastidores do mestre.</p>
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

      <div className="player-actions">
        <div>
          <p className="eyebrow">Ações do jogador</p>
          <h3>O que você quer fazer agora?</h3>
          <p>Escolha uma intenção e o Arquivo Vivo ajuda a transformar isso em próximo passo sem abrir spoiler.</p>
        </div>
        <div className="action-grid">
          {PLAYER_ACTIONS.map((action) => (
            <button
              key={action.key}
              className={selectedAction === action.key ? "active" : ""}
              onClick={() => {
                setSelectedAction(action.key);
                setSelectedTargetId("");
              }}
            >
              {action.label}
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
              Foco da ação
              <select value={selectedTargetId} onChange={(event) => setSelectedTargetId(event.target.value)}>
                <option value="">Escolha uma opção liberada...</option>
                {actionOptions.map((note) => (
                  <option key={note.id} value={note.id}>{note.title}</option>
                ))}
              </select>
            </label>
            {selectedTarget?.description && <p className="action-target-preview">{selectedTarget.description}</p>}
            <button
              className="action-launch"
              disabled={!selectedTarget}
              onClick={() => selectedTarget && onAskPrompt(actionPrompt(actionDefinition.key, selectedTarget))}
            >
              Preparar próximo passo
            </button>
            <small>Nenhuma ação será registrada como acontecida; o Arquivo apenas ajuda a preparar a intenção.</small>
          </div>
        )}
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
