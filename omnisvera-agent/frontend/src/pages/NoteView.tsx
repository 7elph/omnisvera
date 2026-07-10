import { useEffect, useState } from "react";
import { getAccessMode, getNote, NoteDetail } from "../api";
import RenderedNote from "../components/RenderedNote";

function normalizeTitle(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

function stripDuplicateTitleHeading(content: string, title: string) {
  const lines = content.split(/\r?\n/);
  const firstContentIndex = lines.findIndex((line) => line.trim().length > 0);
  if (firstContentIndex < 0) return content;

  const firstLine = lines[firstContentIndex].trim();
  const heading = firstLine.match(/^#{1,2}\s+(.+)$/);
  if (!heading) return content;

  const headingTitle = heading[1].trim();
  if (normalizeTitle(headingTitle) !== normalizeTitle(title)) return content;

  const nextLines = [...lines.slice(0, firstContentIndex), ...lines.slice(firstContentIndex + 1)];
  while (nextLines[0]?.trim() === "") nextLines.shift();
  return nextLines.join("\n").trimStart();
}

export default function NoteView({
  noteId,
  onOpenNote,
}: {
  noteId: number | null;
  onOpenNote?: (id: number) => void;
}) {
  const [note, setNote] = useState<NoteDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!noteId) return;
    setLoading(true);
    getNote(noteId)
      .then(setNote)
      .catch(() => setNote(null))
      .finally(() => setLoading(false));
  }, [noteId]);

  if (!noteId) {
    return (
      <section className="panel">
        <h2>Ver Nota</h2>
        <p>Selecione uma nota na busca, sessão ou chat.</p>
      </section>
    );
  }

  if (loading || !note) {
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
  const isPlayer = getAccessMode() === "player";
  const visibilityLabel = note.visibility || (isPlayer ? "Liberado" : "sem visibility");
  const typeLabel = note.type || "";
  const renderedContent = stripDuplicateTitleHeading(note.content, note.title);

  return (
    <section className="panel note-view">
      <p className="eyebrow">{isPlayer ? "Nota liberada" : note.path}</p>
      <h2>{note.title}</h2>
      {!isPlayer && <p className="note-path">{note.path}</p>}
      {cover && <RenderedNote content={`![[${cover}]]`} onOpenNote={onOpenNote} />}
      <div className="metadata">
        {typeLabel && <span>{typeLabel}</span>}
        <span>{visibilityLabel}</span>
      </div>
      <RenderedNote content={renderedContent} onOpenNote={onOpenNote} />
    </section>
  );
}
