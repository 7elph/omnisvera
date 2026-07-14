import { useEffect, useMemo, useState } from "react";
import {
  approveTrainingExample,
  deleteTrainingExample,
  duplicateTrainingExample,
  exportTrainingReport,
  getTrainingExample,
  getTrainingStats,
  listTrainingExamples,
  rejectTrainingExample,
  TrainingExample,
  TrainingStats,
  updateTrainingExample,
} from "../api";

const FLAG_LABELS: Record<string, string> = {
  hallucination_detected: "Inventou",
  leak_detected: "Vazou",
  incomplete_detected: "Incompleta",
  artificial_detected: "Artificial",
  incorrect_source_detected: "Fonte incorreta",
};

function statusLabel(value: string) {
  return ({ pending: "Pendente", approved: "Aprovado", rejected: "Rejeitado", captured: "Capturado" } as Record<string, string>)[value] || value;
}

export default function ModelCurationPanel() {
  const [stats, setStats] = useState<TrainingStats | null>(null);
  const [examples, setExamples] = useState<TrainingExample[]>([]);
  const [selected, setSelected] = useState<TrainingExample | null>(null);
  const [status, setStatus] = useState("pending");
  const [profile, setProfile] = useState("");
  const [flag, setFlag] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [personaFilter, setPersonaFilter] = useState("");
  const [qualityFilter, setQualityFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState({
    category: "",
    source_type: "corrected_chat",
    persona_id: "",
    ideal_response: "",
    facts_text: "",
    theories_text: "",
    quality: 4,
    notes: "",
    contains_canon: false,
    contains_secret: false,
    requires_rag: true,
    insufficient_information_expected: false,
    flags: {} as Record<string, boolean>,
  });

  async function refresh() {
    const filters: Record<string, string> = {};
    if (status) filters.status = status;
    if (profile) filters.access_profile = profile;
    if (flag) filters.flag = flag;
    if (categoryFilter) filters.category = categoryFilter;
    if (modelFilter) filters.model = modelFilter;
    if (personaFilter) filters.persona_id = personaFilter;
    if (qualityFilter) filters.quality = qualityFilter;
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    const [nextStats, nextExamples] = await Promise.all([getTrainingStats(), listTrainingExamples(filters)]);
    setStats(nextStats);
    setExamples(nextExamples);
  }

  useEffect(() => {
    void refresh().catch((error) => setNotice(error instanceof Error ? error.message : "Falha ao carregar curadoria."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, profile, flag, categoryFilter, modelFilter, personaFilter, qualityFilter, dateFrom, dateTo]);

  const filtered = useMemo(() => {
    const term = query.trim().toLocaleLowerCase("pt-BR");
    if (!term) return examples;
    return examples.filter((item) => `${item.instruction} ${item.ideal_response} ${item.category}`.toLocaleLowerCase("pt-BR").includes(term));
  }, [examples, query]);

  const approvalBlockingFlags = ["hallucination_detected", "leak_detected", "incorrect_source_detected"]
    .filter((key) => Boolean(form.flags[key]));
  const approvalBlocked = form.contains_secret || approvalBlockingFlags.length > 0;

  async function openExample(id: string) {
    setBusy(true);
    setNotice("");
    try {
      const detail = await getTrainingExample(id);
      setSelected(detail);
      setForm({
        category: detail.category,
        source_type: detail.source_type,
        persona_id: detail.persona_id || "",
        ideal_response: detail.ideal_response,
        facts_text: detail.facts_expected.join("\n"),
        theories_text: detail.theories_allowed.join("\n"),
        quality: detail.curation?.quality_5 || (detail.quality_score === 2 ? 5 : detail.quality_score === 1 ? 3 : 2),
        notes: detail.curation?.curator_notes || "",
        contains_canon: detail.contains_canon,
        contains_secret: detail.contains_secret,
        requires_rag: detail.requires_rag,
        insufficient_information_expected: detail.insufficient_information_expected,
        flags: { ...(detail.curation?.flags || {}) },
      });
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao abrir exemplo.");
    } finally {
      setBusy(false);
    }
  }

  function patchPayload() {
    return {
      category: form.category,
      source_type: form.source_type,
      persona_id: form.persona_id || null,
      ideal_response: form.ideal_response,
      facts_expected: form.facts_text.split("\n").map((value) => value.trim()).filter(Boolean),
      theories_allowed: form.theories_text.split("\n").map((value) => value.trim()).filter(Boolean),
      quality: form.quality,
      notes: form.notes,
      contains_canon: form.contains_canon,
      contains_secret: form.contains_secret,
      requires_rag: form.requires_rag,
      insufficient_information_expected: form.insufficient_information_expected,
      ...form.flags,
      reason: "Revisão no painel de curadoria",
    };
  }

  async function save(approve = false) {
    if (!selected || busy) return;
    setBusy(true);
    setNotice("");
    try {
      const updated = await updateTrainingExample(selected.id, patchPayload());
      if (approve) {
        await approveTrainingExample(updated.example.id, {
          ideal_response: form.ideal_response,
          quality: form.quality,
          reason: "Revisão confirmada no painel de curadoria",
        });
        setNotice("Exemplo aprovado. Você voltou à fila de revisão.");
        setSelected(null);
      } else {
        setNotice("Alterações salvas. O exemplo continua pendente e você voltou à fila.");
        setSelected(null);
      }
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao salvar exemplo.");
    } finally {
      setBusy(false);
    }
  }

  async function reject() {
    if (!selected || busy || !window.confirm("Rejeitar este exemplo? Ele não será usado no treinamento.")) return;
    setBusy(true);
    try {
      await rejectTrainingExample(selected.id, form.notes || "Rejeitado pelo painel de curadoria");
      setSelected(null);
      setNotice("Exemplo rejeitado.");
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao rejeitar.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!selected || busy || !window.confirm("Excluir este candidato pendente?")) return;
    setBusy(true);
    try {
      await deleteTrainingExample(selected.id);
      setSelected(null);
      setNotice("Candidato pendente excluído.");
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao excluir.");
    } finally {
      setBusy(false);
    }
  }

  async function duplicate() {
    if (!selected || busy) return;
    setBusy(true);
    try {
      const copy = await duplicateTrainingExample(selected.id);
      setNotice("Variação pendente criada.");
      await refresh();
      await openExample(copy.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao duplicar.");
    } finally {
      setBusy(false);
    }
  }

  async function exportReport() {
    try {
      const report = await exportTrainingReport();
      const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `omnisvera-curation-report-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao exportar relatório.");
    }
  }

  return (
    <section className="panel curation-panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Laboratório do Modelo</p>
          <h2>Curadoria da IA</h2>
          <p>Transforme respostas reais em exemplos revisados. Nenhum treinamento começa por aqui.</p>
        </div>
        <div className="row"><button className="secondary-button" onClick={() => void exportReport()}>Exportar</button><button className="secondary-button" onClick={() => void refresh()} disabled={busy}>Atualizar</button></div>
      </div>

      {stats && (
        <>
          <div className="curation-summary">
            <span><strong>{stats.approved}</strong><small>aprovados</small></span>
            <span><strong>{stats.statuses.pending || 0}</strong><small>pendentes</small></span>
            <span><strong>{stats.statuses.rejected || 0}</strong><small>rejeitados</small></span>
            <span><strong>{stats.flags.hallucination_detected || 0}</strong><small>invenções</small></span>
            <span><strong>{stats.flags.leak_detected || 0}</strong><small>vazamentos</small></span>
          </div>
          <div className="coverage-progress" aria-label={`${stats.approved} de ${stats.minimum_approved} aprovados`}>
            <div><span style={{ width: `${Math.max(1, stats.progress_percent)}%` }} /></div>
            <p><strong>{stats.approved}/{stats.minimum_approved}</strong> · {stats.progress_percent}%</p>
          </div>
          <p className="danger-note">{stats.warning}</p>
        </>
      )}

      <div className="curation-filters">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar pergunta ou resposta" />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="pending">Pendentes</option><option value="approved">Aprovados</option><option value="rejected">Rejeitados</option><option value="">Todos</option>
        </select>
        <select value={profile} onChange={(event) => setProfile(event.target.value)}>
          <option value="">Player e GM</option><option value="player">Player</option><option value="gm">GM</option>
        </select>
        <select value={flag} onChange={(event) => setFlag(event.target.value)}>
          <option value="">Todas as avaliações</option>
          {Object.entries(FLAG_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
          <option value="">Todas as categorias</option>
          {Object.keys(stats?.coverage.categories || {}).map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <select value={modelFilter} onChange={(event) => setModelFilter(event.target.value)}>
          <option value="">Todos os modelos</option>
          {Object.keys(stats?.models || {}).map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <select value={personaFilter} onChange={(event) => setPersonaFilter(event.target.value)}>
          <option value="">Todas as personas</option>
          {Object.keys(stats?.coverage.personas || {}).filter((value) => value !== "none").map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <select value={qualityFilter} onChange={(event) => setQualityFilter(event.target.value)}>
          <option value="">Qualquer qualidade</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} aria-label="Data inicial" />
        <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} aria-label="Data final" />
      </div>
      {notice && <p className="curation-notice">{notice}</p>}

      <div className="curation-queue">
        {filtered.map((item) => (
          <button key={item.id} className="curation-row" onClick={() => void openExample(item.id)}>
            <span><strong>{item.instruction}</strong><small>{item.category} · {item.access_profile} · {item.curation?.model || "modelo não registrado"}</small></span>
            <em>{statusLabel(item.review_status)}</em>
          </button>
        ))}
        {!filtered.length && <p className="muted">Nenhum exemplo neste filtro.</p>}
      </div>

      {stats && (
        <details className="coverage-details">
          <summary>Cobertura por categoria</summary>
          <div className="coverage-grid">
            {Object.entries(stats.coverage.categories).map(([category, value]) => (
              <span key={category}><strong>{category}</strong><small>{value.current}/{value.target} · faltam {value.missing}</small></span>
            ))}
          </div>
        </details>
      )}

      {selected && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => !busy && setSelected(null)}>
          <section className="curation-modal wide" role="dialog" aria-modal="true" aria-label="Revisar exemplo" onMouseDown={(event) => event.stopPropagation()}>
            <div className="chat-header curation-modal-header">
              <div><p className="eyebrow">Exemplo {selected.review_status}</p><h2>Revisar resposta</h2></div>
              <button className="secondary-button" onClick={() => setSelected(null)} disabled={busy}>Voltar à fila</button>
            </div>
            {notice && <p className="curation-notice modal-notice" role="status" aria-live="polite">{notice}</p>}
            <label>Pergunta<textarea value={selected.instruction} readOnly /></label>
            <div className="curation-form-row">
              <label>Categoria<input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} /></label>
              <label>Qualidade<select value={form.quality} onChange={(event) => setForm({ ...form, quality: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            </div>
            <div className="curation-form-row">
              <label>Origem<select value={form.source_type} onChange={(event) => setForm({ ...form, source_type: event.target.value })}><option value="real_chat">Chat real</option><option value="corrected_chat">Chat corrigido</option><option value="manual">Manual</option><option value="synthetic_candidate">Candidato sintético</option></select></label>
              <label>Persona<input value={form.persona_id} onChange={(event) => setForm({ ...form, persona_id: event.target.value })} placeholder="sem persona" /></label>
            </div>
            <label>Resposta ideal<textarea className="ideal-response-editor" value={form.ideal_response} onChange={(event) => setForm({ ...form, ideal_response: event.target.value })} /></label>
            <div className="curation-form-row">
              <label>Fatos esperados, um por linha<textarea value={form.facts_text} onChange={(event) => setForm({ ...form, facts_text: event.target.value })} /></label>
              <label>Teorias permitidas, uma por linha<textarea value={form.theories_text} onChange={(event) => setForm({ ...form, theories_text: event.target.value })} /></label>
            </div>
            <div className="curation-checks">
              {Object.entries(FLAG_LABELS).map(([key, label]) => (
                <label key={key}><input type="checkbox" checked={Boolean(form.flags[key])} onChange={(event) => setForm({ ...form, flags: { ...form.flags, [key]: event.target.checked } })} />{label}</label>
              ))}
              <label><input type="checkbox" checked={form.contains_canon} onChange={(event) => setForm({ ...form, contains_canon: event.target.checked })} />Contém cânone</label>
              <label><input type="checkbox" checked={form.contains_secret} onChange={(event) => setForm({ ...form, contains_secret: event.target.checked })} />Contém segredo</label>
              <label><input type="checkbox" checked={form.requires_rag} onChange={(event) => setForm({ ...form, requires_rag: event.target.checked })} />Exige contexto</label>
              <label><input type="checkbox" checked={form.insufficient_information_expected} onChange={(event) => setForm({ ...form, insufficient_information_expected: event.target.checked })} />Deve declarar insuficiência</label>
            </div>
            <label>Observações<textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
            {selected.interaction && (
              <details className="raw-response-box">
                <summary>Dados técnicos da interação</summary>
                <p>{selected.interaction.model || "modelo desconhecido"} · {selected.interaction.retrieval_mode || "modo desconhecido"} · {selected.interaction.response_time_ms} ms</p>
                <h4>Resposta exibida</h4><pre>{selected.interaction.final_response}</pre>
                <h4>Resposta bruta (somente mestre)</h4><pre>{selected.interaction.raw_model_response || "Não disponível."}</pre>
              </details>
            )}
            {approvalBlocked && (
              <p className="danger-note approval-blocker" role="status">
                Para aprovar, corrija a resposta e desmarque: {[...approvalBlockingFlags.map((key) => FLAG_LABELS[key]), ...(form.contains_secret ? ["Contém segredo"] : [])].join(", ")}.
                Você ainda pode salvar e voltar à fila.
              </p>
            )}
            <div className="curation-actions">
              <button className="secondary-button" onClick={() => void save(false)} disabled={busy}>{busy ? "Salvando..." : "Salvar e voltar"}</button>
              <button onClick={() => void save(true)} disabled={busy || !form.ideal_response.trim() || approvalBlocked}>{busy ? "Validando..." : "Validar, aprovar e voltar"}</button>
              {selected.review_status !== "approved" && <button className="danger-button" onClick={reject} disabled={busy}>Rejeitar</button>}
              <button className="secondary-button" onClick={duplicate} disabled={busy}>Duplicar variação</button>
              {selected.review_status === "pending" && <button className="danger-button subtle" onClick={remove} disabled={busy}>Excluir pendente</button>}
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
