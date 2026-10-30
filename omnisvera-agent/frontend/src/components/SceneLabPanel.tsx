import { useEffect, useRef, useState } from 'react';
import { attachLabEvidence, createLabProposal, decideLabProposal, getLabProposal, LabKind, LabProposal, LabSummary, listLabProposals, newLabRequestId, updateLabProposal } from '../sceneLabApi';

const label = (status: string) => ({ draft: 'Rascunho', approved: 'Revisada', rejected: 'Rejeitada' }[status] || status);
const readable = (value: unknown) => JSON.stringify(value, null, 2);
const wrap = { whiteSpace: 'pre-wrap' as const, overflowWrap: 'anywhere' as const, maxWidth: '100%' };

/** GM-only caller; API independently enforces authorization. Never publishes or executes content. */
export default function SceneLabPanel({ sceneId }: { sceneId: number }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<LabSummary[]>([]);
  const [proposal, setProposal] = useState<LabProposal | null>(null);
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState<LabKind>('action');
  const [content, setContent] = useState('{}');
  const [runId, setRunId] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const scope = useRef({ sceneId, epoch: 0, mounted: true });
  const readSequence = useRef(0);
  const lock = useRef(false);
  const pending = useRef<{ key: string; requestId: string } | null>(null);
  if (scope.current.sceneId !== sceneId) scope.current = { sceneId, epoch: scope.current.epoch + 1, mounted: true };
  const current = (epoch: number) => scope.current.mounted && scope.current.epoch === epoch;

  useEffect(() => {
    scope.current.mounted = true;
    return () => { scope.current.mounted = false; scope.current.epoch += 1; };
  }, []);
  useEffect(() => {
    setRows([]); setProposal(null); setTitle(''); setContent('{}'); setRunId(''); setReason(''); setError(''); setBusy(false);
    pending.current = null; lock.current = false; readSequence.current += 1;
  }, [sceneId]);

  async function list() {
    const epoch = scope.current.epoch, sequence = ++readSequence.current;
    setError('');
    try {
      const result = await listLabProposals(sceneId);
      if (current(epoch) && sequence === readSequence.current) setRows(result);
    } catch (cause) {
      if (current(epoch) && sequence === readSequence.current) setError(cause instanceof Error ? cause.message : 'Não foi possível carregar as propostas.');
    }
  }
  async function openProposal(id: number) {
    if (lock.current) return;
    const epoch = scope.current.epoch, sequence = ++readSequence.current;
    lock.current = true; setBusy(true); setError('');
    try {
      const result = await getLabProposal(id);
      if (!current(epoch) || sequence !== readSequence.current) return;
      setProposal(result); setTitle(result.title); setKind(result.kind); setContent(readable(result.content)); setReason(result.decision_reason || ''); setRunId(''); pending.current = null;
    } catch (cause) {
      if (current(epoch)) setError(cause instanceof Error ? cause.message : 'Não foi possível abrir a proposta.');
    } finally { if (current(epoch)) { lock.current = false; setBusy(false); } }
  }
  async function mutate(operation: string, payload: Record<string, unknown>, perform: (requestId: string) => Promise<LabProposal>) {
    if (lock.current) return;
    const epoch = scope.current.epoch;
    const key = readable({ sceneId, proposalId: proposal?.id, operation, payload });
    if (pending.current?.key !== key) pending.current = { key, requestId: newLabRequestId() };
    const requestId = pending.current.requestId;
    lock.current = true; setBusy(true); setError('');
    try {
      const result = await perform(requestId);
      if (!current(epoch)) return;
      pending.current = null;
      setProposal(result); setTitle(result.title); setKind(result.kind); setContent(readable(result.content)); setReason(result.decision_reason || '');
      setRows((previous) => [result, ...previous.filter(row => row.id !== result.id)]);
      // The receipt confirms the mutation, but deliberately omits immutable revisions.
      // A failed enrichment is only a read failure: never retry or re-label the write.
      const sequence = ++readSequence.current;
      try {
        const detail = await getLabProposal(result.id);
        if (!current(epoch) || sequence !== readSequence.current) return;
        if (detail.id !== result.id || detail.scene_id !== sceneId || detail.version < result.version) throw new Error('Histórico ainda não atualizado.');
        setProposal(detail); setTitle(detail.title); setKind(detail.kind); setContent(readable(detail.content)); setReason(detail.decision_reason || '');
        setRows((previous) => [detail, ...previous.filter(row => row.id !== detail.id)]);
      } catch {
        if (current(epoch) && sequence === readSequence.current) setError('Proposta confirmada. Não foi possível atualizar o histórico; reabra a proposta para consultá-lo.');
      }
    } catch (cause) {
      if (current(epoch)) setError(cause instanceof Error ? cause.message : 'Falha na operação. Tente novamente para consultar a mesma confirmação.');
    } finally { if (current(epoch)) { lock.current = false; setBusy(false); } }
  }
  async function save() {
    let parsed: Record<string, unknown>;
    try {
      if (content.length > 50000) throw new Error('O conteúdo excede 50.000 caracteres.');
      const value: unknown = JSON.parse(content);
      if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('O conteúdo precisa ser um objeto JSON.');
      parsed = value as Record<string, unknown>;
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'JSON inválido.'); return; }
    const fields = { title: title.trim(), content: parsed };
    if (proposal) {
      const revision = proposal.version, proposalId = proposal.id;
      await mutate('update', { ...fields, expected_version: revision }, request_id => updateLabProposal(proposalId, { ...fields, expected_version: revision, request_id }));
    } else await mutate('create', { ...fields, kind }, request_id => createLabProposal(sceneId, { ...fields, kind, request_id }));
  }
  async function evidence() {
    if (!proposal) return;
    const proposalId = proposal.id, payload = { expected_version: proposal.version, run_id: runId.trim() };
    await mutate('evidence', payload, request_id => attachLabEvidence(proposalId, { ...payload, request_id }));
  }
  async function decide(decision: 'approved' | 'rejected') {
    if (!proposal) return;
    const proposalId = proposal.id, payload = { expected_version: proposal.version, decision, reason: reason.trim() };
    await mutate('decision', payload, request_id => decideLabProposal(proposalId, { ...payload, request_id }));
  }
  return <details className="scene-admin-details scene-section" open={open} onToggle={event => {
    const expanded = event.currentTarget.open;
    setOpen(expanded);
    if (expanded && !open) void list();
  }}>
    <summary>Laboratório de propostas · privado</summary>
    <div className="scene-create-form" style={{ minWidth: 0 }}>
      <p className="muted">Propostas privadas e evidências dos ensaios do código existente. Aprovar não publica nem altera fichas, mapas ou regras da mesa. Este painel não executa o JSON da proposta.</p>
      {error && <p role="alert" className="warning-text">{error}</p>}
      <div className="scene-inline-form"><button type="button" disabled={busy} onClick={() => void list()}>Atualizar propostas</button><button type="button" disabled={busy} onClick={() => { readSequence.current += 1; setProposal(null); setTitle(''); setKind('action'); setContent('{}'); setRunId(''); setReason(''); setError(''); pending.current = null; }}>Nova proposta</button></div>
      {rows.map(row => <button type="button" key={row.id} disabled={busy} onClick={() => void openProposal(row.id)}>{row.title} · v{row.version} · {label(row.status)}</button>)}
      {proposal && <p role="status">Revisão {proposal.version} · {label(proposal.status)}</p>}
      <details className="scene-admin-details" open={!proposal}>
        <summary>{proposal ? 'Editar proposta técnica' : 'Criar proposta técnica'}</summary>
        <div className="scene-create-form">
          <input aria-label="Título da proposta" maxLength={180} value={title} disabled={busy} onChange={event => setTitle(event.target.value)} />
          <select aria-label="Tipo de proposta" value={kind} disabled={busy || !!proposal} onChange={event => setKind(event.target.value as LabKind)}><option value="action">Ação</option><option value="scene_bundle">Material da cena</option></select>
          <textarea aria-label="Conteúdo JSON da proposta" value={content} rows={6} maxLength={50000} disabled={busy} style={wrap} onChange={event => setContent(event.target.value)} />
          <button type="button" disabled={busy || !title.trim()} onClick={save}>{proposal ? 'Salvar nova revisão' : 'Criar proposta privada'}</button>
        </div>
      </details>
      {proposal && <>
        <details className="scene-admin-details"><summary>Conteúdo e histórico · v{proposal.version}</summary><pre style={wrap}>{readable(proposal.content)}</pre>{proposal.revisions?.map(revision => <details className="scene-admin-details" key={revision.version}><summary>Revisão {revision.version} · {revision.title}</summary><pre style={wrap}>{readable(revision.content)}</pre></details>)}<details className="scene-admin-details"><summary>Eventos de revisão</summary><pre style={wrap}>{readable(proposal.history || [])}</pre></details></details>
        <details className="scene-admin-details"><summary>Evidência de ensaio · {proposal.evidence ? 1 : 0}</summary><p className="muted">O servidor verifica o relatório local de um ensaio do código existente, não a execução da proposta. Fonte verificada e PASS parcial não certificam a ficha.</p>{proposal.evidence && <pre style={wrap}>{readable(proposal.evidence)}</pre>}<div className="scene-inline-form"><input aria-label="Identificador do ensaio" placeholder="test-…" value={runId} disabled={busy} onChange={event => setRunId(event.target.value)} /><button type="button" disabled={busy || !/^test-[0-9a-f]{32}$/.test(runId.trim())} onClick={evidence}>Vincular ensaio verificado</button></div></details>
        <details className="scene-admin-details"><summary>Revisão do Mestre</summary><textarea aria-label="Motivo da revisão" value={reason} disabled={busy} onChange={event => setReason(event.target.value)} /><div className="scene-inline-form"><button type="button" disabled={busy || !reason.trim()} onClick={() => void decide('approved')}>Aprovar revisão</button><button type="button" disabled={busy || !reason.trim()} onClick={() => void decide('rejected')}>Rejeitar revisão</button></div></details>
      </>}
    </div>
  </details>;
}
