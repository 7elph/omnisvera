const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };

function harness(fetch) {
  const modules = new Map(), deadlines = new Map(), reconnects = new Map(), intervals = new Map(), sockets = [], events = [];
  let counter = 0, now = 0;
  class FakeSocket {
    static OPEN = 1;
    readyState = 0;
    constructor(url) { this.url = url; this.sent = []; sockets.push(this); }
    open() { this.readyState = 1; this.onopen?.(); }
    message(data) { this.onmessage?.({ data }); }
    send(value) { this.sent.push(value); }
    close() { this.readyState = 3; this.onclose?.(); }
  }
  const window = {
    location: { origin: 'http://127.0.0.1:8871', href: 'http://127.0.0.1:8871/' },
    setTimeout: fn => { reconnects.set(++counter, fn); return counter; }, clearTimeout: id => reconnects.delete(id),
    setInterval: fn => { intervals.set(++counter, fn); return counter; }, clearInterval: id => intervals.delete(id),
    dispatchEvent: event => events.push(event),
  };
  function load(filename) {
    if (modules.has(filename)) return modules.get(filename).exports;
    const module = { exports: {} }; modules.set(filename, module);
    const source = fs.readFileSync(filename, 'utf8').replaceAll('import.meta.env.VITE_API_BASE_URL', '""');
    vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, {
      module, exports: module.exports, fetch, AbortController, URL, WebSocket: FakeSocket, window,
      Date: { now: () => now }, localStorage: { getItem: () => '' },
      setTimeout: fn => { deadlines.set(++counter, fn); return counter; }, clearTimeout: id => deadlines.delete(id),
      CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
      require: name => load(path.resolve(path.dirname(filename), name + '.ts')),
    });
    return module.exports;
  }
  return { api: load(path.resolve('src/api.ts')), deadlines, reconnects, intervals, sockets, events, clock: value => { now = value; } };
}

test('a stalled realtime ticket body times out and recovery can be stopped', async () => {
  let signal;
  const h = harness(async (_, options) => { signal = options.signal; return { ok: true, json: () => new Promise(() => {}) }; });
  const pending = h.api.connectSessionRealtime(() => {});
  await flush(); assert.equal(h.deadlines.size, 1);
  [...h.deadlines.values()][0]();
  const stop = await pending;
  assert.equal(signal.aborted, true); assert.equal(h.reconnects.size, 1);
  stop(); assert.equal(h.reconnects.size, 0); assert.equal(h.deadlines.size, 0);
});

test('realtime connection refreshes missed state immediately and dispatches only real changes', async () => {
  const h = harness(async () => ({ ok: true, json: async () => ({ ticket: 'local-test-ticket' }) }));
  const versions = [];
  const stop = await h.api.connectSessionRealtime(value => versions.push(value));
  h.sockets[0].open();
  h.sockets[0].message(JSON.stringify({ type: 'connected', ledger_id: 42 }));
  assert.deepEqual(versions, [42]); assert.equal(h.events.length, 0);
  h.sockets[0].message(JSON.stringify({ type: 'session_changed', ledger_id: 43 }));
  assert.deepEqual(versions, [42, 43]); assert.equal(h.events.length, 1);
  stop(); assert.equal(h.reconnects.size, 0); assert.equal(h.intervals.size, 0);
});

test('a socket without pong is closed and reconnects instead of appearing connected forever', async () => {
  const h = harness(async () => ({ ok: true, json: async () => ({ ticket: 'local-test-ticket' }) }));
  const stop = await h.api.connectSessionRealtime(() => {});
  const socket = h.sockets[0]; socket.open();
  h.clock(10_000); [...h.intervals.values()][0]();
  assert.deepEqual(socket.sent, ['ping']);
  socket.message('pong');
  h.clock(36_000); [...h.intervals.values()][0]();
  assert.equal(socket.readyState, 1, 'recent pong keeps a healthy connection');
  h.clock(46_000); [...h.intervals.values()][0]();
  assert.equal(socket.readyState, 3); assert.equal(h.reconnects.size, 1);
  stop(); assert.equal(h.reconnects.size, 0);
});
