import { useEffect, useMemo, useState } from "react";
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

  useEffect(() => {
    playerDashboard()
      .then((data) => {
        setDashboard(data);
        setError("");
      })
      .catch(() => setError("Não consegui carregar o painel dos jogadores. Confira o modo e o token."));
  }, []);

  const sections = dashboard?.sections || [];
  const diary = sections.find((section) => section.kind === "diary");
  const featured = useMemo(() => diary?.items[0], [diary]);
  const counts = {
    quests: sections.find((section) => section.kind === "quests")?.items.length || 0,
    rumors: sections.find((section) => section.kind === "rumors")?.items.length || 0,
    characters: sections.find((section) => section.kind === "characters")?.items.length || 0,
    places: sections.find((section) => section.kind === "places")?.items.length || 0,
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
            <span><strong>{counts.quests}</strong><em>missões</em></span>
            <span><strong>{counts.rumors}</strong><em>rumores</em></span>
            <span><strong>{counts.characters}</strong><em>personagens</em></span>
            <span><strong>{counts.places}</strong><em>lugares</em></span>
          </div>
        </div>
        {featured && (
          <button className="featured-card" onClick={() => onOpenNote(featured.id)}>
            <span>Começar por aqui</span>
            <strong>{featured.title}</strong>
          </button>
        )}
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

      {error && <p className="warning-text">{error}</p>}

      {sections.map((section) => (
        <div key={section.title} className={`dashboard-section section-${section.kind || "default"}`}>
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
      ))}
    </section>
  );
}
