import { useMemo, useState } from "react";
import { mediaUrlFromVaultPath, searchNotes, SearchResult } from "../api";

const QUICK_SEARCHES = [
  "Vezemir",
  "Varkh",
  "Raziel",
  "Morthak",
  "Nimalis",
  "missões",
  "rumores",
  "remédios falsos",
];

const TYPE_FILTERS = [
  { label: "Tudo", value: "" },
  { label: "Personagens", value: "character" },
  { label: "Missões", value: "quest" },
  { label: "Rumores", value: "rumor" },
  { label: "Lugares", value: "location" },
  { label: "Facções", value: "faction" },
  { label: "Itens", value: "item" },
];

function ResultCard({ note, onOpenNote }: { note: SearchResult; onOpenNote: (id: number) => void }) {
  const image = mediaUrlFromVaultPath(note.thumbnail || note.cover);

  return (
    <button className={`note-card result-card ${image ? "has-image" : ""}`} onClick={() => onOpenNote(note.id)}>
      {image && <img src={image} alt="" loading="lazy" />}
      <strong>{note.title}</strong>
      <small>
        {note.type || "nota"} · score {note.score}
      </small>
      <span>{note.excerpt}</span>
      <em>{note.path}</em>
    </button>
  );
}

export default function SearchNotes({ onOpenNote }: { onOpenNote: (id: number) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const filtered = useMemo(
    () => (filter ? results.filter((note) => note.type === filter) : results),
    [filter, results],
  );

  async function search(text = query) {
    const clean = text.trim();
    if (!clean) return;
    setLoading(true);
    setQuery(clean);
    try {
      setResults(await searchNotes(clean, 30));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel search-panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Busca do Vault</p>
          <h2>Buscar notas</h2>
          <p>Use busca rápida quando o chat for demais e você só quiser abrir a nota certa.</p>
        </div>
      </div>

      <div className="prompt-chips">
        {QUICK_SEARCHES.map((item) => (
          <button key={item} onClick={() => search(item)}>
            {item}
          </button>
        ))}
      </div>

      <div className="row">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void search();
          }}
          placeholder="Augustus, Varkh, DORN-7, Nimalis..."
        />
        <button onClick={() => search()} disabled={loading || !query.trim()}>
          {loading ? "buscando..." : "Buscar"}
        </button>
      </div>

      <div className="filter-bar">
        {TYPE_FILTERS.map((item) => (
          <button key={item.value || "all"} className={filter === item.value ? "active" : ""} onClick={() => setFilter(item.value)}>
            {item.label}
          </button>
        ))}
      </div>

      <p className="muted">
        {results.length ? `${filtered.length} de ${results.length} resultados` : "Nenhuma busca rodada ainda."}
      </p>

      <div className="cards">
        {filtered.map((note) => (
          <ResultCard key={note.id} note={note} onOpenNote={onOpenNote} />
        ))}
      </div>
    </section>
  );
}
