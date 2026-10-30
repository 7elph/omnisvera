const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync('src/App.tsx', 'utf8');
const flush = async () => { for (let i = 0; i < 25; i++) await Promise.resolve(); };
test('startup failure status remains visible before authentication succeeds', () => {
  assert.match(source, /<h2>Token necessário<\/h2>\s*<p role="status">\{status/);
});
function harness(health) {
  const marker = source.indexOf('    // Keep the embedded Godot');
  const start = source.lastIndexOf('  useEffect(() => {', marker), end = source.indexOf('  }, []);', marker) + '  }, []);'.length;
  assert.ok(start >= 0 && end > start);
  const events = new Map(), visibility = new Map();
  let cleanup, poll;
  const c = {
    navigator: {}, document: { visibilityState: 'visible', addEventListener: (name, fn) => visibility.set(name, fn), removeEventListener: name => visibility.delete(name) },
    window: { addEventListener: (name, fn) => events.set(name, fn), removeEventListener: name => events.delete(name), setInterval: fn => { poll = fn; return 1; }, clearInterval() {} },
    useEffect: fn => { cleanup = fn(); }, health, Error,
    HttpError: class extends Error { constructor(status) { super('HTTP'); this.status = status; } },
    token: 'test-local', getAccessToken: () => c.token,
    setAuthenticated: value => { c.authenticated = value; }, setStatus: value => { c.status = value; },
    setMode: value => { c.mode = value; }, setAccessMode() {}, setGameWebUrl() {}, setPage() {},
    gameUrlWithCompanionIdentity: () => '', connectedStatus: () => 'synchronized',
  };
  vm.runInNewContext(ts.transpileModule(source.slice(start, end), {}).outputText, c);
  return { c, events, visibility, poll: () => poll(), cleanup: () => cleanup() };
}
test('temporary startup failure recovers with saved access without reload or repeated successful authentication', async () => {
  let calls = 0;
  const h = harness(async () => { if (++calls === 1) throw new Error('offline'); return { access_mode: 'player' }; });
  await flush(); assert.equal(h.c.authenticated, false); assert.match(h.c.status, /reconectar/);
  h.events.get('online')(); await flush();
  assert.equal(h.c.authenticated, true); assert.equal(h.c.mode, 'player');
  h.poll(); h.events.get('focus')(); await flush(); assert.equal(calls, 2);
});
test('pending startup checks do not overlap and an invalid credential is never retried automatically', async () => {
  let calls = 0, reject;
  const h = harness(() => { calls++; return new Promise((yes, no) => { reject = no; }); });
  h.poll(); h.events.get('online')(); assert.equal(calls, 1);
  reject(new h.c.HttpError(401)); await flush();
  h.poll(); h.events.get('focus')(); await flush();
  assert.equal(calls, 1); assert.match(h.c.status, /Token inválido/);
});
test('old startup response cannot authenticate a changed token or an unmounted app', async () => {
  let resolve;
  const h = harness(() => new Promise(done => { resolve = done; }));
  h.c.token = 'changed'; resolve({ access_mode: 'gm' }); await flush();
  assert.notEqual(h.c.authenticated, true);
  const other = harness(() => new Promise(done => { resolve = done; }));
  other.cleanup(); resolve({ access_mode: 'gm' }); await flush();
  assert.notEqual(other.c.authenticated, true); assert.equal(other.events.size, 0); assert.equal(other.visibility.size, 0);
});
