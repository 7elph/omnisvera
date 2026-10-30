// Shared native-browser acceptance helper; no new browser/process or production origin.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

module.exports = async function monsterSpecialVisual({ page, api, base, workspace, catalog, output, width }) {
  assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
  assert.ok(![8787, 8788].includes(Number(new URL(base).port)), 'A TEMP fixture is required');
  assert.equal(page.viewportSize()?.width, width);
  const e = encodeURIComponent, owned = [], captures = [], evidence = { status: 'RUNNING', width,
    production_modified: false, destructive_ui_confirmations: 0 };
  const call = async (method, url, data) => {
    const response = await api[method](url, { data });
    assert.ok(response.ok(), `${response.status()} ${url}: ${await response.text()}`);
    return response.json();
  };
  const get = url => call('get', url), post = (url, data) => call('post', url, data), patch = (url, data) => call('patch', url, data);
  const command = async (action, payload = {}) => {
    const state = await get('/combat/effects');
    return post('/gm/combat/effects', { request_id: randomUUID(), expected_version: state.version, action, payload });
  };
  const endBattle = async () => { if ((await get('/combat/effects')).encounter?.active) await command('end'); };
  let map;
  const currentPins = async () => (await get(`/workspace?map_id=${e(map.id)}`)).tokens;
  const create = async (identity, x, y, extras = {}) => {
    const monster = identity ? catalog.monsters.find(entry => entry.id === identity) : null;
    if (identity) assert.ok(monster, identity);
    const token = await post('/gm/workspace/tokens', {
      token_type: 'monster', name: `ENSAIO visual ${identity || 'alvo'} ${width}`, map_id: map.id,
      latitude: (y + 0.5) * 5, longitude: (x + 0.5) * 5, current_hp: 100, maximum_hp: 100,
      visible_to_players: true, sheet: { ...(monster || {}), armor_class: 1, saving_throw: 10,
        ...(identity ? { source: { monster_id: identity } } : {}),
        abilities: (monster?.abilities || []).map(ability => `${ability.name}: ${ability.description}`) }, ...extras,
    });
    owned.push(token.id); return token;
  };
  const enterMesa = async () => {
    await page.goto(base); await page.locator('.app-shell.authenticated').waitFor();
    await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Mesa$/ }).click();
    const adjust = page.locator('.workspace-map-zoom').getByRole('button', { name: 'Ajustar', exact: true });
    if (await adjust.count() && await adjust.isEnabled()) await adjust.click();
  };
  const openAndAim = async (actor, victim) => {
    const sourcePin = page.locator(`[data-grid-token="${actor.id}"]`);
    await sourcePin.waitFor({ state: 'visible' }); await sourcePin.scrollIntoViewIfNeeded(); await sourcePin.click();
    const sheet = page.getByRole('dialog', { name: `Ficha de ${actor.name}`, exact: true });
    await sheet.waitFor();
    const panel = sheet.getByRole('region', { name: `Ataques de ${actor.name}` });
    // The section has aria-label, but is not a browser landmark in every engine.
    const catalogPanel = await panel.count() ? panel : sheet.locator('.workspace-attack-catalog');
    const attack = catalogPanel.locator('article').first(); await attack.waitFor();
    const use = attack.locator('button[data-card-command]');
    await use.waitFor({state:'attached'}); assert.equal(await use.isEnabled(), true);
    assert.equal(await sheet.getByText('Configurar ofertas',{exact:true}).count(),1,'Pin modal must not accumulate duplicate commerce components');
    // Click the card heading, exercising the one-card activation adapter.
    await attack.locator('strong').first().click();
    await page.getByRole('group', { name: 'Mira no grid' }).waitFor();
    await page.getByLabel('Alcance da ação', { exact: true }).waitFor();
    const targetPin = page.locator(`[data-grid-token="${victim.id}"].target-valid`);
    await targetPin.waitFor(); await targetPin.scrollIntoViewIfNeeded(); await targetPin.click();
    const confirmation = page.getByRole('dialog', { name: 'Confirmar alvo', exact: true });
    await confirmation.waitFor();
    const bounds = await confirmation.boundingBox();
    assert.ok(bounds && bounds.x >= -1 && bounds.x + bounds.width <= width + 1,
      `Confirmation does not fit viewport: ${JSON.stringify(bounds)}`);
    assert.equal(await confirmation.evaluate(element => element.scrollWidth <= element.clientWidth + 2), true);
    return confirmation;
  };
  const dismiss = async confirmation => {
    await confirmation.getByRole('button', { name: 'Não', exact: true }).click();
    const close = page.getByRole('button', { name: 'Fechar ficha', exact: true });
    if (await close.count() && await close.isVisible()) await close.click();
  };
  try {
    await endBattle();
    let background = { content_type: 'image/png', filename: 'fixture.png',
      data_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==' };
    const sourcePath = workspace.map?.image_path;
    if (sourcePath) {
      const clean = sourcePath.replace(/^\/media\//, '').replace(/^\/+/, '');
      const media = await api.get(`/media/${clean.split('/').map(e).join('/')}`);
      const type = (media.headers()['content-type'] || '').split(';')[0];
      if (media.ok() && ['image/png', 'image/jpeg', 'image/webp'].includes(type)) {
        const content = await media.body();
        if (content.length <= 10 * 1024 * 1024) {
          background = { content_type: type, filename: `fixture.${type === 'image/jpeg' ? 'jpg' : type.split('/')[1]}`,
            data_base64: content.toString('base64') };
          evidence.background = 'existing_fixture_bitmap';
        }
      }
    }
    evidence.background ||= 'one_pixel_fixture_bitmap';
    map = await post('/gm/workspace/map', { title: `ENSAIO visual contatos ${width}`,
      ...background, visible_to_players: true });
    await patch('/gm/workspace/maps/active', { map_id: map.id });
    await post(`/workspace/maps/${e(map.id)}/grid`, { request_id: randomUUID(), expected_version: 0,
      cols: 20, rows: 20, cell_size_m: 1.5 });
    const sphere = await create('esfera-da-aniquilacao', 8, 8), rust = await create('monstro-ferrugem', 8, 11);
    const victim = await create(null, 9, 8, { token_type: 'character', character_id: 'vezemir',
      name: `Vezemir · fixture visual ${width}` });
    const before = await get('/characters/vezemir');
    await command('start', { battle_mode: true, map_id: map.id, title: 'ENSAIO visual — perigo sem turno',
      participants: [{ target_type: 'character', target_id: 'vezemir', initiative: 20 }] });
    const battle = (await get('/combat/effects')).encounter;
    assert.equal(battle.participants.length, 1); assert.equal(battle.participants[0].target_id, 'vezemir');
    await enterMesa();
    const sphereDialog = await openAndAim(sphere, victim);
    assert.match(await sphereDialog.innerText(), /desintegrado sem ataque nem JP/i);
    assert.equal(await sphereDialog.getByRole('button', { name: 'Sim', exact: true }).isEnabled(), true);
    const sphereFile = path.join(output, `monster-special-sphere-confirm-${width}.png`);
    await sphereDialog.screenshot({ path: sphereFile }); captures.push(sphereFile);
    await dismiss(sphereDialog);
    assert.equal((await get('/characters/vezemir')).state.current_hp, before.state.current_hp);
    evidence.sphere_visible_without_initiative = true;

    await endBattle();
    const position = (await currentPins()).find(token => token.id === victim.id).grid_position;
    await post(`/workspace/maps/${e(map.id)}/move`, { request_id: randomUUID(), token_id: victim.id,
      mode: 'GM_REPOSITION', path: [[position.cell_x, position.cell_y], [9, 11]],
      expected_position_version: position.version, expected_grid_version: 1 });
    await enterMesa();
    const rustDialog = await openAndAim(rust, victim);
    assert.match(await rustDialog.innerText(), /equipamento.*contato|corrosão/i);
    const confirm = rustDialog.getByRole('button', { name: 'Sim', exact: true });
    assert.equal(await confirm.isDisabled(), true);
    const preview = await get(`/gm/workspace/tokens/${e(rust.id)}/contact-preview?aim_token_id=${e(victim.id)}`);
    const option = preview.inventory.find(item => item.needs_metadata);
    if (option) {
      await rustDialog.getByLabel('Item tocado pela Ferrugem', { exact: true }).selectOption(String(option.inventory_id));
      await rustDialog.getByLabel('Material do item', { exact: true }).waitFor();
      await rustDialog.getByLabel('Encantamento do item', { exact: true }).waitFor();
      assert.equal(await confirm.isDisabled(), true);
      await rustDialog.getByLabel('Material do item', { exact: true }).selectOption('metal');
      assert.equal(await confirm.isDisabled(), true);
      evidence.rust_metadata_choices_visible = true;
    } else {
      evidence.rust_metadata_choices_visible = false;
      evidence.rust_metadata_limit = 'Fixture has no equipped item awaiting material confirmation; empty/identified inventory state only';
    }
    const rustFile = path.join(output, `monster-special-rust-confirm-${width}.png`);
    await rustDialog.screenshot({ path: rustFile }); captures.push(rustFile);
    await dismiss(rustDialog);
    const after = await get('/characters/vezemir');
    assert.equal(after.state.current_hp, before.state.current_hp);
    assert.deepEqual(after.inventory, before.inventory);
    evidence.status = 'PASS'; evidence.screenshots = captures;
    evidence.limitations = ['Capture files require explicit visual inspection', 'No physical device or distinct-network proof'];
    return evidence;
  } catch (error) {
    evidence.status = 'FAIL'; evidence.error = String(error.stack || error);
    await page.screenshot({ path: path.join(output, `monster-special-visual-failure-${width}.png`) }).catch(() => {});
    throw error;
  } finally {
    const cancel = page.getByRole('button', { name: 'Cancelar ação', exact: true });
    if (await cancel.count() && await cancel.isVisible()) await cancel.click().catch(() => {});
    await endBattle();
    if (workspace.map?.id) await patch('/gm/workspace/maps/active', { map_id: workspace.map.id });
    for (const id of owned) {
      const response = await api.delete(`/gm/workspace/tokens/${e(id)}`);
      assert.ok(response.ok(), `Unable to clean fixture pin: ${response.status()}`);
    }
    if (map) { const response = await api.delete(`/gm/workspace/maps/${e(map.id)}`); assert.ok(response.ok()); }
    fs.writeFileSync(path.join(output, `monster-specials-visual-${width}.json`), JSON.stringify(evidence, null, 2));
  }
};

