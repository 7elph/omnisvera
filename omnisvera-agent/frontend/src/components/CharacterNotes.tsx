import { useEffect, useRef, useState } from "react";
import { CharacterNotes as Notes, getCharacterNotes, saveCharacterNotes } from "../api";
import "./CharacterNotes.css";

// Mounted with a character key so late responses cannot reach another sheet.
export default function CharacterNotes({ characterId }: { characterId: string }) {
  const [saved, setSaved] = useState<Notes | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const alive = useRef(true);
  const dirty = saved !== null && draft !== saved.content;

  useEffect(() => {
    let cancelled = false;
    alive.current = true;
    getCharacterNotes(characterId).then((notes) => {
      if (!cancelled) { setSaved(notes); setDraft(notes.content); }
    }).catch(() => { if (!cancelled) setError("Não foi possível carregar as anotações. Tente novamente."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; alive.current = false; };
  }, [characterId]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  async function reload() {
    if (inFlight.current || (dirty && !window.confirm("Descartar o rascunho e carregar as anotações salvas?"))) return;
    inFlight.current = true; setLoading(true); setError("");
    try {
      const notes = await getCharacterNotes(characterId);
      if (alive.current) { setSaved(notes); setDraft(notes.content); }
    } catch { if (alive.current) setError("Não foi possível carregar as anotações. Seu rascunho foi mantido."); }
    finally { inFlight.current = false; if (alive.current) setLoading(false); }
  }

  async function save() {
    if (!saved || !dirty || inFlight.current) return;
    inFlight.current = true; setSaving(true); setError("");
    try {
      const notes = await saveCharacterNotes(characterId, draft, saved.version);
      if (alive.current) setSaved(notes);
    } catch (reason) {
      if (alive.current) setError(reason instanceof Error ? reason.message : "Não foi possível salvar. Seu rascunho foi mantido.");
    } finally { inFlight.current = false; if (alive.current) setSaving(false); }
  }

  return <details className="character-personal-notes" aria-label="Anotações do personagem">
    <summary>Anotações</summary>
    <textarea aria-label="Anotações do personagem" rows={3} maxLength={12000} value={draft}
      disabled={loading || !saved} onChange={(event) => { setDraft(event.target.value); setError(""); }}
    />
    <div className="character-notes-actions">
      <button type="button" disabled={loading || saving || !dirty} onClick={() => void save()}>{saving ? "Salvando…" : "Salvar alterações"}</button>
      {error && <button type="button" disabled={loading || saving} onClick={() => void reload()}>Recarregar notas salvas</button>}
    </div>
    {error && <p role="alert">{error}</p>}
  </details>;
}
