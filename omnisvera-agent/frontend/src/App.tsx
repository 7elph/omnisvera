import { useEffect, useState } from "react";
import { AccessMode, getAccessMode, getAccessToken, health, rebuildIndex, setAccessMode, setAccessToken } from "./api";
import ConclaveHub from "./pages/ConclaveHub";
import SessionWorkspace from "./pages/SessionWorkspace";
import DiceRollOverlay from "./components/DiceRollOverlay";

type Page = "session" | "player" | "conclave" | "game";

function gameUrlWithCompanionIdentity(url: string, token: string, accessMode: AccessMode, profileId: string) {
  if (!token.trim()) return url;
  const [base, existingHash] = url.split("#", 2);
  const params = new URLSearchParams(existingHash || "");
  params.set("companion_token", token.trim());
  params.set("companion_mode", accessMode);
  params.set("companion_profile", profileId || (accessMode === "gm" ? "sage" : ""));
  return `${base}#${params.toString()}`;
}

export default function App() {
  const initialMode = getAccessMode();
  const initialToken = getAccessToken();
  const [page, setPage] = useState<Page>(initialMode === "player" ? "player" : "session");
  const [status, setStatus] = useState<string>("");
  const [tokenDraft, setTokenDraft] = useState<string>(initialToken);
  const [mode, setMode] = useState<AccessMode>(initialMode);
  const [authVersion, setAuthVersion] = useState(0);
  const [authenticated, setAuthenticated] = useState(false);
  const [accessPanelOpen, setAccessPanelOpen] = useState(!initialToken);
  // Do not boot Godot before the Companion validates the saved token.
  // Otherwise the game can start anonymously with its scene default (Vezemir)
  // and the first visual may be captured before identity/animation setup.
  const [gameWebUrl, setGameWebUrl] = useState("");
  const [gameFullscreen, setGameFullscreen] = useState(false);

  const toggleGameFullscreen = async () => {
    const frame = document.querySelector<HTMLIFrameElement>(".game-frame");
    if (!frame) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await frame.requestFullscreen();
    } catch {
      setStatus("O navegador bloqueou a tela cheia; use o menu do navegador.");
    }
  };

  useEffect(() => {
    const syncFullscreen = () => setGameFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  useEffect(() => {
    // Keep the embedded Godot runtime on the phone after the first download.
    // The worker is scoped only to /nimalis/, so it cannot affect Companion
    // API calls or the rest of the site.
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/nimalis/sw.js", { scope: "/nimalis/" }).catch(() => {
        // The game remains playable without caching when the browser blocks SW.
      });
    }

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
        setGameWebUrl(gameUrlWithCompanionIdentity(
          typeof data.game_web_url === "string" ? data.game_web_url : "/nimalis/nimalis.html",
          token,
          detectedMode,
          detectedMode === "gm" ? "sage" : (data.player_profile_id || ""),
        ));
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
  }, [page]);

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
        setGameWebUrl(gameUrlWithCompanionIdentity(
          typeof data.game_web_url === "string" ? data.game_web_url : "/nimalis/nimalis.html",
          tokenDraft,
          detectedMode,
          detectedMode === "gm" ? "sage" : (data.player_profile_id || ""),
        ));
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

  function navigate(next: Page) {
    setPage(next);
  }

  function openScenePanel(sceneId?: number) {
    if (sceneId) localStorage.setItem("omnisvera_selected_scene", String(sceneId));
    navigate(mode === "gm" ? "session" : "player");
  }

  return (
    <main className={`app-shell ${authenticated ? "authenticated" : ""}`}>
      <header className="hero">
        <h1>OMNISVERA</h1>
      </header>

      {authenticated && !accessPanelOpen ? (
        <section className="access-summary">
          <span><b>{mode === "player" ? "Jogador" : "Mestre"}</b><small>{status}</small></span>
          <div className="access-summary-actions"><button className="secondary-button" onClick={() => setAccessPanelOpen(true)}>Trocar acesso</button></div>
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
        <button className={page === "conclave" ? "active" : ""} onClick={() => navigate("conclave")}>
          <span>◈</span><small>Conclave</small>
        </button>
        {gameWebUrl && (
          <button className={page === "game" ? "active" : ""} onClick={() => navigate("game")}>
            <span>▶</span><small>Jogar</small>
          </button>
        )}
      </nav>

      {!authenticated && page !== "game" && (
        <section className="panel">
          <div className="chat-header">
            <h2>Token necessário</h2>
            <p>Digite o token de acesso no campo acima e clique em "Salvar token" para começar.</p>
          </div>
        </section>
      )}
      {authenticated && page === "session" && mode === "gm" && <SessionWorkspace key={`workspace-${authVersion}-gm`} mode="gm" />}
      {authenticated && page === "player" && mode === "player" && <SessionWorkspace key={`workspace-${authVersion}-player`} mode="player" />}
      {authenticated && page === "conclave" && <ConclaveHub key={`conclave-${authVersion}-${mode}`} mode={mode === "player" ? "player" : "gm"} onOpenScene={openScenePanel} />}
      {authenticated && page === "game" && gameWebUrl && (
        <section className="panel game-panel">
          <div className="chat-header">
            <h2>Nimalis</h2>
            <button className="game-fullscreen-button" type="button" onClick={toggleGameFullscreen}>
              {gameFullscreen ? "Sair da tela cheia" : "Tela cheia"}
            </button>
            <p>Jogo conectado ao Companion. O mesmo token permanece válido dentro do jogo.</p>
          </div>
          <iframe key={gameWebUrl} title="Nimalis" src={gameWebUrl} className="game-frame" allow="fullscreen" allowFullScreen />
        </section>
      )}
      <DiceRollOverlay />
    </main>
  );
}
