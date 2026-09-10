const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "..");
const apiSource = fs.readFileSync(path.join(root, "src", "api.ts"), "utf8");
const appSource = fs.readFileSync(path.join(root, "src", "App.tsx"), "utf8");
const stylesSource = fs.readFileSync(path.join(root, "src", "styles.css"), "utf8");

test("player access can be bootstrapped from a URL fragment", () => {
  assert.match(apiSource, /consumeAccessBootstrapFromUrl/);
  assert.match(apiSource, /params\.get\("token"\)/);
  assert.match(apiSource, /setAccessToken\(token\)/);
  assert.match(apiSource, /setAccessMode\(mode\)/);
  assert.match(appSource, /consumeAccessBootstrapFromUrl\(\)/);
});

test("bootstrap credential is removed from the address bar", () => {
  assert.match(apiSource, /params\.delete\(key\)/);
  assert.match(apiSource, /window\.history\.replaceState/);
});

test("player status reports Companion synchronization instead of Ollama availability", () => {
  assert.match(appSource, /player_character_title \|\| "Jogador"} · sincronizado/);
  assert.match(appSource, /Mestre · Ollama/);
});

test("title, access role and runtime status share one header line", () => {
  assert.match(appSource, /<header className="hero app-title-bar">[\s\S]*?<h1>OMNISVERA<\/h1>[\s\S]*?className="access-summary"/);
  assert.doesNotMatch(appSource, /<\/header>\s*\{authenticated && !accessPanelOpen \? \(/);
  assert.match(stylesSource, /\.app-shell > \.hero \.access-summary \{[\s\S]*?background: transparent;[\s\S]*?border-radius: 0;[\s\S]*?box-shadow: none;/);
});
