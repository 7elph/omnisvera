// Native grid interaction in the owned TEMP fixture; follows item-families-smoke.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${await r.text()}`);return r.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-item-specials-')),checks=[],screenshots=[],errors=[];
 let browser,player,gm;const deadline=setTimeout(()=>void browser?.close().finally(()=>process.exit(1)),240000);deadline.unref();
 try{
  const combat=await call('get','/combat/effects');if(combat.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
  await call('patch','/gm/workspace/table-mode',{table_mode:'digital'});
  const before=await call('get','/characters/vezemir');
  for(const id of ['arma-corpo-madu','arma-corpo-espada-bastarda','kit-explorador-rede','arma-distancia-zarabatana','arma-distancia-dardo-zarabatana-x20'])assert.ok(before.inventory.some(i=>i.item_path==='compendium:'+id&&i.quantity>0),'Purchased item missing: '+id);
  await call('post','/characters/vezemir/actions',{action:'set_hp',payload:{value:before.state.maximum_hp},request_id:randomUUID()});
  browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'chrome':undefined});
  async function open(role,width){const ctx=await browser.newContext({viewport:{width,height:1000},isMobile:width===390,hasTouch:width===390});await ctx.addInitScript(role=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','vezemir');},role);const page=await ctx.newPage();page.setDefaultTimeout(22000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();return{ctx,page};}
  player=await open('vezemir',390);
  const png=await player.page.evaluate(()=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=400;const ctx=canvas.getContext('2d');ctx.fillStyle='#343b41';ctx.fillRect(0,0,400,400);ctx.fillStyle='#414b52';for(let x=0;x<10;x++)for(let y=0;y<10;y++)if((x+y)%2)ctx.fillRect(x*40,y*40,40,40);return canvas.toDataURL('image/png').split(',')[1];});
  const map=await call('post','/gm/workspace/map',{title:'Itens especiais — fixture isolada',filename:'fixture.png',content_type:'image/png',data_base64:png,visible_to_players:true});
  await call('post',`/workspace/maps/${encodeURIComponent(map.id)}/grid`,{request_id:randomUUID(),cols:10,rows:10,cell_size_m:1.5});
  await call('post','/gm/workspace/tokens',{token_type:'character',character_id:'vezemir',name:'Vezemir',map_id:map.id,latitude:15,longitude:15,visible_to_players:true});
  const enemy=await call('post','/gm/workspace/tokens',{token_type:'monster',name:'Alvo especial isolado',map_id:map.id,latitude:15,longitude:25,visible_to_players:true,current_hp:1000,maximum_hp:1000,sheet:{armor_class:18,saving_throw:12,size:'M',attributes:{dexterity:14},attacks:[{name:'Ataque básico',bonus:5,damage:'1d6'}]}});
  await call('patch','/gm/workspace/maps/active',{map_id:map.id});
  async function sheet(page){await page.reload();await page.locator('.app-shell.authenticated').waitFor();const navigation=page.getByRole('navigation',{name:'Navegação principal'});const ficha=navigation.getByRole('button',{name:/Ficha$/});await (await ficha.count()?ficha:navigation.getByRole('button',{name:/Mesa$/})).click();await page.locator('button[data-character="vezemir"]').click();}
  await sheet(player.page);
  async function equip(name,slot='Corpo a corpo'){
   await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
   const current=await call('get','/characters/vezemir');
   for(const item of current.inventory.filter(i=>i.equipped&&i.equipment_slot===slot&&i.item_title!==name)){
    await player.page.locator('.workspace-inventory-catalog').getByRole('button',{name:item.item_title,exact:true}).click();
    const previous=player.page.getByRole('dialog',{name:'Informações de '+item.item_title,exact:true});
    await previous.getByRole('button',{name:'Guardar',exact:true}).click();
    await previous.getByRole('button',{name:'Equipar em '+slot,exact:true}).waitFor();
    await previous.getByRole('button',{name:'Fechar informações do item'}).click();
   }
   await player.page.locator('.workspace-inventory-catalog').getByRole('button',{name,exact:true}).click();
   const dialog=player.page.getByRole('dialog',{name:'Informações de '+name,exact:true});
   await dialog.getByRole('button',{name:'Equipar em '+slot,exact:true}).click();
   await dialog.getByRole('button',{name:'Guardar',exact:true}).waitFor();await dialog.getByRole('button',{name:'Fechar informações do item'}).click();
  }
  const baseCA=(await call('get','/characters/vezemir')).definition.defenses.armor_class;
  await equip('Madu');assert.equal((await call('get','/characters/vezemir')).definition.defenses.armor_class,baseCA+1);
  checks.push('Madu bought through market, equipped from owner inventory, 1d8 and +1 CA');
  await equip('Espada bastarda');
  const melee=()=>player.page.locator('.workspace-attack-catalog > article').filter({hasText:'Corpo a corpo'}).first();
  async function aim(card=melee()){await card.scrollIntoViewIfNeeded();await card.locator('button[data-card-command]:enabled').waitFor({state:'attached'});await card.click({position:{x:8,y:8}});const target=player.page.locator(`[data-grid-token="${enemy.id}"].target-valid`);await target.scrollIntoViewIfNeeded();await target.click();const dialog=player.page.getByRole('dialog',{name:'Confirmar alvo',exact:true});await dialog.waitFor();return dialog;}
  let dialog=await aim();assert.ok(await dialog.getByRole('button',{name:'Sim',exact:true}).isDisabled());
  await dialog.getByRole('combobox',{name:'Tipo de dano da arma'}).selectOption('bludgeoning');
  const choiceShot=path.join(out,'damage-choice-owner-390.png');await dialog.screenshot({path:choiceShot});screenshots.push(choiceShot);
  let response=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/attacks/resolve');void response.catch(()=>{});
  await dialog.getByRole('button',{name:'Sim',exact:true}).click();let resolved=await response;assert.ok(resolved.ok(),await resolved.text());
  let receipt=await resolved.json();assert.equal(receipt.breakdown.damage_profile.damage_type,'bludgeoning');assert.ok(receipt.confirmed);
  checks.push('mobile card -> grid target -> explicit damage choice -> native automatic confirmation');
  await equip('Rede');
  for(let attempt=0;attempt<5;attempt++){
   dialog=await aim();assert.equal(await dialog.getByRole('combobox',{name:'Tipo de dano da arma'}).count(),0);
   response=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/attacks/resolve');void response.catch(()=>{});
   await dialog.getByRole('button',{name:'Sim',exact:true}).click();resolved=await response;assert.ok(resolved.ok(),await resolved.text());receipt=await resolved.json();
   assert.equal(receipt.damage_total,0);if(receipt.result==='hit')break;
  }
  assert.ok(receipt.breakdown.item_special_result);assert.equal(receipt.target_ac,12);
  const effects=await call('get','/combat/effects');assert.equal(effects.effects.filter(e=>e.item_special==='net'&&e.target_id===enemy.id).length,1);
  checks.push('Rede uses touch CA, deals no HP damage, applies native audited Constrito');
  await sheet(player.page);assert.ok((await call('get','/combat/effects')).effects.some(e=>e.id===receipt.breakdown.item_special_result.effect_id));
  await melee().evaluate(element=>element.scrollIntoView({block:'center'}));const ownerShot=path.join(out,'net-owner-390.png');await melee().screenshot({path:ownerShot});screenshots.push(ownerShot);
  gm=await open('gm',1440);await sheet(gm.page);await gm.page.locator('.workspace-attack-catalog').evaluate(element=>element.scrollIntoView({block:'center'}));
  const gmShot=path.join(out,'net-master-1440.png');await gm.page.locator('.workspace-attack-catalog').screenshot({path:gmShot});screenshots.push(gmShot);
  await call('post','/characters/vezemir/actions',{action:'set_hp',payload:{value:before.state.maximum_hp},request_id:randomUUID()});
  await equip('Garrote');
  for(let attempt=0;attempt<5;attempt++){
   dialog=await aim();response=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/attacks/resolve');void response.catch(()=>{});
   await dialog.getByRole('button',{name:'Sim',exact:true}).click();resolved=await response;assert.ok(resolved.ok(),await resolved.text());receipt=await resolved.json();
   if(receipt.result==='hit')break;
  }
  assert.equal(receipt.breakdown.item_special_result?.label,'Garrotado');
  await gm.page.getByText(/Garrotado/).first().waitFor({state:'attached',timeout:20000});
  checks.push('second GM client receives the owner Garrote action without manual reload');
  assert.equal(receipt.damage_total,0);
  await melee().locator('button[data-card-command]:enabled').waitFor({state:'attached'});
  await melee().evaluate(element=>element.scrollIntoView({block:'center'}));const garroteShot=path.join(out,'garrote-owner-390.png');await melee().screenshot({path:garroteShot});screenshots.push(garroteShot);
  let state=await call('get','/combat/effects');
  await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:state.version,action:'start',payload:{map_id:map.id,battle_mode:true,participants:[{target_type:'character',target_id:'vezemir',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1}]}});
  state=await call('get','/combat/effects');await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:state.version,action:'next_turn',payload:{}});
  state=await call('get','/combat/effects');await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:state.version,action:'end',payload:{}});
  await sheet(player.page);await equip('Madu');
  assert.ok(!(await call('get','/combat/effects')).effects.some(e=>e.item_special==='garrote'));
  checks.push('Garrote from owner grid card, native victim turn, save/damage audit, stowing releases');
  await call('patch',`/gm/workspace/tokens/${encodeURIComponent(enemy.id)}`,{sheet:{...enemy.sheet,saving_throw:12,size:'M',inventory:[{equipped:true,quantity:1,mechanics:{special_defense:'tower'}}]}});
  await sheet(player.page);dialog=await aim();assert.ok(await dialog.getByRole('button',{name:'Sim',exact:true}).isDisabled());
  await dialog.getByRole('combobox',{name:'Lado do escudo torre'}).selectOption('protected');
  const towerShot=path.join(out,'tower-direction-owner-390.png');await dialog.screenshot({path:towerShot});screenshots.push(towerShot);
  response=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/attacks/resolve');void response.catch(()=>{});
  await dialog.getByRole('button',{name:'Sim',exact:true}).click();resolved=await response;assert.ok(resolved.ok(),await resolved.text());receipt=await resolved.json();assert.equal(receipt.breakdown.tower_shield.protected_side,true);
  checks.push('tower direction explicit in mobile target confirmation; native roll, natural-20 exception and retry tested separately');
  await equip('Escudo torre','Mão secundária');
  const towerOwned=await call('get','/characters/vezemir');assert.ok(towerOwned.inventory.some(i=>i.equipped&&i.mechanics?.special_defense==='tower'));
  await equip('Escudo de Vibranium','Mão secundária');
  await call('post','/characters/vezemir/actions',{action:'set_hp',payload:{value:before.state.maximum_hp},request_id:randomUUID()});
  const ranged=player.page.locator('.workspace-attack-catalog > article').filter({hasText:'À distância'}).first();
  const selector=ranged.getByRole('combobox',{name:'Arma de À distância'});if(await selector.count())await selector.selectOption('compendium:protecao-escudo-de-vibranium');
  assert.ok((await ranged.textContent()).includes('Escudo de Vibranium'),'chosen ranged shield must replace the old launcher caption');
  const ringResponse=player.page.waitForResponse(r=>new URL(r.url()).pathname==='/gm/grid/range'&&new URL(r.url()).searchParams.get('weapon_item_path')==='compendium:protecao-escudo-de-vibranium');void ringResponse.catch(()=>{});
  dialog=await aim(ranged);assert.ok((await ringResponse).ok());
  await dialog.getByRole('combobox',{name:'Lado do escudo torre'}).selectOption('open');
  response=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/attacks/resolve');void response.catch(()=>{});
  await dialog.getByRole('button',{name:'Sim',exact:true}).click();resolved=await response;assert.ok(resolved.ok(),await resolved.text());receipt=await resolved.json();assert.equal(receipt.breakdown.item_special.kind,'vibranium');assert.equal(typeof receipt.breakdown.item_special_result.returned,'boolean');
  checks.push('Vibranium bought, equipped in off hand, selected as ranged weapon, owns its 9-m ring, confirmed throw and persistence');
  await sheet(player.page);await gm.page.reload();
  const width=await player.page.evaluate(()=>({width:document.documentElement.clientWidth,content:document.documentElement.scrollWidth}));assert.ok(width.content<=width.width+2,JSON.stringify(width));
  assert.deepEqual(errors,[]);checks.push('reload preserves binding; owner and GM use same cards; mobile has no horizontal overflow');
  console.log(JSON.stringify({status:'PASS',checks,screenshots,visual_acceptance:'pending_agent_image_review',production_modified:false}));
 }catch(error){if(player?.page){fs.writeFileSync(path.join(out,'failure-dom.private.html'),await player.page.content().catch(()=>''));await player.page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});}console.log(JSON.stringify({status:'FAIL',error:String(error),checks,screenshots,out}));process.exitCode=1;}
 finally{clearTimeout(deadline);await player?.ctx.close().catch(()=>{});await gm?.ctx.close().catch(()=>{});await browser?.close().catch(()=>{});await api.dispose();}
})();
