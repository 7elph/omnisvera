import type { GameScene, SceneParticipant, WorkspaceSnapshot, WorkspaceToken } from './api';
import { cellCenter, type MapGrid } from './spatialGrid';

export type SceneAsset = {
  id: string; kind: string; title: string; image?: string | null;
  text?: string | null; privateText?: string | null; hidden?: boolean;
  token?: WorkspaceToken;
};
export const assetLabels: Record<string, string> = {
  image: 'Imagem', map: 'Mapa', text: 'Texto', character: 'Personagem', npc: 'NPC',
  creature: 'Criatura', pin: 'Pin', clue: 'Pista', threat: 'Ameaça', objective: 'Objetivo',
  object: 'Objeto', exit: 'Saída', environmental_effect: 'Ambiente',
};
export const sceneStatusLabel = (status: string) => ({ draft: 'Rascunho', active: 'Ativa',
  paused: 'Pausada', resolved: 'Encerrada', abandoned: 'Abandonada' }[status] || status);
export const sceneContexts = [
  { id: 'exploration', label: 'Exploração', symbol: '⌖', hint: 'Mapa, locais e descobertas', groups: [
    { title: 'Mapa e pontos de interesse', kinds: ['map', 'pin', 'exit'] },
    { title: 'Abertura e ambiente', kinds: ['image', 'text', 'objective', 'environmental_effect'] },
    { title: 'Descobertas', kinds: ['clue', 'object'] },
  ] },
  { id: 'combat', label: 'Combate', symbol: '⚔', hint: 'Arena, criaturas e ameaças', groups: [
    { title: 'Arena', kinds: ['map', 'environmental_effect'] },
    { title: 'Participantes e ameaças', kinds: ['character', 'creature', 'threat', 'pin'] },
    { title: 'Objetivo e recompensas', kinds: ['objective', 'object', 'text'] },
  ] },
  { id: 'conversation', label: 'Conversa', symbol: '☏', hint: 'NPCs, falas e segredos', groups: [
    { title: 'Interlocutores', kinds: ['npc', 'character'] },
    { title: 'Falas e informações', kinds: ['text', 'objective', 'clue', 'image'] },
  ] },
  { id: 'commerce', label: 'Comércio', symbol: '⚖', hint: 'Comerciantes e objetos da cena', groups: [
    { title: 'Comerciantes e locais', kinds: ['npc', 'pin'] },
    { title: 'Objetos e informações', kinds: ['object', 'text', 'objective', 'image'] },
  ] },
  { id: 'investigation', label: 'Investigação', symbol: '⌕', hint: 'Pistas, documentos e conexões', groups: [
    { title: 'Pistas e objetos', kinds: ['clue', 'object'] },
    { title: 'Documentos e contexto', kinds: ['text', 'image', 'objective', 'exit'] },
  ] },
  { id: 'travel', label: 'Viagem / descanso', symbol: '☽', hint: 'Rota, passagem de tempo e acontecimentos', groups: [
    { title: 'Rota e grupo', kinds: ['map', 'character', 'exit'] },
    { title: 'Acontecimentos', kinds: ['text', 'image', 'environmental_effect', 'objective'] },
  ] },
] as const;
export type SceneContext = typeof sceneContexts[number]['id'];

/** Presentation only: source data and publication selection remain independent of the chosen layout. */
export function contextSections(context: SceneContext, assets: SceneAsset[]) {
  const profile = sceneContexts.find(item => item.id === context)!;
  return profile.groups.map(group => ({ title: group.title,
    assets: assets.filter(asset => (group.kinds as readonly string[]).includes(asset.kind)),
  })).filter(group => group.assets.length > 0);
}
const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

export function filterPreparations(scenes: GameScene[], query: string, status: string, session: string) {
  const search = normalize(query.trim());
  return scenes.filter(s => (status === 'all' || s.status === status)
    && (session === 'all' || (session === 'unassigned' ? !s.session_id : String(s.session_id) === session))
    && (!search || normalize(`${s.title} ${s.location_name} ${s.objective || ''}`).includes(search)))
    .sort((a, b) => (a.order_index || 0) - (b.order_index || 0) || a.id - b.id);
}

export function selectionForAssets(assets:SceneAsset[],selectedIds:string[]){
  const chosen=assets.filter(a=>selectedIds.includes(a.id));
  return {element_ids:chosen.filter(a=>/:element:\d+$/.test(a.id)).map(a=>Number(a.id.split(':').pop())),
    token_ids:chosen.filter(a=>a.kind==='pin'&&a.token).map(a=>a.token!.id),include_map:chosen.some(a=>a.kind==='map')};
}

export function scenePinPoint(token: WorkspaceToken, grid?: MapGrid) {
  const pos = token.grid_position;
  if (grid && pos && pos.map_id === grid.map_id) {
    return cellCenter(grid, [pos.cell_x, pos.cell_y], pos.footprint_w, pos.footprint_h);
  }
  return { longitude: Math.max(0, Math.min(100, token.longitude)), latitude: Math.max(0, Math.min(100, token.latitude)) };
}

/** Same legacy/density semantics as native fog; conservative, not a permission grant. */
export function pinInPublicView(token: WorkspaceToken, workspace: WorkspaceSnapshot) {
  if (!workspace.map?.visible_to_players || !token.visible_to_players) return false;
  // Visibility follows the native persisted fog coordinates, including legacy pins.
  const point = { longitude: token.longitude, latitude: token.latitude };
  return Object.values(workspace.fog || {}).every(layer => {
    if (!layer.enabled) return true;
    const cell = `${Math.min(layer.columns - 1, Math.floor(point.longitude / 100 * layer.columns))}:${Math.min(layer.rows - 1, Math.floor(point.latitude / 100 * layer.rows))}`;
    if (Object.keys(layer.mist_density || {}).length) return !(Number(layer.mist_density[cell] || 0) > 0);
    return !layer.revealed_cells.length || layer.revealed_cells.includes(cell);
  });
}

function participantToken(p: SceneParticipant, tokens: WorkspaceToken[]) {
  return tokens.find(t => (p.character_id && t.character_id === p.character_id)
    || t.id === p.npc_source?.replace(/^map-token:/, ''));
}

/** Read-only projection. Never stores campaign data or treats a draft as published. */
export function sceneAssets(scene: GameScene, workspace: WorkspaceSnapshot | null, publicOnly: boolean): SceneAsset[] {
  if (publicOnly && (scene.status === 'draft' || scene.visibility !== 'table')) return [];
  const assets: SceneAsset[] = [];
  const add = (asset: SceneAsset) => assets.push({ ...asset, id: `${scene.id}:${asset.id}` });
  const matched = workspace?.map?.id === scene.map_id ? workspace : null;
  const tokens = (matched?.tokens || []).filter(t => t.map_id === scene.map_id);
  if (scene.image_path) add({ id: 'image', kind: 'image', title: 'Imagem da cena', image: scene.image_path });
  if (matched?.map && (!publicOnly || matched.map.visible_to_players)) add({ id: 'map', kind: 'map', title: matched.map.title, image: matched.map.image_path });
  if (scene.public_description) add({ id: 'opening', kind: 'text', title: 'Abertura', text: scene.public_description });
  if (!publicOnly && scene.objective) add({ id: 'objective', kind: 'objective', title: 'Objetivo', text: scene.objective });
  if (!publicOnly && scene.private_notes) add({ id: 'notes', kind: 'text', title: 'Notas do Mestre', text: scene.private_notes, hidden: true });
  scene.participants.filter(p => !p.left_at && (!publicOnly || p.visible_to_players)).forEach(p => {
    const token = participantToken(p, tokens);
    const publicToken = token && matched && pinInPublicView(token, matched);
    const npc = !publicOnly || p.npc?.visible_to_players ? p.npc : null;
    add({ id: `participant:${p.id}`, kind: p.participant_type === 'creature' ? 'creature' : p.participant_type === 'player_character' ? 'character' : 'npc',
      title: p.public_label, image: p.character?.portrait || npc?.portrait_path || (!publicOnly || publicToken ? token?.image_path : null),
      text: [p.public_status, npc?.public_description].filter(Boolean).join('\n\n'),
      privateText: publicOnly ? null : [p.private_status, npc?.private_description].filter(Boolean).join('\n\n'), hidden: !p.visible_to_players });
  });
  scene.elements.filter(e => !publicOnly || (e.visibility === 'table' && e.status !== 'hidden')).forEach(e => {
    add({ id: `element:${e.id}`, kind: e.element_type, title: e.title, text: e.public_description,
      privateText: publicOnly ? null : e.private_description, hidden: e.status === 'hidden' || e.visibility !== 'table' });
  });
  tokens.filter(t => !publicOnly || (matched && pinInPublicView(t, matched))).forEach(t => {
    const pos = t.grid_position;
    const projectedToken: WorkspaceToken = publicOnly ? {
      id: t.id, name: t.name, map_id: t.map_id, token_type: t.token_type, character_id: t.character_id,
      image_path: t.image_path, color: t.color, visible_to_players: t.visible_to_players,
      latitude: t.latitude, longitude: t.longitude, grid_position: t.grid_position,
      current_hp: t.current_hp, maximum_hp: t.maximum_hp, conditions: t.conditions,
      created_at: t.created_at, updated_at: t.updated_at,
    } : t;
    add({ id: `pin:${t.id}`, kind: 'pin', title: t.name, image: t.image_path, token: projectedToken,
      text: pos ? `Célula ${pos.cell_x}, ${pos.cell_y}` : 'Posição visual · mapa sem grid',
      hidden: matched ? !pinInPublicView(t, matched) : !t.visible_to_players });
  });
  return assets;
}

export function fogPreviewCells(workspace: WorkspaceSnapshot) {
  const result = new Map<string, { x: number; y: number; w: number; h: number; density: number }>();
  Object.values(workspace.fog || {}).filter(layer => layer.enabled).forEach(layer => {
    for (let y = 0; y < layer.rows; y++) for (let x = 0; x < layer.columns; x++) {
      const cell = `${x}:${y}`;
      const density = Object.keys(layer.mist_density || {}).length ? Number(layer.mist_density[cell] || 0)
        : layer.revealed_cells.length && !layer.revealed_cells.includes(cell) ? 1 : 0;
      if (density > 0) {
        const key = `${layer.columns}:${layer.rows}:${cell}`;
        result.set(key, { x: x * 100 / layer.columns, y: y * 100 / layer.rows,
          w: 100 / layer.columns, h: 100 / layer.rows, density: Math.max(result.get(key)?.density || 0, Math.min(1, density)) });
      }
    }
  });
  return [...result.values()];
}
