import { useEffect, useMemo, useRef, useState } from "react";
import {
  approveTrainingExample,
  captureTrainingInteraction,
  chatVault,
  ChatResult,
  getAccessMode,
  mediaUrlFromVaultPath,
  NoteSummary,
  TrainingFeedbackAction,
  updateTrainingExample,
} from "../api";
import RenderedNote from "../components/RenderedNote";

type ChatMessage = {
  id: number;
  question: string;
  result: ChatResult;
};

const FEEDBACK_ACTIONS: Array<{ action: TrainingFeedbackAction; label: string; hint: string }> = [
  { action: "good", label: "Boa", hint: "Criar candidata para revisão" },
  { action: "correct", label: "Corrigir e aprovar", hint: "Editar antes de aprovar" },
  { action: "reject", label: "Rejeitar", hint: "Não usar no treinamento" },
  { action: "hallucination", label: "Inventou", hint: "Marcar invenção factual" },
  { action: "leak", label: "Vazou", hint: "Registrar incidente sem guardar o segredo" },
  { action: "incomplete", label: "Incompleta", hint: "Faltou informação relevante" },
  { action: "artificial", label: "Artificial", hint: "Fatos bons, voz ruim" },
  { action: "incorrect_source", label: "Fonte incorreta", hint: "Bloquear até corrigir a fonte" },
];

const DEFAULT_PLAYER_PROMPTS = [
  "O que aconteceu até agora?",
  "Quais missões estão ativas?",
  "Quais rumores estão ativos?",
  "Quem são os personagens jogadores?",
  "O que sabemos sobre Nimalis?",
];

function SourceCard({ note, onOpenNote }: { note: NoteSummary; onOpenNote: (id: number) => void }) {
  const image = mediaUrlFromVaultPath(note.thumbnail || note.cover);
  const isPlayer = getAccessMode() === "player";

  return (
    <button className={`source-card ${image ? "has-image" : ""}`} onClick={() => onOpenNote(note.id)}>
      {image && <img src={image} alt="" loading="lazy" />}
      <span>
        <strong>{note.title}</strong>
        <small>{note.type || "registro"} · {note.visibility || "liberado"}</small>
        {!isPlayer && <em>{note.path}</em>}
      </span>
    </button>
  );
}

function runtimeLabel(result: ChatResult) {
  if (result.ollama_used) return "Ollama respondeu";
  if (result.ollama_attempted) return "Ollama filtrado";
  return "Resposta segura do índice";
}

function runtimeClass(result: ChatResult) {
  if (result.ollama_used) return "runtime-ok";
  if (result.ollama_attempted) return "runtime-filtered";
  return "runtime-fallback";
}

export default function ChatVault({
  onOpenNote,
  onUnknownNote,
  initialQuestion,
}: {
  onOpenNote: (id: number) => void;
  onUnknownNote?: (target: string) => void;
  initialQuestion?: string;
}) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastSeed, setLastSeed] = useState("");
  const [feedbackTarget, setFeedbackTarget] = useState<{ message: ChatMessage; action: TrainingFeedbackAction } | null>(null);
  const [feedbackResponse, setFeedbackResponse] = useState("");
  const [feedbackReason, setFeedbackReason] = useState("");
  const [feedbackCategory, setFeedbackCategory] = useState("");
  const [feedbackQuality, setFeedbackQuality] = useState(4);
  const [feedbackSaving, setFeedbackSaving] = useState(false);
  const [feedbackState, setFeedbackState] = useState<Record<number, string>>({});
  const threadEndRef = useRef<HTMLDivElement | null>(null);
  const sessionIdRef = useRef(
    typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `session-${Date.now()}`,
  );
  const isPlayer = getAccessMode() === "player";

  const latestSuggestions = useMemo(() => {
    const latest = messages.at(-1)?.result.suggested_questions || [];
    return latest.length ? latest : DEFAULT_PLAYER_PROMPTS;
  }, [messages]);

  async function ask(text = question) {
    const clean = text.trim();
    if (!clean || loading) return;
    setLoading(true);
    setQuestion("");
    try {
      const contextNoteIds = (messages.at(-1)?.result.notes_used || []).map((note) => note.id);
      const data = await chatVault(clean, 6, contextNoteIds, sessionIdRef.current);
      setMessages((current) => [
        ...current.slice(-8),
        {
          id: Date.now(),
          question: clean,
          result: data,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current.slice(-8),
        {
          id: Date.now(),
          question: clean,
          result: {
            answer: "Não consegui falar com o backend/Ollama. Tente de novo em alguns segundos.",
            notes_used: [],
            note_paths: [],
            insufficient_context: true,
            warning: "Backend indisponível.",
            suggested_questions: DEFAULT_PLAYER_PROMPTS,
            ollama_used: false,
            ollama_attempted: false,
            model: null,
            retrieval_mode: "offline",
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const clean = initialQuestion?.trim();
    if (!clean || clean === lastSeed) return;
    setLastSeed(clean);
    void ask(clean);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  useEffect(() => {
    if (messages.length) threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  function openFeedback(message: ChatMessage, action: TrainingFeedbackAction) {
    setFeedbackTarget({ message, action });
    setFeedbackResponse(action === "hallucination" || action === "leak" || action === "incorrect_source" ? "" : message.result.answer);
    setFeedbackReason("");
    setFeedbackCategory("");
    setFeedbackQuality(action === "good" ? 5 : 4);
  }

  async function submitFeedback() {
    if (!feedbackTarget || feedbackSaving) return;
    const { message, action } = feedbackTarget;
    setFeedbackSaving(true);
    try {
      const captured = await captureTrainingInteraction({
        interaction_id: message.result.interaction_id,
        created_at: message.result.created_at,
        session_id: sessionIdRef.current,
        user_profile: "gm",
        question: message.question,
        raw_model_response: message.result.raw_model_response,
        final_response: message.result.answer,
        verified_facts: message.result.fatos_confirmados || [],
        theories: message.result.teorias || [],
        insufficient_information: message.result.informacoes_insuficientes || [],
        retrieved_sources: message.result.notes_used,
        retrieval_mode: message.result.retrieval_mode,
        model: message.result.model,
        ollama_used: Boolean(message.result.ollama_used),
        response_time_ms: message.result.response_time_ms || 0,
        validator_rejections: message.result.validator_rejections || [],
        warning: message.result.warning,
        behavior_memory_used: Boolean(message.result.behavior_memory_used),
        behavioral_trace: message.result.behavioral_trace,
        feedback_action: action,
        reason: feedbackReason || undefined,
        category: feedbackCategory || undefined,
      });
      if (action === "correct") {
        const updated = await updateTrainingExample(captured.example.id, {
          ideal_response: feedbackResponse,
          category: feedbackCategory || captured.example.category,
          quality: feedbackQuality,
          hallucination_detected: false,
          leak_detected: false,
          incorrect_source_detected: false,
          contains_secret: false,
          reason: feedbackReason || "Correção rápida pelo chat",
        });
        await approveTrainingExample(updated.example.id, {
          ideal_response: feedbackResponse,
          quality: feedbackQuality,
          reason: feedbackReason || "Revisado e aprovado pelo Sage",
        });
        setFeedbackState((current) => ({ ...current, [message.id]: "Exemplo corrigido e aprovado." }));
      } else if (action === "reject") {
        setFeedbackState((current) => ({ ...current, [message.id]: "Resposta rejeitada; não entrará no treino." }));
      } else {
        if (feedbackResponse && feedbackResponse !== captured.example.ideal_response) {
          await updateTrainingExample(captured.example.id, {
            ideal_response: feedbackResponse,
            category: feedbackCategory || captured.example.category,
            quality: feedbackQuality,
            reason: feedbackReason || undefined,
          });
        }
        setFeedbackState((current) => ({ ...current, [message.id]: "Candidato pendente salvo para revisão." }));
      }
      setFeedbackTarget(null);
    } catch (error) {
      setFeedbackState((current) => ({ ...current, [message.id]: error instanceof Error ? error.message : "Falha ao salvar avaliação." }));
    } finally {
      setFeedbackSaving(false);
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Arquivo Vivo</p>
          <h2>Fale com Omnisvera</h2>
          <p>A entidade responde apenas com lembranças já reveladas ao grupo.{messages.length ? ` Mantendo o fio de ${messages.length} troca(s).` : ""}</p>
        </div>
        {messages.length > 0 && (
          <button className="secondary-button" onClick={() => setMessages([])}>
            Limpar
          </button>
        )}
      </div>

      <div className="prompt-chips" aria-label="Perguntas rápidas">
        {latestSuggestions.map((prompt) => (
          <button key={prompt} onClick={() => ask(prompt)} disabled={loading}>
            {prompt}
          </button>
        ))}
      </div>

      <div className="chat-input-box">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
              event.preventDefault();
              void ask();
            }
          }}
          placeholder="Pergunte: quem é Vezemir? Quais rumores estão ativos? O que sabemos sobre Nimalis?"
        />
        <button onClick={() => ask()} disabled={loading || !question.trim()}>
          {loading ? "consultando..." : "Perguntar"}
        </button>
      </div>

      {messages.length === 0 && (
        <div className="empty-chat">
          <strong>Bom para usar na mesa:</strong>
          <span>pergunte por personagens, rumores, missões, lugares e resumos públicos.</span>
        </div>
      )}

      <div className="chat-thread">
        {messages.map((message) => (
          <article key={message.id} className="chat-message">
            <div className="user-bubble">{message.question}</div>
            {message.result.warning && <p className="warning-text">{message.result.warning}</p>}
            <RenderedNote
              content={message.result.answer || "Sem resposta."}
              onOpenNote={onOpenNote}
              onUnknownNote={onUnknownNote}
            />
            {message.result.teorias && message.result.teorias.length > 0 && (
              <div className="grounded-note theory-note">
                <strong>Teoria do Arquivo</strong>
                {message.result.teorias.slice(0, 2).map((item, index) => (
                  <p key={`${message.id}-theory-${index}`}>{item.teoria}</p>
                ))}
              </div>
            )}
            {message.result.informacoes_insuficientes && message.result.informacoes_insuficientes.length > 0 && (
              <div className="grounded-note missing-note">
                <strong>O Arquivo não tem certeza</strong>
                {message.result.informacoes_insuficientes.slice(0, 2).map((item, index) => (
                  <p key={`${message.id}-missing-${index}`}>{item}</p>
                ))}
              </div>
            )}
            {!isPlayer && (
              <div className="chat-runtime">
                <span className={runtimeClass(message.result)}>{runtimeLabel(message.result)}</span>
                {message.result.model && (message.result.ollama_used || message.result.ollama_attempted) && <span>{message.result.model}</span>}
                {message.result.retrieval_mode && <span>{message.result.retrieval_mode}</span>}
              </div>
            )}
            {!isPlayer && (
              <div className="chat-feedback">
                <details>
                  <summary>Avaliar resposta</summary>
                  <div className="feedback-menu">
                    {FEEDBACK_ACTIONS.map((item) => (
                      <button key={item.action} onClick={() => openFeedback(message, item.action)}>
                        <strong>{item.label}</strong>
                        <small>{item.hint}</small>
                      </button>
                    ))}
                  </div>
                </details>
                {feedbackState[message.id] && <p>{feedbackState[message.id]}</p>}
              </div>
            )}
            {message.result.suggested_questions && message.result.suggested_questions.length > 0 && (
              <div className="message-suggestions">
                <span>Continuar com:</span>
                {message.result.suggested_questions.map((prompt) => (
                  <button key={`${message.id}-${prompt}`} onClick={() => ask(prompt)} disabled={loading}>
                    {prompt}
                  </button>
                ))}
              </div>
            )}
            {message.result.notes_used[0] && (
              <button className="chat-primary-source" onClick={() => onOpenNote(message.result.notes_used[0].id)}>Abrir registro principal · {message.result.notes_used[0].title}</button>
            )}
            {message.result.notes_used.length > 0 && (
              <details className="source-list chat-sources">
                <summary>{message.result.notes_used.length} fonte(s) consultada(s)</summary>
                <div className="source-grid">
                  {message.result.notes_used.map((note) => (
                    <SourceCard key={`${message.id}-${note.id}`} note={note} onOpenNote={onOpenNote} />
                  ))}
                </div>
              </details>
            )}
          </article>
        ))}
        <div ref={threadEndRef} />
      </div>
      {feedbackTarget && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => !feedbackSaving && setFeedbackTarget(null)}>
          <section className="curation-modal" role="dialog" aria-modal="true" aria-label="Avaliar resposta" onMouseDown={(event) => event.stopPropagation()}>
            <div className="chat-header">
              <div>
                <p className="eyebrow">Curadoria da IA</p>
                <h2>{FEEDBACK_ACTIONS.find((item) => item.action === feedbackTarget.action)?.label}</h2>
              </div>
              <button className="secondary-button" onClick={() => setFeedbackTarget(null)} disabled={feedbackSaving}>Fechar</button>
            </div>
            <label>Pergunta<input value={feedbackTarget.message.question} readOnly /></label>
            {feedbackTarget.action !== "reject" && feedbackTarget.action !== "leak" && (
              <label>Resposta ideal<textarea value={feedbackResponse} onChange={(event) => setFeedbackResponse(event.target.value)} /></label>
            )}
            <div className="curation-form-row">
              <label>Categoria sugerida<input value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)} placeholder="automática" /></label>
              <label>Qualidade<select value={feedbackQuality} onChange={(event) => setFeedbackQuality(Number(event.target.value))}>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            </div>
            <label>Observação<textarea value={feedbackReason} onChange={(event) => setFeedbackReason(event.target.value)} placeholder="O que ficou bom ou precisa ser corrigido?" /></label>
            {feedbackTarget.action === "leak" && <p className="danger-note">A resposta bruta e o texto exibido serão removidos do registro do incidente. Este candidato ficará inelegível para aprovação.</p>}
            <p className="muted">Nenhuma ação inicia treinamento. “Boa” apenas cria um candidato pendente.</p>
            <button onClick={submitFeedback} disabled={feedbackSaving || (feedbackTarget.action === "correct" && !feedbackResponse.trim())}>
              {feedbackSaving ? "Salvando..." : feedbackTarget.action === "correct" ? "Validar e aprovar" : feedbackTarget.action === "reject" ? "Confirmar rejeição" : "Salvar candidato"}
            </button>
          </section>
        </div>
      )}
    </section>
  );
}
