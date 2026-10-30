// Real built frontend + existing temporary CF-01 HTTP fixture. Never live tokens/data.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { randomUUID } = require('node:crypto');

async function main() {
  const base = process.env.OMNISVERA_QA_BASE || 'http://127.0.0.1:8871';
  const parsed = new URL(base);
  assert.equal(parsed.hostname, '127.0.0.1');
  assert.equal(parsed.port, '8871', 'Only the existing loopback rehearsal port is allowed');
  const { chromium, request } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
  const api = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  async function read(url) { const r = await api.get(url); assert.equal(r.ok(), true, url); return r.json(); }
  async function post(url, data) { const r = await api.post(url, { data }); assert.equal(r.ok(), true, url + ': ' + await r.text()); return r.json(); }
  assert.equal((await read('/health')).access_mode, 'gm', 'Fixture token must be accepted before any writes');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const clients = [], errors = [], marker = 'Browser recovery ' + randomUUID();
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'omnisvera-table-recovery-'));
  try {
    let combat = await read('/combat/effects');
    if (combat.encounter?.active) await post('/gm/combat/effects', { request_id: marker + '-reset', expected_version: combat.version, action: 'end', payload: {} });
    for (const role of ['gm', 'vezemir', 'raziel', 'morthak']) {
      const context = await browser.newContext({ viewport: role === 'gm' ? { width: 1440, height: 1000 } : { width: 390, height: 844 } });
      await context.addInitScript(({ role }) => {
        localStorage.setItem('omnisvera_access_token', 'cf01-local-' + role);
        localStorage.setItem('omnisvera_access_mode', role === 'gm' ? 'gm' : 'player');
      }, { role });
      const page = await context.newPage();
      page.on('pageerror', e => errors.push(role + ': ' + e.message));
      if (role === 'vezemir') {
        let checks = 0;
        await page.route(base + '/health', route => ++checks === 1 ? route.abort('failed') : route.continue());
      }
      await page.goto(base, { waitUntil: 'domcontentloaded' });
      await page.locator('.app-shell.authenticated').waitFor({ timeout: 30000 });
      if (role !== 'gm') await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Ficha$/ }).click();
      else await page.getByRole('button', { name: 'Abrir ficha de Vezemir', exact: true }).click();
      try { await page.locator('.workspace-character-identity h2').waitFor({ timeout: 30000 }); }
      catch (error) {
        await page.screenshot({ path: path.join(output, role + '-failed.png'), fullPage: true });
        console.error('SHEET_FAILURE', role, JSON.stringify(errors), await page.locator('[role="alert"]').allTextContents(), 'SCREENSHOTS=' + output);
        throw error;
      }
      if (role !== 'gm') {
        assert.equal((await page.locator('.workspace-character-identity h2').innerText()).toLowerCase(), role);
        assert.equal(await page.getByRole('button', { name: 'Abrir painel do Mestre' }).count(), 0);
      }
      clients.push({ role, context, page });
      console.log('SHEET_OK=' + role);
    }
    const workspace = await read('/workspace');
    combat = await read('/combat/effects');
    await post('/gm/combat/effects', {
      request_id: marker + '-start', expected_version: combat.version, action: 'start',
      payload: { title: marker, map_id: workspace.map.id, battle_mode: true,
        participants: ['vezemir', 'raziel', 'morthak'].map((id, index) => ({ target_type: 'character', target_id: id, initiative: 20 - index })) },
    });
    for (const client of clients.filter(c => c.role !== 'gm')) {
      await client.page.locator('.workspace-combat-live').getByText(marker, { exact: true }).waitFor({ timeout: 30000 });
      await client.page.screenshot({ path: path.join(output, client.role + '.png') });
    }
    const vezemir = clients.find(c => c.role === 'vezemir');
    let mainNavigations = 0;
    vezemir.page.on('framenavigated', frame => { if (frame === vezemir.page.mainFrame()) mainNavigations++; });
    const hp = await vezemir.page.locator('.workspace-hp-heading').innerText();
    await vezemir.context.setOffline(true);
    await vezemir.page.waitForTimeout(11000);
    assert.equal(await vezemir.page.locator('.workspace-hp-heading').innerText(), hp, 'Offline must retain the confirmed sheet');
    const missedMessage = marker + '-missed-message';
    await post('/workspace/messages', { text: missedMessage, message_kind: 'message' });
    await vezemir.context.setOffline(false);
    await vezemir.page.getByText(missedMessage, { exact: true }).first().waitFor({ timeout: 30000 });
    assert.equal(mainNavigations, 0, 'Recovery must not reload the document');
    await vezemir.page.getByRole('button', { name: 'Concluir e passar turno →', exact: true }).click();
    await clients.find(c => c.role === 'raziel').page.getByText('É o seu turno!', { exact: true }).waitFor({ timeout: 30000 });
    assert.equal(mainNavigations, 0);
    assert.deepEqual(errors, [], 'Built frontend must not produce uncaught JavaScript errors');
    console.log('PASS: built frontend; Master + Vezemir/Raziel/Morthak; own sheets on mobile; offline retains HP; missed ledger recovered without reload; combat visible; player next turn synchronized.');
    console.log('SCREENSHOTS=' + output);
  } finally {
    const combat = await read('/combat/effects').catch(() => null);
    if (combat?.encounter?.active && combat.encounter.title === marker) await post('/gm/combat/effects', { request_id: marker + '-end', expected_version: combat.version, action: 'end', payload: {} });
    await browser.close();
    await api.dispose();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
