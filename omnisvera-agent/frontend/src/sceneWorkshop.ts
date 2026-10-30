import { getAccessToken, listScenes, workshopRequest } from './api';

export type WorkshopJob = { id: number; queue: string; entity_type: string; entity_id: string; purpose: string; status: string; attempts?: number; revision?: string };
export type WorkshopReview = {
  job_id: number; decision: 'import' | 'reject'; status: string; scene_id?: number | null;
  element_id?: number | null; element_ids?: number[]; output_hash: string; revision: string; request_id: string;
  reviewed_at?: string;
};
export type WorkshopPreview = WorkshopJob & {
  output_hash?: string;
  review?: WorkshopReview | null;
  preview: { quality_notes?: string[]; asset_job_id?: number; image_path?: string; draft?: string; facts?: string[]; suggestions?: string[]; questions?: string[]; provider?: string; model?: string };
};
export type WorkshopOverview = {
  initialized: boolean; worker: { state: string }; counts: Record<string, Record<string, number>>;
  stats: { samples: number; average_ms: number | null; p50_ms: number | null; p95_ms: number | null };
  table_state: string; admission: { free_ram_mb: number | null; min_free_ram_mb: number; ram_ok: boolean };
  jobs: WorkshopJob[];
  automation?: { enabled: boolean; text: boolean; image: boolean; code: boolean; code_provider?: 'opencode' | 'ollama-cloud'; daily_limits: Record<string, number> };
};
export type WorkshopSceneOption = { id: number; title: string; status: string; location_name?: string };
export type WorkshopReviewInput = {
  decision: 'import' | 'reject'; scene_id: number | null; expected_revision: string;
  expected_output_hash: string; request_id: string;
};

export const getWorkshop = () => workshopRequest<WorkshopOverview>('/gm/ai-workshop');
export async function getWorkshopAssetPreview(id: number, signal: AbortSignal) {
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error('Imagem inválida.');
  const response = await fetch(`/gm/assets/${id}/preview`, {
    signal, headers: { 'X-Omnisvera-Token': getAccessToken() || '' }, cache: 'no-store',
  });
  if (!response.ok) throw new Error('Prévia indisponível.');
  return response.blob();
}
export function getWorkshopJob(id: number) {
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error('Bloco inválido.');
  return workshopRequest<WorkshopPreview>(`/gm/ai-workshop/jobs/${id}`);
}

export async function listWorkshopScenes(): Promise<WorkshopSceneOption[]> {
  const scenes = await listScenes();
  return scenes
    .filter(scene => !(scene as { archived?: boolean }).archived)
    .map(scene => ({ id: scene.id, title: scene.title, status: scene.status, location_name: scene.location_name }));
}

export function reviewWorkshopJob(id: number, input: WorkshopReviewInput): Promise<WorkshopReview> {
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error('Bloco inválido.');
  if (input.decision !== 'import' && input.decision !== 'reject') throw new Error('Decisão inválida.');
  if (input.decision === 'import' && (!Number.isSafeInteger(input.scene_id) || Number(input.scene_id) <= 0))
    throw new Error('Escolha uma cena existente.');
  if (!input.expected_revision.trim()) throw new Error('Revisão do bloco ausente.');
  if (!/^[0-9a-f]{64}$/i.test(input.expected_output_hash)) throw new Error('Hash do bloco inválido.');
  if (!/^[A-Za-z0-9._:-]{8,120}$/.test(input.request_id)) throw new Error('Identificador de revisão inválido.');
  const body: WorkshopReviewInput = {
    decision: input.decision,
    scene_id: input.decision === 'import' ? input.scene_id : null,
    expected_revision: input.expected_revision,
    expected_output_hash: input.expected_output_hash.toLowerCase(),
    request_id: input.request_id,
  };
  return workshopRequest<WorkshopReview>(`/gm/ai-workshop/jobs/${id}/review`, 'POST', body);
}
