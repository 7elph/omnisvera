// Read-only Cenas UI acceptance against a proven TEMP fixture; no live credentials.
const assert = require('node:assert/strict'), fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const { chromium, request } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
(async () => {
  const base = process.env.OMNISVERA_SHEET_QA_URL;
  assert.match(base || '', /^http:\/\/127\.0\.0\.1:\d+$/);
  assert.ok(![8787, 8788].includes(Number(new URL(base).port)));
  const api = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  const get = async url => { const r = await api.get(url); assert.ok(r.ok(), `${url}: ${r.status()}`); return r.json(); };
  const health = await get('/health');
  for (const value of [health.database_path, health.vault_path])
    assert.ok(path.resolve(value).startsWith(path.resolve(os.tmpdir()) + path.sep), 'TEMP database and Vault required');
  const scenes = await get('/scenes');
  const scene = scenes.find(s => s.status === 'draft' && s.map_id && s.participants.length && s.elements.length)
    || scenes.find(s => s.map_id && s.participants.length && s.elements.length);
  assert.ok(scene, 'Existing preparation with map, participants and elements required');
  const before = await get('/workspace'), combatBefore = await get('/combat/effects');
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'omni-scene-context-'));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const screenshots = [], errors = [], writes = [], checks = [];
  const contexts = ['Exploração', 'Combate', 'Conversa', 'Comércio', 'Investigação', 'Viagem / descanso'];
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, isMobile: width === 390, hasTouch: width === 390 });
      await context.addInitScript(id => {
        localStorage.setItem('omnisvera_access_token', 'cf01-local-gm');
        localStorage.setItem('omnisvera_access_mode', 'gm');
        localStorage.setItem('omnisvera_selected_scene', String(id));
      }, scene.id);
      const page = await context.newPage(); page.setDefaultTimeout(15000);
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => { if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method())
        && /\/(gm\/(scenes|workspace)|combat|characters\/[^/]+\/actions)/.test(new URL(r.url()).pathname)) writes.push(new URL(r.url()).pathname); });
      await page.goto(base); await page.locator('.app-shell.authenticated').waitFor();
      await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Cenas$/ }).click();
      const viewer = page.getByRole('region', { name: `Preparação: ${scene.title}`, exact: true }); await viewer.waitFor();
      const sequence = page.getByLabel('Sequência de preparações', { exact: true });
      assert.ok((await sequence.boundingBox()).height < 340, 'Preparation sequence must stay compact');
      const sequenceShot = path.join(output, `sequence-${width}.png`); await sequence.screenshot({ path: sequenceShot }); screenshots.push(sequenceShot);
      const mapCard = viewer.locator('.scene-context-content .scene-map-card'); await mapCard.waitFor();
      const thumb = await mapCard.boundingBox(); assert.ok(thumb.width < 360 && thumb.height < 240, 'Map is a compact card');
      assert.equal(await viewer.locator('.scene-map-preview').count(), 0);
      await mapCard.locator('.scene-asset-inspect').click();
      const dialog = page.locator('dialog.scene-map-dialog'); await dialog.waitFor();
      assert.ok((await dialog.boundingBox()).width <= width);
      const viewport = dialog.locator('.scene-map-preview-viewport'), size = await viewport.boundingBox();
      await dialog.getByRole('button', { name: 'Ampliar prévia', exact: true }).click();
      await dialog.getByRole('button', { name: 'Ampliar prévia', exact: true }).click();
      assert.ok(Math.abs(size.height - (await viewport.boundingBox()).height) < 2);
      await dialog.getByRole('button', { name: 'Ajustar', exact: true }).click();
      const pins = dialog.locator('.scene-preview-pin');
      if (await pins.count()) {
        await pins.last().click();
        await page.getByRole('button', { name: '← Voltar ao mapa', exact: true }).click();
        await page.locator('dialog.scene-map-dialog .scene-map-preview').waitFor();
      }
      const mapShot = path.join(output, `map-dialog-${width}.png`); await page.screenshot({ path: mapShot }); screenshots.push(mapShot);
      await page.keyboard.press('Escape'); await dialog.waitFor({ state: 'hidden' });
      assert.ok(await mapCard.locator('.scene-asset-inspect').evaluate(el => document.activeElement === el), 'Closing restores card focus');
      await mapCard.getByRole('checkbox').check();
      for (const label of contexts) {
        const control = viewer.getByRole('button', { name: `Contexto: ${label}`, exact: true }); await control.click();
        assert.equal(await control.getAttribute('aria-pressed'), 'true');
        assert.ok(await viewer.getByRole('button', { name: 'Levar seleção à Mesa', exact: true }).isEnabled(), 'Selection survives context changes');
        assert.equal(await viewer.locator('.scene-map-preview').count(), 0);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${label} fits ${width}`);
        if (['Combate', 'Conversa'].includes(label)) {
          const contextShot = path.join(output, `${label === 'Combate' ? 'combat' : 'conversation'}-${width}.png`);
          await viewer.screenshot({ path: contextShot }); screenshots.push(contextShot);
        }
      }
      await viewer.getByRole('button', { name: 'Contexto: Exploração', exact: true }).click();
      const shot = path.join(output, `contexts-${width}.png`); await viewer.screenshot({ path: shot }); screenshots.push(shot);
      await viewer.getByRole('button', { name: /^Biblioteca ·/ }).click();
      const library = viewer.getByRole('complementary', { name: 'Biblioteca de elementos' }); await library.waitFor();
      assert.ok(await library.locator('.scene-asset-card').count() > 0);
      const libraryShot = path.join(output, `library-${width}.png`); await viewer.screenshot({ path: libraryShot }); screenshots.push(libraryShot);
      await viewer.getByRole('button', { name: 'Fechar biblioteca', exact: true }).click();
      await viewer.getByRole('button', { name: 'Levar seleção à Mesa', exact: true }).click();
      await page.getByRole('dialog', { name: 'Confirmar envio à Mesa' }).getByRole('button', { name: 'Cancelar', exact: true }).click();
      await viewer.getByRole('button', { name: 'Conteúdo público', exact: true }).click();
      if (scene.status === 'draft' || scene.visibility !== 'table') {
        assert.equal(await viewer.locator('.scene-asset-card').count(), 0);
        assert.equal(await viewer.locator('dialog').count(), 0);
      }
      await page.reload(); await page.locator('.app-shell.authenticated').waitFor();
      await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Cenas$/ }).click();
      await viewer.waitFor(); assert.equal(await viewer.locator('.scene-map-preview').count(), 0);
      checks.push({ width, contexts: 6, compact_map: true, zoom: true, focus_restored: true, selection_preserved: true, cancellation: true, reload: true });
      await context.close();
    }
    const player = await browser.newContext();
    await player.addInitScript(() => {
      localStorage.setItem('omnisvera_access_token', 'cf01-local-raziel'); localStorage.setItem('omnisvera_access_mode', 'player');
      localStorage.setItem('omnisvera_selected_character', 'raziel');
    });
    const page = await player.newPage(); await page.goto(base); await page.locator('.app-shell.authenticated').waitFor();
    assert.equal(await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Cenas$/ }).count(), 0);
    await player.close();
    const after = await get('/workspace'); assert.equal(after.map?.id, before.map?.id); assert.deepEqual(after.tokens, before.tokens);
    assert.deepEqual(await get('/combat/effects'), combatBefore); assert.deepEqual(errors, []); assert.deepEqual(writes, []);
    const result = { status: 'PASS', scope: 'scene_context_readonly_desktop_mobile', checks, screenshots, production_modified: false,
      no_ui_mutations: true, player_private_area_denied: true, visual_acceptance: 'pending_agent_image_review', real_mobile_and_external_networks: 'INCONCLUSIVE' };
    fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result, null, 2)); console.log(JSON.stringify(result));
  } finally { await browser.close(); await api.dispose(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
