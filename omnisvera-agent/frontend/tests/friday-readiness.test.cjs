const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const privatePreparation = (...files) => files.every(file=>fs.existsSync(path.join(root,'docs/preparation',file)))
 ? false : 'Requires private GM preparation, deliberately excluded from GitHub';

test('today preparation has real consistent portraits and captures each scene at both widths',{
 skip:privatePreparation('FRIDAY_ASSETS.json'),
},()=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'docs/preparation/FRIDAY_ASSETS.json'),'utf8'));
 for(const id of ['friday-thoradin-v1','friday-military-role-v1','friday-conclave-role-v1','friday-teren-human-v1']){
  const asset=manifest.assets.find(a=>a.id===id);assert.ok(asset,`Missing portrait: ${id}`);
  const bytes=fs.readFileSync(path.join(root,asset.workspace_file));
  assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
  assert.equal(asset.changes_tactical_map,false);
  assert.ok(asset.prompt&&asset.generator==='built_in_image_gen');
 }
 const source=fs.readFileSync(path.join(__dirname,'scene-preparation-smoke.cjs'),'utf8');
 assert.ok(source.includes('scene-${scene.id}-${width}.png'),'Need evidence of every map, not just the last viewer');
 assert.ok(source.includes('.scene-asset-card img'),'Inspect linked NPC/creature media, not just covers');
});

test('preparation rehearsal proves native opening and retry only after its read-only checks',()=>{
 const source=fs.readFileSync(path.join(__dirname,'scene-preparation-smoke.cjs'),'utf8');
 const opening=source.indexOf('/open-on-table');
 assert.ok(opening>source.indexOf('deepEqual(writes,[])'),'Keep read-only inspection separate from TEMP publication');
 assert.ok(source.includes('opening_checks'),'Record which prepared scenes actually opened');
 assert.ok(source.includes("assert.equal(replay.created,false)"),'Opening retry must not duplicate its publication');
 assert.ok(source.includes("'ELENCO DE HOJE'"),'Public snapshot must not expose private preparation notes');
});
test('Friday cover is a real local image, not a tactical map replacement',{
 skip:privatePreparation('FRIDAY_ASSETS.json','FRIDAY_BLOCKS.json'),
},()=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'docs/preparation/FRIDAY_ASSETS.json'),'utf8'));
 const asset=manifest.assets.find(a=>a.id==='friday-office-v1');assert.ok(asset);
 assert.equal(asset.changes_tactical_map,false);assert.equal(asset.generator,'built_in_image_gen');
 const bytes=fs.readFileSync(path.join(root,asset.workspace_file));
 assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
 assert.ok(bytes.readUInt32BE(16)>=1024);assert.ok(bytes.readUInt32BE(20)>=768);
 const blocks=JSON.parse(fs.readFileSync(path.join(root,'docs/preparation/FRIDAY_BLOCKS.json'),'utf8'));
 const scenes=blocks.blocks||blocks.scenes;assert.ok(Array.isArray(scenes));
 const office=scenes.find(s=>s.key==='decision');assert.equal(office.image_path,asset.path);
 assert.equal(office.map_id,'map:099fb4a0028040eb');
});
test('fixed Friday browser flows are isolated and never claim screenshot review',()=>{
 for(const script of ['scene-preparation-smoke.cjs','thoradin-wallet-smoke.cjs']){
  const source=fs.readFileSync(path.join(__dirname,script),'utf8');
  assert.match(source,/assert.equal\(base,'http:\/\/127\.0\.0\.1:8871'\)/);
  assert.match(source,/health.database_path/);assert.match(source,/health.vault_path/);
  assert.match(source,/pending_human_or_agent_image_review/);
  assert.doesNotMatch(source,/access_tokens\.json|8787|8788/);
 }
 const scenes=fs.readFileSync(path.join(__dirname,'scene-preparation-smoke.cjs'),'utf8');
 assert.match(scenes,/deepEqual\(writes,\[\]/);assert.match(scenes,/\[1440,390\]/);
 const shop=fs.readFileSync(path.join(__dirname,'thoradin-wallet-smoke.cjs'),'utf8');
 assert.match(shop,/price_copper===50/);assert.match(shop,/silver_coins:20/);
 assert.match(shop,/page.reload\(\)/);
 const reloaded=shop.slice(shop.indexOf('await player.page.reload()'));
 const sheetAt=reloaded.indexOf('name:/Ficha$/');
 assert.ok(sheetAt>=0&&sheetAt<reloaded.indexOf('Prata: saldo'),
  'Player reload returns to Session; open the real sheet before inspecting its wallet');
 assert.match(reloaded,/raziel-wallet-reload-390\.png/);
});

test('passive rehearsal activates current clickable blood cards, not hidden Use buttons',()=>{
 const source=fs.readFileSync(path.join(__dirname,'hemomancy-passives-smoke.cjs'),'utf8');
 assert.doesNotMatch(source,/card\.getByRole\('button',\{name:'Usar'/);
 assert.doesNotMatch(source,/shieldCard\.getByRole\('button',\{name:'Usar'/);
 assert.match(source,/await card\.click\(\{position:\{x:8,y:8\}\}\)/);
 assert.match(source,/await shieldCard\.click\(\{position:\{x:8,y:8\}\}\)/);
 assert.ok(source.includes("getAttribute('data-combat-version')"),'The passive flow must observe the confirmed shield snapshot in its live card');
 assert.ok(source.includes("getByText('Ação concluída. Use “Concluir e passar turno”.'"),'Passing the monster turn waits for the native completed-action UI');
});

test('summon rehearsal uses current card and grid targeting instead of legacy dropdowns',()=>{
 const source=fs.readFileSync(path.join(__dirname,'summon-turns-smoke.cjs'),'utf8');
 assert.ok(!source.includes("card.getByLabel(/^Alvo de /).selectOption"),'Corpse must be picked on the native grid');
 assert.ok(!source.includes('await button.waitFor()'),'Hidden card commands are not visible buttons');
 assert.ok(!source.includes('await endButton.click()'),'Concentration ends through its clickable card');
 assert.match(source,/async function clickCard\(page,card\)/);
 assert.ok(source.includes("getByText('Ação concluída. Use “Concluir e passar turno”.'"),
  'Wait for the native encounter refresh, not just the HTTP attack response');
});

test('combat rehearsals inspect the live GM card rather than unopened admin tools',()=>{
 for(const file of ['hemomancy-passives-smoke.cjs','summon-turns-smoke.cjs']){
  const source=fs.readFileSync(path.join(__dirname,file),'utf8');
  assert.ok(!source.includes("page.locator('.workspace-gm-tools"),file);
  assert.ok(source.includes('.workspace-combat-live'),file);
 }
});
