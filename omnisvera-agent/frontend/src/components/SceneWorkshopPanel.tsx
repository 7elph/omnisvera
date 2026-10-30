import { useEffect, useRef, useState } from 'react';
import { getWorkshopAssetPreview, getWorkshop, getWorkshopJob, listWorkshopScenes, reviewWorkshopJob, WorkshopOverview, WorkshopPreview, WorkshopSceneOption } from '../sceneWorkshop';

function WorkshopImage({ id }: { id: number }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController(); let active = true; let objectUrl = '';
    const timer = setTimeout(() => controller.abort(), 20000);
    setUrl(''); setError('');
    void getWorkshopAssetPreview(id, controller.signal).then(blob => {
      if (!active) return;
      objectUrl = URL.createObjectURL(blob); setUrl(objectUrl);
    }).catch(() => { if (active) setError('Prévia indisponível.'); }).finally(() => clearTimeout(timer));
    return () => { active = false; controller.abort(); clearTimeout(timer); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [id]);
  return url ? <img src={url} alt="Rascunho privado para revisão" style={{ maxWidth: '100%', maxHeight: 360, objectFit: 'contain' }} /> : <p>{error || 'Carregando imagem…'}</p>;
}

const statusLabel = (status: string) => ({ queued: 'Na fila', running: 'Gerando', awaiting_approval: 'Rascunho para revisão', completed: 'Concluído', failed: 'Falhou', blocked: 'Bloqueado', waiting_permission: 'Aguardando permissão', needs_review: 'Precisa de revisão', external_pending: 'Na fila de imagens', cancelled: 'Cancelado' }[status] || 'Aguardando');
const queueLabel = (queue: string) => ({ text: 'Texto e lore', image: 'Imagens', code: 'Código e testes' }[queue] || 'Preparação');
const seconds = (ms: number | null) => ms === null ? '—' : `${(ms / 1000).toFixed(1)} s`;

function newReviewRequestId() {
  const cryptoApi = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  const raw = cryptoApi?.randomUUID ? cryptoApi.randomUUID() : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `workshop-review-${raw.replace(/[^A-Za-z0-9._:-]/g, '')}`;
}

/** Private preparation read model, not a second scene system or a generation button. */
export default function SceneWorkshopPanel() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<WorkshopOverview | null>(null);
  const [selected, setSelected] = useState<WorkshopPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'import' | 'reject' | null>(null);
  const [sceneId, setSceneId] = useState<number | null>(null);
  const [scenes, setScenes] = useState<WorkshopSceneOption[] | null>(null);
  const [retry, setRetry] = useState(false);
  const pending = useRef<{ key: string; requestId: string } | null>(null);
  const life = useRef({ mounted: true, overview: 0, detail: 0, review: 0, scenes: 0, reviewing: false });
  useEffect(() => {
    life.current.mounted = true;
    return () => {
      life.current.mounted = false;
      life.current.overview++; life.current.detail++; life.current.review++; life.current.scenes++;
      life.current.reviewing = false;
    };
  }, []);

  async function refresh() {
    const sequence = ++life.current.overview;
    setBusy(true); setError('');
    try {
      const next = await getWorkshop();
      if (life.current.mounted && sequence === life.current.overview) setData(next);
    } catch (cause) {
      if (life.current.mounted && sequence === life.current.overview) setError(cause instanceof Error ? cause.message : 'Oficina indisponível.');
    } finally {
      if (life.current.mounted && sequence === life.current.overview) setBusy(false);
    }
  }

  async function select(id: number) {
    const sequence = ++life.current.detail;
    setSelected(null); setMode(null); setSceneId(null); setRetry(false); pending.current = null; setError('');
    try {
      const next = await getWorkshopJob(id);
      if (life.current.mounted && sequence === life.current.detail) setSelected(next);
    } catch (cause) {
      if (life.current.mounted && sequence === life.current.detail) setError(cause instanceof Error ? cause.message : 'Bloco indisponível.');
    }
  }

  async function loadScenes() {
    const sequence = ++life.current.scenes;
    setBusy(true); setError('');
    try {
      const next = await listWorkshopScenes();
      if (life.current.mounted && sequence === life.current.scenes) setScenes(next);
    } catch (cause) {
      if (life.current.mounted && sequence === life.current.scenes) setError(cause instanceof Error ? cause.message : 'Cenas indisponíveis.');
    } finally {
      if (life.current.mounted && sequence === life.current.scenes) setBusy(false);
    }
  }

  function openImport() {
    setMode('import'); setRetry(false); pending.current = null; setSceneId(null); setError('');
    if (scenes === null) void loadScenes();
  }

  function cancelReview() {
    setMode(null); setRetry(false); pending.current = null; setError('');
  }

  async function submitReview(decision: 'import' | 'reject') {
    const block = selected;
    if (!block || !block.output_hash || !block.revision || life.current.reviewing) return;
    const targetScene = decision === 'import' ? sceneId : null;
    if (decision === 'import' && !targetScene) { setError('Escolha uma cena existente.'); return; }
    const key = [block.id, block.output_hash, block.revision, decision, targetScene ?? ''].join('|');
    if (!pending.current || pending.current.key !== key) pending.current = { key, requestId: newReviewRequestId() };
    const requestId = pending.current.requestId;
    const sequence = ++life.current.review;
    life.current.reviewing = true;
    setBusy(true); setError(''); setRetry(false);
    try {
      const result = await reviewWorkshopJob(block.id, {
        decision, scene_id: targetScene, expected_revision: block.revision,
        expected_output_hash: block.output_hash, request_id: requestId,
      });
      if (!life.current.mounted || sequence !== life.current.review) return;
      pending.current = null;
      life.current.reviewing = false;
      setSelected(current => current && current.id === block.id ? { ...current, status: result.status || current.status, review: result } : current);
      setMode(null);
      await refresh();
      await select(block.id);
    } catch (cause) {
      if (!life.current.mounted || sequence !== life.current.review) return;
      setRetry(true);
      setError(cause instanceof Error ? cause.message : 'Não foi possível revisar o bloco.');
    } finally {
      if (sequence === life.current.review) life.current.reviewing = false;
      if (life.current.mounted && sequence === life.current.review) setBusy(false);
    }
  }

  return <details className="scene-section scene-workshop" open={open} onToggle={event => {
    const expanded = event.currentTarget.open;
    setOpen(expanded);
    if (expanded && !open) void refresh();
    if (!expanded) {
      life.current.overview++; life.current.detail++; life.current.review++; life.current.scenes++;
      life.current.reviewing = false; pending.current = null; setBusy(false); setMode(null); setRetry(false);
    }
  }}>
    <summary>Oficina de preparação · privado</summary>
    <div className="scene-create-form">
      <p className="muted">Blocos para preparar a mesa. Rascunhos não alteram fichas, mapas ou regras e não são publicados para jogadores.</p>
      <button type="button" disabled={busy} onClick={() => void refresh()}>Atualizar oficina</button>
      {error && <p role="alert" className="warning-text">{error}</p>}
      {busy && <p role="status">Carregando oficina…</p>}
      {data && <>
        <p role="status">{data.worker.state === 'running' ? 'Produção ativa' : data.worker.state === 'paused' ? 'Produção pausada' : 'Produção parada'} · {data.table_state === 'inactive' ? 'Mesa inativa' : data.table_state === 'unknown' ? 'Estado da mesa não confirmado' : 'Mesa em andamento'}</p>
        {!data.admission.ram_ok && <p className="warning-text">Novas gerações aguardam memória: {data.admission.free_ram_mb ?? '—'} MB livres; mínimo {data.admission.min_free_ram_mb} MB.</p>}
        <div className="scene-workshop-queues">{['text', 'image', 'code'].map(queue => {
          const counts = data.counts[queue] || {};
          return <article className="scene-element" key={queue}><div><strong>{queueLabel(queue)}</strong><p>{counts.queued || 0} na fila · {(counts.awaiting_approval || 0) + (counts.needs_review || 0)} para revisão</p><small>{queue === 'image' ? (data.automation?.enabled && data.automation.image ? 'Geração configurada; requer revisão' : 'Geração automática desativada') : queue === 'code' ? (data.automation?.enabled && data.automation.code ? (data.automation.code_provider === 'ollama-cloud' ? 'Ollama Cloud · propostas de código' : 'OpenCode · propostas de código') : 'Análise automática desativada') : 'Fontes: transcrições da campanha'}</small></div></article>;
        })}</div>
        <p className="muted">{data.stats.samples ? `${data.stats.samples} medições · média ${seconds(data.stats.average_ms)} · p50 ${seconds(data.stats.p50_ms)} · p95 ${seconds(data.stats.p95_ms)}` : 'Ainda sem medições reais de geração.'}</p>
        {!data.jobs.length && <p>Nenhum bloco na oficina.</p>}
        <div className="scene-workshop-blocks">{data.jobs.map(job => <button type="button" className="scene-element" key={job.id} aria-label={`Ver bloco ${job.id}`} disabled={busy} onClick={() => select(job.id)}><div><strong>{job.entity_type === 'session' ? `Sessão ${job.entity_id.split(':')[0]}` : 'Bloco de preparação'}</strong><small>{queueLabel(job.queue)} · {statusLabel(job.status)}</small></div></button>)}</div>
      </>}
      {selected && <article className="scene-section" aria-label="Prévia do bloco">
        <header><h3>Bloco {selected.id} · {statusLabel(selected.status)}</h3></header>
        {selected.queue === 'code' && <p className="muted">Análise/sugestão textual de código. O conteúdo é privado e não é executado.</p>}
        {selected.preview.quality_notes?.length ? <p className="warning-text">Revisão necessária: {selected.preview.quality_notes.map(note => note === 'repeated_content' ? 'trechos repetidos no rascunho' : note === 'oversized_block' ? 'bloco muito longo' : note === 'uncertain_names_used_as_lore' ? 'nomes incertos usados como fatos' : note === 'image_anatomy_unverified' ? 'anatomia da imagem não corresponde ao monstro' : 'conferir fontes').join(' · ')}.</p> : null}
        {selected.preview.asset_job_id && <><WorkshopImage key={selected.preview.asset_job_id} id={selected.preview.asset_job_id} /><p>Imagem privada #{selected.preview.asset_job_id}: revisar na biblioteca de imagens antes de publicar.</p></>}
        {selected.preview.draft ? <p className="scene-workshop-draft">{selected.preview.draft}</p> : <p>Este bloco ainda não tem conteúdo gerado.</p>}
        {([['facts', 'Fatos usados'], ['suggestions', 'Sugestões'], ['questions', 'Dúvidas']] as const).map(([key, label]) => {
          const items = selected.preview[key] || [];
          return items.length ? <details key={key}><summary>{label}</summary><ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul></details> : null;
        })}
        {selected.review && <p role="status">Revisão registrada: {selected.review.decision === 'import' ? `guardado como elemento privado #${selected.review.element_id} na cena ${selected.review.scene_id}; a cena não foi publicada nem ativada.` : 'rascunho rejeitado; a campanha não foi alterada.'}</p>}
        {['text', 'code'].includes(selected.queue) && ['awaiting_approval', 'needs_review'].includes(selected.status) && selected.preview.draft && !selected.review && <>
          {(!selected.output_hash || !selected.revision)
            ? <p className="warning-text">Detalhe sem hash ou revisão do resultado; recarregue o bloco antes de revisar.</p>
            : <>
              {!mode && <div className="scene-workshop-review">
                <button type="button" disabled={busy || selected.status !== 'awaiting_approval' || selected.queue === 'image'} onClick={openImport}>Revisar e guardar em cena</button>
                <button type="button" disabled={busy} onClick={() => { setMode('reject'); setRetry(false); pending.current = null; setError(''); }}>Rejeitar rascunho</button>
              </div>}
              {mode === 'import' && <div className="scene-workshop-review">
                <p>Escolha uma cena existente. O bloco será guardado como elemento privado oculto; a cena não será publicada nem ativada.</p>
                {scenes === null
                  ? <p role="status">Carregando cenas…</p>
                  : scenes.length
                    ? <select aria-label="Cena de destino" value={sceneId ?? ''} disabled={busy} onChange={event => {
                        const value = Number(event.target.value);
                        setSceneId(Number.isSafeInteger(value) && value > 0 ? value : null);
                        setRetry(false); pending.current = null;
                      }}><option value="">Selecione uma cena…</option>{scenes.map(scene => <option key={scene.id} value={scene.id}>{scene.title} · {scene.status}</option>)}</select>
                    : <p className="warning-text">Nenhuma cena existente disponível.</p>}
                <button type="button" disabled={busy || !sceneId} onClick={() => submitReview('import')}>{retry ? 'Tentar importação novamente' : 'Confirmar importação'}</button>
                {scenes === null && !busy && <button type="button" onClick={() => loadScenes()}>Recarregar cenas</button>}
                <button type="button" disabled={busy} onClick={cancelReview}>Cancelar</button>
              </div>}
              {mode === 'reject' && <div className="scene-workshop-review">
                <p>Rejeitar este rascunho? A oficina marca o bloco como cancelado e a campanha não é alterada.</p>
                <button type="button" disabled={busy} onClick={() => submitReview('reject')}>{retry ? 'Tentar rejeição novamente' : 'Confirmar rejeição'}</button>
                <button type="button" disabled={busy} onClick={cancelReview}>Cancelar</button>
              </div>}
            </>}
        </>}
      </article>}
    </div>
  </details>;
}
