// Native TEMP fixture only. One browser, sequential desktop/mobile contexts.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { chromium, request } = require(require.resolve('playwright', {
  paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()],
}));

(async () => {
  const base = process.env.OMNISVERA_SHEET_QA_URL;
  assert.match(base || '', /^http:\/\/127\.0\.0\.1:\d+$/);
  assert.ok(![8787, 8788].includes(Number(new URL(base).port)), 'Operational ports are forbidden');
  const tempRoot = path.resolve(os.tmpdir()) + path.sep;
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'omni-active-spells-'));
  const api = await request.newContext({ baseURL: base, timeout: 15000,
    extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  let browser, page, context, map, originalMap;
  const owned = [], checks = [], api_coverage = [], visual_actors = [], action_coverage = [], errors = [];
  const evidence = { status: 'RUNNING', production_modified: false, screenshots: output,
    checks, api_coverage, action_coverage, visual_actors, dispel_results: [] };
  const deadline = Date.now() + 270000;
  const ensureTime = () => assert.ok(Date.now() < deadline, 'The bounded smoke exceeded its 270-second work budget');
  const hardStop = setTimeout(() => {
    console.error('Active-spell smoke reached its finite 285-second deadline');
    Promise.race([Promise.allSettled([browser?.close(), api.dispose()]),
      new Promise(resolve => setTimeout(resolve, 3000))]).finally(() => process.exit(1));
  }, 285000);
  hardStop.unref();
  const e = encodeURIComponent;
  const call = async (method, url, data) => {
    ensureTime(); const response = await api[method](url, { data });
    assert.ok(response.ok(), `${response.status()} ${url}: ${await response.text()}`);
    return response.json();
  };
  const get = url => call('get', url), post = (url, data) => call('post', url, data), patch = (url, data) => call('patch', url, data);
  const command = async (action, payload = {}, request_id = randomUUID()) => {
    const snapshot = await get('/combat/effects');
    return post('/gm/combat/effects', { request_id, expected_version: snapshot.version, action, payload });
  };
  const endBattle = async () => { if ((await get('/combat/effects')).encounter?.active) await command('end'); };
  const clearEffects = async () => {
    const initial = (await get('/combat/effects')).effects.filter(effect => !effect.environmental);
    for (const effect of initial) {
      if ((await get('/combat/effects')).effects.some(active => active.id === effect.id))
        await command('remove', { id: effect.id });
    }
  };
  const actors = ['vezemir', 'raziel', 'dorn7', 'morthak'];
  const rest = actor => post(`/characters/${actor}/actions`, { action: 'rest_at_inn', payload: {},
    request_id: randomUUID(), reason: 'Ensaio TEMP — restaurar recursos antes do cenário' });
  const currentPins = async () => (await get(`/workspace?map_id=${e(map.id)}`)).tokens;
  const hp = async id => (await currentPins()).find(token => token.id === id).current_hp;
  const resource = (character, key) => character.state.resources.find(value => value.key === key)?.current;
  const sameReceipt = async (url, payload, receipt) => {
    assert.deepEqual(await post(url, payload), receipt, 'Retry must recover the original native receipt');
  };
  try {
    const health = await get('/health');
    for (const key of ['database_path', 'vault_path']) {
      assert.equal(typeof health[key], 'string');
      assert.ok(path.resolve(health[key]).toLowerCase().startsWith(tempRoot.toLowerCase()), `${key} must belong to TEMP`);
    }
    // No mutation is permitted before the independent path/origin checks above.
    originalMap = (await get('/workspace')).map;
    await endBattle(); await clearEffects();
    for (const actor of actors) await rest(actor);
    map = await post('/gm/workspace/map', { title: 'ENSAIO efeitos arcanos — isolado', filename: 'fixture.png',
      content_type: 'image/png', visible_to_players: true,
      data_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==' });
    await patch('/gm/workspace/maps/active', { map_id: map.id });
    await post(`/workspace/maps/${e(map.id)}/grid`, { request_id: randomUUID(), expected_version: 0,
      cols: 20, rows: 20, cell_size_m: 1.5 });
    const pins = {};
    for (const [actor, x, y] of [['dorn7', 4, 5], ['vezemir', 4, 7], ['raziel', 4, 8], ['morthak', 4, 9]]) {
      pins[actor] = await post('/gm/workspace/tokens', { token_type: 'character', character_id: actor,
        name: `ENSAIO ${actor}`, map_id: map.id, latitude: (y + 0.5) * 5, longitude: (x + 0.5) * 5,
        visible_to_players: true });
      owned.push(pins[actor].id);
    }
    const victims = [];
    for (const x of [5, 6]) {
      const token = await post('/gm/workspace/tokens', { token_type: 'monster', name: `Alvo arcano TEMP ${x}`,
        map_id: map.id, latitude: 27.5, longitude: (x + 0.5) * 5, current_hp: 500, maximum_hp: 500,
        visible_to_players: true, sheet: { armor_class: 1, saving_throw: 99, hit_dice: 1,
          attributes: { strength: 16, constitution: 10, dexterity: 10, wisdom: 10 },
          attacks: [{ name: 'Ataque da fixture', bonus: 1, damage: '1d6' }] } });
      victims.push(token); owned.push(token.id);
    }

    // API proof is recorded separately from actual card/grid UI proof below.
    const vezBefore = await get('/characters/vezemir');
    const speedPayload = { request_id: randomUUID() };
    const speed = await post('/characters/vezemir/techniques/velocidade', speedPayload);
    await sameReceipt('/characters/vezemir/techniques/velocidade', speedPayload, speed);
    assert.ok((await get('/combat/effects')).effects.some(effect => effect.target_id === 'vezemir' && effect.modifiers?.extra_attacks === 1));
    assert.equal(resource(await get('/characters/vezemir'), 'velocidade'), resource(vezBefore, 'velocidade') - 1);
    api_coverage.push({ actor: 'vezemir', action: 'velocidade', checks: ['effect', 'one_resource', 'retry'] });

    const raziel = await get('/characters/raziel');
    await post('/characters/raziel/actions', { request_id: randomUUID(), action: 'set_hp',
      payload: { value: Math.max(1, raziel.state.maximum_hp - 4) }, reason: 'Somente fixture TEMP — preparar regeneração' });
    const razBefore = await get('/characters/raziel'), regenPayload = { request_id: randomUUID() };
    const regeneration = await post('/characters/raziel/techniques/regeneracao-vampirica', regenPayload);
    await sameReceipt('/characters/raziel/techniques/regeneracao-vampirica', regenPayload, regeneration);
    const razAfter = await get('/characters/raziel');
    assert.ok(regeneration.healed >= 1 && regeneration.healed <= 4);
    assert.equal(razAfter.state.current_hp, razBefore.state.current_hp + regeneration.healed);
    assert.equal(resource(razAfter, 'reserva_de_sangue'), resource(razBefore, 'reserva_de_sangue') - 1);
    api_coverage.push({ actor: 'raziel', action: 'regeneracao-vampirica', checks: ['healing', 'one_blood', 'retry'] });

    const morthakBefore = await get('/characters/morthak');
    const missileAbility = morthakBefore.definition.session_abilities.find(ability => ability.id === 'misseis-magicos');
    const missileResource = missileAbility?.uses?.resource_key?.replace(/-/g, '_');
    assert.ok(missileResource && Number.isFinite(resource(morthakBefore, missileResource)));
    const targetBefore = await hp(victims[0].id), missilePayload = { request_id: randomUUID(),
      attack_id: 'misseis-magicos', target_type: 'token', target_id: victims[0].id, roll_mode: 'digital', grid_automatic: true };
    const missiles = await post('/characters/morthak/attacks/resolve', missilePayload);
    await sameReceipt('/characters/morthak/attacks/resolve', missilePayload, missiles);
    assert.equal(missiles.result, 'hit'); assert.ok(missiles.damage_total > 0);
    assert.equal(await hp(victims[0].id), missiles.hp_after);
    assert.equal(targetBefore - missiles.hp_after, missiles.damage_total);
    assert.equal(resource(await get('/characters/morthak'), missileResource), resource(morthakBefore, missileResource) - 1);
    api_coverage.push({ actor: 'morthak', action: 'misseis-magicos', checks: ['automatic_hit', 'native_damage', 'one_resource', 'retry'] });
    checks.push('Native API: Vezemir speed, Raziel regeneration and Morthak missiles; effects/costs/damage/retries are asserted separately from UI acceptance');

    browser = await chromium.launch({ channel: 'msedge', headless: true });
    for (const width of [1440, 390]) {
      ensureTime(); await endBattle(); await clearEffects();
      for (const actor of actors) await rest(actor);
      await patch('/gm/workspace/maps/active', { map_id: map.id });
      const reflection = await command('dorn_spell_cast', { spell_id: 'reflexos' });
      const reflectionEffect = reflection.protocol_result.results[0].effect;
      assert.equal(reflectionEffect.intercept_chance_percent, 90);
      assert.ok(reflectionEffect.images_remaining >= 2 && reflectionEffect.images_remaining <= 5);
      const web = await command('dorn_spell_cast', { spell_id: 'teia', targets: [{ type: 'token', id: victims[0].id }] });
      const webId = web.protocol_result.results[0].effect.id;
      const force = await command('dorn_spell_cast', { spell_id: 'forca-arcana', targets: [{ type: 'token', id: victims[0].id }] });
      const forceId = force.protocol_result.results[0].effect.id;
      const prepared = await get('/combat/effects');
      assert.ok(victims.every(victim => prepared.effects.some(effect => effect.target_id === victim.id && effect.web_parent_id === webId)));
      const preview = await get(`/gm/combat/spells/dispel-preview?target_token_id=${e(victims[0].id)}`);
      assert.equal(preview.effects.length, 2); assert.ok(preview.effects.some(effect => effect.id === webId && effect.kind === 'area'));
      assert.ok(preview.effects.some(effect => effect.id === forceId && effect.kind === 'entity'));
      assert.ok(preview.effects.every(effect => Number.isFinite(effect.distance_m)));
      await command('start', { map_id: map.id, battle_mode: true, title: 'ENSAIO Dissipar por ocupante',
        participants: [{ target_type: 'character', target_id: 'dorn7', initiative: 40 },
          ...actors.filter(actor => actor !== 'dorn7').map((actor, index) => ({ target_type: 'character', target_id: actor, initiative: 30 - index })),
          ...victims.map((victim, index) => ({ target_type: 'token', target_id: victim.id, initiative: 10 - index }))] });
      context = await browser.newContext({ viewport: { width, height: 900 }, isMobile: width === 390, hasTouch: width === 390 });
      context.setDefaultTimeout(12000); context.setDefaultNavigationTimeout(20000);
      await context.addInitScript(() => {
        localStorage.setItem('omnisvera_access_token', 'cf01-local-gm');
        localStorage.setItem('omnisvera_access_mode', 'gm');
        localStorage.setItem('omnisvera_selected_character', 'dorn7');
        localStorage.setItem('omnisvera_session_map_zoom', '1');
      });
      page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
      await page.goto(base); await page.locator('.app-shell.authenticated').waitFor();
      await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('button', { name: /Mesa$/ }).click();
      for (const actor of actors) {
        await page.locator(`[data-character="${actor}"]`).click();
        const actorSheet = await get(`/characters/${actor}`), panel = page.locator('.workspace-character-panel');
        await panel.getByRole('heading', { name: actorSheet.definition.name, exact: true }).waitFor();
        const identity = panel.locator('.workspace-character-identity'); await identity.waitFor();
        assert.equal(await identity.evaluate(element => element.scrollWidth <= element.clientWidth + 2), true);
        await identity.screenshot({ path: path.join(output, `${actor}-identity-active-spells-${width}.png`) });
        visual_actors.push({ actor, width, checks: ['identity_visible', 'no_identity_overflow'], scope: 'Identity layout; not full combat certification' });
      }
      await page.locator('[data-character="dorn7"]').click();
      const dorn = page.locator('.workspace-character-panel');
      await dorn.getByRole('heading', { name: (await get('/characters/dorn7')).definition.name, exact: true }).waitFor();
      for (const summary of await dorn.locator('.workspace-sheet-section > summary').all())
        if (!(await summary.evaluate(element => element.parentElement.open))) await summary.click();
      const card = dorn.locator('article').filter({ has: page.getByRole('button', { name: 'Dissipar Magia', exact: true, includeHidden: true }) })
        .filter({ has: page.locator('button[data-card-command]') }).first();
      await card.waitFor();
      await page.waitForFunction(element => element?.querySelector('button[data-card-command]') && !element.querySelector('button[data-card-command]').disabled,
        await card.elementHandle());
      const dornBefore = await get('/characters/dorn7'), beforeCancel = await get('/combat/effects');
      const posts = [];
      page.on('request', req => {
        if (req.method() === 'POST' && req.url().endsWith('/gm/combat/effects') && req.postDataJSON()?.payload?.spell_id === 'dissipar-magia')
          posts.push(req.postDataJSON());
      });
      const choose = async () => {
        await card.click({ position: { x: 8, y: 8 } });
        await page.locator('.targeting-overlay').waitFor();
        const target = page.locator(`[data-grid-token="${victims[0].id}"].target-valid`);
        await target.waitFor(); await target.click();
        const dialog = page.getByRole('dialog', { name: 'Confirmar alvo', exact: true }); await dialog.waitFor();
        const group = dialog.getByRole('group', { name: 'Magia a dissipar', exact: true }); await group.waitFor();
        assert.equal(await group.getByRole('radio').count(), 2);
        const radioBox=await group.getByRole('radio').first().boundingBox();
        assert.ok(radioBox&&radioBox.width<=24&&radioBox.height<=24,'Effect selector must use compact radio icons');
        assert.equal(await group.getByRole('radio', { checked: true }).count(), 0);
        assert.equal(await dialog.getByRole('button', { name: 'Sim', exact: true }).isDisabled(), true);
        const box = await dialog.boundingBox(); assert.ok(box && box.x >= -1 && box.x + box.width <= width + 1);
        assert.equal(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth + 2), true);
        return { dialog, group };
      };
      let selection = await choose();
      await selection.dialog.screenshot({ path: path.join(output, `dispel-two-effects-cancel-${width}.png`) });
      await selection.dialog.getByRole('button', { name: 'Não', exact: true }).click();
      assert.equal(posts.length, 0);
      assert.deepEqual((await get('/characters/dorn7')).state.resources, dornBefore.state.resources);
      assert.deepEqual((await get('/combat/effects')).effects, beforeCancel.effects);

      selection = await choose();
      const radio = selection.group.getByRole('radio', { name: /Teia/ }); await radio.check();
      assert.equal(await selection.dialog.getByRole('button', { name: 'Sim', exact: true }).isEnabled(), true);
      await selection.dialog.screenshot({ path: path.join(output, `dispel-web-selected-${width}.png`) });
      const appliedResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/gm/combat/effects') &&
        response.request().postDataJSON()?.payload?.spell_id === 'dissipar-magia');
      await selection.dialog.getByRole('button', { name: 'Sim', exact: true }).click();
      const response = await appliedResponse; assert.ok(response.ok(), await response.text());
      const receipt = await response.json(); assert.equal(posts.length, 1);
      assert.equal(posts[0].payload.effect_id, webId); assert.equal(posts[0].payload.target_token_id, victims[0].id);
      assert.ok(posts[0].payload.definition_revision); assert.ok(posts[0].payload.target_fingerprint);
      const result = receipt.protocol_result.results[0];
      assert.equal(result.success, result.total >= result.difficulty);
      assert.ok(result.d20 >= 1 && result.d20 <= 20);
      const after = await get('/combat/effects'), dornAfter = await get('/characters/dorn7');
      assert.equal(resource(dornAfter, 'dorn_dissipar_magia'), resource(dornBefore, 'dorn_dissipar_magia') - 1);
      assert.equal(after.encounter.action_committed, true);
      assert.equal(after.effects.some(effect => effect.id === webId), !result.success);
      assert.equal(after.effects.filter(effect => effect.web_parent_id === webId).length, result.success ? 0 : victims.length);
      assert.ok(after.effects.some(effect => effect.id === forceId));
      await sameReceipt('/gm/combat/effects', posts[0], receipt);
      assert.deepEqual((await get('/characters/dorn7')).state.resources, dornAfter.state.resources);
      const ledger = await get('/workspace/ledger?limit=1000');
      const narrative = ledger.filter(event => event.source_id === posts[0].request_id && event.source_type === 'ability_activation');
      assert.equal(narrative.length, 1); assert.match(narrative[0].title, /Dissipar Magia/i);
      assert.ok(!narrative[0].title.trim().startsWith('{'));
      await page.reload(); await page.locator('.app-shell.authenticated').waitFor();
      assert.deepEqual((await get('/characters/dorn7')).state.resources, dornAfter.state.resources);
      const reloaded = await get('/combat/effects');
      assert.equal(reloaded.effects.some(effect => effect.id === webId), !result.success);
      evidence.dispel_results.push({ width, success: result.success, d20: result.d20, total: result.total, difficulty: result.difficulty,
        cleared_entire_area: result.success, failure_preserved_area: !result.success, resource_consumptions: 1 });
      action_coverage.push({ actor: 'dorn7', key: 'ability:dissipar-magia', width, verified_checks: ['ui'],
        proof: 'Card -> grid occupant -> two-effect chooser -> native cast/retry/reload' });
      await context.close(); context = null; page = null;
    }
    checks.push('Reflexos stores the approved 90% cast contract and its image count; native API setup gives two eligible spells on a grid occupant');
    checks.push('Desktop1440/mobile390: two-effect chooser, disabled unselected confirmation, cancel without cost, canonical Teia selection, native outcome, one resource/action, exact retry, ledger and reload');
    assert.deepEqual(errors, []);
    evidence.status = 'PASS';
    evidence.controlled_inputs = ['Only native GM setup/rest/HP preparation in TEMP', 'Dissipar d20 remains genuinely random; success and resistance consequences follow the actual receipt'];
    evidence.limitations = ['Screenshots require explicit visual inspection before accepting layout',
      'API-only Vezemir/Raziel/Morthak checks are not card/grid UI certification',
      'Reflexos 90% value is persisted and checked; empirical interception distribution is not statistically certified here',
      'Toque Sombrio/Frenesi/privacy adversarial branches are covered by backend deterministic tests, not this UI scenario',
      'No physical mobile or clients on distinct networks were used'];
  } catch (error) {
    evidence.status = 'FAIL'; evidence.error = String(error.stack || error);
    if (page) await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
    console.error(error.stack || error); process.exitCode = 1;
  } finally {
    if (context) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
    // Cleanup only after successful origin + TEMP verification and map setup.
    if (map) {
      try {
        await endBattle();
        if (originalMap?.id) await patch('/gm/workspace/maps/active', { map_id: originalMap.id });
        for (const id of owned) { const response = await api.delete(`/gm/workspace/tokens/${e(id)}`); assert.ok(response.ok()); }
        const response = await api.delete(`/gm/workspace/maps/${e(map.id)}`); assert.ok(response.ok());
      } catch (error) { evidence.status = 'FAIL'; evidence.cleanup_error = String(error); process.exitCode = 1; }
    }
    clearTimeout(hardStop); await api.dispose();
    fs.writeFileSync(path.join(output, 'active-spell-effects-result.json'), JSON.stringify(evidence, null, 2));
    console.log(JSON.stringify(evidence));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
