import { useEffect, useState } from "react";
import { AccessMode, consumeAccessBootstrapFromUrl, getAccessMode, getAccessToken, health, listCampaignSessions, rebuildIndex, recordRuntimeEvent, setAccessMode, setAccessToken } from "./api";
import SessionWorkspace from "./pages/SessionWorkspace";
import ScenePanel from "./pages/ScenePanel";
import CampaignMemoryPage from "./pages/CampaignMemoryPage";
import DiceRollOverlay from "./components/DiceRollOverlay";

type Page = "session" | "maps" | "conclave" | "scenes" | "game";
type CampaignView = "history" | "missions";
type PlayerSessionView = "memory" | "table";

function gameUrlWithCompanionIdentity(url: string, token: string, accessMode: AccessMode, profileId: string) {
  if (!token.trim()) return url;
  const [base, existingHash] = url.split("#", 2);
  const params = new URLSearchParams(existingHash || "");
  params.set("companion_token", token.trim());
  params.set("companion_mode", accessMode);
  params.set("companion_profile", profileId || (accessMode === "gm" ? "sage" : ""));
  return `${base}#${params.toString()}`;
}

function connectedStatus(data: { access_mode: string; player_character_title?: string | null; ollama_accessible: boolean; ollama_model: string }) {
  if (data.access_mode === "player") return `${data.player_character_title || "Jogador"} · sincronizado`;
  return `Mestre · Ollama ${data.ollama_accessible ? "ok" : "offline"} · ${data.ollama_model}`;
}

export default function App() {
  consumeAccessBootstrapFromUrl();
  const initialMode = getAccessMode();
  const initialToken = getAccessToken();
  const [page, setPage] = useState<Page>(initialMode === "player" ? "conclave" : "session");
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
  const [campaignView, setCampaignView] = useState<CampaignView>("history");
  const [playerSessionView, setPlayerSessionView] = useState<PlayerSessionView>("memory");
  const [playerLiveAvailable, setPlayerLiveAvailable] = useState(false);

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
          if (detectedMode === "player" && current !== "conclave") return "conclave";
          return current;
        });
        setStatus(connectedStatus(data));
      })
      .catch(() => {
        setAuthenticated(false);
        setStatus("token inválido ou backend indisponível");
      });
  }, []);

  useEffect(() => {
    if (!authenticated || mode !== "player") {
      setPlayerLiveAvailable(false);
      return;
    }
    let active = true;
    const refreshSessionState = async () => {
      try {
        const sessions = await listCampaignSessions();
        if (!active) return;
        const available = sessions.some((session) => session.status === "active");
        setPlayerLiveAvailable(available);
        if (!available) setPlayerSessionView("memory");
      } catch {
        // Keep the last known table state during a brief connection loss.
      }
    };
    void refreshSessionState();
    const timer = window.setInterval(() => void refreshSessionState(), 10_000);
    const refreshNow = () => void refreshSessionState();
    window.addEventListener("omnisvera-scene-updated", refreshNow);
    window.addEventListener("omnisvera-session-changed", refreshNow);
    window.addEventListener("online", refreshNow);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener("omnisvera-scene-updated", refreshNow);
      window.removeEventListener("omnisvera-session-changed", refreshNow);
      window.removeEventListener("online", refreshNow);
    };
  }, [authenticated, mode]);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [page]);

  useEffect(() => {
    const openWorkspace = (event: Event) => {
      const target = (event as CustomEvent<"maps" | "tools" | "table" | "scenes">).detail;
      if (mode === "player") {
        setPage("conclave");
        if (playerLiveAvailable && target !== "scenes") setPlayerSessionView("table");
        return;
      }
      if (target === "maps") setPage("maps");
      else if (target === "scenes") setPage("scenes");
      else {
        setPage("session");
        if (target === "tools") window.setTimeout(() => window.dispatchEvent(new CustomEvent("omnisvera-open-gm-tools")), 0);
      }
    };
    const openMap = () => {
      if (mode === "gm") setPage("maps");
      else {
        setPage("conclave");
        if (playerLiveAvailable) setPlayerSessionView("table");
      }
    };
    const viewCharacter = (event: Event) => {
      const characterId = String((event as CustomEvent<string>).detail || "");
      if (mode === "player") {
        setPage("conclave");
        if (playerLiveAvailable) setPlayerSessionView("table");
        return;
      }
      setPage("session");
      window.setTimeout(() => window.dispatchEvent(new CustomEvent("omnisvera-open-character", { detail: characterId })), 0);
    };
    window.addEventListener("omnisvera-open-workspace", openWorkspace);
    window.addEventListener("omnisvera-open-map", openMap);
    window.addEventListener("omnisvera-view-character", viewCharacter);
    return () => {
      window.removeEventListener("omnisvera-open-workspace", openWorkspace);
      window.removeEventListener("omnisvera-open-map", openMap);
      window.removeEventListener("omnisvera-view-character", viewCharacter);
    };
  }, [mode, playerLiveAvailable]);

  useEffect(() => {
    if (!authenticated || mode !== "player") return;
    const labels: Record<Page, string> = { session: "Mesa", maps: "Mapas", conclave: "Sessão", scenes: "Cenas", game: "Jogar" };
    void recordRuntimeEvent("navigation_view", {
      page,
      label: labels[page],
      device: window.innerWidth <= 720 ? "celular" : "desktop",
      online: navigator.onLine,
      path: window.location.pathname,
    }).catch(() => undefined);
  }, [authenticated, mode, page]);

  useEffect(() => {
    if (!authenticated) return;
    const offline = () => setStatus("sem conexão · mantendo a tela atual");
    const online = () => {
      setStatus("conexão restaurada · sincronizando");
      if (mode === "player") void recordRuntimeEvent("reconnected", {
        page,
        label: "Companion",
        device: window.innerWidth <= 720 ? "celular" : "desktop",
      }).catch(() => undefined);
      void health().then(() => setStatus(mode === "player" ? "Jogador · sincronizado" : "Mestre · sincronizado")).catch(() => undefined);
    };
    window.addEventListener("offline", offline);
    window.addEventListener("online", online);
    return () => { window.removeEventListener("offline", offline); window.removeEventListener("online", online); };
  }, [authenticated, mode, page]);

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
        setPage(detectedMode === "player" ? "conclave" : "session");
        setPlayerSessionView("memory");
        setStatus(connectedStatus(data));
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

  return (
    <main className={`app-shell ${authenticated ? "authenticated" : ""}`}>
      <header className="hero app-title-bar">
        <h1>OMNISVERA</h1>
        {authenticated && !accessPanelOpen && (
          <section className="access-summary">
            <span><b>{mode === "player" ? "Jogador" : "Mestre"}</b><small>{status}</small></span>
            <div className="access-summary-actions"><button className="secondary-button" onClick={() => setAccessPanelOpen(true)}>Trocar acesso</button></div>
          </section>
        )}
      </header>

      {(!authenticated || accessPanelOpen) && <section className="token-bar">
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
              navigate("conclave");
              setPlayerSessionView("memory");
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
          <button className={page === "conclave" ? "active" : ""} onClick={() => { navigate("conclave"); setPlayerSessionView("memory"); }}>
            <span>◉</span><small>Sessão</small>
          </button>
        )}
        {mode === "gm" && <button className={page === "maps" ? "active" : ""} onClick={() => navigate("maps")}>
          <span>▧</span><small>Mapas</small>
        </button>}
        {mode === "gm" && <button className={page === "conclave" ? "active" : ""} onClick={() => navigate("conclave")}>
          <span>◉</span><small>Sessão</small>
        </button>}
        {mode === "gm" && <button className={page === "scenes" ? "active" : ""} onClick={() => navigate("scenes")}>
          <span>✦</span><small>Cenas</small>
        </button>}
        {mode === "gm" && gameWebUrl && (
          <button className={page === "game" ? "active" : ""} onClick={() => navigate("game")}>
            <span>▶</span><small>Jogar</small>
          </button>
        )}
        {mode === "gm" && (
          <button className="gm-tools-tab" onClick={() => { navigate("session"); window.setTimeout(() => window.dispatchEvent(new CustomEvent("omnisvera-open-gm-tools")), 0); }}>
            <span>⚙</span><small>Mestre</small>
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
      {authenticated && ((mode === "gm" && ["session", "maps", "conclave", "scenes"].includes(page)) || (mode === "player" && page === "conclave")) && (
        <section className={page === "scenes" ? "session-workspace unified-workspace scene-workspace-surface" : page === "conclave" && (mode === "gm" || playerSessionView === "memory") ? `session-workspace unified-workspace campaign-memory-surface campaign-memory-${campaignView}` : "workspace-surface"}>
          <SessionWorkspace
            key={`workspace-${authVersion}-${mode}`}
            mode={mode}
            view={page === "maps" ? "maps" : page === "scenes" || (page === "conclave" && (mode === "gm" || playerSessionView === "memory")) ? "memory" : "table"}
          />
          {page === "conclave" && (mode === "gm" || playerSessionView === "memory") && <CampaignMemoryPage key={`campaign-memory-${authVersion}-${mode}`} mode={mode} view={campaignView} onViewChange={setCampaignView} />}
          {page === "scenes" && mode === "gm" && <ScenePanel key={`scene-admin-${authVersion}`} mode="gm" surface="admin" />}
        </section>
      )}
      {authenticated && mode === "gm" && page === "game" && gameWebUrl && (
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
      <DiceRollOverlay enabled={authenticated} />
    </main>
  );
}
