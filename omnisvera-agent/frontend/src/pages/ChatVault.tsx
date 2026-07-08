import { useEffect, useState } from "react";
import { chatVault, NoteSummary } from "../api";

export default function ChatVault({
  onOpenNote,
  initialQuestion,
}: {
  onOpenNote: (id: number) => void;
  initialQuestion?: string;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [notes, setNotes] = useState<NoteSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuestion) setQuestion(initialQuestion);
  }, [initialQuestion]);

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const data = await chatVault(question);
      setAnswer(data.answer || data.warning || "Sem resposta.");
      setNotes(data.notes_used || []);
    } catch (error) {
      setAnswer("Não consegui falar com o backend/Ollama.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h2>Chat com o Vault</h2>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Pergunte: o que sabemos sobre Varkh? Quais rumores estão ativos?"
      />
      <button onClick={ask} disabled={loading}>
        {loading ? "consultando..." : "Perguntar"}
      </button>
      {answer && <pre className="answer">{answer}</pre>}
      {notes.length > 0 && (
        <div className="cards">
          {notes.map((note) => (
            <button key={note.id} className="note-card" onClick={() => onOpenNote(note.id)}>
              <strong>{note.title}</strong>
              <span>{note.path}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
