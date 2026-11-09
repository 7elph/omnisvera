const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium, request } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES] }));

(async () => {
  const fixture = JSON.parse(fs.readFileSync(process.env.COMPANION3_FIXTURE, 'utf8'));
  assert.equal(fixture.synthetic, true);
  const output = fixture.directory;
  const base = process.env.COMPANION3_URL;
  assert.equal(new URL(base).hostname, '127.0.0.1');
  const report = { status: 'RUNNING', source: 'synthetic', checks: [], errors: [], screenshots: [] };
  const browser = await chromium.launch({
    headless: true, channel: 'chrome',
    args: ['--enable-unsafe-swiftshader'],
  });
  const gmApi = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  const nativeCommands = await request.newContext({ baseURL: 'http://127.0.0.1:8891', extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  const playerApi = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-vezemir' } });
  const call = async (api, method, url, data) => {
    const response = await api[method](url, { data });
    assert.ok(response.ok(), await response.text());
    return response.json();
  };
  async function pageFor(identity, width, height) {
    const context = await browser.newContext({ viewport: { width, height }, isMobile: Math.min(width, height) < 600, hasTouch: Math.min(width, height) < 600 });
    const page = await context.newPage();
    page.setDefaultTimeout(25000);
    const reads = [];
    page.on('response', response => {
      if (/\/(characters|workspace|sessions|media)(\/|\?|$)/.test(response.url())) {
        reads.push({ url: new URL(response.url()).pathname + new URL(response.url()).search, status: response.status() });
      }
    });
    page.on('console', message => {
      const text = message.text();
      if (message.type() === 'error' || message.type() === 'warning') console.log('BROWSER', text);
      if (/SCRIPT ERROR|Parse Error|Invalid call|Failed to load script|Failed to instantiate|ERROR:/.test(text)) report.errors.push(text);
    });
    page.on('pageerror', error => report.errors.push(error.message));
    await page.goto(base + '/#token=cf01-local-' + identity);
    await page.locator('#loading').waitFor({ state: 'detached', timeout: 60000 });
    await page.waitForFunction(() => location.hash === '');
    const deadline = Date.now() + 45000;
    while (!reads.some(r => r.url === '/workspace' && r.status === 200) && Date.now() < deadline) {
      await page.waitForTimeout(250);
    }
    while (!reads.some(r => /^\/characters\/[^?]+\?read_only=true$/.test(r.url) && r.status === 200) && Date.now() < deadline) {
      await page.waitForTimeout(250);
    }
    return { page, context, reads };
  }
  async function screenshot(page, name) {
    const file = path.join(output, name);
    await page.screenshot({ path: file });
    report.screenshots.push(file);
  }
  try {
    await call(playerApi, 'post', '/workspace/heartbeat', {});
    const desktop = await pageFor('gm', 1440, 900);
    await screenshot(desktop.page, 'godot-desktop-startup.png');
    console.log('INITIAL_READS', JSON.stringify(desktop.reads));
    assert.ok(desktop.reads.some(r => r.url === '/characters?read_only=true' && r.status === 200));
    assert.ok(desktop.reads.some(r => r.url === '/characters/vezemir?read_only=true' && r.status === 200));
    const wasm = await desktop.page.request.get(base + '/index.wasm');
    assert.equal(wasm.headers()['content-type'], 'application/wasm');
    await screenshot(desktop.page, 'godot-desktop-world.png');
    // Native floating Ficha button, positioned by the Godot viewport layout.
    await desktop.page.mouse.click(35, 35);
    await desktop.page.waitForTimeout(1600);
    await screenshot(desktop.page, 'godot-desktop-sheet.png');
    await desktop.page.keyboard.press('Escape');
    await desktop.page.mouse.move(720, 490);
    await desktop.page.mouse.wheel(0, -240);
    await desktop.page.mouse.down();
    await desktop.page.mouse.move(820, 530, { steps: 12 });
    await desktop.page.mouse.up();
    await screenshot(desktop.page, 'godot-desktop-pan-zoom.png');
    report.checks.push('Godot WebAssembly initialized at origin root', 'authenticated native character reads use read_only',
      'desktop native Ficha panel opened; Escape, zoom and pan exercised');
    const world = await call(gmApi, 'get', '/workspace');
    const dorn = world.tokens.find(token => token.character_id === 'dorn7');
    assert.ok(dorn?.grid_position);
    const start = dorn.grid_position;
    await call(nativeCommands, 'post', '/workspace/maps/default/move', {
      request_id: 'companion3-confirmed-reposition-test',
      token_id: dorn.id, mode: 'GM_REPOSITION',
      path: [[start.cell_x, start.cell_y], [start.cell_x + 1, start.cell_y]],
      expected_position_version: start.version, expected_grid_version: world.map.grid.version,
    });
    await desktop.page.waitForTimeout(9000);
    await screenshot(desktop.page, 'godot-confirmed-position.png');
    await call(nativeCommands, 'post', '/characters/vezemir/actions', {
      action: 'damage', request_id: 'companion3-fixture-hp-update', payload: { amount: 3 },
    });
    const refreshed = desktop.page.waitForResponse(response =>
      response.url().includes('/characters/vezemir?read_only=true') && response.status() === 200);
    await desktop.page.mouse.click(35, 35);
    assert.equal((await (await refreshed).json()).state.current_hp, 24);
    await desktop.page.waitForTimeout(500);
    await screenshot(desktop.page, 'godot-desktop-updated-sheet.png');
    await desktop.page.keyboard.press('Escape');
    await desktop.page.mouse.click(1230, 809);
    await desktop.page.keyboard.type('Mensagem do Godot no ensaio isolado');
    const delivered = desktop.page.waitForResponse(response =>
      response.url().endsWith('/workspace/messages') && response.status() === 200);
    await desktop.page.keyboard.press('Enter');
    await delivered;
    const messages = await call(gmApi, 'get', '/workspace/ledger?limit=80');
    assert.equal(messages.filter(event => event.title.includes('Mensagem do Godot no ensaio isolado')).length, 1);
    report.checks.push('backend confirmed native grid position update while Godot scene stayed mounted');
    report.checks.push('native sheet refreshed confirmed HP from 27 to 24', 'Godot message entered the existing ledger exactly once');
    await call(playerApi, 'post', '/workspace/heartbeat', {});
    const mobile = await pageFor('vezemir', 390, 844);
    await mobile.page.locator('#landscape-guide').waitFor({ state: 'visible' });
    assert.equal(await mobile.page.locator('#enter-landscape').isEnabled(), true);
    await screenshot(mobile.page, 'godot-mobile-rotate.png');
    await mobile.page.setViewportSize({ width: 844, height: 390 });
    await mobile.page.locator('#landscape-guide').waitFor({ state: 'hidden' });
    await mobile.page.waitForTimeout(800);
    assert.ok(mobile.reads.some(r => r.url === '/characters/vezemir?read_only=true' && r.status === 200));
    const publicWorld = await call(playerApi, 'get', '/workspace');
    assert.equal(publicWorld.tokens.some(token => token.name === 'GM_HIDDEN_COMPANION3'), false);
    assert.ok(publicWorld.presence.some(user => user.character_id === 'vezemir' && user.online));
    const publicLedger = await call(playerApi, 'get', '/workspace/ledger?limit=80');
    assert.equal(JSON.stringify(publicLedger).includes('GM_PRIVATE_COMPANION3'), false);
    const publicDorn = await call(playerApi, 'get', '/characters/dorn7?read_only=true');
    assert.equal(Boolean(publicDorn.state), false);
    assert.deepEqual(publicDorn.inventory, []);
    await screenshot(mobile.page, 'godot-mobile-world.png');
    await mobile.page.touchscreen.tap(35, 49);
    await mobile.page.waitForTimeout(1200);
    await screenshot(mobile.page, 'godot-mobile-sheet.png');
    await mobile.page.keyboard.press('Escape');
    await mobile.page.touchscreen.tap(35, 275);
    await mobile.page.waitForTimeout(800);
    await screenshot(mobile.page, 'godot-mobile-map-library.png');
    const publicMaps = await call(playerApi, 'get', '/workspace/maps');
    assert.equal(publicMaps.some(map => map.id === fixture.private_map), false);
    const chosenMapIndex = publicMaps.findIndex(map => map.id === fixture.public_map);
    assert.ok(chosenMapIndex >= 0);
    const mapRead = mobile.page.waitForResponse(response => response.url().includes('/workspace?map_id=') && response.status() === 200);
    await mobile.page.touchscreen.tap(240, 122 + chosenMapIndex * 80);
    const mapSnapshot = await (await mapRead).json();
    assert.equal(mapSnapshot.map.id, fixture.public_map);
    assert.equal(mapSnapshot.tokens.some(pin => pin.name === 'GM_HIDDEN_MAP_PIN'), false);
    assert.equal(mapSnapshot.fog.exploration.mist_density['0:0'], 1);
    await mobile.page.waitForTimeout(2000);
    await screenshot(mobile.page, 'godot-mobile-existing-map-pins.png');
    await mobile.page.touchscreen.tap(453, 195);
    await mobile.page.waitForTimeout(800);
    await screenshot(mobile.page, 'godot-mobile-pin-details.png');
    await mobile.page.keyboard.press('Escape');
    await mobile.page.mouse.move(310, 150);
    await mobile.page.mouse.down();
    await mobile.page.mouse.move(350, 170, { steps: 6 });
    await mobile.page.mouse.up();
    await mobile.page.mouse.wheel(0, -120);
    await mobile.page.waitForTimeout(600);
    await screenshot(mobile.page, 'godot-mobile-floating-map-pan-zoom.png');
    const afterView = await call(playerApi, 'get', '/workspace?map_id=' + encodeURIComponent(fixture.public_map));
    assert.deepEqual(afterView.tokens.map(pin => [pin.id, pin.latitude, pin.longitude]),
      mapSnapshot.tokens.map(pin => [pin.id, pin.latitude, pin.longitude]));
    await mobile.page.keyboard.press('Escape');
    await mobile.page.touchscreen.tap(35, 323);
    await mobile.page.waitForTimeout(1000);
    await screenshot(mobile.page, 'godot-mobile-sessions.png');
    const sessionRead = mobile.page.waitForResponse(response => response.url().includes('/sessions/' + fixture.session_id) && response.status() === 200);
    await mobile.page.touchscreen.tap(240, 122);
    const session = await (await sessionRead).json();
    assert.equal(session.private_notes, undefined);
    assert.equal(JSON.stringify(session).includes('GM_PRIVATE_SESSION_COMPANION3'), false);
    await mobile.page.waitForTimeout(1500);
    await screenshot(mobile.page, 'godot-mobile-session-summary.png');
    await mobile.page.keyboard.press('Escape');
    await mobile.page.setViewportSize({ width: 390, height: 844 });
    await mobile.page.locator('#landscape-guide').waitFor({ state: 'visible' });
    await mobile.page.setViewportSize({ width: 844, height: 390 });
    await mobile.page.locator('#landscape-guide').waitFor({ state: 'hidden' });
    await mobile.page.touchscreen.tap(35, 49);
    await mobile.page.waitForTimeout(800);
    await screenshot(mobile.page, 'godot-mobile-sheet-after-rotation.png');
    await mobile.page.keyboard.press('Escape');
    await mobile.page.reload();
    await mobile.page.locator('#loading').waitFor({ state: 'detached', timeout: 60000 });
    await mobile.page.waitForTimeout(1500);
    // Fragment token is deliberately not saved. Reload requires access again.
    assert.equal(await mobile.page.evaluate(() => localStorage.getItem('omnisvera_access_token')), null);
    report.checks.push('portrait rotate prompt, 844x390 landscape touch sheet and repeated rotation exercised', 'presence comes from native heartbeat',
      'hidden NPC and GM ledger event excluded by backend', 'fragment consumed and credentials absent from persistent storage',
      'left drawers, transparent larger touch icons and real portrait media exercised',
      'existing map library, authorized pins and fog loaded; private map and pin excluded',
      'session chronology and illustrated public summary opened without private notes');
    assert.equal(report.errors.length, 0, report.errors.join('\n'));
    report.status = 'PASS';
  } finally {
    await browser.close();
    await gmApi.dispose();
    await nativeCommands.dispose();
    await playerApi.dispose();
    fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
