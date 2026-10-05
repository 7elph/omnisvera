import { WorkspaceToken } from '../api';

export default function AttackTargetLine({ tokens, actorId, targetId }: { tokens: WorkspaceToken[]; actorId?: string; targetId?: string }) {
  const pin = (id?: string) => id ? tokens.find(t => t.id === id) || tokens.find(t => (t.token_type || 'character') === 'character' && t.character_id === id) : undefined;
  const source = pin(actorId);
  const target = pin(targetId);
  if (!source || !target || source.id === target.id) return null;
  return <svg className="workspace-target-line" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={`Alvo: ${source.name} → ${target.name}`}>
    <line x1={source.longitude} y1={source.latitude} x2={target.longitude} y2={target.latitude} />
    <ellipse cx={target.longitude} cy={target.latitude} rx="2.5" ry="3.5" />
  </svg>;
}
