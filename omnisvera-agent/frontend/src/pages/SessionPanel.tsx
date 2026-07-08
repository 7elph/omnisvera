import { useEffect, useState } from "react";
import { searchNotes, SearchResult } from "../api";

const QUICK_SEARCHES = [
  "Sessão 01 Roteiro de Mesa",
  "01 Ecos do Mundo Perdido",
  "Varkh Nimalis",
  "Vezemir",
  "Raziel",
  "Morthak",
  "Unidade DORN-7",
  "Remédios Falsos",
  "O Frasco Afogado",
  "Guarda Real de Nimalia",
];

export default function SessionPanel({ onOpenNote }: { onOpenNote: (id: number) => void }) {
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
      <h2>Painel da Sessão</h2>
      <p>Atalhos rápidos para mesa. Reindexe o vault se algo não aparecer.</p>
      <div className="cards">
        {items.map((note) => (
          <button key={note.id} className="note-card" onClick={() => onOpenNote(note.id)}>
            <strong>{note.title}</strong>
            <span>{note.path}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
