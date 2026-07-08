import { useEffect, useState } from "react";
import { getNote, NoteDetail } from "../api";
import RenderedNote from "../components/RenderedNote";

export default function NoteView({ noteId }: { noteId: number | null }) {
  const [note, setNote] = useState<NoteDetail | null>(null);

  useEffect(() => {
    if (!noteId) return;
    getNote(noteId).then(setNote).catch(() => setNote(null));
  }, [noteId]);

  if (!noteId) {
    return (
      <section className="panel">
        <h2>Ver Nota</h2>
        <p>Selecione uma nota na busca, sessão ou chat.</p>
      </section>
    );
  }

  if (!note) {
    return (
      <section className="panel">
        <h2>Carregando...</h2>
      </section>
    );
  }

  const mediaField =
    typeof note.frontmatter.cover === "string"
      ? note.frontmatter.cover
      : typeof note.frontmatter.thumbnail === "string"
        ? note.frontmatter.thumbnail
        : typeof note.frontmatter.portrait === "string"
          ? note.frontmatter.portrait
          : "";
  const cover = mediaField
    .replace(/^\[\[/, "")
    .replace(/\]\]$/, "")
    .split("|")[0]
    .trim();

  return (
    <section className="panel">
      <p className="eyebrow">{note.path}</p>
      <h2>{note.title}</h2>
      {cover && <RenderedNote content={`![[${cover}]]`} />}
      <div className="metadata">
        <span>{note.type || "sem type"}</span>
        <span>{note.visibility || "sem visibility"}</span>
      </div>
      <RenderedNote content={note.content} />
    </section>
  );
}
