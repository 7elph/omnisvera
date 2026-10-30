import { useEffect, useRef, useState } from "react";
import { editWorkspaceMap, listWorkspaceMaps, mediaUrlFromVaultPath, WorkspaceMap } from "../api";
import './mapManagement.css';

/** Presentation grouping from explicit names only, not inferred play history. */
export function mapLibraryGroup(map: Pick<WorkspaceMap, 'title'>) {
  const title=(map.title || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  if (/nimalis|nimalia|earthropo/.test(title)) return 'Mundos e cidades';
  const session=title.match(/(?:^|\b)(?:s|sessao\s*|session\s*)(\d+)\b/);
  return session ? `Sessão ${Number(session[1])}` : 'Outros mapas';
}

export default function WorkspaceMapLibrary({ maps, activeId, onChange, onSelect, selectionDisabled=false }: {
  maps: WorkspaceMap[]; activeId?: string; onChange: () => Promise<void>; onSelect: (id:string)=>Promise<void>; selectionDisabled?:boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedMaps,setSavedMaps]=useState(maps);
  const [query,setQuery]=useState('');
  const [group,setGroup]=useState('');
  const [loading,setLoading]=useState(false);
  const mounted=useRef(true),reading=useRef(false);
  useEffect(()=>{setSavedMaps(maps);},[maps]);
  useEffect(()=>{mounted.current=true;void refresh();return()=>{mounted.current=false;};},[]);
  async function refresh() {
    if(reading.current)return;reading.current=true;setLoading(true);setError('');
    try {const result=await listWorkspaceMaps();if(mounted.current)setSavedMaps(result);}
    catch(reason){if(mounted.current)setError(reason instanceof Error?reason.message:'Falha ao carregar mapas');}
    finally {reading.current=false;if(mounted.current)setLoading(false);}
  }
  async function open(id:string){
    if(busy||selectionDisabled)return;setBusy(true);setError('');
    try {await onSelect(id);}catch(reason){setError(reason instanceof Error?reason.message:'Falha ao abrir mapa');}
    finally {setBusy(false);}
  }
  async function change(map: WorkspaceMap, remove: boolean) {
    const title = remove ? undefined : window.prompt("Nome do mapa", map.title);
    if (!remove && !title?.trim()) return;
    if (remove && !window.confirm(`Excluir “${map.title}” da biblioteca? A imagem original será preservada.`)) return;
    setBusy(true); setError("");
    try { await editWorkspaceMap(map.id, title ?? undefined); await refresh(); await onChange(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao alterar mapa"); }
    finally { setBusy(false); }
  }
  const groups=Array.from(new Set(savedMaps.map(mapLibraryGroup)));
  const visibleMaps=savedMaps.filter(map=>(!group || mapLibraryGroup(map)===group) && map.title.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  return <section className="workspace-map-library" aria-label="Biblioteca de mapas">
    <header><h3>Mapas salvos</h3><button type="button" disabled={loading} onClick={()=>void refresh()}>Atualizar lista</button></header>
    <input type="search" aria-label="Buscar mapas" placeholder="Buscar mapa…" value={query} onChange={event=>setQuery(event.target.value)}/>
    <select aria-label="Grupo de mapas" value={group} onChange={event=>setGroup(event.target.value)}><option value="">Todos os mapas</option>{groups.map(label=><option key={label} value={label}>{label}</option>)}</select>
    {error && <p role="alert">{error}</p>}
    {loading&&<p role="status">Atualizando lista…</p>}
    {selectionDisabled&&<p>Encerre o combate para trocar a arena. A biblioteca continua acessível.</p>}
    <div className="workspace-map-library-list">{visibleMaps.map(map => <article key={map.id}>
      {map.image_path && <img className="workspace-map-library-preview" src={mediaUrlFromVaultPath(map.image_path)} alt="" loading="lazy" />}
      <strong>{map.title}</strong><small>{map.id===activeId?'Em uso · ':''}{map.visible_to_players?'Público':'Privado'}</small>
      <small>{mapLibraryGroup(map)}{map.grid ? ' · Com grade' : ''}</small>
      <div><button type="button" disabled={busy||selectionDisabled||map.id===activeId} onClick={()=>void open(map.id)}>Abrir</button>
      <button type="button" disabled={busy} onClick={() => void change(map, false)}>Renomear</button>
      <button type="button" disabled={busy || map.id === activeId || map.id.startsWith("official:")}
        onClick={() => void change(map, true)}>Excluir</button>
      </div>
    </article>)}</div>
    {!visibleMaps.length&&!loading&&<p>{query?'Nenhum mapa corresponde à busca.':'Nenhum mapa salvo. Envie uma imagem acima ou atualize a lista.'}</p>}
    <p>Excluir preserva a imagem original. Não é possível excluir o mapa ativo.</p>
  </section>;
}
