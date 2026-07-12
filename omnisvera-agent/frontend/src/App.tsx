import { useEffect, useState } from "react";
import { AccessMode, getAccessMode, getAccessToken, health, rebuildIndex, resolveNote, setAccessMode, setAccessToken } from "./api";
import ChatVault from "./pages/ChatVault";
import CharacterSheetBuilder from "./pages/CharacterSheetBuilder";
import NoteView from "./pages/NoteView";
import PlayerPanel from "./pages/PlayerPanel";
import SearchNotes from "./pages/SearchNotes";
import SessionPanel from "./pages/SessionPanel";

type Page = "chat" | "search" | "note" | "session" | "player" | "sheet";

export default function App() {
  const initialMode = getAccessMode();
  const initialToken = getAccessToken();
  const [page, setPage] = useState<Page>(initialMode === "player" ? "player" : "session");
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [unknownTarget, setUnknownTarget] = useState<string | null>(null);
  const [noteHistory, setNoteHistory] = useState<number[]>([]);
  const [chatSeed, setChatSeed] = useState("");
  const [status, setStatus] = useState<string>("");
  const [tokenDraft, setTokenDraft] = useState<string>(initialToken);
  const [mode, setMode] = useState<AccessMode>(initialMode);
  const [authVersion, setAuthVersion] = useState(0);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setAuthenticated(false);
      setStatus("token necessário");
      return;
    }
    health()
      .then((data) => {
        const detectedMode: AccessMode = data.access_mode === "player" ? "player" : "gm";
        setMode(detectedMode);
        setAccessMode(detectedMode);
        setAuthenticated(true);
        setPage((current) => {
          if (current === "session" && detectedMode === "player") return "player";
          if (current === "player" && detectedMode === "gm") return "session";
          return current;
        });
        setStatus(
          `${data.access_mode === "player" ? (data.player_character_title || "Jogador") : "Mestre"} · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        );
      })
      .catch(() => {
        setAuthenticated(false);
        setStatus("token inválido ou backend indisponível");
      });
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function openHashNote() {
      const prefix = "#/note/";
      if (!window.location.hash.startsWith(prefix)) return;
      const target = decodeURIComponent(window.location.hash.slice(prefix.length));
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
      if (!target.trim()) return;

      try {
        const note = await resolveNote(target);
        if (cancelled) return;
        if (note) {
          setUnknownTarget(null);
          setSelectedNoteId(note.id);
        } else {
          setSelectedNoteId(null);
          setUnknownTarget(target);
        }
        setPage("note");
      } catch {
        if (cancelled) return;
        setSelectedNoteId(null);
        setUnknownTarget(target);
        setPage("note");
      }
    }

    void openHashNote();
    window.addEventListener("hashchange", openHashNote);
    return () => {
      cancelled = true;
      window.removeEventListener("hashchange", openHashNote);
    };
  }, []);

  function saveToken() {
    setAuthenticated(false);
    setAccessToken(tokenDraft);
    setAccessMode(mode);
    setStatus("token salvo; verificando backend...");
    health()
      .then((data) => {
        const detectedMode: AccessMode = data.access_mode === "player" ? "player" : "gm";
        setMode(detectedMode);
        setAccessMode(detectedMode);
        setAuthenticated(true);
        setPage(detectedMode === "player" ? "player" : "session");
        setStatus(
          `${data.access_mode === "player" ? (data.player_character_title || "Jogador") : "Mestre"} · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`,
        );
        setAuthVersion((current) => current + 1);
      })
      .catch(() => {
        setAuthenticated(false);
        setStatus("backend indisponível ou token inválido");
      });
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
    setUnknownTarget(null);
    setSelectedNoteId(id);
    setPage("note");
  }

  function openUnknownNote(target: string) {
    setNoteHistory((current) => (selectedNoteId ? [...current.slice(-12), selectedNoteId] : current));
    setSelectedNoteId(null);
    setUnknownTarget(target);
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
        <button className={page === "sheet" ? "active" : ""} onClick={() => setPage("sheet")}>
          Ficha
        </button>
        <button className={page === "search" ? "active" : ""} onClick={() => setPage("search")}>
          Buscar
        </button>
        <button className={page === "note" ? "active" : ""} onClick={() => setPage("note")}>
          Nota
        </button>
      </nav>

      {!authenticated && (
        <section className="panel">
          <div className="chat-header">
            <h2>Token necessário</h2>
            <p>Digite o token de acesso no campo acima e clique em "Salvar token" para começar.</p>
          </div>
        </section>
      )}
      {authenticated && page === "session" && mode === "gm" && <SessionPanel key={`session-${authVersion}`} onOpenNote={openNote} onAskPrompt={askPrompt} />}
      {authenticated && page === "player" && mode === "player" && (
        <PlayerPanel key={`player-${authVersion}`} onOpenNote={openNote} onAskPrompt={askPrompt} />
      )}
      {authenticated && page === "chat" && <ChatVault onOpenNote={openNote} onUnknownNote={openUnknownNote} initialQuestion={chatSeed} />}
      {authenticated && page === "sheet" && <CharacterSheetBuilder key={`sheet-${authVersion}-${mode}`} mode={mode === "player" ? "player" : "gm"} />}
      {authenticated && page === "search" && <SearchNotes onOpenNote={openNote} />}
      {authenticated && page === "note" && (
        <>
          {noteHistory.length > 0 && (
            <button className="back-button" onClick={goBackNote}>
              Voltar
            </button>
          )}
          <NoteView
            noteId={selectedNoteId}
            unknownTarget={unknownTarget}
            onOpenNote={openNote}
            onUnknownNote={openUnknownNote}
          />
        </>
      )}
    </main>
  );
}
