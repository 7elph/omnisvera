import { useEffect, useState } from "react";
import { AccessMode, getAccessMode, getAccessToken, health, rebuildIndex, resolveNote, setAccessMode, setAccessToken } from "./api";
import DiceTray from "./components/DiceTray";
import QuickCharacterSheet from "./components/QuickCharacterSheet";
import ChatVault from "./pages/ChatVault";
import PlayableCharacterSheet from "./pages/PlayableCharacterSheet";
import NoteView from "./pages/NoteView";
import PlayerPanel from "./pages/PlayerPanel";
import SearchNotes from "./pages/SearchNotes";
import SessionPanel from "./pages/SessionPanel";
import ModelCurationPanel from "./pages/ModelCurationPanel";

type Page = "chat" | "search" | "note" | "session" | "player" | "sheet" | "curation";

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
  const [accessPanelOpen, setAccessPanelOpen] = useState(!initialToken);

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
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [page, selectedNoteId]);

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
        setAccessPanelOpen(false);
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

  function navigate(next: Page) {
    setPage(next);
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <h1>OMNISVERA</h1>
      </header>

      {authenticated && !accessPanelOpen ? (
        <section className="access-summary">
          <span><b>{mode === "player" ? "Jogador" : "Mestre"}</b><small>{status}</small></span>
          <button className="secondary-button" onClick={() => setAccessPanelOpen(true)}>Trocar acesso</button>
        </section>
      ) : <section className="token-bar">
        <div className="mode-switch">
          <button
            className={mode === "gm" ? "active" : ""}
            onClick={() => {
              setMode("gm");
              setAccessMode("gm");
              navigate("session");
            }}
          >
            Mestre
          </button>
          <button
            className={mode === "player" ? "active" : ""}
            onClick={() => {
              setMode("player");
              setAccessMode("player");
              navigate("player");
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
        {authenticated && <button className="secondary-button" onClick={() => setAccessPanelOpen(false)}>Fechar</button>}
      </section>}

      <nav className="tabs" aria-label="Navegação principal">
        {mode === "gm" ? (
          <button className={page === "session" ? "active" : ""} onClick={() => navigate("session")}>
            <span>⌂</span><small>Mesa</small>
          </button>
        ) : (
          <button className={page === "player" ? "active" : ""} onClick={() => navigate("player")}>
            <span>⌂</span><small>Início</small>
          </button>
        )}
        <button className={page === "chat" ? "active" : ""} onClick={() => navigate("chat")}>
          <span>✦</span><small>Chat</small>
        </button>
        <button className={page === "sheet" ? "active" : ""} onClick={() => navigate("sheet")}>
          <span>♜</span><small>{mode === "gm" ? "Fichas" : "Ficha"}</small>
        </button>
        {mode === "gm" && (
          <button className={page === "curation" ? "active" : ""} onClick={() => navigate("curation")}>
            <span>⚗</span><small>Curadoria</small>
          </button>
        )}
        <button className={page === "search" || page === "note" ? "active" : ""} onClick={() => navigate("search")}>
          <span>⌕</span><small>Arquivo</small>
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
      {authenticated && page === "sheet" && <PlayableCharacterSheet key={`sheet-${authVersion}-${mode}`} mode={mode === "player" ? "player" : "gm"} />}
      {authenticated && page === "curation" && mode === "gm" && <ModelCurationPanel key={`curation-${authVersion}`} />}
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
      {authenticated && <QuickCharacterSheet hidden={page === "sheet"} onOpen={() => navigate("sheet")} />}
      {authenticated && <DiceTray key={`dice-${authVersion}-${mode}`} mode={mode === "player" ? "player" : "gm"} />}
    </main>
  );
}
