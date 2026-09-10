import { useRef, useState } from "react";
import "./CharacterLevel.css";

type Props = {
  level: number;
  experience: number | null;
  canEdit: boolean;
  onSave: (fields: { level: number; experience: number }) => Promise<void>;
};

export default function CharacterLevel({ level, experience, canEdit, onSave }: Props) {
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
    <strong className="character-level-number">{level}</strong><small>Nível</small>
    {canEdit && <button type="button" className="character-level-edit" onClick={() => {
      setDraft({ level: String(level), experience: String(experience ?? 0) }); setError(""); setEditing(true);
    }}>Editar nível e XP</button>}
    {canEdit && editing && <div className="character-level-backdrop">
      <form className="character-level-dialog" role="dialog" aria-modal="true" aria-label="Editar nível e experiência"
        onSubmit={(event) => { event.preventDefault(); void save(); }}>
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
