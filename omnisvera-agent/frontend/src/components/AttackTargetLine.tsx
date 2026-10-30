import { WorkspaceToken } from '../api';

export default function AttackTargetLine({ tokens, actorId, targetId, targetIds }: { tokens: WorkspaceToken[]; actorId?: string; targetId?: string; targetIds?:string[] }) {
  const pin = (id?: string) => id ? tokens.find(t => t.id === id) || tokens.find(t => (t.token_type || 'character') === 'character' && t.character_id === id) : undefined;
  const source = pin(actorId);
  const targets=(targetIds || (targetId?[targetId]:[])).map(id=>pin(id)).filter((t):t is WorkspaceToken=>Boolean(t && t.id!==source?.id));
  if (!source || !targets.length) return null;
  return <svg className="workspace-target-line" width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={`Alvo: ${source.name} → ${targets.map(t=>t.name).join(', ')}`}>
    {targets.map(target=><line key={target.id} x1={source.longitude} y1={source.latitude} x2={target.longitude} y2={target.latitude} />)}
  </svg>;
}
