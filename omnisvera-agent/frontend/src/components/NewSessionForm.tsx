import { useRef, useState } from "react";
import { createGameSession, newSceneRequestId, updateGameSessionStatus } from "../api";

/** Retain the request and saved session across network retries; never replay a new creation. */
export default function NewSessionForm({ onCreated }: { onCreated: (id: number) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const attempt = useRef<{ request_id: string; title: string; sessionId?: number } | null>(null);

  async function submit() {
    if (lock.current || !title.trim()) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const current = attempt.current ??= { request_id: newSceneRequestId("session"), title: title.trim() };
    try {
      if (!current.sessionId) current.sessionId = (await createGameSession({ request_id: current.request_id, title: current.title })).id;
      await updateGameSessionStatus(current.sessionId, "active");
      await onCreated(current.sessionId);
      attempt.current = null;
      setTitle("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível iniciar a sessão. Tente novamente.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  return <section className="scene-section">
    <h3>Nova sessão</h3>
    <p>Comece pelo nome. Depois escolha o grupo, a cena e o objetivo imediato; o restante pode ser preparado durante o jogo.</p>
    <div className="scene-create-form">
      <label>Nome da sessão<input value={title} disabled={busy || Boolean(attempt.current)} onChange={(event) => setTitle(event.target.value)} /></label>
      <button type="button" disabled={busy || !title.trim()} onClick={() => void submit()}>{busy ? "Iniciando sessão…" : attempt.current ? "Tentar iniciar novamente" : "Criar e iniciar sessão"}</button>
    </div>
    {error && <p role="alert" className="warning-text">{error}</p>}
  </section>;
}
