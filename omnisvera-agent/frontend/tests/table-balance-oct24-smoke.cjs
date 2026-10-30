// Fixed native test suite, never operational tokens or real campaign writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.equal(base,'http://127.0.0.1:8871');
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api.fetch(url,{method,data});assert.ok(r.ok(),await r.text());return r.json();},get=url=>call('GET',url),post=(url,data)=>call('POST',url,data);
 const health=await get('/health');for(const p of [health.database_path,health.vault_path])assert.ok(path.resolve(p).startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(process.env.OMNISVERA_SIMULATION_EVIDENCE,'utf8'));
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-oct24-ui-')),screenshots=[],errors=[],checks=[];
 const browser=await chromium.launch({channel:'msedge',headless:true});let current;
 async function open(actor,width){
  const gm=actor==='dorn7',context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
  await context.addInitScript(({actor,gm})=>{localStorage.setItem('omnisvera_access_token',gm?'cf01-local-gm':'cf01-local-'+actor);localStorage.setItem('omnisvera_access_mode',gm?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{actor,gm});
  const page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:gm?/Mesa$/:/Ficha$/}).click();await page.locator(`button[data-character="${actor}"]`).click();
  return {context,page};
 }
 async function move(token,x,y,grid){await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});}
 try{
  if((await get('/combat/effects')).encounter?.active)await command('end');
  await call('PATCH','/gm/workspace/maps/active',{map_id:evidence.map_id});
  for(const actor of ['vezemir','morthak','raziel','dorn7'])await post(`/characters/${actor}/actions`,{request_id:randomUUID(),action:'rest_at_inn',payload:{}});
  let ws=await get('/workspace'),grid=ws.map.grid,enemy=ws.tokens.find(t=>t.id===evidence.enemy_id),raz=ws.tokens.find(t=>t.character_id==='raziel'),dorn=ws.tokens.find(t=>t.character_id==='dorn7');
  for(const [token,x,y] of [[raz,5,5],[dorn,5,6],[enemy,6,5]]){await call('PATCH','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:true});await move(token,x,y,grid);}
  await call('PATCH','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{current_hp:25,maximum_hp:100,sheet:{...enemy.sheet,armor_class:1,has_blood:true,is_undead:false,is_construct:false}});
  await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:30},{target_type:'token',target_id:enemy.id,initiative:10},{target_type:'character',target_id:'dorn7',initiative:1}]});
  // All four sheets render; inactive outsiders do not gain a combat panel.
  for(const [actor,width] of [['vezemir',390],['morthak',1440]]){const {context,page}=await open(actor,width);await page.locator('.workspace-character-panel').waitFor();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await context.close();}
  current=await open('raziel',390);let {page,context}=current;
  assert.equal(await page.locator('.workspace-combat-content').first().evaluate(el=>el.open),false);
  for(const summary of await page.locator('.workspace-sheet-section>summary').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();
  const blood=(await get('/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue');assert.equal(blood.maximum,10);assert.equal(blood.current,10);
  await context.route(/\/characters\/raziel\/techniques\/hemomancia-foice-habilidade$/,route=>route.continue({postData:JSON.stringify({...route.request().postDataJSON(),roll_mode:'physical',d20:15})}));
  const card=page.locator('article.workspace-spell-card').filter({has:page.getByRole('button',{name:'Ceifa Rubra',exact:true})});
  const resolved=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/hemomancia-foice-habilidade'));
  await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();await page.locator(`[data-grid-token="${enemy.id}"]`).click();await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
  const preview=await (await resolved).json();assert.equal(preview.breakdown.hemomancy.passive_d6,1);
  await page.waitForFunction(()=>document.querySelector('[aria-label="Arma ativa"]')?.getAttribute('title')==='Foice de Sangue');
  let state=await get('/combat/effects');assert.equal(state.effects.find(e=>e.hemomancy_kind==='bleed').remaining_turns,2);assert.equal(state.active_effect_icons.find(e=>e.card.name==='Ceifa Rubra').turns_remaining,2);
  assert.equal((await get('/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current,9);
  const shot=path.join(out,'raziel-ceifa-390.png');await page.locator('.workspace-hemomancy').screenshot({path:shot});screenshots.push(shot);
  checks.push('Ceifa: +1d6 at 25%, cost 1, active scythe, visible two-turn bleeding');
  for(let tick=0;tick<2;tick++){
   const before=(await get('/workspace')).tokens.find(t=>t.id===enemy.id).current_hp;
   const body={request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action:'next_turn',payload:{}};
   await post('/combat/next-turn',body);const after=(await get('/workspace')).tokens.find(t=>t.id===enemy.id).current_hp;assert.ok(before-after>=1&&before-after<=4);
   await post('/combat/next-turn',body);assert.equal((await get('/workspace')).tokens.find(t=>t.id===enemy.id).current_hp,after);
   await command('next_turn');await command('next_turn');
  }
  assert.ok(!(await get('/combat/effects')).effects.some(e=>e.hemomancy_kind==='bleed'));checks.push('Two pre-turn ticks and no duplicate retry damage');
  await context.close();current=null;await command('end');
  await command('dorn_spell_cast',{spell_id:'reflexos'});
  current=await open('dorn7',1440);page=current.page;
  const count=(await get('/combat/effects')).effects.find(e=>e.spell==='reflexos').images_remaining;
  await page.waitForFunction(n=>document.querySelectorAll('.workspace-map-spell-effects image').length===n,count);
  await command('dorn_spell_cast',{spell_id:'teia',targets:[{type:'token',id:enemy.id}]});
  await page.locator('.workspace-map-spell-effects [aria-label="Área de Teia"]').waitFor({state:'attached'});
  const mapShot=path.join(out,'dorn-reflections-web-1440.png');await page.locator('.workspace-map-spell-effects').locator('..').screenshot({path:mapShot});screenshots.push(mapShot);checks.push('Dorn reflection images and web area visible');
  await current.context.close();current=null;
  // Approved new pipeline: healthy cross selection, one charge, multiplier and speed.
  await post('/characters/raziel/actions',{request_id:randomUUID(),action:'rest_at_inn',payload:{}});
  await call('PATCH','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{current_hp:100,maximum_hp:100});
  current=await open('raziel',390);page=current.page;
  const abilitiesSummary=page.locator('.workspace-sheet-section>summary').filter({hasText:'Habilidades'}).first();await abilitiesSummary.waitFor();
  if(!await abilitiesSummary.evaluate(el=>el.parentElement.open))await abilitiesSummary.click();
  for(const summary of await page.locator('.workspace-sheet-section>summary').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();
  const markCard=page.locator('.workspace-action-catalog article').filter({has:page.getByRole('button',{name:'Marca Rubra',exact:true})});
  await markCard.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
  await page.locator(`[data-grid-token="${enemy.id}"]`).click();
  assert.equal(await page.locator('.targeting-cross-cell').count(),5);
  const markResponse=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/marca-rubra'));
  await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
  assert.equal((await markResponse).status(),200);
  assert.equal((await get('/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current,9);
  const boostResponse=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/reforco'));
  await page.getByRole('button',{name:'x2',exact:true}).click();assert.equal((await boostResponse).status(),200);
  await page.getByRole('button',{name:'x2',exact:true,pressed:true}).waitFor();
  assert.equal((await get('/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current,7);
  const speedCard=page.locator('.workspace-action-catalog article').filter({has:page.getByRole('button',{name:'Velocidade',exact:true})});
  // The boost response arrives before its sheet refresh finishes. Card clicks
  // intentionally ignore disabled commands; wait for that native lock to clear.
  await page.waitForFunction(button=>!button.disabled,await speedCard.locator('button[data-card-command]').elementHandle());
  const speedResponse=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/velocidade'));
  await speedCard.click({position:{x:8,y:8}});assert.equal((await speedResponse).status(),200);
  state=await get('/combat/effects');assert.ok(state.effects.some(e=>e.skill==='raziel_speed'));
  assert.equal(state.effects.find(e=>e.hemomancy_kind==='boost').turns_remaining,2);
  const boostShot=path.join(out,'raziel-cross-boost-speed-390.png');await page.locator('.workspace-blood-multipliers').screenshot({path:boostShot});screenshots.push(boostShot);
  const vitalsShot=path.join(out,'raziel-vitals-390.png');await page.locator('.workspace-vitals-and-controls').screenshot({path:vitalsShot});screenshots.push(vitalsShot);
  checks.push('Healthy Mark Rubra cross / cost 1; x2 BA+damage / cost 2 / two turns; native Speed from player card');
  await current.context.close();current=null;
  const preparation=await post('/gm/scenes',{request_id:randomUUID(),title:'Ensaio seletivo de preparação',location_name:'Fixture',map_id:evidence.map_id,visibility:'gm'});
  await post(`/gm/scenes/${preparation.id}/elements`,{request_id:randomUUID(),element_type:'clue',title:'Pista do ensaio',public_description:'Descrição pública.',private_description:'Nota privada da fixture.',visibility:'gm',status:'hidden'});
  current=await open('dorn7',390);page=current.page;
  let publications=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/selection-on-table'))publications++;});
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).click();
  await page.locator('.scene-library-card').filter({hasText:'Ensaio seletivo de preparação'}).click();
  await page.getByRole('checkbox',{name:'Selecionar Pista do ensaio',exact:true}).check();
  await page.getByRole('button',{name:'Levar seleção à Mesa',exact:true}).click();
  const selectionDialog=page.getByRole('dialog',{name:'Confirmar envio à Mesa'});await selectionDialog.waitFor();
  const sceneShot=path.join(out,'scene-selection-390.png');await page.screenshot({path:sceneShot});screenshots.push(sceneShot);
  await selectionDialog.getByRole('button',{name:'Cancelar',exact:true}).click();
  assert.equal(publications,0);assert.equal((await get('/scenes/'+preparation.id)).status,'draft');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  checks.push('Scene cards: native element selection, mobile confirmation, cancel sends no publication');
  await current.context.close();current=null;
  assert.deepEqual(errors,[]);
  await require('./bestiary-rules-smoke.cjs')({browser,api,base,out,screenshots,checks});
  await require('./monster-combat-smoke.cjs')({browser,api,base,out,screenshots,checks});
  await require('./monster-conditions-smoke.cjs')({browser,api,base,out,screenshots,checks});
  console.log(JSON.stringify({status:'PASS',checks,screenshots,physical_die_injected:15,production_modified:false,visual_acceptance:'pending_agent_image_review',limitations:'One host, fixture only; reflections are derived images, not independent combatants.'}));
 }finally{if(current)await current.context.close();await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
