import { useEffect, useMemo, useRef, useState } from 'react';
import type { GameScene, WorkspaceMap, WorkspaceSnapshot,SceneTableSelection } from '../api';
import { mediaUrlFromVaultPath } from '../api';
import { assetLabels, contextSections, filterPreparations, fogPreviewCells, sceneAssets, sceneContexts, scenePinPoint, sceneStatusLabel, selectionForAssets, type SceneAsset, type SceneContext } from '../scenePreparation';
import { LogicalGrid } from './LogicalGrid';
import './scenePreparation.css';

function Art({ path, title, symbol = '◇' }: { path?: string | null; title: string; symbol?: string }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [path]);
  const src = mediaUrlFromVaultPath(path);
  return src && !failed ? <img src={src} alt={title} loading="lazy" decoding="async" onError={() => setFailed(true)} />
    : <span className="scene-art-placeholder" aria-label={`${title}: sem imagem`}>{symbol}</span>;
}

export function ScenePreparationLibrary({ scenes, maps, selectedId, sessions, onSelect, onCreate, onRefresh }: {
  scenes: GameScene[]; maps: Array<Pick<WorkspaceMap, 'id' | 'title' | 'image_path'>>; selectedId: number | null;
  sessions: Array<{ id: number; title: string }>; onSelect: (id: number) => void; onCreate: () => void; onRefresh: () => void;
}) {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('all');
  const [session, setSession] = useState('all');
  const filtered = useMemo(() => filterPreparations(scenes, query, status, session), [scenes, query, status, session]);
  return <section className="scene-preparation-library" aria-label="Biblioteca de preparações">
    <header className="scene-gallery-heading"><div><small>Somente Mestre · sequência de preparações</small><h2>Preparações de cena</h2><p>Escolha um bloco e organize a prévia pelo contexto da sessão.</p></div>
      <div><button type="button" onClick={onRefresh} aria-label="Atualizar preparações">↻</button><button type="button" onClick={onCreate}>＋ Nova preparação</button></div></header>
    <div className="scene-gallery-filters">
      <label>Buscar<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Cena, local ou objetivo" /></label>
      <label>Estado<select value={status} onChange={e => setStatus(e.target.value)}><option value="all">Todos</option>{['draft', 'active', 'paused', 'resolved', 'abandoned'].map(s => <option key={s} value={s}>{sceneStatusLabel(s)}</option>)}</select></label>
      <label>Sessão<select value={session} onChange={e => setSession(e.target.value)}><option value="all">Todas</option><option value="unassigned">Blocos sem sessão</option>{sessions.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
      <output aria-live="polite">{filtered.length}/{scenes.length}</output>
    </div>
    <div className="scene-preparation-card-grid" tabIndex={0} aria-label="Sequência de preparações">{filtered.map((scene, index) => {
      const cover = scene.image_path || maps.find(m => m.id === scene.map_id)?.image_path;
      const done = Object.values(scene.checklist || {}).filter(Boolean).length;
      return <button type="button" key={scene.id} className="companion-card scene-library-card" aria-pressed={selectedId === scene.id} onClick={() => onSelect(scene.id)}>
        <div className="scene-library-cover"><Art path={cover} title={scene.title} symbol="▧" /><span>{String(index + 1).padStart(2, '0')} · {sceneStatusLabel(scene.status)}</span></div>
        <div className="scene-library-copy"><strong>{scene.title}</strong><small>{scene.location_name}</small>
          <p>{scene.objective || scene.public_description || 'Sem resumo.'}</p>
          <div className="scene-card-meta"><span>{scene.participants.filter(p => !p.left_at).length} participantes</span><span>{scene.elements.length} elementos</span><span>{done}/17</span></div>
          <small>{scene.session_id ? sessions.find(s => s.id === scene.session_id)?.title || `Sessão ${scene.session_id}` : 'Bloco sem sessão'} · {scene.visibility === 'table' && scene.status !== 'draft' ? 'Publicado' : 'Privado'}</small>
        </div>
      </button>;
    })}</div>
    {!filtered.length && <p className="sheet-empty">Nenhuma preparação neste filtro.</p>}
  </section>;
}

function AssetInspector({ asset, onClose, workspace, pins, publicOnly, onInspect, onBack }: {
  asset: SceneAsset; onClose: () => void; workspace: WorkspaceSnapshot | null;
  pins: SceneAsset[]; publicOnly: boolean; onInspect: (id: string) => void; onBack?: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const node = dialog.current;
    node?.showModal();
    return () => { node?.close(); previous?.focus(); };
  }, []);
  useEffect(() => { close.current?.focus(); }, [asset.id]);
  const mapPreview = asset.kind === 'map' && workspace?.map;
  return <dialog ref={dialog} className={`scene-asset-dialog${mapPreview ? ' scene-map-dialog' : ''}`} aria-label={asset.title} onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <header><div><small>{assetLabels[asset.kind] || 'Elemento'}{asset.hidden ? ' · Reservado' : ''}</small><h3>{asset.title}</h3></div><button ref={close} type="button" onClick={onClose} aria-label="Fechar detalhes">×</button></header>
    {onBack && <button type="button" onClick={onBack}>← Voltar ao mapa</button>}
    {mapPreview && workspace ? <SceneMapPreview workspace={workspace} pins={pins} publicOnly={publicOnly} onInspect={onInspect} />
      : asset.image && <Art path={asset.image} title={asset.title} />}
    {asset.text && <p className="scene-asset-text">{asset.text}</p>}
    {asset.privateText && <section className="scene-asset-private"><small>Somente Mestre</small><p className="scene-asset-text">{asset.privateText}</p></section>}
    {asset.token?.current_hp != null && <p>PV {asset.token.current_hp}/{asset.token.maximum_hp ?? '—'}{asset.token.sheet?.armor_class != null ? ` · CA ${asset.token.sheet.armor_class}` : ''}</p>}
    {!asset.text && !asset.privateText && !asset.image && <p>Sem descrição adicional cadastrada.</p>}
  </dialog>;
}

export function SceneMapPreview({ workspace, pins, publicOnly, onInspect }: {
  workspace: WorkspaceSnapshot; pins: SceneAsset[]; publicOnly: boolean; onInspect: (id: string) => void;
}) {
  const [zoom, setZoom] = useState(1);
  const map = workspace.map;
  const fog = useMemo(() => fogPreviewCells(workspace), [workspace]);
  if (!map) return null;
  return <section className="scene-map-preview" aria-label="Prévia do mapa e pins">
    <header><strong>{map.title}</strong><div className="scene-preview-zoom"><button type="button" disabled={zoom <= 1} aria-label="Reduzir prévia" onClick={() => setZoom(z => Math.max(1, z - .25))}>−</button><output>{Math.round(zoom * 100)}%</output><button type="button" disabled={zoom >= 3} aria-label="Ampliar prévia" onClick={() => setZoom(z => Math.min(3, z + .25))}>＋</button><button type="button" onClick={() => setZoom(1)}>Ajustar</button></div></header>
    <div className="scene-map-preview-viewport"><div className="scene-map-preview-surface" style={{ width: `${zoom * 100}%` }}>
      <Art path={map.image_path} title={map.title} symbol="▧" />
      {map.grid && <LogicalGrid grid={map.grid} destination={null} />}
      <svg className="scene-preview-fog" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{fog.map((cell, index) => <rect key={index} x={cell.x} y={cell.y} width={cell.w} height={cell.h} fill={publicOnly ? '#080b0d' : '#d2dce2'} opacity={cell.density * (publicOnly ? 1 : .4)} />)}</svg>
      {pins.map(asset => {
        if (!asset.token) return null;
        const point = scenePinPoint(asset.token, map.grid);
        const pos = asset.token.grid_position;
        const footprint = map.grid && pos ? { width: `${pos.footprint_w * (100 - map.grid.origin_x) / map.grid.cols}%`, height: `${pos.footprint_h * (100 - map.grid.origin_y) / map.grid.rows}%` } : {};
        return <button type="button" key={asset.id} className={`scene-preview-pin ${asset.hidden ? 'reserved' : ''}`} style={{ left: `${point.longitude}%`, top: `${point.latitude}%`, ...footprint }}
          aria-label={`Inspecionar pin ${asset.title}${asset.hidden ? ' · oculto' : ''}`} title={asset.title} onClick={() => onInspect(asset.id)}><Art path={asset.image} title={asset.title} symbol="♟" /></button>;
      })}
    </div></div><small>Somente leitura · clique nos pins para inspecionar. Editar posição e névoa em Mapas.</small>
  </section>;
}

export function ScenePreparationViewer({ scene, workspace, loading, error, onRetry,onPublish }: {
  scene: GameScene; workspace: WorkspaceSnapshot | null; loading: boolean; error: string; onRetry: () => void;
  onPublish?:(selection:SceneTableSelection,requestId:string)=>Promise<void>;
}) {
  const [publicOnly, setPublicOnly] = useState(false);
  const [context, setContext] = useState<SceneContext>('exploration');
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [inspectingMap, setInspectingMap] = useState(false);
  const [kind, setKind] = useState('all');
  const [selected, setSelected] = useState<string | null>(null);
  const [publishIds,setPublishIds]=useState<string[]>([]),[confirm,setConfirm]=useState(false),[publishing,setPublishing]=useState(false),[publishError,setPublishError]=useState('');
  const publishLock=useRef(false),receipt=useRef<{intent:string;id:string}|null>(null);
  const assets = useMemo(() => sceneAssets(scene, workspace, publicOnly), [scene, workspace, publicOnly]);
  const current = assets.find(a => a.id === selected);
  const filtered = assets.filter(a => kind === 'all' || a.kind === kind);
  const privateScene = scene.visibility !== 'table' || scene.status === 'draft';
  const sections = contextSections(context, assets);
  const profile = sceneContexts.find(item => item.id === context)!;
  const mapAsset = assets.find(asset => asset.kind === 'map');
  const selection=selectionForAssets(assets,publishIds);
  const hasSelection=selection.include_map||selection.element_ids.length>0||selection.token_ids.length>0;
  async function publish(){
    if(publishLock.current||!onPublish||!hasSelection)return;
    publishLock.current=true;setPublishing(true);setPublishError('');
    const intent=JSON.stringify(selection);
    if(receipt.current?.intent!==intent)receipt.current={intent,id:'scene-selection:'+crypto.randomUUID()};
    try{await onPublish(selection,receipt.current.id);setConfirm(false);setPublishIds([]);receipt.current=null;}
    catch(reason){setPublishError(reason instanceof Error?reason.message:'Não foi possível enviar a seleção.');}
    finally{publishLock.current=false;setPublishing(false);}
  }
  function inspect(asset: SceneAsset) {
    setInspectingMap(asset.kind === 'map');
    setSelected(asset.id);
  }
  function assetCard(asset: SceneAsset) {
    return <article className={`companion-card scene-asset-card${asset.kind === 'map' ? ' scene-map-card' : ''}`} key={asset.id} data-asset-kind={asset.kind}>
      {onPublish&&!publicOnly&&(asset.kind==='map'||asset.kind==='pin'||/:element:\d+$/.test(asset.id))&&<input type="checkbox" aria-label={`Selecionar ${asset.title}`} checked={publishIds.includes(asset.id)} disabled={publishing} onChange={e=>setPublishIds(ids=>e.target.checked?[...ids,asset.id]:ids.filter(id=>id!==asset.id))}/>}
      <button type="button" className="scene-asset-inspect" onClick={()=>inspect(asset)}>
        <Art path={asset.image} title={asset.title} symbol={asset.kind === 'text' ? '▤' : asset.kind === 'pin' ? '♟' : asset.kind === 'map' ? '▧' : '◇'} />
        <div><small>{assetLabels[asset.kind] || 'Elemento'}{asset.hidden ? ' · Reservado' : ''}</small><strong>{asset.title}</strong><p>{asset.kind === 'map' ? 'Abrir mapa e pins' : asset.text || asset.privateText || 'Clique para inspecionar'}</p></div>
      </button>
    </article>;
  }
  return <section id="scene-preparation-viewer" tabIndex={-1} className="scene-preparation-viewer" aria-label={`Preparação: ${scene.title}`}>
    <header className="scene-gallery-heading"><div><small>{scene.location_name}</small><h2>{scene.title}</h2><p>{publicOnly ? 'Conteúdo já publicado; não é simulação de uma conta de jogador.' : 'Visualizador privado · os dados continuam nos cadastros originais.'}</p></div>
      <div className="scene-preview-modes" role="group" aria-label="Camada da prévia"><button type="button" aria-pressed={!publicOnly} onClick={() => setPublicOnly(false)}>Preparação</button><button type="button" aria-pressed={publicOnly} onClick={() => setPublicOnly(true)}>Conteúdo público</button></div></header>
    {publicOnly && privateScene && <p role="status">Este bloco é privado e ainda não foi publicado para os jogadores.</p>}
    {loading && !publicOnly && <p role="status">Carregando mapa da preparação…</p>}
    {error && !publicOnly && <p role="alert">{error} <button type="button" onClick={onRetry}>Tentar novamente</button></p>}
    <div className="scene-context-cards" role="group" aria-label="Contextos da preparação">{sceneContexts.map(item => <button type="button" key={item.id} className="companion-card scene-context-card" aria-label={`Contexto: ${item.label}`} aria-pressed={context === item.id} onClick={() => setContext(item.id)}>
      <span aria-hidden="true">{item.symbol}</span><strong>{item.label}</strong><small>{item.hint}</small>
    </button>)}</div>
    <div className="scene-context-heading"><div><h3>{profile.label}</h3><small>{profile.hint}</small></div><button type="button" aria-controls="scene-element-library" aria-expanded={libraryOpen} onClick={() => setLibraryOpen(open => !open)}>Biblioteca · {assets.length}</button></div>
    {onPublish&&!publicOnly&&<div className="scene-selection-toolbar"><span>{publishIds.length} selecionados</span><button disabled={!hasSelection||publishing} onClick={()=>{setPublishError('');setConfirm(true);}}>Levar seleção à Mesa</button></div>}
    <div className={`scene-context-layout${libraryOpen ? ' library-open' : ''}`}>
      <div className="scene-context-content" data-scene-context={context}>{sections.map(group => <section className="scene-context-section" key={group.title} aria-label={group.title}>
        <h4>{group.title} <small>{group.assets.length}</small></h4><div className="scene-asset-card-grid">{group.assets.map(assetCard)}</div>
      </section>)}{!sections.length && !(publicOnly && privateScene) && <p className="sheet-empty">Nenhum elemento neste contexto. Consulte a biblioteca ou edite a preparação.</p>}</div>
      {libraryOpen && <aside id="scene-element-library" className="scene-element-library" aria-label="Biblioteca de elementos">
        <header><strong>Todos os elementos</strong><button type="button" onClick={() => setLibraryOpen(false)} aria-label="Fechar biblioteca">×</button></header>
        <div className="scene-asset-filters" role="group" aria-label="Tipos de elemento"><button type="button" aria-pressed={kind === 'all'} onClick={() => setKind('all')}>Todos · {assets.length}</button>{[...new Set(assets.map(a => a.kind))].map(type => <button type="button" key={type} aria-pressed={kind === type} onClick={() => setKind(type)}>{assetLabels[type] || 'Elemento'} · {assets.filter(a => a.kind === type).length}</button>)}</div>
        <div className="scene-asset-card-grid">{filtered.map(assetCard)}</div>
        {!filtered.length && <p className="sheet-empty">Nenhum elemento deste tipo.</p>}
      </aside>}
    </div>
    {current && <AssetInspector asset={current} workspace={workspace} pins={assets.filter(a => a.kind === 'pin')} publicOnly={publicOnly} onInspect={setSelected} onClose={() => setSelected(null)} onBack={inspectingMap && current.kind !== 'map' && mapAsset ? () => setSelected(mapAsset.id) : undefined} />}
    {confirm&&<dialog open className="scene-selection-confirm" aria-label="Confirmar envio à Mesa"><h3>Levar seleção à Mesa?</h3><p>{assets.filter(a=>publishIds.includes(a.id)).map(a=>a.title).join(' · ')}</p><p>Somente descrições públicas. A névoa do mapa é preservada.</p>{publishError&&<p role="alert">{publishError}</p>}<button disabled={publishing} onClick={()=>void publish()}>Confirmar</button><button disabled={publishing} onClick={()=>setConfirm(false)}>Cancelar</button></dialog>}
  </section>;
}
