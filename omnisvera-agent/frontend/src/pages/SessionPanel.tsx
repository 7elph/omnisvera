import { useEffect, useState } from "react";
import { mediaUrlFromVaultPath, searchNotes, SearchResult } from "../api";

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

      <div className="cards">
        {items.map((note) => (
          <SessionCard key={note.id} note={note} onOpenNote={onOpenNote} />
        ))}
      </div>
    </section>
  );
}
