import { useEffect, useMemo, useState } from "react";
import { chatVault, ChatResult, mediaUrlFromVaultPath, NoteSummary } from "../api";
import RenderedNote from "../components/RenderedNote";

type ChatMessage = {
  id: number;
  question: string;
  result: ChatResult;
};

const DEFAULT_PLAYER_PROMPTS = [
  "O que aconteceu até agora?",
  "Quais missões estão ativas?",
  "Quais rumores estão ativos?",
  "Quem são os personagens jogadores?",
  "O que sabemos sobre Nimalis?",
];

function SourceCard({ note, onOpenNote }: { note: NoteSummary; onOpenNote: (id: number) => void }) {
  const image = mediaUrlFromVaultPath(note.thumbnail || note.cover);

  return (
    <button className={`source-card ${image ? "has-image" : ""}`} onClick={() => onOpenNote(note.id)}>
      {image && <img src={image} alt="" loading="lazy" />}
      <span>
        <strong>{note.title}</strong>
        <small>{note.type || "nota"} · {note.visibility || "liberado"}</small>
        <em>{note.path}</em>
      </span>
    </button>
  );
}

export default function ChatVault({
  onOpenNote,
  initialQuestion,
}: {
  onOpenNote: (id: number) => void;
  initialQuestion?: string;
}) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastSeed, setLastSeed] = useState("");

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
      const data = await chatVault(clean);
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

  return (
    <section className="panel chat-panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Consulta do Vault</p>
          <h2>Chat com Omnisvera</h2>
          <p>Respostas com fontes do vault, respeitando o modo atual e o filtro player-safe.</p>
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
            <RenderedNote content={message.result.answer || "Sem resposta."} onOpenNote={onOpenNote} />
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
            {message.result.notes_used.length > 0 && (
              <div className="source-list">
                <p className="eyebrow">Fontes usadas</p>
                <div className="source-grid">
                  {message.result.notes_used.map((note) => (
                    <SourceCard key={`${message.id}-${note.id}`} note={note} onOpenNote={onOpenNote} />
                  ))}
                </div>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
