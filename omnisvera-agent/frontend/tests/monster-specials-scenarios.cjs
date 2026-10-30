// Called by the MCP-managed native smoke. Never accepts an operational origin.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

module.exports = async function monsterSpecialScenarios({ api, base, workspace, catalog, output, checks, created }) {
  assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
  assert.ok(![8787, 8788].includes(Number(new URL(base).port)), 'Only an isolated loopback fixture is allowed');
  const call = async (method, url, data) => {
    const response = await api[method](url, { data });
    assert.ok(response.ok(), `${response.status()} ${url}: ${await response.text()}`);
    return response.json();
  };
  const get = url => call('get', url), post = (url, data) => call('post', url, data);
  const patch = (url, data) => call('patch', url, data);
  const e = encodeURIComponent, evidence = { status: 'RUNNING', checks: [], production_modified: false };
  const command = async (action, payload = {}, request_id = randomUUID()) => {
    const snapshot = await get('/combat/effects');
    return post('/gm/combat/effects', { action, payload, request_id, expected_version: snapshot.version });
  };
  const endBattle = async () => {
    const snapshot = await get('/combat/effects');
    if (snapshot.encounter?.active) await command('end');
  };
  let map, grantedItem;
  const ownTokens = [];
  const currentPins = async () => (await get(`/workspace?map_id=${e(map.id)}`)).tokens;
  const pin = async id => (await currentPins()).find(token => token.id === id);
  const make = async (identity, x, y, extra = {}) => {
    const monster = identity ? catalog.monsters.find(entry => entry.id === identity) : null;
    if (identity) assert.ok(monster, identity);
    const token = await post('/gm/workspace/tokens', {
      token_type: 'monster', name: `ENSAIO especial ${identity || 'alvo'} ${ownTokens.length}`,
      map_id: map.id, visible_to_players: true, latitude: (y + 0.5) * 5, longitude: (x + 0.5) * 5,
      current_hp: 100, maximum_hp: 100,
      sheet: { ...(monster || {}), armor_class: 1, saving_throw: 100,
        abilities: (monster?.abilities || []).map(a => `${a.name}: ${a.description}`),
        ...(identity ? { source: { monster_id: identity } } : {}), ...extra.sheet },
      ...Object.fromEntries(Object.entries(extra).filter(([key]) => key !== 'sheet')),
    });
    created.push(token.id); ownTokens.push(token.id); return token;
  };
  const assertRejected = async (response, pattern) => {
    assert.ok([400, 403, 409, 422].includes(response.status()), `Expected rejection, got ${response.status()}`);
    if (pattern) assert.match(await response.text(), pattern);
  };
  const move = async (token, destination) => {
    const before = await pin(token.id), snapshot = await get('/combat/effects');
    const position = before.grid_position;
    const payload = { request_id: randomUUID(), token_id: token.id, mode: 'GM_REPOSITION',
      path: [[position.cell_x, position.cell_y], destination],
      expected_position_version: position.version, expected_grid_version: 1,
      expected_combat_version: snapshot.version };
    const result = await post(`/workspace/maps/${e(map.id)}/move`, payload);
    assert.deepEqual(await post(`/workspace/maps/${e(map.id)}/move`, payload), result);
    assert.equal(result.combat_version, (await get('/combat/effects')).version);
    return result;
  };
  const contactPreview = (actor, target) => get(`/gm/workspace/tokens/${e(actor.id)}/contact-preview?aim_token_id=${e(target.id)}`);
  const attackParasite = async (actor, victim) => {
    const attack = await post(`/gm/combat/tokens/${e(actor.id)}/attacks/resolve`, {
      request_id: randomUUID(), attack_id: '0', target_type: 'token', target_id: victim.id,
      roll_mode: 'physical', d20: 20,
    });
    assert.equal(attack.damage_total, 0); assert.deepEqual(attack.damage_rolls, []);
    const result = await post(`/combat/attacks/${e(attack.resolution_id)}/confirm`);
    assert.deepEqual(await post(`/combat/attacks/${e(attack.resolution_id)}/confirm`), result);
    const rider = result.breakdown.monster_rider_results.find(entry => entry.effect === 'parasite');
    assert.ok(rider); assert.equal(rider.resisted, false);
    assert.equal((await get('/combat/effects')).effects.find(effect => effect.target_id === victim.id && effect.monster_condition === 'parasite').turns_remaining, 3);
    return result;
  };
  try {
    await endBattle();
    map = await post('/gm/workspace/map', { title: 'ENSAIO isolado especiais', filename: 'fixture.png',
      content_type: 'image/png', visible_to_players: true,
      data_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==' });
    await patch('/gm/workspace/maps/active', { map_id: map.id });
    await post(`/workspace/maps/${e(map.id)}/grid`, { request_id: randomUUID(), expected_version: 0,
      cols: 20, rows: 20, cell_size_m: 1.5 });

    const sphere = await make('esfera-da-aniquilacao', 1, 1), doomed = await make(null, 2, 1);
    const sphereActions = await get(`/gm/workspace/tokens/${e(sphere.id)}/actions`);
    assert.equal(sphereActions.attacks[0].execution_kind, 'native_contact');
    assert.equal(sphereActions.attacks[0].native_contact, 'disintegration');
    assert.equal((await pin(sphere.id)).current_hp, null);
    const snapshot = await get('/combat/effects');
    await assertRejected(await api.post('/gm/combat/effects', { data: { request_id: randomUUID(),
      expected_version: snapshot.version, action: 'start', payload: { map_id: map.id,
        participants: [{ target_type: 'token', target_id: sphere.id, initiative: 20 }] } } }), /Esfera|cenário|cen.rio|iniciativa/i);
    const preview = await contactPreview(sphere, doomed);
    assert.equal(preview.kind, 'disintegration');
    const contact = { request_id: randomUUID(), expected_version: preview.version, action: 'monster_contact',
      payload: { token_id: sphere.id, target_pin_id: doomed.id, fingerprint: preview.fingerprint } };
    const disintegrated = await post('/gm/combat/effects', contact);
    assert.equal(disintegrated.protocol_result.kind, 'disintegration');
    assert.deepEqual(await post('/gm/combat/effects', contact), disintegrated);
    const reloadedDoomed = await pin(doomed.id);
    assert.ok(reloadedDoomed.current_hp <= 0); assert.equal(reloadedDoomed.sheet.disintegrated, true);
    assert.equal(reloadedDoomed.visible_to_players, false); assert.equal(reloadedDoomed.sheet.reanimation_allowed, false);
    assert.ok(!reloadedDoomed.sheet.corpse);
    checks.push('Sphere: statless native contact, initiative rejected, idempotent disintegration persists without a reanimatable corpse');

    const flagelo = await make('flagelo-da-podridao', 4, 5), victim = await make(null, 5, 5);
    const flageloActions = await get(`/gm/workspace/tokens/${e(flagelo.id)}/actions`);
    assert.equal(flageloActions.attacks[0].status, 'ready'); assert.equal(flageloActions.attacks[0].effect_only, true);
    assert.equal(flageloActions.attacks[0].campaign_rule, 'flagelo-provisional-v1');
    await attackParasite(flagelo, victim);
    const battlePayload = { map_id: map.id, battle_mode: true, title: 'ENSAIO parasita', participants: [
      { target_type: 'token', target_id: victim.id, initiative: 20 },
      { target_type: 'token', target_id: flagelo.id, initiative: 10 },
    ] };
    let hp = (await pin(victim.id)).current_hp;
    for (let tick = 0; tick < 3; tick++) {
      const result = tick === 0 ? await command('start', battlePayload) : await command('next_turn');
      const after = (await pin(victim.id)).current_hp;
      assert.ok(hp - after >= 1 && hp - after <= 4); hp = after;
      const effect = result.effects.find(entry => entry.target_id === victim.id && entry.monster_condition === 'parasite');
      if (tick < 2) assert.equal(effect.turns_remaining, 2 - tick); else assert.equal(effect, undefined);
      if (tick < 2) { await command('next_turn'); assert.equal((await pin(victim.id)).current_hp, hp); }
    }
    await endBattle();
    await attackParasite(flagelo, victim); await command('start', battlePayload);
    const removeState = await get('/combat/effects'), removePayload = { request_id: randomUUID(),
      expected_version: removeState.version, action: 'parasite_remove', payload: { target_type: 'token', target_id: victim.id } };
    const removed = await post('/combat/parasite/remove', removePayload);
    assert.equal(removed.encounter.action_committed, true);
    assert.ok(!removed.effects.some(effect => effect.target_id === victim.id && effect.monster_condition === 'parasite'));
    assert.deepEqual(await post('/combat/parasite/remove', removePayload), removed);
    await endBattle();
    checks.push('Flagelo campaign rule: zero fake damage, guaranteed failed JPC fixture, exactly three victim-start ticks, removal consumes the native main action and retries once');

    const swarmTarget = await make(null, 10, 10), bats = [];
    for (let index = 0; index < 10; index++) {
      bats.push(await make('morcego', 10, 10, { current_hp: 1, maximum_hp: 1 }));
      const state = await get('/combat/effects');
      assert.equal(state.effects.some(effect => effect.bat_swarm && effect.target_id === swarmTarget.id), index === 9);
    }
    const batActions = await get(`/gm/workspace/tokens/${e(bats[0].id)}/actions`);
    assert.equal(batActions.attacks[0].execution_kind, 'passive_grid');
    await move(swarmTarget, [11, 10]);
    assert.ok(!(await get('/combat/effects')).effects.some(effect => effect.bat_swarm && effect.target_id === swarmTarget.id));
    await move(swarmTarget, [10, 10]);
    assert.ok((await get('/combat/effects')).effects.some(effect => effect.bat_swarm && effect.target_id === swarmTarget.id));
    await patch(`/gm/workspace/tokens/${e(bats[0].id)}`, { current_hp: 0 });
    assert.ok(!(await get('/combat/effects')).effects.some(effect => effect.bat_swarm && effect.target_id === swarmTarget.id));
    checks.push('Swarm: nine living individual bats do not confuse; ten do; native movement/death reconcile immediately with correct cached combat version');

    const rust = await make('monstro-ferrugem', 13, 13);
    const character = await post('/gm/workspace/tokens', { token_type: 'character', character_id: 'vezemir',
      name: 'Vezemir — somente fixture TEMP', map_id: map.id, latitude: 67.5, longitude: 72.5 });
    created.push(character.id); ownTokens.push(character.id);
    const rustActions = await get(`/gm/workspace/tokens/${e(rust.id)}/actions`);
    assert.equal(rustActions.attacks[0].native_contact, 'rust');
    grantedItem = await post('/gm/workspace/items', { name: 'ENSAIO aço comum descartável', item_type: 'accessory',
      description: 'Objeto metálico comum exclusivamente da fixture TEMP.',
      mechanics: { equipment_slots: ['accessory'], magical: false } });
    await post('/gm/workspace/items/grant', { character_id: 'vezemir', item_id: grantedItem.id, quantity: 1, equipped: true });
    const rustPreview = await contactPreview(rust, character);
    const option = rustPreview.inventory.find(item => item.item_path === grantedItem.item_path);
    assert.ok(option); assert.equal(option.needs_metadata, true);
    await assertRejected(await api.post('/gm/combat/effects', { data: { request_id: randomUUID(),
      expected_version: rustPreview.version, action: 'monster_contact', payload: { token_id: rust.id,
        target_pin_id: character.id, fingerprint: rustPreview.fingerprint, inventory_id: option.inventory_id } } }), /material|metadados|encantamento/i);
    const rustPayload = { request_id: randomUUID(), expected_version: rustPreview.version, action: 'monster_contact',
      payload: { token_id: rust.id, target_pin_id: character.id, fingerprint: rustPreview.fingerprint,
        inventory_id: option.inventory_id, selection: { material: 'metal', magical: false,
          enchantment_bonus: 0, enhancement_rule_ids: [] } } };
    const rustResult = await post('/gm/combat/effects', rustPayload);
    assert.deepEqual(await post('/gm/combat/effects', rustPayload), rustResult);
    const inventory = await get('/gm/workspace/inventory/vezemir'), instance = inventory.find(item => item.item_path === grantedItem.item_path);
    if (rustResult.protocol_result.hit) {
      assert.equal(rustResult.protocol_result.corrosion.destroyed, true);
      assert.ok(!instance || instance.quantity === 0);
    } else assert.equal(instance.quantity, 1);
    evidence.rust_hit = rustResult.protocol_result.hit;
    checks.push('Ferrugem: native inventory requires explicit material; command/retry resolve once; confirmed mundane metal contact destroys only the fixture instance on a hit');
    evidence.status = 'PASS'; evidence.checks = checks.slice(-4);
    evidence.limitations = ['Rust attack d20 is native random: both hit/destruction and miss/no-mutation branches are asserted; enhancement degradation is covered by deterministic backend tests',
      'No physical mobile or distinct-network proof; this module has no separate browser'];
  } catch (error) {
    evidence.status = 'FAIL'; evidence.error = String(error.stack || error); throw error;
  } finally {
    await endBattle();
    if (grantedItem) {
      const inventory = await get('/gm/workspace/inventory/vezemir');
      if (inventory.some(item => item.item_path === grantedItem.item_path && item.quantity > 0))
        await post('/gm/workspace/inventory/remove', { target_id: 'vezemir', item_path: grantedItem.item_path, quantity: 1 });
    }
    if (workspace.map?.id) await patch('/gm/workspace/maps/active', { map_id: workspace.map.id });
    fs.writeFileSync(path.join(output, 'monster-specials-http.json'), JSON.stringify(evidence, null, 2));
  }
};
