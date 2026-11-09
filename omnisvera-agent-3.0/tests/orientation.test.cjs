const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const shell = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');

function policy({ fullscreen = true, lock = true, active = false } = {}) {
  const source = shell.match(/<script id="landscape-policy">([\s\S]*?)<\/script>/);
  assert.ok(source, 'Web shell must provide the mobile landscape policy');
  const calls = [];
  const button = { disabled: false, addEventListener: (_event, callback) => { button.click = callback; } };
  const hint = { textContent: '' };
  const root = fullscreen ? { requestFullscreen: async () => { calls.push('fullscreen'); } } : {};
  const orientation = lock ? { lock: async direction => { calls.push(direction); } } : {};
  const document = { getElementById: id => id === 'enter-landscape' ? button : hint,
    documentElement: root, fullscreenElement: active ? root : null };
  vm.runInNewContext(source[1], { document, screen: { orientation } });
  return { button, hint, calls, orientation };
}

test('landscape lock is requested only after a user gesture, following fullscreen', async () => {
  const env = policy();
  assert.deepEqual(env.calls, []);
  await env.button.click();
  assert.deepEqual(env.calls, ['fullscreen', 'landscape']);
  assert.equal(env.button.disabled, false);
});

test('unsupported or rejected browser APIs retain the rotate-device fallback', async () => {
  for (const options of [{ fullscreen: false, lock: false }, {}]) {
    const env = policy(options);
    env.orientation.lock = async () => { throw new Error('NotAllowedError'); };
    await env.button.click();
    assert.match(env.hint.textContent, /Gire o celular/);
    assert.equal(env.button.disabled, false);
  }
});

test('an existing fullscreen session is reused', async () => {
  const env = policy({ active: true });
  await env.button.click();
  assert.deepEqual(env.calls, ['landscape']);
});

test('native Godot defaults to landscape', () => {
  const project = fs.readFileSync(path.join(__dirname, '../project.godot'), 'utf8');
  assert.match(project, /window\/handheld\/orientation=0/);
});
