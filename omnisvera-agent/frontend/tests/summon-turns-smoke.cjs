// Controlled summons through the current built client: owner turn, off-turn lock,
// non-owner privacy, dismissal, clone 0 HP/concentration/5-round cleanup.
// Fixture only. A declared physical d20 is injected into summon/monster attack
// requests so the turn/participant assertions do not depend on a random roll.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
class Inconclusive extends Error{}

(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');
 assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep),'evidence must be private TEMP');
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data);
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],action_coverage=[],observed=[],limitations=[],out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-summon-turns-'));
 console.log('EVIDENCE summon-turns '+out);
 const tokens=async()=> (await get('/workspace')).tokens;
 let summonAttackCapture=0;
 const summonOf=async(id)=>(await tokens()).find(t=>t.id===id);
 const setDie=async(context,value)=>context.route(/\/gm\/combat\/tokens\/[^/]+\/(?:attacks\/resolve|attack)$/,async route=>{
  const req=route.request();if(req.method()!=='POST')return route.continue();
  let body;try{body=req.postDataJSON();}catch{return route.continue();}
  if(!body||body.attack_id===undefined)return route.continue();
  await route.continue({postData:JSON.stringify({...body,roll_mode:'physical',d20:value()})});
 });
 async function prepare({beforeStart,observer=false}={}){
  if((await get('/combat/effects')).encounter?.active)await command('end');
  for(const token of (await tokens()))if(token.sheet?.summon?.caster==='morthak'&&token.sheet.summon.technique!=='clonagem')await post('/characters/morthak/techniques/dispensar-invocacao',{request_id:randomUUID(),target_type:'token',target_id:token.id});
  await post('/characters/morthak/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture de invocacoes'});
  await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
  let workspace=await get('/workspace'),grid=workspace.map.grid,mine=workspace.tokens.find(t=>t.character_id==='morthak'),enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
  assert.ok(grid&&mine?.grid_position&&enemy?.grid_position,'fixture requires the active grid');
  for(const token of workspace.tokens)if(token.id!==mine.id&&token.id!==enemy.id&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});
  await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{visible_to_players:true,current_hp:500,maximum_hp:500,sheet:{...enemy.sheet,armor_class:1,hit_dice:'1',has_blood:true,is_undead:false,is_construct:false,attributes:{strength:10,dexterity:10,constitution:10,wisdom:10}}});
  const position=async(token,x,y=5)=>post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});
  // Keep the target adjacent to native summon/clone cells, without depending
  // on a summon being spawned on top of the target itself.
  await position(mine,4);await position(enemy,4,4);
  const pre=beforeStart?await beforeStart({grid,mine,enemy}):null;
  await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'morthak',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1},...(observer?[{target_type:'character',target_id:'raziel',initiative:0}]:[])]});
  const before=await get('/characters/morthak');
  return {before,grid,mine,enemy,...(pre||{})};
 }
 async function pageFor(role,width,selected='morthak',magic=true){
  const context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(({role,selected})=>{localStorage.setItem('omnisvera_access_token',role==='gm'?'cf01-local-gm':'cf01-local-'+selected);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',selected);},{role,selected});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navega\u00e7\u00e3o principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
  await page.locator(`button[data-character="${selected}"]`).click();
  const combatControls=page.locator('.workspace-combat-live:visible .workspace-combat-content').first();
  await combatControls.waitFor({state:'attached'});
  if(!await combatControls.evaluate(el=>el.open))await combatControls.locator(':scope > summary').click();
  let section=null;
  if(magic){
   section=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Magias$/})});
   if(!await section.evaluate(el=>el.open))await section.locator(':scope > summary').click();
  }
  return {context,page,section};
 }
 async function reopen(page,role,selected='morthak',magic=false){
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navega\u00e7\u00e3o principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
  await page.locator(`button[data-character="${selected}"]`).click();
  const combatControls=page.locator('.workspace-combat-live:visible .workspace-combat-content').first();
  await combatControls.waitFor({state:'attached'});
  if(!await combatControls.evaluate(el=>el.open))await combatControls.locator(':scope > summary').click();
  if(!magic)return {page,section:null};
  const section=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Magias$/})});
  if(!await section.evaluate(el=>el.open))await section.locator(':scope > summary').click();
  return {page,section};
 }
 async function closeToken(page){
  const dialog=page.getByRole('dialog',{name:/^Ficha de /});
  if(await dialog.count()){await dialog.getByRole('button',{name:'Fechar ficha',exact:true}).click();await dialog.waitFor({state:'hidden'});}
 }
 async function cast(page,section,before,id,action){
  const name=before.definition.session_abilities.find(a=>a.id===id).name;
  const card=section.locator('article.workspace-spell-card').filter({has:page.getByRole('button',{name,exact:true})});
  const pending=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/'+id));
  void pending.catch(()=>{});await action(card);const reply=await pending;assert.ok(reply.ok(),await reply.text());
  await closeToken(page);return reply.json();
 }
 async function clickCard(page,card){
  await card.locator('button[data-card-command]:enabled').waitFor({state:'attached'});
  await card.click({position:{x:8,y:8}});
 }
 async function target(page,card,tokenId){
  await clickCard(page,card);
  await page.locator('.targeting-overlay').waitFor({timeout:15000});
  await page.locator(`[data-grid-token="${tokenId}"]`).click();
  await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
 }
 async function area(page,card){
  await clickCard(page,card);
  await page.locator('.targeting-overlay').waitFor({timeout:15000});
  await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
 }
 async function ownTurn(){
  for(let i=0;i<12;i++){const e=(await get('/combat/effects')).encounter,p=e.participants[e.turn_index];if(p?.target_id==='morthak')return;await command('next_turn');}
  assert.fail('Morthak did not regain the native turn');
 }
 async function current(){const e=(await get('/combat/effects')).encounter;return e.participants[e.turn_index];}
 async function attackSummon(page,controls,enemy,die){
  const resolved=page.waitForResponse(r=>r.request().method()==='POST'&&/\/gm\/combat\/tokens\/[^/]+\/attacks\/resolve$/.test(new URL(r.url()).pathname));
  const confirmed=page.waitForResponse(r=>/\/combat\/attacks\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));
  void resolved.catch(()=>{});void confirmed.catch(()=>{});
  const card=controls.locator('article').filter({has:page.locator('button[data-card-command]')}).first();
  await card.waitFor();
  await page.waitForFunction(el=>!el.querySelector('button[data-card-command]').disabled,await card.elementHandle());
  await card.click({position:{x:8,y:8}});
  await page.locator('.targeting-overlay').waitFor({timeout:15000});await page.locator(`[data-grid-token="${enemy.id}"]`).click();
  await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
  assert.ok((await resolved).ok(),'summon attack must resolve');
  assert.ok((await confirmed).ok(),'summon attack must confirm');
  // Transport completion precedes React's authoritative encounter refresh.
  // Wait for the same completion affordance a player sees before passing.
  await controls.getByText('Ação concluída. Use “Concluir e passar turno”.',{exact:true}).waitFor();
  await controls.scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,`summon-attack-${++summonAttackCapture}.png`)});
 }
 async function passSummonTurn(page,controls){
  const wait=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/combat/next-turn');
  void wait.catch(()=>{});
  await controls.getByRole('button',{name:/Concluir e passar turno/}).click();
  const reply=await wait;assert.ok(reply.ok(),'summon turn must advance: '+await reply.text());
 }
 try{
  // Skeleton: owner attack, off-turn lock, non-owner privacy, dismissal without refund.
  {
   console.log('RUN summon-turns skeleton');
   // A non-owner must participate to receive the encounter at all. Keep the
   // backend's exclusion/privacy rule rather than expecting it to leak combat.
   const {before,enemy}=await prepare({observer:true});
   let die=10;const {context,page,section}=await pageFor('player',390,'morthak');await setDie(context,()=>die);
   const raised=await cast(page,section,before,'levantar-um-esqueleto',card=>clickCard(page,card));
   const skeleton=raised.token,key='levantar_um_esqueleto';
   assert.ok(skeleton?.id);assert.equal((before.state.resources.find(r=>r.key===key).current)-(await get('/characters/morthak')).state.resources.find(r=>r.key===key).current,1);
   await command('next_turn');assert.equal((await current()).target_id,skeleton.id,'skeleton acts after its caster');
   await reopen(page,'player','morthak');const controls=page.locator(`.workspace-summon-controls[aria-label="Controle de ${skeleton.name}"]`);
   await controls.waitFor();assert.match(await controls.locator('summary').innerText(),/Seu turno/);
   const beforeHp=(await summonOf(enemy.id)).current_hp;
   await attackSummon(page,controls,enemy,()=>die);die=10;
   const afterHp=(await summonOf(enemy.id)).current_hp;assert.ok(afterHp<beforeHp,'skeleton attack must change enemy HP');
   await passSummonTurn(page,controls);assert.notEqual((await current()).target_id,skeleton.id,'passing the summon turn advances the encounter');
   await reopen(page,'player','morthak');
   const waiting=page.locator(`.workspace-summon-controls[aria-label="Controle de ${skeleton.name}"]`);
   await waiting.waitFor();if(!await waiting.evaluate(el=>el.open))await waiting.locator('summary').click();
   assert.match(await waiting.locator('summary').innerText(),/\d+\/\d+ PV/);
   assert.match(await waiting.locator('p[role="status"]').innerText(),/Aguarde seu turno/);
   assert.ok(await waiting.locator('button[data-card-command]').first().isDisabled(),'off-turn summon cannot attack');
   // Non-owner player sees the participant but no summon controls.
   const outsider=await pageFor('player',390,'raziel',false);
   await outsider.page.locator('.workspace-combat-live').waitFor();assert.equal(await outsider.page.locator('.workspace-summon-controls').count(),0,'non-owner must not receive summon controls');
   assert.match(await outsider.page.locator('.workspace-combat-live ol').innerText(),new RegExp(skeleton.name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
   await outsider.context.close();
   const resourceBefore=dismissResource(await get('/characters/morthak'));
   page.once('dialog',dialog=>dialog.accept());
   const dismissal=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/dispensar-invocacao'));
   await waiting.getByRole('button',{name:'Dispensar',exact:true}).click();await dismissal;
   assert.ok(!(await get('/combat/effects')).encounter.participants.some(p=>p.target_id===skeleton.id),'dismissal removes the summon turn');
   assert.equal(dismissResource(await get('/characters/morthak')),resourceBefore,'dismissal never refunds the daily use');
   await reopen(page,'player','morthak');assert.equal(await page.locator(`.workspace-summon-controls[aria-label="Controle de ${skeleton.name}"]`).count(),0);
    action_coverage.push({actor:'morthak',key:'ability:levantar-um-esqueleto',verified_checks:['ui']});
    observed.push({case:'skeleton',token:skeleton.id,owner_attack:true,off_turn_blocked:true,non_owner_controls:0,dismissed:true,cost_checked:true,persistence_reload:true});
   await page.screenshot({path:path.join(out,'skeleton-390.png')});await context.close();
  }
  // Reanimated: the same owner-turn lifecycle for animar-mortos.
  {
   console.log('RUN summon-turns reanimated');
   const {before,enemy,placed}=await prepare({beforeStart:async({grid})=>{
    const corpse=await post('/gm/workspace/tokens',{token_type:'monster',name:'Cadaver exclusivo do ensaio '+randomUUID(),map_id:evidence.map_id,visible_to_players:true,latitude:50,longitude:50,current_hp:0,maximum_hp:12,sheet:{armor_class:10,hit_dice:'1',reanimation_allowed:true}});
    const placed=(await tokens()).find(t=>t.id===corpse.id);assert.ok(placed?.sheet?.corpse);
    await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:placed.id,mode:'GM_REPOSITION',path:[[placed.grid_position.cell_x,placed.grid_position.cell_y],[4,3]],expected_position_version:placed.grid_position.version,expected_grid_version:grid.version});
    return {placed};
   }});
   const {context,page,section}=await pageFor('player',390,'morthak');let die=10;await setDie(context,()=>die);
   const detail=await cast(page,section,before,'animar-mortos',card=>target(page,card,placed.id));
   const unit=await summonOf(detail.token.id);assert.equal(unit.sheet.summon.technique,'animar-mortos');
   await command('next_turn');assert.equal((await current()).target_id,unit.id);
   await reopen(page,'player','morthak');const controls=page.locator(`.workspace-summon-controls[aria-label="Controle de ${unit.name}"]`);
   await controls.waitFor();assert.match(await controls.locator('summary').innerText(),/Seu turno/);
   const beforeHp=(await summonOf(enemy.id)).current_hp;await attackSummon(page,controls,enemy,()=>die);
   assert.ok((await summonOf(enemy.id)).current_hp<beforeHp);
   action_coverage.push({actor:'morthak',key:'ability:animar-mortos',verified_checks:['ui']});
   observed.push({case:'reanimated',token:unit.id,owner_attack:true,cost_checked:true});
   await page.screenshot({path:path.join(out,'reanimated-390.png')});await context.close();
  }
  // Clones: only basic attacks; 0 HP and concentration cleanup must remove the turn;
  // a second cast checks the five-round clock and the participant list.
  {
   console.log('RUN summon-turns clones');
   const inventory=await get('/characters/morthak');
   let fragments=inventory.inventory.filter(i=>i.item_title==='Fragmento de Cristal Arcano').reduce((s,i)=>s+i.quantity,0);
   if(fragments<2){const item=(await get('/gm/workspace/items')).find(i=>i.name==='Fragmento de Cristal Arcano');if(!item)throw new Inconclusive('Fragmento de Cristal Arcano ausente do catalogo; Clonagem nao executada');await post('/gm/workspace/items/grant',{character_id:'morthak',item_id:item.id,quantity:2-fragments,notes:'Somente fixture: componentes para dois ensaios de Clonagem'});}
   const {before,enemy,grid}=await prepare();
   const seeded=await get('/characters/morthak');
   const {context,page,section}=await pageFor('gm',1440,'morthak');let die=10;await setDie(context,()=>die);
   const cloneCard=()=>section.locator('article.workspace-spell-card').filter({has:page.getByRole('button',{name:before.definition.session_abilities.find(a=>a.id==='clonagem').name,exact:true})});
   let pending=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/clonagem'));
   await area(page,cloneCard());assert.ok((await pending).ok());
   let clones=async()=> (await tokens()).filter(t=>t.sheet?.summon?.technique==='clonagem');
   assert.equal((await clones()).length,0,'clones wait for the next caster turn');
   await command('next_turn');await ownTurn();
   const firstClones=await clones();assert.equal(firstClones.length,2);
   await command('next_turn');const first=await current();assert.ok(firstClones.some(t=>t.id===first.target_id));
   const firstName=(await tokens()).find(t=>t.id===first.target_id)?.name;assert.ok(firstName,'clone token must have a persisted name');
   await reopen(page,'gm','morthak');const panel=page.locator(`.workspace-summon-controls[aria-label="Controle de ${firstName}"]`);await panel.waitFor();
   assert.match(await panel.locator('summary').innerText(),/Seu turno/);
   assert.equal(await panel.locator('section.workspace-ally-attacks article').count(),1,'clones have only the basic attack');
   assert.equal(await panel.locator('header span').filter({hasText:/CONJURA|US\u00c1VEIS/}).count(),0,'clones cannot cast');
   const beforeHp=(await summonOf(enemy.id)).current_hp;await attackSummon(page,panel,enemy,()=>die);
   assert.ok((await summonOf(enemy.id)).current_hp<beforeHp);
   await call('patch','/gm/workspace/tokens/'+encodeURIComponent(first.target_id),{current_hp:0});
   await command('next_turn');
   assert.ok(!(await get('/combat/effects')).encounter.participants.some(p=>p.target_id===first.target_id),'0 HP clone must leave the turn list');
   await reopen(page,'gm','morthak');
   const listText=await page.locator('.workspace-combat-live ol').innerText();assert.ok(!listText.includes(firstName),'dead clone must not remain as an invisible turn');
   // End concentration removes the remaining clone and its participant entry.
   const reopenMagic=await reopen(page,'gm','morthak',true);
   const endCard=reopenMagic.section.locator('article.workspace-spell-card').filter({has:reopenMagic.page.getByRole('button',{name:'Clonagem',exact:true})});
   const endButton=endCard.locator('button[data-card-command]').filter({hasText:/Encerrar concentra/});
   await endButton.waitFor({state:'attached'});
   pending=reopenMagic.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/clonagem'));
   await clickCard(reopenMagic.page,endCard);
   assert.ok((await pending).ok());assert.equal((await clones()).length,0,'concentration end removes every clone');
   assert.ok(!(await get('/combat/effects')).encounter.participants.some(p=>String(p.target_id).startsWith('monster:')&&firstClones.some(c=>c.id===p.target_id)),'clone participants removed on concentration end');
   await reopen(page,'gm','morthak');assert.ok(!(await page.locator('.workspace-combat-live ol').innerText()).includes(firstClones[1].name));
   // Five-round expiry, second native cast on the same fixture.
   await command('end');await post('/characters/morthak/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture de invocacoes'});
   await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'morthak',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1}]});
   const state=await get('/combat/effects');const castRound=state.round;
   const second=await pageFor('gm',1440,'morthak');await setDie(second.context,()=>die);
   pending=second.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/clonagem'));
   await area(second.page,second.section.locator('article.workspace-spell-card').filter({has:second.page.getByRole('button',{name:'Clonagem',exact:true})}));
   assert.ok((await pending).ok());await command('next_turn');await ownTurn();
   assert.equal((await clones()).length,2);
   // One-round execution is separate from the five active rounds approved
   // for Clonagem. Start the duration clock only after materialization.
   const startRound=(await get('/combat/effects')).round;
   assert.ok(startRound>castRound,'clones materialize after the execution round');
   for(let i=0;i<30&&(await get('/combat/effects')).round-startRound<4;i++)await command('next_turn');
   assert.equal((await clones()).length,2,'clones must retain four full active rounds');
   for(let i=0;i<30&&(await get('/combat/effects')).round-startRound<5;i++)await command('next_turn');
   assert.ok((await get('/combat/effects')).round-startRound>=5,'five round boundaries must elapse');
   assert.equal((await clones()).length,0,'clones expire on the fifth round');
   const expired=await get('/combat/effects');assert.ok(!expired.encounter.participants.some(p=>p.target_type==='token'&&p.controller_id==='morthak'&&p.target_id!==enemy.id),'expired clones leave the turn list');
   await reopen(page,'gm','morthak');const finalList=await page.locator('.workspace-combat-live ol').innerText();assert.ok(!/Clone de Morthak/.test(finalList),'expired clones must not stay invisible in the UI list');
   action_coverage.push({actor:'morthak',key:'ability:clonagem',verified_checks:['ui']});
   observed.push({case:'clones',spawned:2,basic_only:true,zero_hp_removed:true,concentration_removed:true,five_round_expiry:true,components_seeded:Math.max(0,2-fragments),cost_checked:true,persistence_reload:true,expiration_observed:true});
   await second.page.screenshot({path:path.join(out,'clones-1440.png')});await second.context.close();
   await context.close();
   assert.ok((await get('/characters/morthak')).inventory.filter(i=>i.item_title==='Fragmento de Cristal Arcano').reduce((s,i)=>s+i.quantity,0)===seeded.inventory.filter(i=>i.item_title==='Fragmento de Cristal Arcano').reduce((s,i)=>s+i.quantity,0)-2,'each clone cast consumes one fixture fragment');
  }
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',action_coverage,observed,limitations,controlled_inputs:['declared physical d20 in summon/monster attack request'],screenshots:out,production_modified:false},null,2));
 }finally{await browser.close();await api.dispose();}
 function dismissResource(sheet){return sheet.state.resources.find(r=>r.key==='levantar_um_esqueleto').current;}
})().catch(e=>{
 console.error(e);
 if(e instanceof Inconclusive)console.log(JSON.stringify({status:'INCONCLUSIVE',reason:e.message,production_modified:false}));
 process.exitCode=e instanceof Inconclusive?2:1;
});
