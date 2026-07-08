import { useState } from "react";
import { searchNotes, SearchResult } from "../api";

export default function SearchNotes({ onOpenNote }: { onOpenNote: (id: number) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);

  async function search() {
    if (!query.trim()) return;
    setResults(await searchNotes(query, 20));
  }

  return (
    <section className="panel">
      <h2>Buscar Notas</h2>
      <div className="row">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Augustus, Varkh, DORN-7..." />
        <button onClick={search}>Buscar</button>
      </div>
      <div className="cards">
        {results.map((note) => (
          <button key={note.id} className="note-card" onClick={() => onOpenNote(note.id)}>
            <strong>{note.title}</strong>
            <small>{note.type || "nota"} · score {note.score}</small>
            <span>{note.excerpt}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
