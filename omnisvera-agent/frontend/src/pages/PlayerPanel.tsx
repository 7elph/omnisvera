import { useEffect, useState } from "react";
import { playerDashboard, PlayerDashboard } from "../api";

export default function PlayerPanel({ onOpenNote }: { onOpenNote: (id: number) => void }) {
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

  return (
    <section className="panel">
      <h2>Painel dos Jogadores</h2>
      <p>O que o grupo pode consultar sem abrir bastidores do mestre.</p>
      <div className="player-prompts">
        <span>Perguntas úteis:</span>
        <code>Quais rumores estão ativos?</code>
        <code>Quais missões estão ativas?</code>
        <code>O que sabemos sobre Nimalis?</code>
      </div>
      {error && <p className="warning-text">{error}</p>}
      {dashboard?.sections.map((section) => (
        <div key={section.title} className="dashboard-section">
          <h3>{section.title}</h3>
          <div className="cards">
            {section.items.map((note) => (
              <button key={note.id} className="note-card" onClick={() => onOpenNote(note.id)}>
                <strong>{note.title}</strong>
                <small>{note.type || "nota"} · {note.visibility || "sem visibility"}</small>
                <span>{note.path}</span>
              </button>
            ))}
            {section.items.length === 0 && <p className="muted">Nada liberado nesta seção ainda.</p>}
          </div>
        </div>
      ))}
    </section>
  );
}
