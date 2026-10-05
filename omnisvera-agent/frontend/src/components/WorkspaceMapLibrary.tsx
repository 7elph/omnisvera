import { useState } from "react";
import { editWorkspaceMap, WorkspaceMap } from "../api";

export default function WorkspaceMapLibrary({ maps, activeId, onChange }: {
  maps: WorkspaceMap[]; activeId?: string; onChange: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function change(map: WorkspaceMap, remove: boolean) {
    const title = remove ? undefined : window.prompt("Nome do mapa", map.title);
    if (!remove && !title?.trim()) return;
    if (remove && !window.confirm(`Excluir “${map.title}” da biblioteca? A imagem original será preservada.`)) return;
    setBusy(true); setError("");
    try { await editWorkspaceMap(map.id, title ?? undefined); await onChange(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao alterar mapa"); }
    finally { setBusy(false); }
  }
  return <details><summary>Gerenciar mapas salvos</summary>
    {error && <p role="alert">{error}</p>}
    <p>Selecione outro mapa antes de excluir o mapa ativo. Imagem e pins são preservados para recuperação.</p>
    {maps.map(map => <div key={map.id} className="workspace-icon-toolbar">
      <span>{map.title}</span>
      <button type="button" disabled={busy} onClick={() => void change(map, false)}>Renomear</button>
      <button type="button" disabled={busy || map.id === activeId || map.id.startsWith("official:")}
        onClick={() => void change(map, true)}>Excluir</button>
    </div>)}
  </details>;
}
