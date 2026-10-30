import { useRef, useState } from "react";
import "./CharacterLevel.css";
import type { PlayableCharacter } from "../api";

type Props = {
  level: number | null;
  experience: number | null;
  canEdit: boolean;
  characterId?: string;
  confirmedLevel?: number | null;
  onApplied?: (character: PlayableCharacter) => Promise<void>;
  onSave: (fields: { level: number; experience: number }) => Promise<void>;
};

export default function CharacterLevel({ level, experience, canEdit, onSave, characterId, onApplied, confirmedLevel }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ level: String(level), experience: String(experience ?? 0) });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const valid = draft.level.trim() !== "" && draft.experience.trim() !== ""
    && Number.isInteger(Number(draft.level)) && Number(draft.level) >= 1 && Number(draft.level) <= 20
    && Number.isInteger(Number(draft.experience)) && Number(draft.experience) >= 0 && Number(draft.experience) <= 2147483647;

  async function save() {
    if (!canEdit || !valid || pending.current) return;
    pending.current = true; setSaving(true); setError("");
    try {
      await onSave({ level: Number(draft.level), experience: Number(draft.experience) });
      setEditing(false);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar."); }
    finally { pending.current = false; setSaving(false); }
  }

  return <div className="character-level-control">
    <strong className="character-level-number">{level ?? "—"}</strong><small>Nível</small>
    <div className="character-level-tools">
    {canEdit && typeof level === 'number' && <button aria-label="Subir nível" title="Subir nível" disabled={saving} onClick={() => {
      setDraft({ level: String(level + 1), experience: String(experience ?? 0) }); setError(''); setEditing(true);
    }}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 7-7 7 7M12 5v15" fill="none" stroke="currentColor" strokeWidth="2"/></svg></button>}
    {canEdit && <button type="button" className="character-level-edit" aria-label="Correção manual de nível e XP" title="Correção manual de nível e XP" onClick={() => {
      setDraft({ level: level == null ? "" : String(level), experience: String(experience ?? 0) }); setError(""); setEditing(true);
    }}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 3-1 3-3 1 1 3-2 2 2 2-1 3 3 1 1 3h6l1-3 3-1-1-3 2-2-2-2 1-3-3-1-1-3Z" fill="none" stroke="currentColor" strokeWidth="1.5"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></button>}
    </div>
    {canEdit && editing && <div className="character-level-backdrop">
      <form className="character-level-dialog" role="dialog" aria-modal="true" aria-label="Editar nível e experiência"
        onSubmit={(event) => { event.preventDefault(); void save(); }}>
        <p>O nível recalcula a progressão aprovada. PV que exigem dado ficam pendentes para o controlador rolar, sem cura automática.</p>
        <label>Nível<input autoFocus type="number" min={1} max={20} step={1} required value={draft.level}
          disabled={saving} onChange={(event) => setDraft({ ...draft, level: event.target.value })} /></label>
        <label>Experiência<input type="number" min={0} max={2147483647} step={1} required value={draft.experience}
          disabled={saving} onChange={(event) => setDraft({ ...draft, experience: event.target.value })} /></label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={saving || !valid}>{saving ? "Salvando…" : "Salvar alterações"}</button>
        <button type="button" disabled={saving} onClick={() => setEditing(false)}>Cancelar</button>
      </form>
    </div>}
  </div>;
}
