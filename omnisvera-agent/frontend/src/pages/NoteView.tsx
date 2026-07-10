import { useEffect, useState } from "react";
import { getAccessMode, getNote, mediaUrlFromVaultPath, NoteDetail } from "../api";
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

function inferUnknownKind(target: string, note?: NoteDetail | null) {
  const value = `${target} ${note?.path || ""} ${note?.type || ""}`.toLowerCase();
  if (value.includes("character") || value.includes("characters/") || value.includes("personagem")) return "character";
  if (
    value.includes("location")
    || value.includes("locations/")
    || value.includes("territor")
    || value.includes("territories/")
    || value.includes("local")
    || value.includes("lugar")
  ) return "location";
  return "unknown";
}

function unknownImageFor(kind: string) {
  if (kind === "character") return "zz_media/covers/unknown_character.jpg";
  return "zz_media/covers/unknown_location.jpg";
}

function unknownMessageFor(kind: string) {
  if (kind === "character") {
    return "Você ainda não sabe nada confiável sobre esse personagem.";
  }
  if (kind === "location") {
    return "Você ainda não conhece esse lugar.";
  }
  return "Essa informação ainda não foi revelada.";
}

function shouldShowUnknownPlayerPage(note: NoteDetail) {
  if (getAccessMode() !== "player") return false;
  const status = String(note.status || note.frontmatter.status || "").toLowerCase();
  return ["velado", "hidden", "oculto", "não revelado", "nao revelado"].includes(status);
}

function UnknownKnowledgeView({
  target,
  note,
}: {
  target: string;
  note?: NoteDetail | null;
}) {
  const title = note?.title || target.split("|")[0].split("/").pop()?.replace(/\.md$/i, "") || "Informação velada";
  const kind = inferUnknownKind(target, note);
  const image = mediaUrlFromVaultPath(unknownImageFor(kind));

  return (
    <section className={`panel unknown-note unknown-${kind}`}>
      <div className="unknown-hero">
        {image && <img src={image} alt="" loading="lazy" />}
        <span />
      </div>
      <p className="eyebrow">Arquivo velado</p>
      <h2>{title}</h2>
      <p className="unknown-message">{unknownMessageFor(kind)}</p>
      <p className="muted">
        O Arquivo reconhece o nome, mas ainda não há lembrança segura liberada para os jogadores.
        Quando isso aparecer em jogo, a névoa recua.
      </p>
    </section>
  );
}

export default function NoteView({
  noteId,
  unknownTarget,
  onOpenNote,
  onUnknownNote,
}: {
  noteId: number | null;
  unknownTarget?: string | null;
  onOpenNote?: (id: number) => void;
  onUnknownNote?: (target: string) => void;
}) {
  const [note, setNote] = useState<NoteDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!noteId) {
      setNote(null);
      return;
    }
    setLoading(true);
    getNote(noteId)
      .then(setNote)
      .catch(() => setNote(null))
      .finally(() => setLoading(false));
  }, [noteId]);

  if (unknownTarget && !noteId) {
    return <UnknownKnowledgeView target={unknownTarget} />;
  }

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

  if (shouldShowUnknownPlayerPage(note)) {
    return <UnknownKnowledgeView target={note.title} note={note} />;
  }

  return (
    <section className="panel note-view">
      <p className="eyebrow">{isPlayer ? "Nota liberada" : note.path}</p>
      <h2>{note.title}</h2>
      {!isPlayer && <p className="note-path">{note.path}</p>}
      {cover && <RenderedNote content={`![[${cover}]]`} onOpenNote={onOpenNote} onUnknownNote={onUnknownNote} />}
      <div className="metadata">
        {typeLabel && <span>{typeLabel}</span>}
        <span>{visibilityLabel}</span>
      </div>
      <RenderedNote content={renderedContent} onOpenNote={onOpenNote} onUnknownNote={onUnknownNote} />
    </section>
  );
}
