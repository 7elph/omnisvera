const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "..");
const app = fs.readFileSync(path.join(root, "src", "App.tsx"), "utf8");
const page = fs.readFileSync(path.join(root, "src", "pages", "CampaignMemoryPage.tsx"), "utf8");
const scene = fs.readFileSync(path.join(root, "src", "pages", "ScenePanel.tsx"), "utf8");
const workspace = fs.readFileSync(path.join(root, "src", "pages", "SessionWorkspace.tsx"), "utf8");
const styles = fs.readFileSync(path.join(root, "src", "styles.css"), "utf8");
const api = fs.readFileSync(path.join(root, "src", "api.ts"), "utf8");
const conclave = fs.readFileSync(path.join(root, "src", "pages", "ConclaveHub.tsx"), "utf8");

test("players and master share the narrative Session surface", () => {
  assert.match(app, /useState<Page>\(initialMode === "player" \? "conclave" : "session"\)/);
  assert.match(app, /setPage\(detectedMode === "player" \? "conclave" : "session"\)/);
  assert.match(app, /<CampaignMemoryPage[^>]+mode=\{mode\}/);
  assert.match(app, /mode === "gm" \? \([\s\S]*?<small>Mesa<\/small>[\s\S]*?\) : \([\s\S]*?<small>Sessão<\/small>/);
  assert.doesNotMatch(app, /<small>Início<\/small>/);
});

test("campaign memory is narrative and keeps GM structure collapsed", () => {
  assert.match(page, /ANTERIORMENTE EM OMNISVERA/);
  assert.match(page, /SESSÕES RECENTES/);
  assert.match(page, /HISTÓRIAS EM ANDAMENTO/);
  assert.match(page, /<details className="campaign-gm-layer">/);
  assert.doesNotMatch(page, /FIOS ESTACIONADOS/);
});

test("Session uses the same direct workspace shell as Mesa", () => {
  assert.match(app, /page === "conclave"[\s\S]*?`session-workspace unified-workspace campaign-memory-surface campaign-memory-\$\{campaignView\}`/);
  assert.match(page, /className="campaign-memory-layout"/);
  assert.match(page, /className="party-status-header campaign-memory-party-header"/);
  assert.match(page, /<span>AGORA<\/span>/);
  assert.match(page, /className="campaign-memory-now-bar"/);
  assert.match(page, /className="workspace-character-panel campaign-memory-current"/);
  assert.match(page, /className="workspace-timeline-panel campaign-memory-timeline"/);
  assert.doesNotMatch(page, /party-status-list|campaign-memory-grid/);
});

test("the view reuses campaign entities instead of a parallel inventory", () => {
  for (const call of ["listCampaignSessions", "listContracts", "listPlayableCharacters"]) {
    assert.match(page, new RegExp(`${call}\\(`));
  }
  assert.match(app, /view=\{page === "maps" \? "maps" : page === "scenes" \|\| \(page === "conclave"[\s\S]*?\? "memory" : "table"\}/);
  assert.doesNotMatch(page, /SessionWorkspace/);
  assert.doesNotMatch(page, /ReadOnlyCampaignMap|campaign-map-stage|const sessions\s*=\s*\[/);
  assert.doesNotMatch(page, /create(Session|Item|Reward|Character)/);
});

test("Mesa, Mapas, Sessão and Cenas keep one stable SessionWorkspace instance", () => {
  assert.equal((app.match(/<SessionWorkspace/g) || []).length, 1);
  assert.match(app, /key=\{`workspace-\$\{authVersion\}-\$\{mode\}`\}/);
  assert.match(app, /page === "scenes" \? "session-workspace unified-workspace scene-workspace-surface"/);
  assert.doesNotMatch(app, /workspace-\$\{authVersion\}-(gm|player|gm-maps)/);
});

test("player table exists only inside an active session and keeps only the owner sheet selectable", () => {
  assert.match(app, /const available = sessions\.some\(\(session\) => session\.status === "active"\)/);
  assert.match(app, /if \(!available\) setPlayerSessionView\("memory"\)/);
  assert.match(page, /const canOpenTable = mode === "gm" \|\| Boolean\(activeSession\)/);
  assert.match(page, /Aguardando Mestre/);
  assert.match(page, /const liveScene = activeSession \? activeScene : null/);
  assert.match(workspace, /const ownerId = ordered\.find\(\(item\) => item\.access_level === "owner"\)/);
  assert.match(workspace, /const selectable = mode === "gm" \|\| item\.access_level === "owner"/);
  assert.match(workspace, /mode === "player" && !preferred && currentSelection/);
  assert.match(workspace, /if \(mode !== "gm" && summary\?\.access_level !== "owner"\) return/);
  assert.match(workspace, /onClick=\{\(\) => void openTokenDetails\(token\)\}/);
  assert.match(page, /const ownerCharacterId = characters\.find\(\(character\) => character\.access_level === "owner"\)/);
  assert.match(page, /disabled=\{!canOpenCharacter\}/);
  assert.match(workspace, /initialSnapshot\.active_map_id !== activeMapIdRef\.current/);
  assert.match(workspace, /snapshot = await getSessionWorkspace\(\)/);
});

test("GM scene preparation uses the Mesa three-column shell and current map", () => {
  assert.match(app, /<ScenePanel[^>]+mode="gm" surface="admin"/);
  assert.match(scene, /className=\{surface === "admin" \? "scene-workspace-left"/);
  assert.match(scene, /surface === "live" && viewerMode === "player"[\s\S]*?active\?\.id/);
  assert.match(styles, /\.scene-workspace-surface\s*\{[\s\S]*?grid-template-areas: "header header header" "left map right"/);
  assert.match(styles, /\.scene-workspace-surface \.workspace-map-panel \{ grid-area: map/);
});

test("campaign status refreshes across clients and on mobile resume", () => {
  assert.match(page, /omnisvera-session-changed/);
  assert.match(page, /visibilitychange/);
  assert.match(page, /setInterval\(refresh, 10_000\)/);
  assert.match(app, /omnisvera-scene-updated/);
  assert.match(app, /omnisvera-session-changed/);
});

test("recent session cards come only from the backend chronology", () => {
  assert.match(page, /const latest = memories\.slice\(0, 4\)/);
  assert.match(page, /public_summary/);
  assert.match(page, /public_chronicle/);
  assert.doesNotMatch(page, /buildMemories\(sessions, scenes/);
});

test("contracts are the one operational mission source in both views", () => {
  assert.match(api, /function getCurrentOperationalContract/);
  assert.match(api, /status === "active"[\s\S]*status === "accepted"/);
  assert.match(page, /getCurrentOperationalContract\(contracts\)/);
  assert.match(conclave, /getCurrentOperationalContract\(contracts\)/);
  assert.doesNotMatch(page, /listGmQuests|listPlayerQuests|quests\.filter/);
});
