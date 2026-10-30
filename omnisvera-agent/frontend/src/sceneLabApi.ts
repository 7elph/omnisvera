import { newSceneRequestId, sceneLabRequest } from './api';

export type LabKind = 'action' | 'scene_bundle';
export type LabStatus = 'draft' | 'approved' | 'rejected';
export type LabSummary = { id: number; scene_id: number; title: string; kind: LabKind; version: number; status: LabStatus; updated_at?: string };
export type LabProposal = LabSummary & { content: Record<string, unknown>; history: Array<Record<string, unknown>>; revisions: Array<{ version: number; title: string; content: Record<string, unknown>; created_at: string }>; evidence: Record<string, unknown> | null; decision_reason?: string };
type Revision = { request_id: string; expected_version: number };
function id(value: number) {
  if (!Number.isSafeInteger(value) || value <= 0) throw new Error('Identificador inválido.');
  return value;
}
export const newLabRequestId = () => newSceneRequestId('scene-lab');
export const listLabProposals = (sceneId: number) => sceneLabRequest<LabSummary[]>(`/gm/scenes/${id(sceneId)}/lab/proposals`);
export const getLabProposal = (proposalId: number) => sceneLabRequest<LabProposal>(`/gm/scene-lab/proposals/${id(proposalId)}`);
export const createLabProposal = (sceneId: number, body: { request_id: string; title: string; kind: LabKind; content: Record<string, unknown> }) => sceneLabRequest<LabProposal>(`/gm/scenes/${id(sceneId)}/lab/proposals`, 'POST', body);
export const updateLabProposal = (proposalId: number, body: Revision & { title: string; content: Record<string, unknown> }) => sceneLabRequest<LabProposal>(`/gm/scene-lab/proposals/${id(proposalId)}`, 'PUT', body);
export const attachLabEvidence = (proposalId: number, body: Revision & { run_id: string }) => sceneLabRequest<LabProposal>(`/gm/scene-lab/proposals/${id(proposalId)}/evidence`, 'POST', body);
export const decideLabProposal = (proposalId: number, body: Revision & { decision: 'approved' | 'rejected'; reason: string }) => sceneLabRequest<LabProposal>(`/gm/scene-lab/proposals/${id(proposalId)}/decision`, 'POST', body);
