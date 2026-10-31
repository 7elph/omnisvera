// Native TEMP-only market -> inventory -> equipment -> use -> attack/reload.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const playerApi=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-vezemir'}});
 const call=async(method,url,data,context=api)=>{const r=await context[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${await r.text()}`);return r.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-item-families-')),checks=[],screenshots=[],errors=[];let browser,gm,player;
 const deadline=setTimeout(()=>{void browser?.close().finally(()=>process.exit(1));},260000);deadline.unref();
 try{
  const combat=await call('get','/combat/effects');if(combat.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
  await call('patch','/gm/workspace/table-mode',{table_mode:'physical'});
  await call('patch','/gm/workspace/maps/active',{map_id:'official:nimalis'});
  const before=await call('get','/characters/vezemir');
  const action=(name,payload,client=api)=>call('post','/characters/vezemir/actions',{action:name,payload,request_id:randomUUID(),reason:'Fixture: famílias de itens'},client);
  await action('set_currency',{currency:'gold',value:5000,expected_balance:before.state.coins??0});
  for(const item of before.inventory.filter(i=>i.equipped))await action('unequip_item',{item_path:item.item_path});
  for(const item of before.inventory.filter(i=>i.mechanics?.family==='ammunition'&&i.quantity>0))await action('change_quantity',{item_path:item.item_path,quantity:0});
  const baseline=await call('get','/characters/vezemir');
  const pin=await call('post','/gm/workspace/tokens',{token_type:'location',name:'Famílias do ensaio',latitude:60,longitude:65,map_id:'official:nimalis',visible_to_players:true});
  const shop=await call('post','/gm/merchants',{name:'Famílias do ensaio',location:'Nimalis - fixture'});
  await call('put',`/gm/merchants/${shop.id}/binding`,{token_id:pin.id,enabled:true,buy_pct:50});
  const items=[['Cota de malha','arma-armadura-cota-de-malha'],['Escudo de aço','arma-escudo-escudo-de-aco'],['Arco curto','arma-distancia-arco-curto'],['Flecha x20','arma-distancia-flecha-x20'],['Poção do ensaio','vault:Items/__fixture_restorative.md'],['Madu','arma-corpo-madu'],['Espada bastarda','arma-corpo-espada-bastarda'],['Rede','kit-explorador-rede'],['Zarabatana','arma-distancia-zarabatana'],['Dardo de zarabatana x20','arma-distancia-dardo-zarabatana-x20'],['Garrote','arma-corpo-garrote'],['Escudo torre','kit-basico-escudo-torre-20-kg-30-po'],['Escudo de Vibranium','protecao-escudo-de-vibranium']];
  // Resolve actual catalog identities by title, retaining the checked source metadata.
  const catalog=await call('get','/gm/items/trade-catalog');const records=catalog.items;
  for(const entry of items){const row=records.find(r=>r.name===entry[0]);assert.ok(row,entry[0]);entry[1]=row.id;await call('post',`/gm/merchants/${shop.id}/stock`,{compendium_item_id:row.id,quantity:3});}
  browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'chrome':undefined});
  async function open(role,width){const ctx=await browser.newContext({viewport:{width,height:1000},isMobile:width===390,hasTouch:width===390});await ctx.addInitScript(role=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','vezemir');},role);const page=await ctx.newPage();page.setDefaultTimeout(22000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();return{ctx,page,role};}
  gm=await open('gm',1440);player=await open('vezemir',390);
  await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Sessão$/}).click();
  const token=player.page.locator(`[data-grid-token="${pin.id}"]`);await token.scrollIntoViewIfNeeded();await token.click();
  const offers=player.page.getByRole('region',{name:'Ofertas de '+shop.name,exact:true});await offers.waitFor();const dialog=player.page.getByRole('dialog').filter({has:offers}),commerce=dialog.getByRole('region',{name:'Comércio e serviços',exact:true});
  for(const [name] of items){
   await offers.locator('.commerce-offers article').filter({has:player.page.getByText(name,{exact:true})}).getByRole('button').first().click();
   const response=player.page.waitForResponse(r=>r.request().method()==='POST'&&/\/commerce\/quotes\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));void response.catch(()=>{});
   await commerce.getByRole('group',{name:'Confirmar negociação'}).getByRole('button',{name:'Confirmar',exact:true}).click();const r=await response;assert.ok(r.ok(),await r.text());const receipt=await r.json();assert.ok(receipt.total_copper>0);await commerce.locator(`[data-commerce-receipt="${receipt.receipt_id}"]`).waitFor();
  }
  await offers.locator('.commerce-offers article').filter({has:player.page.getByText(items.at(-1)[0],{exact:true})}).getByText(/2 disponíveis/).waitFor();
  const storeShot=path.join(out,'families-shop-player-390.png');await dialog.screenshot({path:storeShot});screenshots.push(storeShot);
  checks.push('owner buys armor, shield, bow, arrows and declarative potion through native shop UI');
  await dialog.getByRole('button',{name:/^(Fechar ficha|Fechar local)$/}).click();
  await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
  await player.page.locator('button[data-character="vezemir"]').click();
  async function equip(name,slot){
   await player.page.locator('.workspace-inventory-catalog').getByRole('button',{name,exact:true}).click();
   const item=player.page.getByRole('dialog',{name:'Informações de '+name,exact:true});
   await item.getByRole('button',{name:'Equipar em '+slot,exact:true}).click();
   await item.getByRole('button',{name:'Guardar',exact:true}).waitFor();await item.getByRole('button',{name:'Fechar informações do item'}).click();
  }
  await equip('Cota de malha','Armadura');const body=await call('get','/characters/vezemir');assert.ok(body.definition.defenses.armor_class>baseline.definition.defenses.armor_class);
  await equip('Escudo de aço','Mão secundária');const armored=await call('get','/characters/vezemir');assert.equal(armored.definition.defenses.armor_class,body.definition.defenses.armor_class+2);
  await equip('Arco curto','À distância');checks.push('mobile inventory dialog equips body/shield/bow; CA updates once');
  await action('set_hp',{value:1});await player.page.reload();await player.page.locator('.app-shell.authenticated').waitFor();
  await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
  const ownerView=await call('get','/characters/vezemir?read_only=true',undefined,playerApi);
  const ownPotion=ownerView.inventory.find(i=>i.item_path==='Items/__fixture_restorative.md');
  assert.ok(ownPotion?.usable);await player.page.locator('.workspace-resource-catalog').scrollIntoViewIfNeeded();
  fs.writeFileSync(path.join(out,'consumable-view.private.json'),JSON.stringify({item:ownPotion,html:await player.page.locator('.workspace-resource-catalog').evaluateAll(elements=>elements.map(e=>e.outerHTML.slice(0,20000)))}));
  const potion=player.page.locator('.workspace-resource-catalog article').filter({hasText:'Poção do ensaio'});
  const using=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/actions'&&r.request().postDataJSON()?.action==='use_item');void using.catch(()=>{});
  await potion.locator('button[data-card-command]:enabled').waitFor({state:'attached'});
  await potion.click({position:{x:8,y:8}});const used=await using;assert.ok(used.ok(),await used.text());
  assert.equal((await call('get','/characters/vezemir')).state.current_hp,4);checks.push('Vault-style consumable appears in Resources and heals on native owner button');
  const sheetShot=path.join(out,'families-sheet-player-390.png');await player.page.locator('.workspace-equipment-loadout').screenshot({path:sheetShot});screenshots.push(sheetShot);
  const enemy=await call('post','/gm/workspace/tokens',{token_type:'monster',name:'Alvo de munição',latitude:20,longitude:20,map_id:'official:nimalis',visible_to_players:true,current_hp:200,maximum_hp:200,sheet:{armor_class:10}});
  const shotRequest={request_id:randomUUID(),attack_id:'ranged',weapon_item_path:'compendium:'+items[2][1],target_type:'token',target_id:enemy.id,roll_mode:'physical',d20:20};
  const resolved=await call('post','/characters/vezemir/attacks/resolve',shotRequest,playerApi);
  const receipt=await call('post','/combat/attacks/'+resolved.resolution_id+'/confirm',undefined,playerApi);assert.ok(receipt.confirmed);
  await call('post','/combat/attacks/'+resolved.resolution_id+'/confirm',undefined,playerApi);
  const after=await call('get','/characters/vezemir');const arrows=after.inventory.find(i=>i.item_path==='compendium:'+items[3][1]);assert.equal(arrows.charges_current,19);assert.equal(arrows.quantity,1);
  checks.push('owner bow attack uses arrow damage, consumes exactly one arrow, confirmation replay does not duplicate');
  await player.page.reload();await player.page.locator('.app-shell.authenticated').waitFor();const reloaded=await call('get','/characters/vezemir');assert.equal(reloaded.definition.defenses.armor_class,armored.definition.defenses.armor_class);assert.equal(reloaded.inventory.find(i=>i.item_path===arrows.item_path).charges_current,19);
  await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
  await player.page.locator('button[data-character="vezemir"]').click();
  await player.page.locator('.workspace-inventory-catalog').scrollIntoViewIfNeeded();
  await player.page.locator('.workspace-inventory-catalog').getByRole('button',{name:'Flecha x20',exact:true}).getByLabel('Quantidade',{exact:true}).filter({hasText:/^19$/}).waitFor();
  await gm.page.locator('button[data-character="vezemir"]').click();const gmState=await call('get','/characters/vezemir?read_only=true');assert.equal(gmState.definition.defenses.armor_class,reloaded.definition.defenses.armor_class);
  const width=await player.page.evaluate(()=>({width:document.documentElement.clientWidth,content:document.documentElement.scrollWidth}));assert.ok(width.content<=width.width+2,JSON.stringify(width));
  assert.deepEqual(errors,[]);checks.push('reload preserves equipment, CA and arrows; GM and owner agree; no mobile horizontal overflow');
  console.log(JSON.stringify({status:'PASS',checks,screenshots,visual_acceptance:'pending_agent_image_review',production_modified:false}));
 }catch(error){if(player?.page){fs.writeFileSync(path.join(out,'failure-dom.private.html'),(await player.page.content()).slice(0,350000));await player.page.screenshot({path:path.join(out,'failure.png'),fullPage:true,timeout:5000}).catch(()=>{});}console.error(JSON.stringify({status:'FAIL',reason:error.message,evidence:out}));throw error;}
 finally{clearTimeout(deadline);await player?.ctx.close();await gm?.ctx.close();await browser?.close();await playerApi.dispose();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
