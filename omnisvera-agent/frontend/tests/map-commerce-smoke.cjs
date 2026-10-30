// Real Nimalis pins copied by the native CF fixture. Never use operational credentials/state.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data,context=api)=>{const r=await context[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${await r.text()}`);return r.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 assert.ok(path.resolve(health.vault_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const battle=await call('get','/combat/effects');if(battle.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:battle.version,action:'end',payload:{}});
 const maps=await call('get','/workspace/maps');const map=maps.find(m=>/nimalis/i.test(m.title));assert.ok(map,'Nimalis must exist in copied campaign');
 const image=map.image_path,root=path.resolve(__dirname,'../../..');assert.ok(image.startsWith('zz_media/'));
 const original=path.resolve(root,image),copy=path.resolve(health.vault_path,image);
 assert.ok(original.startsWith(path.join(root,'zz_media')+path.sep)&&copy.startsWith(path.resolve(health.vault_path)+path.sep));
 if(fs.existsSync(original)){fs.mkdirSync(path.dirname(copy),{recursive:true});fs.copyFileSync(original,copy);}
 await call('patch',`/gm/workspace/maps/${encodeURIComponent(map.id)}/visibility`,{visible_to_players:true});
 await call('patch','/gm/workspace/maps/active',{map_id:map.id});
 const beforePins=(await call('get','/workspace')).tokens;
 let pin=beforePins.find(t=>t.token_type==='location'&&t.visible_to_players);
 if(!pin)pin=await call('post','/gm/workspace/tokens',{token_type:'location',name:'Balcão de ensaio Nimalis',latitude:47,longitude:48,map_id:map.id,visible_to_players:true,sheet:{description:'Estabelecimento exclusivo da fixture.'}});
 const npc=await call('post','/gm/npcs',{request_id:randomUUID(),name:'Mercador do ensaio '+randomUUID().slice(0,5),visible_to_players:true,private_description:'COMMERCE-GM-SECRET',public_description:'Comerciante de Nimalis'});
 const place=await call('post','/gm/world/locations',{request_id:randomUUID(),name:'Loja de ensaio em Nimalis',location_type:'unknown',visibility:'table'});
 const merchant=await call('post','/gm/merchants',{name:'Ofertas de Nimalis '+randomUUID().slice(0,5),location:map.title});
 const bind={token_id:pin.id,npc_id:npc.id,location_id:place.id,enabled:true,buy_pct:50};
 await call('put',`/gm/merchants/${merchant.id}/binding`,bind);
 const stock=await call('post',`/gm/merchants/${merchant.id}/stock`,{compendium_item_id:'arma-corpo-espada-longa',quantity:2,price_override_po:1});
 const delivery=await call('post',`/gm/merchants/${merchant.id}/services`,{name:'Reposição de equipamento',kind:'delivery',price_copper:10,compendium_item_id:'arma-corpo-espada-longa',amount:1});
 await call('post',`/gm/merchants/${merchant.id}/services`,{name:'Hospedagem de Nimalis',kind:'lodging',price_copper:10,amount:1});
 const sheet=await call('get','/characters/vezemir');await call('post','/characters/vezemir/actions',{action:'set_currency',payload:{currency:'gold',value:100,expected_balance:sheet.state.coins??0},request_id:randomUUID(),reason:'Fixture: comércio'});
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-commerce-ui-'));
 try{
  const contexts=[];
  async function open(role,width){
   const ctx=await browser.newContext({viewport:{width,height:width===390?844:1000},isMobile:width===390,hasTouch:width===390});contexts.push(ctx);
   await ctx.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','vezemir');},{role});
   const page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   const nav=page.getByRole('navigation',{name:'Navegação principal'});await nav.getByRole('button',{name:role==='gm'?/Mapas$/:/Sessão$/}).click();
   const button=page.locator(`[data-grid-token="${pin.id}"]`);await button.scrollIntoViewIfNeeded();await button.click();
   const dialog=page.getByRole('dialog',{name:`Local ${pin.name}`,exact:true});await dialog.waitFor();
   const shop=dialog.getByRole('region',{name:'Comércio e serviços'});await shop.getByText(merchant.name,{exact:true}).waitFor();const offers=shop.getByRole('region',{name:`Ofertas de ${merchant.name}`,exact:true});return {ctx,page,dialog,shop,offers};
  }
  const gm=await open('gm',1440),player=await open('vezemir',390);
  const configured=gm.shop.locator('.commerce-setup');await configured.locator('summary').click();await configured.getByRole('combobox',{name:'Estabelecimento',exact:true}).selectOption(merchant.id);
  const bindingSaved=gm.page.waitForResponse(r=>r.url().endsWith('/binding')&&r.request().method()==='PUT');
  await configured.getByRole('button',{name:'Salvar vínculo',exact:true}).click();assert.ok((await bindingSaved).ok());
  assert.equal(await player.shop.getByText('Configurar ofertas',{exact:true}).count(),0);
  assert.ok(!(await player.page.content()).includes('COMMERCE-GM-SECRET'));
  // Cancellation cannot spend money or change stock.
  const offer=player.offers.getByRole('button',{name:/Espada longa.*1 PO/}).first();await offer.click();
  await player.shop.getByRole('button',{name:'Cancelar',exact:true}).click();
  assert.equal((await call('get','/characters/vezemir')).state.coins,100);
  await player.offers.getByRole('button',{name:'Barganhar Espada longa',exact:true}).first().click();
  const confirmation=player.shop.getByRole('group',{name:'Confirmar negociação'});await confirmation.waitFor();assert.match(await confirmation.innerText(),/d20/);
  const responsePromise=player.page.waitForResponse(r=>/\/commerce\/quotes\/.*\/confirm$/.test(r.url())&&r.request().method()==='POST');
  await confirmation.getByRole('button',{name:'Confirmar',exact:true}).click();const response=await responsePromise;assert.ok(response.ok());const receipt=await response.json();
  await player.shop.getByRole('status').waitFor();
  // Another browser must receive the native ledger websocket and update this open shop.
  await gm.page.waitForFunction(name=>[...document.querySelectorAll('.workspace-commerce section[aria-label]')].find(el=>el.getAttribute('aria-label')==='Ofertas de '+name)?.querySelector('.commerce-offers')?.textContent.includes('· 1'),merchant.name);
  const replay=await player.ctx.request.post(`${base}/commerce/quotes/${receipt.receipt_id}/confirm`,{headers:{'X-Omnisvera-Token':'cf01-local-vezemir'},data:{request_id:randomUUID()}});assert.ok(replay.ok());assert.equal((await replay.json()).receipt_id,receipt.receipt_id);
  const afterBuy=await call('get','/characters/vezemir');const bought=afterBuy.inventory.find(i=>i.item_path==='compendium:arma-corpo-espada-longa');assert.ok(bought);assert.equal(bought.damage_formula,'1d8');
  await player.offers.getByRole('button',{name:'Vender',exact:true}).click();await player.offers.locator('.commerce-offers button').filter({hasText:'Espada longa'}).first().click();
  await player.shop.getByRole('button',{name:'Confirmar',exact:true}).click();await player.shop.getByRole('status').filter({hasText:'Vendido:'}).waitFor();
  await player.offers.getByRole('button',{name:'Serviços',exact:true}).click();await player.offers.getByRole('button',{name:/Reposição de equipamento/}).click();await player.shop.getByRole('button',{name:'Confirmar',exact:true}).click();await player.shop.getByRole('status').filter({hasText:'Reposição'}).waitFor();
  const beforeRest=await call('get','/characters/vezemir');await player.offers.getByRole('button',{name:/Hospedagem de Nimalis/}).click();await player.shop.getByRole('button',{name:'Confirmar',exact:true}).click();await player.shop.getByRole('status').filter({hasText:'reservado até o descanso'}).waitFor();
  const afterRoom=await call('get','/characters/vezemir');assert.equal(afterRoom.state.current_hp,beforeRest.state.current_hp);assert.deepEqual(afterRoom.state.resources,beforeRest.state.resources);
  const commerceResponse=await player.ctx.request.get(`${base}/workspace/tokens/${encodeURIComponent(pin.id)}/commerce?character_id=vezemir`,{headers:{'X-Omnisvera-Token':'cf01-local-vezemir'}});assert.ok(commerceResponse.ok());assert.ok(!(await commerceResponse.text()).includes('COMMERCE-GM-SECRET'));
  const other=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
  const steal=await other.post(`/commerce/${merchant.id}/quotes`,{data:{request_id:randomUUID(),character_id:'vezemir',kind:'buy',target_id:stock.id}});assert.equal(steal.status(),403);await other.dispose();
  const tamper=await player.ctx.request.post(`${base}/commerce/${merchant.id}/quotes`,{headers:{'X-Omnisvera-Token':'cf01-local-vezemir'},data:{request_id:randomUUID(),character_id:'vezemir',kind:'buy',target_id:stock.id,final_price_po:0}});assert.equal(tamper.status(),422);
  const history=await call('get',`/npcs/${npc.id}`);assert.equal(history.events.filter(e=>e.event_type==='commerce').length,4);
  await player.offers.getByRole('button',{name:'Comprar',exact:true}).click();await configured.locator('summary').click();
  await player.dialog.evaluate(el=>el.scrollTop=0);await gm.dialog.evaluate(el=>el.scrollTop=0);
  await player.dialog.screenshot({path:path.join(output,'nimalis-player-390.png')});await gm.dialog.screenshot({path:path.join(output,'nimalis-gm-1440.png')});
  for(const view of [gm,player]){const size=await view.dialog.evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth}));assert.ok(size.scroll<=size.width+1,'Commerce dialog must fit viewport');}
  await player.page.reload();await player.page.locator('.app-shell.authenticated').waitFor();await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Sessão$/}).click();await player.page.locator(`[data-grid-token="${pin.id}"]`).click();await player.page.getByText(merchant.name,{exact:true}).waitFor();
  const reloaded=await call('get','/characters/vezemir');assert.equal(reloaded.state.coins,afterRoom.state.coins);assert.equal(reloaded.inventory.find(i=>i.item_path===bought.item_path)?.quantity,afterRoom.inventory.find(i=>i.item_path===bought.item_path)?.quantity);
  const reloadedShop=player.page.getByRole('region',{name:`Ofertas de ${merchant.name}`,exact:true});
  await reloadedShop.locator('.commerce-offers button').filter({hasText:'Espada longa'}).first().click();
  const rejectedGroup=player.page.getByRole('group',{name:'Confirmar negociação'});await rejectedGroup.waitFor();
  await call('delete',`/gm/merchants/${merchant.id}/stock/${stock.id}`);
  await rejectedGroup.getByRole('button',{name:'Confirmar',exact:true}).click();
  await player.page.getByRole('alert').filter({hasText:'Oferta removida'}).waitFor();
  assert.equal((await call('get','/characters/vezemir')).state.coins,reloaded.state.coins,'Rejected offer cannot spend money');
  // NPC pins use the same commerce window, not just location pins.
  const npcPin=await call('post','/gm/workspace/tokens',{token_type:'monster',name:'Mercador de Nimalis (ensaio)',latitude:46,longitude:46,map_id:map.id,visible_to_players:true,current_hp:1,maximum_hp:1,sheet:{role:'Mercador',description:'NPC comercial da fixture.'}});
  await call('put',`/gm/merchants/${merchant.id}/binding`,{...bind,token_id:npcPin.id});
  await player.page.getByRole('button',{name:'Fechar local',exact:true}).click();
  await player.page.locator(`[data-grid-token="${npcPin.id}"]`).click();
  const npcDialog=player.page.getByRole('dialog',{name:`Ficha de ${npcPin.name}`,exact:true});await npcDialog.getByText(merchant.name,{exact:true}).waitFor();
  await npcDialog.screenshot({path:path.join(output,'nimalis-npc-player-390.png')});
  const afterPins=(await call('get','/workspace')).tokens;for(const old of beforePins){const current=afterPins.find(t=>t.id===old.id);assert.ok(current);assert.equal(current.latitude,old.latitude);assert.equal(current.longitude,old.longitude);}
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',map:map.title,pins_preserved:beforePins.length,checks:['GM configuration','player mobile buy/cancel/haggle','native sell and restock','delivery service','lodging waits for GM rest','receipt replay','owner/price privacy','NPC history','realtime second browser','reload persistence'],evidence:output}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
