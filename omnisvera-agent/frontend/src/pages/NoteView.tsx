import { useEffect, useState } from "react";
import { EditableNote, getAccessMode, getEditableNote, getNote, mediaUrlFromVaultPath, NoteDetail, saveEditableNote } from "../api";
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
  if (
    value.includes("character")
    || value.includes("characters/")
    || value.includes("personagem")
    || value.includes("dragão")
    || value.includes("dragao")
    || value.includes("criatura")
  ) return "character";
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
  const [editing, setEditing] = useState<EditableNote | null>(null);
  const [editorFeedback, setEditorFeedback] = useState("");

  useEffect(() => {
    if (!noteId) {
      setNote(null);
      return;
    }
    let active = true;
    setLoading(true);

    async function refresh(initial = false) {
      try {
        const current = await getNote(noteId as number);
        if (active) setNote(current);
      } catch {
        if (active && initial) setNote(null);
      } finally {
        if (active && initial) setLoading(false);
      }
    }

    void refresh(true);
    const timer = window.setInterval(() => void refresh(false), 15_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [noteId, editing]);

  async function openEditor() {
    if (!note) return;
    setEditorFeedback("");
    try { setEditing(await getEditableNote(note.path)); }
    catch (error) { setEditorFeedback(error instanceof Error ? error.message : "Não foi possível abrir o editor."); }
  }

  async function saveEditor() {
    if (!editing || !noteId) return;
    setEditorFeedback("Salvando e reindexando...");
    try {
      const saved = await saveEditableNote(editing);
      setEditing(null);
      setNote(await getNote(noteId));
      setEditorFeedback(`Salvo com backup automático às ${new Date(saved.updated_at).toLocaleTimeString("pt-BR")}.`);
    } catch (error) {
      setEditorFeedback(error instanceof Error ? error.message : "Não foi possível salvar.");
    }
  }

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
      {!isPlayer && (
        <div className="note-editor-toolbar">
          <button onClick={() => void openEditor()}>{editing ? "Recarregar original" : "Editar Markdown"}</button>
          {editorFeedback && <span>{editorFeedback}</span>}
        </div>
      )}
      {editing && !isPlayer && (
        <section className="note-editor">
          <textarea value={editing.content} spellCheck={false} onChange={(event) => setEditing({ ...editing, content: event.target.value })} />
          <div>
            <button className="secondary-button" onClick={() => setEditing(null)}>Cancelar</button>
            <button onClick={() => void saveEditor()}>Salvar nota</button>
          </div>
          <small>O Companion valida o YAML, impede sobrescrita concorrente e cria backup local antes de salvar.</small>
        </section>
      )}
      {cover && <RenderedNote content={`![[${cover}]]`} onOpenNote={onOpenNote} onUnknownNote={onUnknownNote} />}
      <div className="metadata">
        {typeLabel && <span>{typeLabel}</span>}
        <span>{visibilityLabel}</span>
      </div>
      <RenderedNote content={renderedContent} onOpenNote={onOpenNote} onUnknownNote={onUnknownNote} />
    </section>
  );
}
