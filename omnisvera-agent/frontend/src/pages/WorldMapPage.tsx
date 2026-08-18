import { useEffect, useMemo, useState } from "react";
import {
  addJourneyParticipant,
  advanceJourney,
  createJourney,
  createTravelRoute,
  createWorldLocation,
  createWorldMap,
  discoverWorldLocation,
  discoverTravelRoute,
  importWorldLocation,
  importWorldMap,
  JourneyRecord,
  listJourneys,
  listNpcs,
  listPlayableCharacters,
  listTravelRoutes,
  listWorldLocations,
  listWorldMaps,
  linkJourneyScene,
  mediaUrlFromVaultPath,
  newWorldRequestId,
  NpcRecord,
  PlayableCharacterSummary,
  transitionJourney,
  TravelRouteRecord,
  updateWorldLocation,
  WorldLocationRecord,
  WorldMapRecord,
} from "../api";
import { iconPathForMapLocation } from "../companionIconCatalog";

type Props = { mode: "gm" | "player"; onOpenScene: (id?: number) => void; onOpenContract: (id?: number) => void };

const LOCATION_TYPES = ["realm", "territory", "region", "city", "village", "port", "fortress", "forest", "mountain", "road", "ruin", "dungeon", "building", "district", "landmark", "unknown"];

function locationTypeLabel(value: string) {
  const labels: Record<string, string> = { realm: "Reino", territory: "Território", region: "Região", city: "Cidade", village: "Vila", port: "Porto", fortress: "Fortaleza", forest: "Floresta", mountain: "Montanha", road: "Estrada", ruin: "Ruína", dungeon: "Masmorra", building: "Edifício", district: "Distrito", landmark: "Marco", unknown: "Desconhecido" };
  return labels[value] || value;
}

function statusLabel(value: string) {
  return ({ planned: "Planejada", active: "Em viagem", paused: "Pausada", completed: "Concluída", cancelled: "Cancelada", failed: "Falhou" } as Record<string, string>)[value] || value;
}

export default function WorldMapPage({ mode, onOpenScene, onOpenContract }: Props) {
  const [maps, setMaps] = useState<WorldMapRecord[]>([]);
  const [locations, setLocations] = useState<WorldLocationRecord[]>([]);
  const [routes, setRoutes] = useState<TravelRouteRecord[]>([]);
  const [journeys, setJourneys] = useState<JourneyRecord[]>([]);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [npcs, setNpcs] = useState<NpcRecord[]>([]);
  const [selectedMapId, setSelectedMapId] = useState<number | null>(null);
  const [selectedLocationId, setSelectedLocationId] = useState<number | null>(null);
  const [view, setView] = useState<"map" | "list">("map");
  const [typeFilter, setTypeFilter] = useState("");
  const [territoryFilter, setTerritoryFilter] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [showMapForm, setShowMapForm] = useState(false);
  const [showLocationForm, setShowLocationForm] = useState(false);
  const [showRouteForm, setShowRouteForm] = useState(false);
  const [showJourneyForm, setShowJourneyForm] = useState(false);

  async function refresh(preferredMap?: number | null) {
    const [mapItems, routeItems, journeyItems, characterItems] = await Promise.all([
      listWorldMaps(), listTravelRoutes(), listJourneys(), listPlayableCharacters(),
    ]);
    const nextMapId = preferredMap || selectedMapId || mapItems[0]?.id || null;
    const locationItems = await listWorldLocations(nextMapId || undefined);
    setMaps(mapItems); setRoutes(routeItems); setJourneys(journeyItems); setCharacters(characterItems);
    setSelectedMapId(nextMapId); setLocations(locationItems);
    if (mode === "gm") setNpcs(await listNpcs().catch(() => []));
    if (selectedLocationId && !locationItems.some((item) => item.id === selectedLocationId)) setSelectedLocationId(null);
  }

  useEffect(() => { void refresh().catch((error) => setMessage(error instanceof Error ? error.message : "Não foi possível carregar o mapa.")); }, [mode]);
  useEffect(() => {
    const update = () => void refresh().catch(() => undefined);
    window.addEventListener("omnisvera-journey-updated", update);
    return () => window.removeEventListener("omnisvera-journey-updated", update);
  }, [mode, selectedMapId]);

  async function changeMap(value: number) {
    setSelectedMapId(value); setSelectedLocationId(null);
    setLocations(await listWorldLocations(value));
  }

  const selectedMap = maps.find((item) => item.id === selectedMapId) || null;
  const selectedLocation = locations.find((item) => item.id === selectedLocationId) || null;
  const filteredLocations = locations.filter((item) => (!typeFilter || item.location_type === typeFilter) && (!territoryFilter || item.territory_name === territoryFilter));
  const territories = [...new Set(locations.map((item) => item.territory_name).filter(Boolean) as string[])].sort();
  const locationMap = useMemo(() => new Map(locations.map((item) => [item.id, item])), [locations]);
  const activeJourney = journeys.find((item) => item.status === "active" || item.status === "paused") || null;

  async function submitMap(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); setMessage("");
    const data = new FormData(event.currentTarget);
    try {
      const item = await createWorldMap({ request_id: newWorldRequestId("map"), title: data.get("title"), image_path: data.get("image_path") || null, map_type: data.get("map_type"), coordinate_system: "percentage", visibility: data.get("visibility") });
      setShowMapForm(false); await refresh(item.id); setMessage("Mapa criado. Agora adicione locais ou importe uma nota de mapa.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao criar mapa."); } finally { setBusy(false); }
  }

  async function submitMapImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); const data = new FormData(event.currentTarget);
    try { const item = await importWorldMap({ request_id: newWorldRequestId("map-import"), source_path: data.get("source_path"), confirm: true }); setShowMapForm(false); await refresh(item.id); setMessage("Mapa importado por referência; o Vault permaneceu intacto."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao importar mapa."); } finally { setBusy(false); }
  }

  async function submitLocation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy || !selectedMapId) return; setBusy(true); const data = new FormData(event.currentTarget);
    try {
      await createWorldLocation({ request_id: newWorldRequestId("location"), map_id: selectedMapId, name: data.get("name"), location_type: data.get("location_type"), territory_name: data.get("territory_name") || null, public_description: data.get("description") || null, visibility: data.get("visibility"), discovered_by_default: data.get("discovered") === "on" });
      setShowLocationForm(false); await refresh(selectedMapId); setMessage("Local criado sem inventar coordenadas.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao criar local."); } finally { setBusy(false); }
  }

  async function submitLocationImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy || !selectedMapId) return; setBusy(true); const data = new FormData(event.currentTarget);
    try {
      await importWorldLocation({ request_id: newWorldRequestId("location-import"), source_path: data.get("source_path"), visibility: data.get("visibility"), discovered_by_default: data.get("discovered") === "on", confirm: true }, selectedMapId);
      setShowLocationForm(false); await refresh(selectedMapId); setMessage("Local importado por referência; a nota permaneceu somente leitura.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao importar local."); } finally { setBusy(false); }
  }

  async function placeLocation(event: React.MouseEvent<HTMLDivElement>) {
    if (mode !== "gm" || !placing || !selectedLocation) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = Math.round(((event.clientX - bounds.left) / bounds.width) * 10000) / 100;
    const y = Math.round(((event.clientY - bounds.top) / bounds.height) * 10000) / 100;
    try { await updateWorldLocation(selectedLocation.id, selectedLocation.version, { x, y }); setPlacing(false); await refresh(selectedMapId); setMessage(`${selectedLocation.name} posicionado em ${x}%, ${y}%.`); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao posicionar local."); }
  }

  async function reveal(level: "rumored" | "approximate" | "discovered" | "visited" | "mapped") {
    if (!selectedLocation || busy) return; setBusy(true);
    try { await discoverWorldLocation(selectedLocation.id, { request_id: newWorldRequestId("discovery"), discoverer_type: "campaign", party_id: "group", knowledge_level: level, public_name_override: level === "rumored" ? selectedLocation.name : null }); setMessage(`Conhecimento atualizado para ${level}.`); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao revelar local."); } finally { setBusy(false); }
  }

  async function submitRoute(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); const data = new FormData(event.currentTarget);
    try { await createTravelRoute({ request_id: newWorldRequestId("route"), title: data.get("title"), origin_location_id: Number(data.get("origin")), destination_location_id: Number(data.get("destination")), route_type: data.get("route_type"), duration_value: data.get("duration") ? Number(data.get("duration")) : null, duration_unit: data.get("duration_unit") || null, public: data.get("public") === "on" }); setShowRouteForm(false); await refresh(selectedMapId); setMessage("Rota unidirecional criada."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao criar rota."); } finally { setBusy(false); }
  }

  async function submitJourney(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); const data = new FormData(event.currentTarget);
    try {
      const item = await createJourney({ request_id: newWorldRequestId("journey"), title: data.get("title"), origin_location_id: Number(data.get("origin")), destination_location_id: Number(data.get("destination")), route_id: data.get("route") ? Number(data.get("route")) : null, progress_target: Number(data.get("target") || 1), visibility: "table" });
      const characterIds = data.getAll("characters").map(String);
      const npcIds = data.getAll("npcs").map(Number);
      for (const id of characterIds) { const character = characters.find((entry) => entry.id === id); await addJourneyParticipant(item.id, { request_id: newWorldRequestId("journey-character"), participant_type: "player_character", character_id: id, public_label: character?.name || id }); }
      for (const id of npcIds) { const npc = npcs.find((entry) => entry.id === id); await addJourneyParticipant(item.id, { request_id: newWorldRequestId("journey-npc"), participant_type: "npc", npc_id: id, public_label: npc?.name || `NPC ${id}` }); }
      setShowJourneyForm(false); await refresh(selectedMapId); setMessage("Viagem planejada. Ninguém foi movido ainda."); window.dispatchEvent(new CustomEvent("omnisvera-journey-updated"));
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao planejar viagem."); } finally { setBusy(false); }
  }

  async function journeyAction(item: JourneyRecord, action: "start" | "pause" | "resume" | "complete" | "cancel" | "fail") {
    if (busy) return; setBusy(true);
    const reason = action === "cancel" || action === "fail" ? window.prompt("Motivo:") : undefined;
    if ((action === "cancel" || action === "fail") && !reason?.trim()) { setBusy(false); return; }
    try { await transitionJourney(item.id, action, { request_id: newWorldRequestId(`journey-${action}`), expected_version: item.version, reason }); await refresh(selectedMapId); setMessage(action === "complete" ? "Chegada confirmada; localizações foram atualizadas." : `Viagem ${statusLabel(action)}.`); window.dispatchEvent(new CustomEvent("omnisvera-journey-updated")); window.dispatchEvent(new CustomEvent("omnisvera-character-state")); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao atualizar viagem."); } finally { setBusy(false); }
  }

  async function advance(item: JourneyRecord) {
    if (busy) return; setBusy(true);
    try { await advanceJourney(item.id, { request_id: newWorldRequestId("journey-advance"), expected_version: item.version, amount: 1 }); await refresh(selectedMapId); setMessage("Viagem avançou uma etapa."); window.dispatchEvent(new CustomEvent("omnisvera-journey-updated")); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao avançar viagem."); } finally { setBusy(false); }
  }

  async function revealRoute(route: TravelRouteRecord) {
    if (busy) return; setBusy(true);
    try {
      await discoverTravelRoute(route.id, { request_id: newWorldRequestId("route-discovery"), discoverer_type: "campaign", party_id: "group", knowledge_level: "discovered" });
      await refresh(selectedMapId); setMessage(`${route.title} foi revelada à mesa.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao revelar rota."); } finally { setBusy(false); }
  }

  async function attachScene(item: JourneyRecord) {
    if (busy) return;
    const value = window.prompt("ID da cena que será vinculada:");
    const sceneId = Number(value);
    if (!value || !Number.isInteger(sceneId) || sceneId < 1) { if (value) setMessage("Informe um ID de cena válido."); return; }
    setBusy(true);
    try {
      await linkJourneyScene(item.id, { request_id: newWorldRequestId("journey-scene"), scene_id: sceneId, progress_value: item.progress_current });
      await refresh(selectedMapId); setMessage("Cena vinculada à etapa atual da viagem.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao vincular cena."); } finally { setBusy(false); }
  }

  return <section className="world-page panel">
    <header className="world-hero">
      <div><p className="eyebrow">Cartografia da campanha</p><h2>Mapa, locais e viagens</h2><p>O mapa mostra apenas o conhecimento permitido para este acesso.</p></div>
      <div className="world-view-switch"><button className={view === "map" ? "active" : ""} onClick={() => setView("map")}>Mapa</button><button className={view === "list" ? "active" : ""} onClick={() => setView("list")}>Lista acessível</button></div>
    </header>

    <div className="world-toolbar">
      <label>Mapa<select value={selectedMapId || ""} onChange={(event) => void changeMap(Number(event.target.value))}><option value="">Nenhum mapa</option>{maps.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
      <label>Tipo<select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}><option value="">Todos</option>{LOCATION_TYPES.map((item) => <option key={item} value={item}>{locationTypeLabel(item)}</option>)}</select></label>
      <label>Território<select value={territoryFilter} onChange={(event) => setTerritoryFilter(event.target.value)}><option value="">Todos</option>{territories.map((item) => <option key={item}>{item}</option>)}</select></label>
      {mode === "gm" && <div className="world-master-actions"><button onClick={() => setShowMapForm((value) => !value)}>Mapa</button><button disabled={!selectedMap} onClick={() => setShowLocationForm((value) => !value)}>Local</button><button disabled={locations.length < 2} onClick={() => setShowRouteForm((value) => !value)}>Rota</button><button disabled={locations.length < 2} onClick={() => setShowJourneyForm((value) => !value)}>Viagem</button></div>}
    </div>

    {message && <p className="world-message" role="status">{message}</p>}
    {showMapForm && <section className="world-admin-form"><form onSubmit={submitMap}><h3>Novo mapa transacional</h3><label>Título<input required name="title" /></label><label>Imagem no Vault<input name="image_path" placeholder="zz_media/maps/...png" /></label><label>Tipo<select name="map_type"><option value="world">Mundo</option><option value="territory">Território</option><option value="city">Cidade</option><option value="custom">Personalizado</option></select></label><label>Visibilidade<select name="visibility"><option value="gm">Mestre</option><option value="table">Mesa</option><option value="public">Público</option></select></label><button disabled={busy}>Criar</button></form><form onSubmit={submitMapImport}><h3>Importar nota de mapa</h3><label>Caminho exato<input required name="source_path" placeholder="MAPA DE NIMALIA.md" /></label><p>Importa referência, imagem e dimensões. Marcadores ambíguos ficam para revisão.</p><button disabled={busy}>Revisar e importar</button></form></section>}
    {showLocationForm && <section className="world-admin-form"><form className="world-inline-form" onSubmit={submitLocation}><h3>Novo local</h3><label>Nome<input required name="name" /></label><label>Tipo<select name="location_type">{LOCATION_TYPES.map((item) => <option key={item} value={item}>{locationTypeLabel(item)}</option>)}</select></label><label>Território<input name="territory_name" /></label><label>Descrição pública<textarea name="description" /></label><label>Visibilidade<select name="visibility"><option value="gm">Mestre</option><option value="table">Mesa</option><option value="public">Público</option></select></label><label className="check-label"><input type="checkbox" name="discovered" />Descoberto por padrão</label><button disabled={busy}>Criar sem coordenada</button></form><form className="world-inline-form" onSubmit={submitLocationImport}><h3>Importar local do Vault</h3><label>Caminho exato<input required name="source_path" placeholder="Locations/Nome do Local.md" /></label><label>Visibilidade<select name="visibility"><option value="gm">Mestre</option><option value="table">Mesa</option><option value="public">Público</option></select></label><label className="check-label"><input type="checkbox" name="discovered" />Liberar ao importar</label><p>A importação é explícita, idempotente e não altera a nota.</p><button disabled={busy}>Revisar e importar</button></form></section>}
    {showRouteForm && <form className="world-admin-form compact" onSubmit={submitRoute}><h3>Nova rota unidirecional</h3><label>Título<input required name="title" /></label><label>Origem<select required name="origin">{locations.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Destino<select required name="destination">{locations.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Tipo<select name="route_type"><option value="road">Estrada</option><option value="trail">Trilha</option><option value="sea">Mar</option><option value="wilderness">Ermos</option><option value="custom">Outro</option></select></label><label>Duração<input type="number" min="0" name="duration" /></label><label>Unidade<input name="duration_unit" placeholder="dias, etapas..." /></label><label className="check-label"><input type="checkbox" name="public" />Rota pública</label><button disabled={busy}>Criar rota</button></form>}
    {showJourneyForm && <form className="world-admin-form compact" onSubmit={submitJourney}><h3>Planejar viagem</h3><label>Título<input required name="title" /></label><label>Origem<select required name="origin">{locations.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Destino<select required name="destination">{locations.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Rota opcional<select name="route"><option value="">Abstrata</option>{routes.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><label>Etapas<input type="number" min="1" defaultValue="4" name="target" /></label><fieldset><legend>Personagens</legend>{characters.filter((item) => item.access_level !== "public").map((item) => <label className="check-label" key={item.id}><input type="checkbox" name="characters" value={item.id} />{item.name}</label>)}</fieldset><fieldset><legend>NPCs</legend>{npcs.map((item) => <label className="check-label" key={item.id}><input type="checkbox" name="npcs" value={item.id} />{item.name}</label>)}</fieldset><button disabled={busy}>Criar viagem planejada</button></form>}

    {!maps.length ? <div className="world-empty"><span aria-hidden="true">⌖</span><h3>Nenhum mapa registrado</h3><p>{mode === "gm" ? "Crie um mapa transacional ou importe explicitamente uma nota de mapa." : "O mestre ainda não liberou um mapa."}</p></div> : <div className="world-layout">
      <div className="world-main">
        {view === "map" ? <div className={`world-map-canvas ${placing ? "placing" : ""}`} role="img" aria-label={`Mapa ${selectedMap?.title || "da campanha"}`} onClick={(event) => void placeLocation(event)}>
          {selectedMap?.image_path ? <img src={mediaUrlFromVaultPath(selectedMap.image_path)} alt={`Mapa-base de ${selectedMap.title}`} /> : <div className="world-map-fallback"><span>⌖</span><p>Mapa sem imagem-base. Os marcadores continuam disponíveis.</p></div>}
          <svg className="world-route-layer" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{routes.map((route) => { const origin = locationMap.get(route.origin_location_id); const destination = locationMap.get(route.destination_location_id); if (origin?.x == null || origin.y == null || destination?.x == null || destination.y == null) return null; return <line key={route.id} x1={origin.x} y1={origin.y} x2={destination.x} y2={destination.y} />; })}</svg>
          {filteredLocations.filter((item) => item.x != null && item.y != null).map((item) => { const icon = iconPathForMapLocation(item.name, item.location_type, item.marker_icon); return <button key={item.id} className={`world-marker ${selectedLocationId === item.id ? "selected" : ""}`} style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={(event) => { event.stopPropagation(); setSelectedLocationId(item.id); }} aria-label={`Abrir ${item.name}`}><span>{icon ? <img src={mediaUrlFromVaultPath(icon)} alt="" /> : item.marker_icon || "◆"}</span><small>{item.name}</small></button>; })}
          {activeJourney && <div className="world-journey-line" aria-label={`Viagem ativa: ${activeJourney.title}`}><strong>{activeJourney.title}</strong><span style={{ width: `${Math.min(100, activeJourney.progress_current / activeJourney.progress_target * 100)}%` }} /></div>}
        </div> : <div className="world-location-list" role="list" aria-label="Locais autorizados">{filteredLocations.length ? filteredLocations.map((item) => { const icon = iconPathForMapLocation(item.name, item.location_type, item.marker_icon); return <button role="listitem" key={item.id} className={selectedLocationId === item.id ? "selected" : ""} onClick={() => setSelectedLocationId(item.id)}><span className="world-list-icon">{icon ? <img src={mediaUrlFromVaultPath(icon)} alt="" /> : item.marker_icon || "◆"}</span><span><strong>{item.name}</strong><small>{locationTypeLabel(item.location_type)}{item.territory_name ? ` · ${item.territory_name}` : ""}</small></span><em>{item.knowledge_level || "mapeado"}</em></button>; }) : <p className="sheet-empty">Nenhum local corresponde aos filtros.</p>}</div>}
      </div>

      <aside className="world-detail">
        {selectedLocation ? <><header>{selectedLocation.portrait_or_cover_path ? <img src={mediaUrlFromVaultPath(selectedLocation.portrait_or_cover_path)} alt="" /> : <img src={mediaUrlFromVaultPath(iconPathForMapLocation(selectedLocation.name, selectedLocation.location_type, selectedLocation.marker_icon))} alt="" />}<div><small>{locationTypeLabel(selectedLocation.location_type)}</small><h3>{selectedLocation.name}</h3><p>{selectedLocation.territory_name || "Território não informado"}</p></div></header><p>{selectedLocation.public_description || "Ainda não há descrição pública para este local."}</p><div className="world-detail-meta"><span><small>Conhecimento</small><strong>{selectedLocation.knowledge_level || "Mestre"}</strong></span><span><small>Estado</small><strong>{selectedLocation.public_status || "Não informado"}</strong></span><span><small>Perigo</small><strong>{selectedLocation.danger_label || "Não informado"}</strong></span><span><small>Coordenada</small><strong>{selectedLocation.x == null ? "Não posicionada" : `${selectedLocation.x}%, ${selectedLocation.y}%`}</strong></span></div>
          <section><h4>Rotas autorizadas</h4>{routes.filter((route) => route.origin_location_id === selectedLocation.id || route.destination_location_id === selectedLocation.id).map((route) => <div key={route.id} className="world-route-row"><strong>{route.title}</strong><span>{route.duration_value ? `${route.duration_value} ${route.duration_unit || ""}` : "Duração não informada"}</span>{mode === "gm" && !route.public && <button disabled={busy} onClick={() => void revealRoute(route)}>Revelar rota</button>}</div>)}</section>
          {mode === "gm" && <div className="world-detail-actions"><button onClick={() => { setPlacing(true); setView("map"); }}>Posicionar no mapa</button><button onClick={() => void reveal("rumored")}>Revelar rumor</button><button onClick={() => void reveal("discovered")}>Revelar local</button><button onClick={() => void reveal("visited")}>Marcar visitado</button></div>}
          {selectedLocation.current_scene_id && <button onClick={() => onOpenScene(selectedLocation.current_scene_id || undefined)}>Abrir cena atual</button>}
        </> : <div className="world-detail-empty"><span>◇</span><h3>Escolha um local</h3><p>Abra um marcador ou use a lista acessível.</p></div>}
      </aside>
    </div>}

    <section className="journey-board"><header><div><p className="eyebrow">Deslocamento persistente</p><h3>Viagens</h3></div><span>{journeys.filter((item) => item.status === "active" || item.status === "paused").length} em andamento</span></header>{journeys.length ? journeys.map((item) => <article className={`journey-card ${item.status}`} key={item.id}><header><div><small>{statusLabel(item.status)}</small><strong>{item.title}</strong></div><em>{item.progress_current}/{item.progress_target}</em></header><div className="journey-progress"><span style={{ width: `${Math.min(100, item.progress_current / item.progress_target * 100)}%` }} /></div><p>{locationMap.get(item.origin_location_id)?.name || `Local ${item.origin_location_id}`} → {locationMap.get(item.destination_location_id)?.name || `Local ${item.destination_location_id}`}</p><div className="journey-participants">{item.participants.map((participant) => <span key={participant.id}>{participant.public_label}</span>)}</div>{item.contract_id && <button className="secondary-button" onClick={() => onOpenContract(item.contract_id || undefined)}>Abrir contrato</button>}{item.scene_links.map((link) => <button className="secondary-button" key={String(link.id)} onClick={() => onOpenScene(Number(link.scene_id))}>Abrir cena</button>)}{mode === "gm" && <footer>{item.status === "planned" && <button disabled={busy} onClick={() => void journeyAction(item, "start")}>Iniciar</button>}{item.status === "active" && <><button disabled={busy || item.progress_current >= item.progress_target} onClick={() => void advance(item)}>Avançar +1</button><button disabled={busy} onClick={() => void journeyAction(item, "pause")}>Pausar</button></>}{item.status === "paused" && <button disabled={busy} onClick={() => void journeyAction(item, "resume")}>Retomar</button>}{(item.status === "planned" || item.status === "active" || item.status === "paused") && <button disabled={busy} onClick={() => void attachScene(item)}>Vincular cena</button>}{(item.status === "active" || item.status === "paused") && <><button disabled={busy} onClick={() => void journeyAction(item, "complete")}>Confirmar chegada</button><button className="danger-button" disabled={busy} onClick={() => void journeyAction(item, "cancel")}>Cancelar</button></>}</footer>}</article>) : <p className="sheet-empty">Nenhuma viagem registrada.</p>}</section>
  </section>;
}
