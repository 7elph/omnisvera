import { useState } from "react";
import { mediaUrlFromVaultPath, updateWorkspaceToken, WorkspaceToken } from "../api";

export default function TokenVitals({ token, editable, showPortrait = true, compact = false, onChange }: { token: WorkspaceToken; editable: boolean; showPortrait?: boolean; compact?: boolean; onChange: () => Promise<void> }) {
  const [hp, setHp] = useState(String(token.current_hp ?? ""));
  const [maximum, setMaximum] = useState(String(token.maximum_hp ?? ""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save() {
    const current = Number(hp), max = Number(maximum);
    if (!hp.trim() || !maximum.trim() || !Number.isInteger(current) || !Number.isInteger(max) || current < 0 || max < 1 || current > max) {
      setError("Informe vida atual entre zero e o máximo; máximo deve ser um inteiro positivo."); return;
    }
    setBusy(true); setError("");
    try { await updateWorkspaceToken(token.id, { current_hp: current, maximum_hp: max }); await onChange(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao salvar vida"); }
    finally { setBusy(false); }
  }
  if (compact && editable) return <><div className="workspace-hp-quick-controls" aria-label="Ajuste rápido de vida">
    <button type="button" disabled={busy} onClick={() => setHp(String(Math.max(0, Number(hp) - 1)))}>−</button>
    <input aria-label="PV" type="number" min={0} max={Number(maximum)} value={hp} onChange={e => setHp(e.target.value)} />
    <button type="button" disabled={busy} onClick={() => setHp(String(Math.min(Number(maximum), Number(hp) + 1)))}>+</button>
    <button type="button" disabled={busy} onClick={() => void save()}>Aplicar</button>
  </div>{error && <p role="alert">{error}</p>}</>;
  return <div>
    {showPortrait && token.image_path && <img src={mediaUrlFromVaultPath(token.image_path)} alt={token.name} style={{ maxWidth: "100%", maxHeight: 260, objectFit: "contain" }} />}
    {editable && token.token_type === "monster" && <fieldset disabled={busy}><legend>Vida da criatura · Mestre</legend>
      <label>Atual <input aria-label="Vida atual da criatura" type="number" min={0} value={hp} onChange={e => setHp(e.target.value)} /></label>
      <label>Máxima <input aria-label="Vida máxima da criatura" type="number" min={1} value={maximum} onChange={e => setMaximum(e.target.value)} /></label>
      <button type="button" onClick={() => void save()}>Salvar vida</button>
    </fieldset>}
    {error && <p role="alert">{error}</p>}
  </div>;
}
