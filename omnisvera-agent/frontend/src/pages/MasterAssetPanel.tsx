import { useEffect, useRef, useState } from "react";
import { getAccessToken, listWorkspaceIcons, mediaUrlFromVaultPath, type WorkspaceIcon } from "../api";
import AssetAdjustmentForm from '../components/AssetAdjustmentForm';
import WorkersQuotaClock from '../components/WorkersQuotaClock';

type Job = {
  id: number;
  entity_type: string;
  entity_id: string;
  asset_type: string;
  style_version: string;
  status: string;
  prompt?: string | null;
  image_path?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
  context_json?: string | null;
};

type AssetContext = { references: { name: string; source: string; index: number }[]; entities: { name: string; species?: string }[]; warnings: string[]; blocking: string[] };

function generationLabel(job: Job) {
  try {
    const route = JSON.parse(job.context_json || '{}').generation;
    if (!route) return '';
    const requested = route.mode === 'test' ? 'Klein 4B · teste' : 'Klein 9B · oficial';
    if (route.used_provider === 'huggingface_zerogpu') return 'Fallback usado: Hugging Face ZeroGPU · Klein 9B';
    if (route.fallback_used) return `${requested} → ZeroGPU tentado, sem imagem`;
    return `${requested} · Cloudflare${route.used_provider ? '' : ' · sem imagem'}`;
  } catch { return ''; }
}

function AutomaticReferences({ job }: { job: Job }) {
  const [context, setContext] = useState<AssetContext | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/gm/assets/${job.id}/context`, { signal: controller.signal, headers: { 'X-Omnisvera-Token': getAccessToken() || '' } })
      .then(async response => { if (!response.ok) throw new Error('Não foi possível consultar as referências'); return response.json(); })
      .then(setContext).catch(error => { if (!controller.signal.aborted) setError(String(error.message)); });
    return () => controller.abort();
  }, [job.id, job.updated_at]);
  return <details><summary>Referências automáticas{context ? ` · ${context.references.length} imagens` : ''}</summary>
    {error && <p role="alert">{error}</p>}
    {context?.entities.map(entity => <p key={entity.name}>{entity.name} · {entity.species || 'Espécie não informada; preservar referência'}</p>)}
    {context?.references.map(reference => <p key={reference.index}>Imagem {reference.index + 1}: {reference.name}</p>)}
    {context?.blocking.map(message => <p role="alert" key={message}>{message}</p>)}
    {context?.warnings.map(message => <p key={message}>{message}</p>)}
    {job.context_json && <small>O contexto usado na última geração está preservado no job.</small>}
  </details>;
}

const STATUS_LABELS: Record<string, string> = {
  missing: "Faltando",
  queued: "Na fila",
  generating: "Gerando",
  ready: "Aguardando aprovação",
  awaiting_approval: "Aguardando aprovação",
  approved: "Aprovadas",
  failed: "Falhou",
  ignored: "Ignorado",
};

function assetTypeLabel(t: string) {
  if (t === "scene_cover") return "Scene Cover";
  if (t === "session_cover") return "Session Cover";
  if (t === "item_art") return "Item Art";
  if (t === "potion_hp") return "Poção HP";
  if (t === "potion_mp") return "Poção MP";
  return t;
}

export default function MasterAssetPanel({ onApproved }: { onApproved?: () => void } = {}) {
  const actionLock = useRef(false);
  const [busy, setBusy] = useState<number | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [imageProblems, setImageProblems] = useState<Record<number, string>>({});
  const [icons, setIcons] = useState<WorkspaceIcon[]>([]);
  const [selectedImage, setSelectedImage] = useState('');
  const [generationMode, setGenerationMode] = useState<'official' | 'test'>('official');

  async function fetchJobs() {
    try {
      const token = getAccessToken();
      const res = await fetch("/gm/assets/jobs", { headers: token ? { "X-Omnisvera-Token": token } : {} });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setJobs((Array.isArray(data) ? data : data.jobs || []).map((job: Job) => ({ ...job, status: job.status === "ready" ? "awaiting_approval" : job.status })));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchJobs();
    listWorkspaceIcons().then(setIcons).catch(() => setError('Não foi possível carregar as imagens da biblioteca.'));
    const t = setInterval(fetchJobs, 4000);
    return () => clearInterval(t);
  }, []);

  async function scan() {
    try {
      const token = getAccessToken();
      const response = await fetch("/gm/assets/scan", { method: "POST", headers: token ? { "X-Omnisvera-Token": token } : {} });
      if (!response.ok) throw new Error(`Não foi possível verificar os assets (HTTP ${response.status}).`);
      await fetchJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function action(jobId: number, act: "ignore" | "regenerate" | "approve") {
    if (actionLock.current) return;
    actionLock.current = true;
    setBusy(jobId);
    setError("");
    try {
      const token = getAccessToken();
      const response = await fetch(`/gm/assets/${jobId}/${act}`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { "X-Omnisvera-Token": token } : {}) }, ...(act === "approve" ? { body: JSON.stringify({ image_path: jobs.find(job => job.id === jobId)?.image_path }) } : act === 'regenerate' ? { body: JSON.stringify({ generation_mode: generationMode }) } : {}) });
      if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail || `Falha HTTP ${response.status}`); }
      if (act === "approve") { onApproved?.(); setIcons(await listWorkspaceIcons()); }
      await fetchJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      actionLock.current = false;
      setBusy(null);
    }
  }

  function previewUrl(job: Job) {
    return `/gm/assets/${job.id}/preview?token=${encodeURIComponent(getAccessToken() || "")}&v=${encodeURIComponent(job.updated_at)}`;
  }

  function adjustmentCreated() { setFilter('all'); void fetchJobs(); }

  const filtered = filter === "all" ? jobs : jobs.filter((j) => j.status === filter);
  const counts = jobs.reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <section className="campaign-section master-asset-panel">
      <WorkersQuotaClock />
      <label>Modelo<select value={generationMode} disabled={busy !== null} onChange={event => setGenerationMode(event.target.value as 'official' | 'test')}>
        <option value="official">Oficial · Klein 9B + fallback ZeroGPU</option>
        <option value="test">Teste · Klein 4B (sem fallback)</option>
      </select></label>
      <small>ZeroGPU tem fila e cota próprias; sua renovação não segue o relógio do Cloudflare. Referências são preservadas em ambas as rotas.</small>
      <header>
        <div>
          <small>ASSETS IA</small>
          <h3>Imagens Faltando / Geradas</h3>
        </div>
        <button type="button" onClick={() => void scan()}>
          Verificar imagens faltantes
        </button>
      </header>
      {error && <p className="error">{error}</p>}
      <details><summary>Ajustar imagem da biblioteca</summary>
        <label>Imagem<select value={selectedImage} onChange={event => setSelectedImage(event.target.value)}>
          <option value="">Escolha uma imagem</option>{icons.map(icon => <option key={icon.id} value={icon.path}>{icon.label}</option>)}
        </select></label>
        {selectedImage && <><img src={mediaUrlFromVaultPath(selectedImage)} alt="Imagem escolhida para ajustar" style={{ maxWidth: '100%', maxHeight: 160, objectFit: 'contain' }} />
          <AssetAdjustmentForm key={selectedImage} imagePath={selectedImage} generationMode={generationMode} category={icons.find(icon => icon.path === selectedImage)?.category === 'items' ? 'items' : 'map'} onCreated={adjustmentCreated} /></>}
      </details>
      <div className="campaign-view-switch" style={{ margin: ".5rem 0" }}>
        <button type="button" className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>
          Todos ({jobs.length})
        </button>
        {(["missing", "queued", "generating", "ready", "awaiting_approval", "approved", "failed"] as const).filter(s => s !== "ready" || counts.ready).map((s) => (
          <button key={s} type="button" className={filter === s ? "active" : ""} onClick={() => setFilter(s)}>
            {STATUS_LABELS[s]} ({counts[s] || 0})
          </button>
        ))}
        <button type="button" className={filter === "ignored" ? "active" : ""} onClick={() => setFilter("ignored")}>
          Ignorado ({counts["ignored"] || 0})
        </button>
      </div>
      {loading ? (
        <p>Carregando…</p>
      ) : filtered.length === 0 ? (
        <p>Nenhum asset nesta categoria.</p>
      ) : (
        <div className="campaign-story-list" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))", overflowWrap: "anywhere" }}>
          {filtered.map((job) => (
            <article key={job.id} className="companion-card">
              <strong>
                {job.entity_type === 'asset_revision' ? `Ajuste de imagem · versão #${job.id}` : `[${assetTypeLabel(job.asset_type)}] ${job.entity_type} #${job.entity_id}`}
              </strong>
              <p style={{ margin: ".25rem 0", fontSize: ".75rem", color: "#b7bcc0" }}>
                Status: {STATUS_LABELS[job.status] || job.status} · Style: {job.style_version}
              </p>
              <AutomaticReferences job={job} />
              {generationLabel(job) && <small>{generationLabel(job)}</small>}
              {job.entity_type === 'asset_revision' && <figure className="asset-edit-before"><figcaption>Antes · preservada</figcaption>
                <img src={`/gm/assets/${job.id}/base-preview?token=${encodeURIComponent(getAccessToken() || '')}`} alt="Imagem antes do ajuste" />
                <figcaption>Depois · nova versão</figcaption>
              </figure>}
              {job.image_path && job.status !== "generating" && (
                <img
                  key={job.image_path}
                  src={previewUrl(job)}
                  alt={`Imagem de ${assetTypeLabel(job.asset_type)} ${job.entity_id}`}
                  style={{ maxWidth: "100%", maxHeight: 160, objectFit: "contain", marginTop: 4 }}
                  onLoad={(e) => { const placeholder = e.currentTarget.naturalWidth <= 1 && e.currentTarget.naturalHeight <= 1; setImageProblems(current => ({ ...current, [job.id]: placeholder ? "Placeholder de teste (1×1), não uma arte gerada." : "" })); }}
                  onError={() => setImageProblems(current => ({ ...current, [job.id]: "Não foi possível carregar a imagem." }))}
                />
              )}
              {imageProblems[job.id] && <p role="status">{imageProblems[job.id]}</p>}
              {!job.image_path && <p>Imagem ainda não gerada.</p>}
              {job.error && <p style={{ color: "#ffb4b4", fontSize: ".7rem" }}>Erro: {job.error}</p>}
              {job.image_path && job.status !== 'generating' && !imageProblems[job.id] &&
                <AssetAdjustmentForm imagePath={job.image_path} parentJobId={job.id} generationMode={generationMode} onCreated={adjustmentCreated} />}
              <div style={{ display: "flex", gap: ".3rem", marginTop: ".4rem", flexWrap: "wrap" }}>
                <button type="button" onClick={() => window.open(previewUrl(job), "_blank", "noopener,noreferrer")} disabled={!job.image_path}>
                  Visualizar
                </button>
                {(["ready", "awaiting_approval"].includes(job.status)) && <button type="button" disabled={busy !== null || Boolean(imageProblems[job.id])} onClick={() => void action(job.id, "approve")}>Aprovar</button>}
                {job.entity_type !== 'asset_revision' && <button type="button" disabled={busy !== null || job.status === "generating"} onClick={() => void action(job.id, "regenerate")}>
                  {busy === job.id ? "Aguarde…" : job.image_path ? "Regenerar" : "Gerar"}
                </button>}
                <button type="button" disabled={busy !== null || job.status === "generating"} onClick={() => void action(job.id, "ignore")}>
                  Ignorar
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
