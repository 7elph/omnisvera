import { useEffect, useState } from "react";
import { mediaUrlFromVaultPath, NoteSummary, playerDashboard, PlayerDashboard } from "../api";

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
  }, []);

  const sections = dashboard?.sections || [];
  const counts = {
    quests: sections.find((section) => section.kind === "quests")?.items.length ?? null,
    rumors: sections.find((section) => section.kind === "rumors")?.items.length ?? null,
    characters: sections.find((section) => section.kind === "characters")?.items.length ?? null,
    places: sections.find((section) => section.kind === "places")?.items.length ?? null,
  };

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
          <button onClick={() => onAskPrompt("Quero investigar uma pista ativa. O que posso fazer sem spoiler?")}>
            Investigar pista
          </button>
          <button onClick={() => onAskPrompt("Quero falar com alguém. Quais personagens ou facções conhecidas fazem sentido procurar?")}>
            Falar com alguém
          </button>
          <button onClick={() => onAskPrompt("Quero seguir uma missão ativa. Quais opções estão abertas para o grupo?")}>
            Seguir missão
          </button>
          <button onClick={() => onAskPrompt("Quero procurar rumores. O que está circulando e pode virar ação?")}>
            Procurar rumores
          </button>
          <button onClick={() => onAskPrompt("Quero revisar lugares conhecidos. Para onde o grupo pode ir agora?")}>
            Escolher destino
          </button>
          <button onClick={() => onAskPrompt("Quero formular uma teoria com o que já sabemos. Quais peças estão conectadas?")}>
            Montar teoria
          </button>
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
