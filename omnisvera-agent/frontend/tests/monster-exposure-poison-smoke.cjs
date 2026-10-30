// Bounded native UI rehearsal; every mutation is restricted to the TEMP fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.equal(base,'http://127.0.0.1:8871');
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api.fetch(url,{method,data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('GET',url),post=(url,data)=>call('POST',url,data);
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const end=async()=>{if((await get('/combat/effects')).encounter?.active)await command('end');};
 const clear=async()=>{for(const e of (await get('/combat/effects')).effects.filter(e=>e.monster_condition))await command('remove',{id:e.id});};
 const rest=async()=>{await end();for(const actor of ['raziel','morthak','vezemir','dorn7'])await post(`/characters/${actor}/actions`,{request_id:randomUUID(),action:'rest_at_inn',payload:{}});};
 await rest();await clear();let ws=await get('/workspace');const mapId=ws.map.id,raz=ws.tokens.find(t=>t.character_id==='raziel');assert.ok(raz);
 const catalog=(await get('/gm/workspace/monster-catalog')).monsters;
 async function create(id,name,extra={}){const source=catalog.find(m=>m.id===id);assert.ok(source);return post('/gm/workspace/tokens',{token_type:'monster',name,map_id:mapId,current_hp:1000,maximum_hp:1000,visible_to_players:true,sheet:{...source,...extra,source:{monster_id:id}}});}
 const tank=await create('goblin','Alvo de ensaio de exposição',{armor_class:1,saving_throw:100,attributes:{strength:17,dexterity:14,constitution:12,intelligence:10}});
 const immune=await create('cocatriz','Imune no ensaio de gás'),outside=await create('goblin','Fora do gás');
 async function move(id,x,y){ws=await get('/workspace');const t=ws.tokens.find(t=>t.id===id);return post(`/workspace/maps/${encodeURIComponent(mapId)}/move`,{request_id:randomUUID(),token_id:id,mode:'GM_REPOSITION',path:[[t.grid_position.cell_x,t.grid_position.cell_y],[x,y]],expected_position_version:t.grid_position.version,expected_grid_version:ws.map.grid.version});}
 async function start(actor,targets){await end();await clear();await move(actor.id,28,28);await move(tank.id,29,28);await move(raz.id,31,28);await move(immune.id,28,31);await move(outside.id,39,39);
  await command('start',{map_id:mapId,battle_mode:true,participants:[{target_type:'token',target_id:actor.id,name:actor.name,initiative:100},...targets.map((t,i)=>({target_type:t.id===raz.id?'character':'token',target_id:t.id===raz.id?'raziel':t.id,name:t.name,initiative:20-i}))]});}
 const browser=await chromium.launch({channel:'msedge',headless:true}),out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-exposure-ui-')),screenshots=[],checks=[];let current;
 async function open(width,player=false){
  const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
  await context.addInitScript(player=>{localStorage.setItem('omnisvera_access_token',player?'cf01-local-raziel':'cf01-local-gm');localStorage.setItem('omnisvera_access_mode',player?'player':'gm');localStorage.setItem('omnisvera_selected_character',player?'raziel':'dorn7');},player);
  await context.route(/\/gm\/combat\/tokens\/[^/]+\/attacks\/resolve$/,route=>route.continue({postData:JSON.stringify({...route.request().postDataJSON(),roll_mode:'physical',d20:15})}));
  const page=await context.newPage();page.setDefaultTimeout(15000);await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:player?/Ficha$/:/Mesa$/}).click();await page.locator(`button[data-character="${player?'raziel':'dorn7'}"]`).click();
  if(!player){await page.locator('.workspace-combat-content > summary').first().waitFor();for(const summary of await page.locator('.workspace-combat-content > summary:visible').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();}
  return {page,context};
 }
 async function shot(page,name){const file=path.join(out,name+'.png');await page.screenshot({path:file});screenshots.push(file);}
 async function use(page,actor,name,target,action='monster_breath',cancel=false){
  const panel=page.getByRole('region',{name:'Ataques de '+actor.name,exact:true});await panel.waitFor();
  const card=panel.locator('article').filter({has:page.locator('strong').filter({hasText:new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$')})});
  // Compact cards activate from their surface; the command button is intentionally hidden.
  await card.locator('button[data-card-command]').waitFor({state:'attached'});
  await page.waitForFunction(button=>!button.disabled,await card.locator('button[data-card-command]').elementHandle());
  await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
  // The range response arrives after the loading overlay; click only a selectable pin.
  await page.locator(`[data-grid-token="${target.id}"].target-valid`).waitFor();
  await page.locator(`[data-grid-token="${target.id}"]`).click();
  const dialog=page.getByRole('dialog',{name:'Confirmar alvo'});await dialog.waitFor();
  if(cancel){await dialog.getByRole('button',{name:'Não',exact:true}).click();await page.locator('.targeting-overlay').waitFor({state:'hidden'});return;}
  if(name==='Petrificação')await shot(page,'gaze-range-1440');
  if(name==='Baforada Petrificante')await shot(page,'gorgon-area-390');
  const response=page.waitForResponse(r=>r.request().method()==='POST'&&(action==='attack'?/\/combat\/attacks\/[^/]+\/confirm$/.test(new URL(r.url()).pathname):r.url().endsWith('/gm/combat/effects')&&r.request().postDataJSON()?.action===action));
  await dialog.getByRole('button',{name:'Sim',exact:true}).click();const r=await response;assert.equal(r.status(),200);return {body:r.request().postDataJSON(),result:await r.json()};
 }
 async function attackApi(actor,index,target=tank){const preview=await post(`/gm/combat/tokens/${actor.id}/attacks/resolve`,{request_id:randomUUID(),attack_id:String(index),target_type:'token',target_id:target.id,roll_mode:'physical',d20:15,range_cells:1});return post('/combat/attacks/'+preview.resolution_id+'/confirm');}
 try{
  // Direct contact is an explicit GM confirmation, never inferred from distance.
  const basilisk=await create('basilisco','Ensaio Olhar');await start(basilisk,[raz,tank]);current=await open(1440);let {page}=current;
  let sent=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/gm/combat/effects')&&r.postDataJSON()?.action==='monster_breath')sent++;});
  await use(page,basilisk,'Petrificação',raz,'monster_breath',true);assert.equal(sent,0);
  const applied=await use(page,basilisk,'Petrificação',tank);assert.equal(applied.body.payload.eye_contact_confirmed,true);assert.equal(applied.result.protocol_result.results.length,1);assert.equal(sent,1);
  assert.ok(applied.result.protocol_result.results[0].condition.effect_id);assert.equal(applied.result.protocol_result.results[0].damage_dealt,0);
  const replay=await post('/gm/combat/effects',applied.body);assert.deepEqual(replay,applied.result);
  await shot(page,'gaze-confirmed-1440');checks.push('Gaze: card/grid/cancel sends no command; confirmed eye contact; one target and idempotent replay');
  await current.context.close();current=null;

  // Gorgon: all combatants in the native circular area, independent JP and immunity.
  const gorgon=await create('gorgon','Ensaio Górgon');await start(gorgon,[tank,immune,outside]);current=await open(390);page=current.page;
  const gas=await use(page,gorgon,'Baforada Petrificante',tank);const results=gas.result.protocol_result.results;
  assert.equal(results.length,2);assert.ok(results.find(r=>r.target_id===tank.id).condition.effect_id);assert.ok(results.find(r=>r.target_id===immune.id).condition.immune);
  assert.ok(!results.some(r=>r.target_id===outside.id));assert.ok(gas.result.encounter.action_committed);
  const log=page.locator('.workspace-timeline article').filter({hasText:`${gorgon.name} usou Baforada Petrificante`}).first();await log.getByRole('button',{name:'Ver resultado',exact:true}).click();
  const detail=page.getByRole('dialog').filter({hasText:'Resultado: '+gorgon.name+' usou'});await detail.waitFor();assert.match(await detail.innerText(),/até remoção/);assert.ok(!((await detail.innerText()).includes('source_token_id')));await shot(page,'gorgon-result-390');
  await current.context.close();current=null;await end();await clear();
  checks.push('Gorgon: mobile circle, per-target JP, petrification without HP loss, explicit immunity and out-of-range exclusion');

  // Six API attacks prepare the fixture; the seventh is executed from the actual card.
  const golem=await create('golem-de-ferro','Ensaio Carga de Gás');await start(golem,[tank]);
  for(let i=0;i<6;i++){const record=await attackApi(golem,0);await post('/combat/attacks/'+record.resolution_id+'/confirm');await command('next_turn');await command('next_turn');}
  current=await open(1440);page=current.page;let panel=page.getByRole('region',{name:'Ataques de '+golem.name,exact:true});
  let gasCard=panel.locator('article').filter({has:page.locator('strong').filter({hasText:/^Baforada de gás$/})});assert.equal(await gasCard.locator('button[data-card-command]').isDisabled(),true);assert.ok((await gasCard.innerText()).includes('0/1'));
  await use(page,golem,catalog.find(m=>m.id==='golem-de-ferro').attacks[0].name,tank,'attack');
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('article')).some(el=>el.querySelector('strong')?.textContent==='Baforada de gás'&&el.textContent.includes('1/1')));
  await command('next_turn');await command('next_turn');await page.reload();await page.locator('.workspace-combat-content > summary').first().waitFor();
  for(const summary of await page.locator('.workspace-combat-content > summary:visible').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();
  const emitted=await use(page,golem,'Baforada de gás',tank);assert.ok(emitted.result.protocol_result.damage_total>=3);
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('article')).some(el=>el.querySelector('strong')?.textContent==='Baforada de gás'&&el.textContent.includes('0/1')));
  await shot(page,'golem-gas-counter-1440');
  const actions=await get(`/gm/workspace/tokens/${golem.id}/actions`);assert.equal(actions.native_breaths['Baforada de gás'].attacks_until_ready,7);
  await current.context.close();current=null;checks.push('Golem: seventh confirmed card attack unlocks gas, previews/retries do not add charge, gas spends charge and action');

  // Real automatic failed JP from a configured fixture NPC, with no guessed attributes.
  const homunculus=await create('homunculo','Ensaio Veneno Adiado');await start(homunculus,[tank]);current=await open(390);page=current.page;
  const sleepAttack=await use(page,homunculus,'Mordida',tank,'attack');let fx=(await get('/combat/effects')).effects.find(e=>e.target_id===tank.id&&e.poison_runtime);assert.ok(fx);assert.equal(fx.blocks_actions,false);
  await end();await command('dorn_spell_time',{seconds:fx.remaining_seconds-1});assert.equal((await get('/combat/effects')).effects.find(e=>e.id===fx.id).blocks_actions,false);
  await command('dorn_spell_time',{seconds:1});fx=(await get('/combat/effects')).effects.find(e=>e.id===fx.id);assert.equal(fx.monster_condition,'asleep');assert.equal(fx.blocks_actions,true);
  await page.reload();const sleepBadge=page.locator(`[data-grid-token="${tank.id}"] [title^="Sono ·"]`);
  await sleepBadge.waitFor();await sleepBadge.scrollIntoViewIfNeeded();await shot(page,'delayed-sleep-390');
  await command('dorn_spell_time',{seconds:fx.remaining_seconds});assert.ok(!(await get('/combat/effects')).effects.some(e=>e.id===fx.id));
  await current.context.close();current=null;checks.push('Homunculus: native mobile attack, no premature block, exact onset, persisted sleep badge and expiration');

  const drider=await create('drider','Ensaio Dreno de Destreza');await start(drider,[tank]);const driderHit=await attackApi(drider,1);await post('/combat/attacks/'+driderHit.resolution_id+'/confirm');await end();
  fx=(await get('/combat/effects')).effects.find(e=>e.target_id===tank.id&&e.poison_runtime);assert.ok(fx);await command('dorn_spell_time',{seconds:599});assert.equal((await get('/combat/effects')).effects.find(e=>e.id===fx.id).attribute_loss,0);
  await command('dorn_spell_time',{seconds:1});let loss=(await get('/combat/effects')).effects.find(e=>e.id===fx.id).attribute_loss;assert.ok(loss>=1&&loss<=6);
  for(let n=0;n<14&&loss<11;n++){await command('dorn_spell_time',{seconds:600});loss=(await get('/combat/effects')).effects.find(e=>e.id===fx.id).attribute_loss;}
  assert.equal(loss,11);await command('dorn_spell_time',{seconds:1200});assert.equal((await get('/combat/effects')).effects.find(e=>e.id===fx.id).attribute_loss,11);
  await clear();checks.push('Drider: confirmed attack/retry, exploration clock, real d6 losses, Dexterity floor 3, no extra loss after stopping');

  const roper=await create('roper','Ensaio Força Adiada');await start(roper,[tank]);await attackApi(roper,1);await end();
  fx=(await get('/combat/effects')).effects.find(e=>e.target_id===tank.id&&e.poison_runtime);assert.ok(fx);await command('dorn_spell_time',{seconds:fx.remaining_seconds});
  fx=(await get('/combat/effects')).effects.find(e=>e.id===fx.id);assert.equal(fx.attribute_multiplier,.5);assert.equal(fx.poison_phase,'active');await command('dorn_spell_time',{seconds:fx.remaining_seconds});
  assert.ok(!(await get('/combat/effects')).effects.some(e=>e.id===fx.id));checks.push('Roper: approved delay followed by complete weakening duration, then automatic expiration');
  await rest();await clear();
  console.log(JSON.stringify({status:'PASS',checks,screenshots,physical_die_injected:15,production_modified:false,visual_acceptance:'pending_agent_image_review',limitations:'Fixture, one host; gaze contact is confirmed by the GM, no automatic LOS; all four sheets covered by the oct24 prefix.'}));
 }catch(error){if(current){const file=path.join(out,'failure.png');await current.page.screenshot({path:file});console.error(JSON.stringify({screenshot:file,alerts:await current.page.getByRole('alert').allTextContents()}));}throw error;}
 finally{await end();if(current)await current.context.close();await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
