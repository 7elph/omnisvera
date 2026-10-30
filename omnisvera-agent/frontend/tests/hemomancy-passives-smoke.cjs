// Five approved hemomancy passives through the current built client and native commands.
// Fixture only: TEMP database, never the live campaign. Controlled physical d20 is
// injected into the declared request because the current hemomancy cards expose no
// physical-die input; this proves the trigger, not UI dice entry.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {shieldNearMiss}=require('./shield-near-miss.cjs');
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
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],action_coverage=[],observed=[],limitations=[],out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-hemomancy-passives-'));
 console.log('EVIDENCE hemomancy-passives '+out);
 let latestPage,complete=false;
 const covered=new Set();
 const hideOthers=async(mine,enemy)=>{for(const token of (await get('/workspace')).tokens)if(token.id!==mine.id&&token.id!==enemy.id&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});};
 const position=async(grid,mapId,token,x,y=5)=>post(`/workspace/maps/${encodeURIComponent(mapId)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});
 async function prepare({razielInit=20,enemyInit=1,enemyHp=500,enemyAc=1,enemyAttacks}={}){
  if((await get('/combat/effects')).encounter?.active)await command('end');
  await post('/characters/raziel/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture de passivas hemomanticas'});
  await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
  const workspace=await get('/workspace'),grid=workspace.map.grid,mine=workspace.tokens.find(t=>t.character_id==='raziel'),enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
  assert.ok(grid&&mine?.grid_position&&enemy?.grid_position,'fixture requires the active grid');
  await hideOthers(mine,enemy);
  await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{visible_to_players:true,current_hp:enemyHp,maximum_hp:500,sheet:{...enemy.sheet,armor_class:enemyAc,hit_dice:'1',has_blood:true,is_undead:false,is_construct:false,attacks:enemyAttacks||enemy.sheet.attacks,attributes:{strength:10,dexterity:10,constitution:10,wisdom:10}}});
  await position(grid,evidence.map_id,mine,4);await position(grid,evidence.map_id,enemy,5);
  await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:razielInit},{target_type:'token',target_id:enemy.id,initiative:enemyInit}]});
  const before=await get('/characters/raziel');assert.equal(before.definition.hemomancy.weapons.length,5);
  return {mine,enemy,before};
 }
 async function open({width=1440,role='gm',actor='raziel'}={}){
  const context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token',role==='gm'?'cf01-local-gm':'cf01-local-'+actor);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
  const page=await context.newPage();latestPage=page;page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navega\u00e7\u00e3o principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
  await page.locator(`button[data-character="${actor}"]`).click();
  const combatControls=page.locator('.workspace-combat-live:visible .workspace-combat-content').first();
  await combatControls.waitFor({state:'attached'});
  if(!await combatControls.evaluate(el=>el.open))await combatControls.locator(':scope > summary').click();
  const hemomancy=page.locator('.workspace-sheet-section').filter({has:page.locator('.workspace-hemomancy')});
  if(!await hemomancy.evaluate(el=>el.open))await hemomancy.locator(':scope > summary').click();
  const active=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Habilidades$/})});
  const powers=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Passivas · (Feridas|Marca)$/i})});
  await powers.first().waitFor();assert.equal(await powers.count(),2,'Approved passive blocks must both be visible');
  for(const section of [active,...await powers.all()])if(!await section.evaluate(el=>el.open))await section.locator(':scope > summary').click();
  assert.equal(await active.locator('.workspace-hemomancy-skill').count(),5);
  const pack=(await get('/characters/raziel')).definition.hemomancy;
  for(const weapon of pack.weapons)assert.equal(await powers.getByRole('button',{name:weapon.passive.name,exact:true}).count(),1,'Weapon passive must be listed once: '+weapon.passive.name);
  assert.equal(await powers.locator('button[data-card-command]').count(),0,'Passives never have activation commands');
  return {context,page,hemomancy,active,powers,weaponCard:page.locator('.workspace-hemomancy-card')};
 }
 async function openSheet(page,role){
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navega\u00e7\u00e3o principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
  await page.locator('button[data-character="raziel"]').click();
  const hemomancy=page.locator('.workspace-sheet-section').filter({has:page.locator('.workspace-hemomancy')});
  if(!await hemomancy.evaluate(el=>el.open))await hemomancy.locator(':scope > summary').click();
  const active=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Habilidades$/})});
  if(!await active.evaluate(el=>el.open))await active.locator(':scope > summary').click();
  return {hemomancy,active,weaponCard:page.locator('.workspace-hemomancy-card')};
 }
 function installD20(context,getDie,pattern=/\/characters\/raziel\/techniques\/hemomancia-[^/]+$/){
  return context.route(pattern,async route=>{
   const req=route.request();if(req.method()!=='POST')return route.continue();
   let body;try{body=req.postDataJSON();}catch{return route.continue();}
   if(!body?.target_id)return route.continue();
   await route.continue({postData:JSON.stringify({...body,roll_mode:'physical',d20:getDie()})});
  });
 }
 async function attack(page,card,weapon,enemy,getDie,setDie,die){
  setDie(die);await card.getByLabel('Arma da Hemomancia').selectOption(weapon);
  const button=card.locator('button[data-card-command]');
  assert.equal(await button.count(),1);
  await page.waitForFunction(el=>el&&!el.disabled,await button.elementHandle());
  const sent=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/hemomancia-'+weapon));
  const confirmed=page.waitForResponse(r=>/\/combat\/attacks\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));
  void sent.catch(()=>{});void confirmed.catch(()=>{});
  await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor({timeout:15000});
  await page.locator(`[data-grid-token="${enemy.id}"]`).click();
  await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
  const reply=await sent;assert.ok(reply.ok(),await reply.text());const resolved=await reply.json();
  const done=await confirmed;assert.ok(done.ok(),await done.text());return {resolved,result:await done.json()};
 }
 try{
  // Mira Predatoria: 19 natural that hits rerolls only the base 1d8, once.
  {
   const width=390,role='player';console.log('RUN hemomancy-passives mira');
   const {enemy,before}=await prepare({enemyHp:500});
   const {context,page,weaponCard}=await open({width,role});
   let die=10;await installD20(context,()=>die);
   const {resolved,result}=await attack(page,weaponCard,'arco',enemy,()=>die,v=>die=v,19);
   assert.equal(resolved.result,'hit');
   const strike=(result.breakdown?.strikes||[])[0]||result.breakdown;
    assert.equal(strike.critical,true,'Mira requires a natural 19-20 hit');
    assert.equal((result.damage_rolls||[]).length,2,'Mira doubles only the base 1d8 (2d8 total)');
    assert.equal((result.damage_formula.match(/1d8/g)||[]).length,2,'base and Mira each contribute one 1d8');
    assert.ok((result.breakdown?.hemomancy?.rolls||[]).length>=1||JSON.stringify(result.breakdown).includes('Mira Predat'));
    const after=await get('/characters/raziel'),key='reserva_de_sangue',cost=before.state.resources.find(r=>r.key===key).current-after.state.resources.find(r=>r.key===key).current;
    assert.ok(cost>0,'Mira attack must spend blood');
    observed.push({case:'mira',die,damage:result.damage_total,formula:result.damage_formula,cost_checked:cost,controlled:'declared physical d20 in request; card has no die input'});
    action_coverage.push({actor:'raziel',key:'ability:hemomancia-passiva-arco',verified_checks:['ui']});covered.add('mira');
   await page.screenshot({path:path.join(out,'mira-390.png')});await context.close();
  }
  // Carrasco: pre-hit quarter HP, then the same strike above quarter HP must not add the d6.
  {
   const width=1440,role='gm';console.log('RUN hemomancy-passives carrasco');
   const {enemy}=await prepare({enemyHp:100});
   const {context,page,weaponCard}=await open({width,role});
   let die=10;await installD20(context,()=>die);
   const first=await attack(page,weaponCard,'foice',enemy,()=>die,v=>die=v,10);
   assert.equal(first.result.breakdown?.hemomancy?.passive_d6,1,'Carrasco reads pre-hit HP');
   await command('next_turn');await command('next_turn');
   await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{current_hp:130,maximum_hp:500});
   const reopened=await openSheet(page,role);
   const second=await attack(page,reopened.weaponCard,'foice',enemy,()=>die,v=>die=v,10);
   assert.equal(second.result.breakdown?.hemomancy?.passive_d6,0,'above quarter HP must not add Carrasco');
    observed.push({case:'carrasco',quarter_hp_bonus:first.result.breakdown.hemomancy.passive_d6,above_quarter_bonus:second.result.breakdown.hemomancy.passive_d6,reload_checked:true,controlled:'declared physical d20 in request; card has no die input'});
    action_coverage.push({actor:'raziel',key:'ability:hemomancia-passiva-foice',verified_checks:['ui']});covered.add('carrasco');
   await page.screenshot({path:path.join(out,'carrasco-1440.png')});await context.close();
  }
  // Trauma Profundo opens Exposed; Ferroada Arterial uses it for +1d6 and +2, then consumes it.
  {
   const width=1440,role='gm';console.log('RUN hemomancy-passives trauma/ferroada');
   const {enemy}=await prepare({enemyHp:500});
   const {context,page,weaponCard}=await open({width,role});
   let die=10;await installD20(context,()=>die);
   const mace=await attack(page,weaponCard,'marreta',enemy,()=>die,v=>die=v,10);
    assert.equal(mace.resolved.result,'hit');
    assert.ok((await get('/combat/effects')).effects.some(e=>e.target_id===enemy.id&&e.hemomancy_kind==='exposed'),'Trauma must create Exposed');
    await command('next_turn');await command('next_turn');
    const reopened=await openSheet(page,role);
    assert.ok((await get('/combat/effects')).effects.some(e=>e.target_id===enemy.id&&e.hemomancy_kind==='exposed'),'Exposed must persist across reload');
    const spear=await attack(page,reopened.weaponCard,'lanca',enemy,()=>die,v=>die=v,10);
    assert.equal(spear.resolved.result,'hit');
    assert.equal(spear.result.breakdown?.hemomancy?.bonus,2,'Current v2 contract keeps the flat Exposed bonus in damage');
    assert.ok((spear.result.breakdown?.hemomancy?.passive_d6||0)>=1,'Ferroada adds 1d6 against Exposed');
    assert.match(spear.result.damage_formula,/\+\s*2/);
    assert.ok(!(await get('/combat/effects')).effects.some(e=>e.target_id===enemy.id&&e.hemomancy_kind==='exposed'),'Exposed is consumed by the next hemomancy attack');
    observed.push({case:'trauma-ferroada',mace_damage:mace.result.damage_total,spear_formula:spear.result.damage_formula,spear_bonus:spear.result.breakdown.hemomancy.bonus,exposed_persisted_across_reload:true,controlled:'declared physical d20 in request; card has no die input'});
    action_coverage.push({actor:'raziel',key:'ability:hemomancia-passiva-marreta',verified_checks:['ui']});
    action_coverage.push({actor:'raziel',key:'ability:hemomancia-passiva-lanca',verified_checks:['ui']});
   covered.add('trauma');covered.add('ferroada');
   limitations.push('Ferroada no-doubling with both Exposed and bleeding was not exercised in this script.');
   await page.screenshot({path:path.join(out,'trauma-ferroada-1440.png')});await context.close();
  }
  // Revanche Rubra: shield changes a miss into a one-charge +1d6 on the next hemomancy hit.
  {
   const width=1440,role='gm';console.log('RUN hemomancy-passives revanche');
   const enemyAttacks=[{name:'Sonda controlada',bonus:0,damage:'1d4'}];
   const {mine,enemy,before}=await prepare({razielInit:20,enemyInit:1,enemyHp:500,enemyAttacks});
   const {context,page,active,weaponCard}=await open({width,role});
   let die=10;await installD20(context,()=>die);
   const current=async()=>{const e=(await get('/combat/effects')).encounter;return e.participants[e.turn_index]};
   assert.equal((await current()).target_id,'raziel','shield is activated on Raziel turn');
   const shieldCard=active.locator('.workspace-hemomancy-skill').filter({has:page.getByRole('button',{name:before.definition.hemomancy.weapons.find(w=>w.weapon==='escudo').skill.name,exact:true})});
   const shieldSent=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/hemomancia-escudo'));
   await page.waitForFunction(el=>el&&!el.disabled,await shieldCard.locator('button[data-card-command]').elementHandle());
   await shieldCard.click({position:{x:8,y:8}});const shieldReply=await shieldSent;assert.ok(shieldReply.ok(),await shieldReply.text());
   const shieldSnapshot=await get('/combat/effects');
   const shieldEffect=shieldSnapshot.effects.find(e=>e.hemomancy_kind==='shield');assert.ok(shieldEffect,'shield effect must persist');
   // A transport receipt is not React completion. The same live combat card
   // must have received this authoritative version before its next command.
   await page.waitForFunction(version=>Number(document.querySelector('.workspace-combat-live')?.getAttribute('data-combat-version'))>=version,shieldSnapshot.version);
   const baseAc=Number(before.definition.defenses.armor_class);
   const effectiveAc=Number((await get('/characters/raziel')).definition.defenses.armor_class);
   assert.equal(Number(shieldEffect.modifiers?.armor_class_bonus),2,'approved shield grants exactly +2 AC');
   assert.equal(effectiveAc,baseAc+2,'character view must include the shield bonus');
   const probe=shieldNearMiss(baseAc,effectiveAc,enemyAttacks[0].bonus);
   if(!probe)throw new Inconclusive(`Revanche has no eligible controlled near miss against AC ${effectiveAc}`);
   die=probe.d20;
   await installD20(context,()=>die,/\/gm\/combat\/tokens\/[^/]+\/attacks\/resolve$/);
   const passTurn=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/combat/next-turn');
   void passTurn.catch(()=>{});
   const passButton=page.locator('.workspace-combat-live:visible').getByRole('button',{name:/Concluir e passar turno/}).first();
   await passButton.waitFor();await passButton.click();const passed=await passTurn;assert.ok(passed.ok(),'GM passes from Raziel to the monster: '+await passed.text());
   assert.equal((await current()).target_id,enemy.id,'monster acts after Raziel');
   const attackCard=page.locator('.workspace-combat-live:visible section.workspace-ally-attacks article').filter({has:page.locator('button[data-card-command]')}).first();
   await attackCard.waitFor();
   await page.waitForFunction(el=>!el.querySelector('button[data-card-command]').disabled,await attackCard.elementHandle());
   const incoming=page.waitForResponse(r=>/\/gm\/combat\/tokens\/[^/]+\/attacks\/resolve$/.test(new URL(r.url()).pathname));
   const confirmed=page.waitForResponse(r=>/\/combat\/attacks\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));
   void incoming.catch(()=>{});void confirmed.catch(()=>{});
   await attackCard.click({position:{x:8,y:8}});
   await page.locator('.targeting-overlay').waitFor({timeout:15000});await page.locator(`[data-grid-token="${mine.id}"]`).click();
   await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
   const incomingReply=await incoming;assert.ok(incomingReply.ok(),await incomingReply.text());
   const incomingDone=await confirmed;assert.ok(incomingDone.ok(),await incomingDone.text());const incomingResult=await incomingDone.json();
   assert.equal(Number(incomingResult.target_ac),effectiveAc,'attack resolves against the shielded effective AC');
   assert.equal(Number(incomingResult.attack_total),probe.attack_total,'controlled enemy attack has the calibrated total');
   assert.equal(incomingResult.result,'miss','shield must turn the near miss into a miss');
   const margin=Number(incomingResult.target_ac)-Number(incomingResult.attack_total);
   assert.ok(margin>=1&&margin<=2,`Revanche requires the miss to be caused by the shield, margin=${margin}`);
   assert.ok(incomingResult.breakdown?.hemomancy_shield,'shield must be the recorded trigger');
   assert.ok((await get('/combat/effects')).effects.some(e=>e.hemomancy_kind==='revenge'),'Revanche stores one charge');
   await page.locator('.workspace-combat-live:visible').getByText('Ação concluída. Use “Concluir e passar turno”.',{exact:true}).waitFor();
   const passBack=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/combat/next-turn');
   void passBack.catch(()=>{});
   await page.locator('.workspace-combat-live:visible').getByRole('button',{name:/Concluir e passar turno/}).first().click();const back=await passBack;assert.ok(back.ok(),'monster turn passes back to Raziel: '+await back.text());
   const reopened=await openSheet(page,role);die=10;
   const bow=await attack(page,reopened.weaponCard,'arco',enemy,()=>die,v=>die=v,10);
   assert.equal(bow.resolved.result,'hit');
   assert.equal(bow.result.breakdown?.hemomancy?.passive_d6,1,'Revanche charge adds one d6');
   assert.ok(!(await get('/combat/effects')).effects.some(e=>e.hemomancy_kind==='revenge'),'Revanche is consumed');
   observed.push({case:'revanche',incoming_total:incomingResult.attack_total,incoming_ac:incomingResult.target_ac,shield_trigger:incomingResult.breakdown.hemomancy_shield,shield_charge:1,bow_formula:bow.result.damage_formula,controlled:'declared physical d20 for incoming and hemomancy request; incoming route overwritten at the real resolve endpoint'});
   action_coverage.push({actor:'raziel',key:'ability:hemomancia-passiva-escudo',verified_checks:['ui']});covered.add('revanche');
   await page.screenshot({path:path.join(out,'revanche-1440.png')});await context.close();
  }
  assert.deepEqual(errors,[]);
  for(const key of ['mira','carrasco','trauma','ferroada','revanche'])assert.ok(covered.has(key),'missing passive '+key);
  complete=true;
  console.log(JSON.stringify({status:'PASS',action_coverage,observed,limitations,controlled_inputs:['declared physical d20 in hemomancy request','declared physical d20 on the real incoming attack resolve endpoint'],screenshots:out,production_modified:false},null,2));
  }finally{
   if(!complete&&latestPage&&!latestPage.isClosed()){
    await latestPage.screenshot({path:path.join(out,'failure.png')});
    console.error(JSON.stringify({screenshot:path.join(out,'failure.png'),combat:await latestPage.locator('.workspace-combat-live').allTextContents(),controls:await latestPage.locator('.workspace-combat-content').evaluateAll(nodes=>nodes.map(el=>({open:el.open,visible:!!el.getClientRects().length})))}));
   }
   await browser.close();await api.dispose();
  }
})().catch(e=>{
 console.error(e);
 if(e instanceof Inconclusive)console.log(JSON.stringify({status:'INCONCLUSIVE',reason:e.message,production_modified:false}));
 process.exitCode=e instanceof Inconclusive?2:1;
});
