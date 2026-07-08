import { useEffect, useState } from "react";
import { getAccessToken, health, rebuildIndex, setAccessToken } from "./api";
import ChatVault from "./pages/ChatVault";
import NoteView from "./pages/NoteView";
import SearchNotes from "./pages/SearchNotes";
import SessionPanel from "./pages/SessionPanel";

type Page = "chat" | "search" | "note" | "session";

export default function App() {
  const [page, setPage] = useState<Page>("session");
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>("verificando...");
  const [tokenDraft, setTokenDraft] = useState<string>(getAccessToken());

  useEffect(() => {
    health()
      .then((data) =>
        setStatus(
          `Backend ok · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        ),
      )
      .catch(() => setStatus("backend indisponível"));
  }, []);

  function saveToken() {
    setAccessToken(tokenDraft);
    setStatus("token salvo; verificando backend...");
    health()
      .then((data) =>
        setStatus(
          `Backend ok · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        ),
      )
      .catch(() => setStatus("backend indisponível ou token inválido"));
  }

  async function onRebuild() {
    setStatus("reindexando vault...");
    try {
      const data = await rebuildIndex();
      setStatus(`índice pronto · ${data.indexed_notes} notas`);
    } catch (error) {
      setStatus("falha ao reindexar");
    }
  }

  function openNote(id: number) {
    setSelectedNoteId(id);
    setPage("note");
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Omnisvera Companion</p>
          <h1>Vault no celular</h1>
          <p>{status}</p>
        </div>
        <button onClick={onRebuild}>Reindexar</button>
      </header>

      <section className="token-bar">
        <input
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder="Token de acesso, se o servidor pedir"
          type="password"
        />
        <button onClick={saveToken}>Salvar token</button>
      </section>

      <nav className="tabs">
        <button className={page === "session" ? "active" : ""} onClick={() => setPage("session")}>
          Sessão
        </button>
        <button className={page === "chat" ? "active" : ""} onClick={() => setPage("chat")}>
          Chat
        </button>
        <button className={page === "search" ? "active" : ""} onClick={() => setPage("search")}>
          Buscar
        </button>
        <button className={page === "note" ? "active" : ""} onClick={() => setPage("note")}>
          Nota
        </button>
      </nav>

      {page === "session" && <SessionPanel onOpenNote={openNote} />}
      {page === "chat" && <ChatVault onOpenNote={openNote} />}
      {page === "search" && <SearchNotes onOpenNote={openNote} />}
      {page === "note" && <NoteView noteId={selectedNoteId} />}
    </main>
  );
}
