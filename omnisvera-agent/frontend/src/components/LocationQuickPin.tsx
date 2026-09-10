import { FormEvent, useEffect, useRef, useState } from "react";
import { createWorkspaceToken, listWorldLocations, mediaUrlFromVaultPath, removeWorkspaceToken, updateWorkspaceToken, WorkspaceToken, WorldLocationRecord } from "../api";
import { COMPANION_ICON_CATALOG, iconPathForMapLocation } from "../companionIconCatalog";
import { nextPinPosition } from "./pinPlacement";

type Props = { mapId: string; tokens: WorkspaceToken[]; onChange: () => Promise<void> };
const empty = { name: "", image_path: "", latitude: 50, longitude: 50, visible_to_players: false, description: "" };

export default function LocationQuickPin({ mapId, tokens, onChange }: Props) {
  const [locations, setLocations] = useState<WorldLocationRecord[]>([]);
  const [draft, setDraft] = useState({ ...empty, ...nextPinPosition(tokens) });
  const [editing, setEditing] = useState("");
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [error, setError] = useState("");
  useEffect(() => { void listWorldLocations().then(setLocations).catch(() => setError("Cadastro de locais indisponível; os ícones prontos continuam disponíveis.")); }, []);
  useEffect(() => { setDraft({ ...empty, ...nextPinPosition(tokens) }); setEditing(""); }, [mapId]);
  function select(value: string) {
    const location = locations.find(l => `world:${l.id}` === value);
    const icon = COMPANION_ICON_CATALOG.find(i => i.category === "map" && i.id === value);
    setEditing("");
    setDraft({ ...empty, name: location?.name || icon?.label || "", image_path: location?.portrait_or_cover_path || (location ? iconPathForMapLocation(location.name, location.location_type, location.marker_icon) : icon?.path) || "",
      description: location?.public_description || "",
      latitude: location?.latitude ?? location?.y ?? nextPinPosition(tokens).latitude, longitude: location?.longitude ?? location?.x ?? nextPinPosition(tokens).longitude });
  }
  async function save(event: FormEvent) {
    event.preventDefault(); if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError("");
    try {
      const payload = { ...draft, sheet: { role: "Local", marker: "⌖", description: draft.description } };
      if (editing) await updateWorkspaceToken(editing, payload);
      else await createWorkspaceToken({ ...payload, token_type: "location", map_id: mapId });
      await onChange(); setDraft(empty); setEditing("");
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao salvar local"); }
    finally { inFlight.current = false; setBusy(false); }
  }
  return <section className="workspace-monster-catalog">
    <header><strong>LOCAIS · CRIAR E PINAR RAPIDAMENTE</strong></header>
    <select aria-label="Local com pin pronto" defaultValue="" onChange={e => select(e.target.value)}>
      <option value="">Selecionar local ou ícone pronto…</option>
      <optgroup label="Locais cadastrados">{locations.map(l => <option key={l.id} value={`world:${l.id}`}>{l.name}</option>)}</optgroup>
      <optgroup label="Pins prontos do Companion">{COMPANION_ICON_CATALOG.filter(i => i.category === "map").map(i => <option key={i.id} value={i.id}>{i.label}</option>)}</optgroup>
    </select>
    <form className="workspace-monster-form" onSubmit={save}>
      {draft.image_path && <img src={mediaUrlFromVaultPath(draft.image_path)} alt="Pin do local" width={48} height={48} />}
      <input aria-label="Nome do local" placeholder="Nome do local" value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} required maxLength={120} />
      <input aria-label="Imagem do local" placeholder="Caminho da imagem/ícone" value={draft.image_path} onChange={e => setDraft({ ...draft, image_path: e.target.value })} />
      <textarea aria-label="Descrição pública do local" placeholder="Descrição pública (opcional)" value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} />
      {!editing && <div className="workspace-monster-hp"><label>Vertical %<input type="number" min={0} max={100} step="any" value={draft.latitude} onChange={e => setDraft({ ...draft, latitude: Number(e.target.value) })} /></label><label>Horizontal %<input type="number" min={0} max={100} step="any" value={draft.longitude} onChange={e => setDraft({ ...draft, longitude: Number(e.target.value) })} /></label></div>}
      <label><input type="checkbox" checked={draft.visible_to_players} onChange={e => setDraft({ ...draft, visible_to_players: e.target.checked })} /> Mostrar aos jogadores</label>
      <button disabled={busy || !draft.name.trim()}>{editing ? "Salvar local" : "Criar pin de local"}</button>
    </form>
    {tokens.filter(t => t.token_type === "location").map(t => <div className="workspace-monster-row" key={t.id}><strong>{t.name}</strong><small>{t.visible_to_players ? "Visível" : "Oculto"}</small><button onClick={() => { setEditing(t.id); setDraft({ name: t.name, image_path: t.image_path || "", description: t.sheet?.description || "", latitude: t.latitude, longitude: t.longitude, visible_to_players: t.visible_to_players }); }}>Editar</button><button disabled={busy} onClick={async () => { if (!window.confirm(`Remover o pin de ${t.name}?`)) return; try { await removeWorkspaceToken(t.id); await onChange(); } catch (e) { setError(String(e)); } }}>Remover</button></div>)}
    {error && <p role="alert">{error}</p>}
  </section>;
}
