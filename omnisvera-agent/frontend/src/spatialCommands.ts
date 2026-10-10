import { getAccessToken } from './api';
import type { MapGrid, SpatialCommand, SpatialResult } from './spatialGrid';
const BASE = import.meta.env.VITE_API_BASE_URL || '';
export class SpatialCommandError extends Error {
  constructor(public status: number, message: string) {super(message);}
}

async function command<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      (async () => {
        const response = await fetch(`${BASE}${path}`, {method:'POST',headers:{'Content-Type':'application/json','X-Omnisvera-Token':getAccessToken()},body:JSON.stringify(body),signal:controller.signal});
        const data = await response.json();
        if(!response.ok) throw new SpatialCommandError(response.status,data.detail || 'Movimento rejeitado');
        return data as T;
      })(),
      new Promise<never>((_,reject) => {timer=setTimeout(() => {controller.abort();reject(new Error('Confirmação não recebida. Reenvie o mesmo comando para consultar o resultado.'));},10000);}),
    ]);
  } finally { clearTimeout(timer); }
}
export function moveGridEntity(mapId: string, value: SpatialCommand) {return command<SpatialResult>(`/workspace/maps/${encodeURIComponent(mapId)}/move`,value);}
export function configureMapGrid(mapId: string, grid: Omit<MapGrid,'map_id'|'grid_type'|'provisional'|'version'>, version: number) {
  return command<{grid:MapGrid}>(`/workspace/maps/${encodeURIComponent(mapId)}/grid`,{...grid,request_id:crypto.randomUUID(),expected_version:version});
}
