const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
const {unexpectedAlerts}=require('./rest-alerts.cjs');
const actors=['vezemir','morthak','raziel','dorn7'];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const action=async(id,name,payload={},reason='Ensaio de descanso')=>post('/characters/'+id+'/actions',{action:name,payload,request_id:randomUUID(),reason});
 const health=await get('/health');
 assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 assert.ok(path.resolve(health.vault_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 if((await get('/combat/effects')).encounter?.active)await command('end');
 const roster=await get('/characters'), names=Object.fromEntries(roster.map(item=>[item.id,item.name]));
 for(const id of actors)assert.ok(names[id],'Missing character '+id);
 const companions=await get('/gm/companions');
 assert.ok(companions.gm_character_ids.includes('dorn7'),'Dorn must remain a GM-controlled real character');
 assert.ok(companions.archived_character_ids.includes('varkh'));
 assert.equal(companions.allies.filter(item=>/dorn/i.test(item.name||'')).length,0,'No Dorn ally token may be invented');
 const workspace=await get('/workspace');assert.ok(workspace.map?.id);
 const pin=workspace.tokens.find(item=>item.token_type==='monster'&&!item.character_id)||await post('/gm/workspace/tokens',{token_type:'monster',map_id:workspace.map.id,name:'Sentinela de descanso',current_hp:20,maximum_hp:20,visible_to_players:true,latitude:10,longitude:80,sheet:{movement:'9 m'}});
 const tokenEffectLabel='Marca no pino de ensaio';
 await command('apply',{target_type:'token',target_id:pin.id,label:tokenEffectLabel,source:'Ensaio de descanso',duration:'manual'});
 const before={};
 for(const id of actors){
  const sheet=await get('/characters/'+id),state=sheet.state,maximum=Number(state.maximum_hp);
  assert.ok(maximum>0,'Configured HP expected for '+id);
  if(id==='raziel'&&state.animal_form)await action(id,'end_night_form');
  await action(id,'set_hp',{value:Math.max(1,maximum-3)});
  await action(id,'grant_temporary_hp',{amount:2});
  await action(id,'add_condition',{condition:'Ferido de ensaio'});
  for(const resource of state.resources||[]){
   if(resource.key==='forma_da_noite'||Number(resource.maximum)<=0||Number(resource.current)<=0)continue;
   await action(id,'consume_resource',{resource_key:resource.key,amount:1});
  }
  // Explicit preparation only in the verified TEMP database; not a spell use.
  for(const item of sheet.inventory.filter(item=>item.recharge==='inn_rest'&&Number(item.charges_max)>0)){
   await action(id,'change_charges',{item_path:item.item_path,charges:0,charges_max:Number(item.charges_max)});
  }
  await command('apply',{target_type:'character',target_id:id,label:'Velocidade de ensaio',source:'Ensaio de descanso',duration:'rounds',rounds:3,modifiers:{attack_bonus:1}});
  await command('apply',{target_type:'character',target_id:id,label:'Marca temporaria de ensaio',source:'Ensaio de descanso',duration:'manual'});
  const prepared=await get('/characters/'+id);
  before[id]={current_hp:Number(prepared.state.current_hp),maximum_hp:Number(prepared.state.maximum_hp),inventory:Object.fromEntries(prepared.inventory.map(item=>[item.item_path,Number(item.quantity||0)])),dailyCharges:prepared.inventory.filter(item=>item.recharge==='inn_rest'&&Number(item.charges_max)>0).map(item=>({path:item.item_path,maximum:Number(item.charges_max)}))};
 }
 const dornBefore=await get('/characters/dorn7');
 assert.ok(dornBefore.inventory.some(item=>/kit|fragmento/i.test(item.item_title)),'Fixture should contain a consumable stock item');
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],assetReads=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-four-sheet-rest-'));
 let activePage;
 const openAll=async panel=>{for(const summary of await panel.locator('details.workspace-sheet-section > summary').all()){const details=summary.locator('..');if(!(await details.evaluate(element=>element.open)))await summary.click();}};
 const counters=async panel=>panel.locator('.workspace-resource-catalog b, .workspace-action-catalog b, .workspace-spell-card b').evaluateAll(elements=>[...new Set(elements.map(element=>element.textContent.trim()).filter(text=>/^\d+\/\d+$/.test(text)))].map(text=>text.split('/').map(Number)));
 const openSheet=async(page,id)=>{
  const nav=page.getByRole('navigation',{name:'Navegação principal'});
  await nav.getByRole('button',{name:/Mesa$/}).click();
  await page.locator(`button[data-character="${id}"]`).first().click();
  await page.waitForFunction(name=>document.querySelector('.workspace-character-copy h2')?.textContent?.trim()===name,names[id]);
  const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
  await openAll(panel);
  return panel;
 };
 const makeContext=async(width,role,actor)=>{
  const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
  await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
  const page=await context.newPage();activePage=page;page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(request.method()==='GET'&&new URL(request.url()).pathname.startsWith('/gm/assets'))assetReads.push(new URL(request.url()).pathname);});await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  return {context,page};
 };
 try{
  const desktop=await makeContext(1440,'gm','vezemir'),page=desktop.page,nav=page.getByRole('navigation',{name:'Navegação principal'});
  for(const id of actors){
   const panel=await openSheet(page,id),hp=(await panel.locator('.workspace-vitals .workspace-hp-heading strong').first().innerText()).replace(/\s+/g,'');
   assert.equal(hp,before[id].current_hp+'/'+before[id].maximum_hp);
   const status=panel.locator('.workspace-conditions[aria-label="Status"]');
   await status.locator('.workspace-active-effect-icons').waitFor();
   await status.locator('.workspace-condition-list').waitFor();
   assert.equal(await status.locator('.workspace-active-effect-icons').count(),1,'Temporary effect must be visible for '+id);
   assert.ok((await status.innerText()).includes('Ferido de ensaio'));
   const visible=await counters(panel);assert.ok(visible.some(([current,maximum])=>current<maximum),'Consumed resource must be visible for '+id);
   await panel.screenshot({path:path.join(output,id+'-before-1440.png')});
  }
  await nav.getByRole('button',{name:/Mestre$/}).click();
  assert.equal(await page.locator('.master-asset-panel').count(),0,'Closed Assets must not mount background work');
  const rest=page.getByRole('button',{name:/Descanso geral/});await rest.waitFor();assert.equal(await rest.isEnabled(),true);
  await page.waitForLoadState('networkidle',{timeout:5000}).catch(()=>{});
  const beforeAlerts=await page.locator('[role="alert"]').allTextContents();
  assert.equal(await page.locator('.workspace-error:visible').count(),0,'No inherited workspace error before rest');
  const restResponses=actors.map(id=>page.waitForResponse(response=>new URL(response.url()).pathname==='/characters/'+id+'/actions'&&response.request().method()==='POST'&&response.request().postDataJSON()?.action==='rest_at_inn'));
  await rest.click();
  for(const response of await Promise.all(restResponses))assert.ok(response.ok(),'Every native full-rest request must succeed');
  await page.waitForFunction(()=>{const button=[...document.querySelectorAll('button')].find(item=>item.textContent.includes('Descanso geral'));return Boolean(button&&!button.disabled);},{timeout:30000});
  let sheets=[],effects=[];
  const deadline=Date.now()+45000;
  while(Date.now()<deadline){
   [sheets,effects]=await Promise.all([Promise.all(actors.map(id=>get('/characters/'+id))),(await get('/combat/effects')).effects]);
   if(sheets.every(sheet=>Number(sheet.state.current_hp)===Number(sheet.state.maximum_hp)&&Number(sheet.state.temporary_hp||0)===0&&!(sheet.state.conditions||[]).length&&(sheet.state.resources||[]).every(resource=>Number(resource.current)===Number(resource.maximum)))&&!effects.some(effect=>effect.target_type==='character'&&actors.includes(effect.target_id)))break;
   await sleep(300);
  }
  assert.ok(!effects.some(effect=>effect.target_type==='character'&&actors.includes(effect.target_id)),'Full rest must clear every character effect');
  assert.ok(effects.some(effect=>effect.target_type==='token'&&effect.target_id===pin.id&&effect.label===tokenEffectLabel),'Token effect must survive character rest');
  for(const sheet of sheets){
   const id=sheet.definition.id;
   assert.equal(Number(sheet.state.current_hp),Number(sheet.state.maximum_hp),'HP after rest: '+id);
   assert.equal(Number(sheet.state.temporary_hp||0),0,'Temporary HP after rest: '+id);
   assert.deepEqual(sheet.state.conditions||[],[]);
   assert.ok((sheet.state.resources||[]).every(resource=>Number(resource.current)===Number(resource.maximum)),'Daily resources after rest: '+id);
   assert.deepEqual(Object.fromEntries(sheet.inventory.map(item=>[item.item_path,Number(item.quantity||0)])),before[id].inventory,'Stock quantities must not be consumed or replenished by rest: '+id);
   for(const expected of before[id].dailyCharges){
    const item=sheet.inventory.find(item=>item.item_path===expected.path);
    assert.equal(Number(item.charges_max),expected.maximum,'Rest must preserve charge maximum');
    assert.equal(Number(item.charges_current),expected.maximum,'Daily item charges must refill: '+id);
   }
  }
  const afterAlerts=await page.locator('[role="alert"]').allTextContents();
  console.log(JSON.stringify({phase:'rest-alerts',before:beforeAlerts,after:afterAlerts}));
  assert.deepEqual(unexpectedAlerts(beforeAlerts,afterAlerts),[],'Rest must not introduce new alerts');
  assert.equal(await page.locator('.workspace-error:visible').count(),0,'Rest must not surface a workspace error');
  assert.deepEqual(assetReads,[],'Closed Assets must not issue context/catalog requests');
  for(const id of actors){
   const panel=await openSheet(page,id),hp=(await panel.locator('.workspace-vitals .workspace-hp-heading strong').first().innerText()).replace(/\s+/g,'');
   assert.equal(hp,before[id].maximum_hp+'/'+before[id].maximum_hp);
   const status=panel.locator('.workspace-conditions[aria-label="Status"]');
   await status.getByText('STATUS - Nenhum',{exact:true}).waitFor();
   assert.equal(await status.getByText('STATUS - Nenhum',{exact:true}).count(),1,'Status must be clear for '+id);
   assert.equal(await status.locator('.workspace-active-effect-icons').count(),0);
   assert.equal(await status.locator('.workspace-condition-list').count(),0);
   const visible=await counters(panel);assert.ok(visible.length>0,'Rendered resource counters expected for '+id);assert.ok(visible.every(([current,maximum])=>current===maximum),'Visible counters must refill for '+id);
   await panel.screenshot({path:path.join(output,id+'-after-1440.png')});
  }
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();
  const dorn=await openSheet(page,'dorn7'),dornHp=(await dorn.locator('.workspace-vitals .workspace-hp-heading strong').first().innerText()).replace(/\s+/g,'');
  assert.equal(dornHp,before.dorn7.maximum_hp+'/'+before.dorn7.maximum_hp);
  const dornStatus=dorn.locator('.workspace-conditions[aria-label="Status"]');await dornStatus.getByText('STATUS - Nenhum',{exact:true}).waitFor();
  assert.equal(await dornStatus.getByText('STATUS - Nenhum',{exact:true}).count(),1);
  await desktop.context.close();

  const mobile=await makeContext(390,'gm','morthak'),mobilePage=mobile.page;
  for(const id of actors){
   const panel=await openSheet(mobilePage,id),hp=(await panel.locator('.workspace-vitals .workspace-hp-heading strong').first().innerText()).replace(/\s+/g,'');
   assert.equal(hp,before[id].maximum_hp+'/'+before[id].maximum_hp);
   const status=panel.locator('.workspace-conditions[aria-label="Status"]');
   await status.getByText('STATUS - Nenhum',{exact:true}).waitFor();
   assert.equal(await status.getByText('STATUS - Nenhum',{exact:true}).count(),1);
   assert.equal(await status.locator('.workspace-active-effect-icons').count(),0);
   const visible=await counters(panel);assert.ok(visible.length>0&&visible.every(([current,maximum])=>current===maximum),'Mobile counters must refill for '+id);
   await panel.locator('.workspace-vitals').screenshot({path:path.join(output,id+'-vitals-after-390.png')});
   await status.screenshot({path:path.join(output,id+'-status-after-390.png')});
   const width=await panel.evaluate(()=>({scroll:document.documentElement.scrollWidth,screen:innerWidth}));assert.ok(width.scroll<=width.screen+2,'Rest sheet must not widen the mobile document');
   await panel.screenshot({path:path.join(output,id+'-after-390.png')});
  }
  await mobile.context.close();

  const player=await makeContext(390,'vezemir','vezemir'),playerPage=player.page;
  await playerPage.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
  await playerPage.locator('button[data-character="vezemir"]').click();
  await playerPage.waitForFunction(name=>document.querySelector('.workspace-character-copy h2')?.textContent?.trim()===name,names.vezemir);
  const playerPanel=playerPage.locator('.workspace-character-panel');await playerPanel.locator('.workspace-character-identity').waitFor();await openAll(playerPanel);
  const playerHp=(await playerPanel.locator('.workspace-vitals .workspace-hp-heading strong').first().innerText()).replace(/\s+/g,'');
  assert.equal(playerHp,before.vezemir.maximum_hp+'/'+before.vezemir.maximum_hp);
  const playerStatus=playerPanel.locator('.workspace-conditions[aria-label="Status"]');
  await playerStatus.getByText('STATUS - Nenhum',{exact:true}).waitFor();
  assert.equal(await playerStatus.getByText('STATUS - Nenhum',{exact:true}).count(),1);
  assert.equal(await playerPage.getByRole('button',{name:/Descanso geral/}).count(),0,'Players must not receive the GM general-rest command');
  const playerCounters=await counters(playerPanel);assert.ok(playerCounters.length>0&&playerCounters.every(([current,maximum])=>current===maximum));
  await playerPanel.screenshot({path:path.join(output,'vezemir-player-390.png')});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['four real sheets prepared with HP, temporary HP, condition, consumed resources and temporary effects','GM general rest clears all character effects while preserving a token effect','all four sheets show full HP, clear status and refilled counters after rest at 1440 and 390','inventory quantities remain unchanged','rest persists after reload','player view shows rested Vezemir without the GM command'],dorn:{gm_character:true,ally_token:false},screenshots:output,production_modified:false}));
  await player.context.close();
 }catch(error){
  if(activePage&&!activePage.isClosed()){
   await activePage.screenshot({path:path.join(output,'failure-viewport.png')}).catch(()=>{});
   console.error(JSON.stringify({phase:'failure',alerts:await activePage.locator('[role="alert"]').allTextContents().catch(()=>[]),workspace_errors:await activePage.locator('.workspace-error').allTextContents().catch(()=>[]),screenshots:output}));
  }
  throw error;
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
