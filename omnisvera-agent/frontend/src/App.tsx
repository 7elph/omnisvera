import { useEffect, useState } from "react";
import { AccessMode, getAccessMode, getAccessToken, health, rebuildIndex, setAccessMode, setAccessToken } from "./api";
import ChatVault from "./pages/ChatVault";
import NoteView from "./pages/NoteView";
import PlayerPanel from "./pages/PlayerPanel";
import SearchNotes from "./pages/SearchNotes";
import SessionPanel from "./pages/SessionPanel";

type Page = "chat" | "search" | "note" | "session" | "player";

export default function App() {
  const initialMode = getAccessMode();
  const [page, setPage] = useState<Page>(initialMode === "player" ? "player" : "session");
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [noteHistory, setNoteHistory] = useState<number[]>([]);
  const [chatSeed, setChatSeed] = useState("");
  const [status, setStatus] = useState<string>("verificando...");
  const [tokenDraft, setTokenDraft] = useState<string>(getAccessToken());
  const [mode, setMode] = useState<AccessMode>(initialMode);
  const [authVersion, setAuthVersion] = useState(0);

  useEffect(() => {
    health()
      .then((data) => {
        const detectedMode: AccessMode = data.access_mode === "player" ? "player" : "gm";
        setMode(detectedMode);
        setAccessMode(detectedMode);
        setPage((current) => {
          if (current === "session" && detectedMode === "player") return "player";
          if (current === "player" && detectedMode === "gm") return "session";
          return current;
        });
        setStatus(
          `${data.access_mode === "player" ? "Jogador" : "Mestre"} · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        );
      })
      .catch(() => setStatus("backend indisponível"));
  }, []);

  function saveToken() {
    setAccessToken(tokenDraft);
    setAccessMode(mode);
    setStatus("token salvo; verificando backend...");
    health()
      .then((data) => {
        const detectedMode: AccessMode = data.access_mode === "player" ? "player" : "gm";
        setMode(detectedMode);
        setAccessMode(detectedMode);
        setPage(detectedMode === "player" ? "player" : "session");
        setStatus(
          `${data.access_mode === "player" ? "Jogador" : "Mestre"} · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        );
        setAuthVersion((current) => current + 1);
      })
      .catch(() => setStatus("backend indisponível ou token inválido"));
  }

  async function onRebuild() {
    if (mode === "player") {
      setStatus("atualização de índice é função do Mestre");
      return;
    }
    setStatus("atualizando índice...");
    try {
      const data = await rebuildIndex();
      setStatus(`índice pronto · ${data.indexed_notes} notas`);
    } catch (error) {
      setStatus("falha ao atualizar índice");
    }
  }

  function openNote(id: number) {
    setNoteHistory((current) => (selectedNoteId ? [...current.slice(-12), selectedNoteId] : current));
    setSelectedNoteId(id);
    setPage("note");
  }

  function goBackNote() {
    const previous = noteHistory.at(-1);
    if (!previous) return;
    setNoteHistory((current) => current.slice(0, -1));
    setSelectedNoteId(previous);
    setPage("note");
  }

  function askPrompt(prompt: string) {
    setChatSeed(prompt);
    setPage("chat");
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <h1>OMNISVERA</h1>
      </header>

      <section className="token-bar">
        <div className="mode-switch">
          <button
            className={mode === "gm" ? "active" : ""}
            onClick={() => {
              setMode("gm");
              setAccessMode("gm");
              setPage("session");
            }}
          >
            Mestre
          </button>
          <button
            className={mode === "player" ? "active" : ""}
            onClick={() => {
              setMode("player");
              setAccessMode("player");
              setPage("player");
            }}
          >
            Jogador
          </button>
        </div>
        <input
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder={mode === "player" ? "Token dos jogadores" : "Token do mestre"}
          type="password"
        />
        <button onClick={saveToken}>Salvar token</button>
        {mode === "gm" && <button onClick={onRebuild}>Atualizar índice</button>}
      </section>

      <nav className="tabs">
        {mode === "gm" ? (
          <button className={page === "session" ? "active" : ""} onClick={() => setPage("session")}>
            Sessão
          </button>
        ) : (
          <button className={page === "player" ? "active" : ""} onClick={() => setPage("player")}>
            Jogadores
          </button>
        )}
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

      {page === "session" && mode === "gm" && <SessionPanel onOpenNote={openNote} onAskPrompt={askPrompt} />}
      {page === "player" && mode === "player" && (
        <PlayerPanel key={`player-${authVersion}`} onOpenNote={openNote} onAskPrompt={askPrompt} />
      )}
      {page === "chat" && <ChatVault onOpenNote={openNote} initialQuestion={chatSeed} />}
      {page === "search" && <SearchNotes onOpenNote={openNote} />}
      {page === "note" && (
        <>
          {noteHistory.length > 0 && (
            <button className="back-button" onClick={goBackNote}>
              Voltar
            </button>
          )}
          <NoteView noteId={selectedNoteId} onOpenNote={openNote} />
        </>
      )}
    </main>
  );
}
