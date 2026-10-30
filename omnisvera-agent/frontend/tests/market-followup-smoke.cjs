// Real UI over copied campaign data. Monetary/HP mutations are TEMP only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${await r.text()}`);return r.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const shops=await call('get','/gm/merchants'),thoradin=shops.find(s=>s.name==='Equipamentos de Thoradin'),guild=shops.find(s=>s.name==='Conclave dos Errantes');assert.ok(thoradin&&guild);
 const state=await call('get','/characters/vezemir');const originalUsedItem=state.inventory.find(i=>i.item_path==='compendium:arma-corpo-espada-longa');assert.ok(originalUsedItem);await call('post','/characters/vezemir/actions',{action:'set_currency',payload:{currency:'gold',value:500,expected_balance:state.state.coins??0},request_id:randomUUID(),reason:'Fixture: comércio avançado'});
 await call('post','/characters/vezemir/actions',{action:'set_hp',payload:{value:1},request_id:randomUUID(),reason:'Fixture: cura de serviço'});
 await call('patch','/gm/workspace/table-mode',{table_mode:'digital'});
 const enemy=await call('post','/gm/workspace/tokens',{token_type:'monster',name:'Alvo do ensaio de Klhauss',latitude:20,longitude:20,map_id:'official:nimalis',visible_to_players:true,current_hp:200,maximum_hp:200,sheet:{armor_class:10}});
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-market-followup-')),checks=[],screenshots=[],errors=[];let browser,gm,player;
 const deadline=setTimeout(()=>{void browser?.close().finally(()=>process.exit(1));},240000);deadline.unref();
 try{
  browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'chrome':undefined});
  async function open(role,width){const ctx=await browser.newContext({viewport:{width,height:1000},isMobile:width===390,hasTouch:width===390});await ctx.addInitScript(role=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','vezemir');},role);const page=await ctx.newPage();page.setDefaultTimeout(25000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();return{ctx,page,role};}
  gm=await open('gm',1440);player=await open('vezemir',390);await gm.page.locator('button[data-character="vezemir"]').click();
  async function openShop(view,shop){await view.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:view.role==='gm'?/Mapas$/:/Sessão$/}).click();const pin=view.page.locator(`[data-grid-token="${shop.token_id}"]`);await pin.scrollIntoViewIfNeeded();await pin.click();const offers=view.page.getByRole('region',{name:'Ofertas de '+shop.name,exact:true});await offers.waitFor();const dialog=view.page.getByRole('dialog').filter({has:offers});return{...view,offers,dialog,commerce:dialog.getByRole('region',{name:'Comércio e serviços',exact:true})};}
  async function close(view){await view.dialog.getByRole('button',{name:/^(Fechar ficha|Fechar local)$/}).click();await view.dialog.waitFor({state:'hidden'});}
  async function confirm(view){const response=view.page.waitForResponse(r=>r.request().method()==='POST'&&/\/commerce\/quotes\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));void response.catch(()=>{});await view.commerce.getByRole('group',{name:'Confirmar negociação'}).getByRole('button',{name:'Confirmar',exact:true}).click();const r=await response;assert.ok(r.ok(),await r.text());const data=await r.json();await view.commerce.locator(`[data-commerce-receipt="${data.receipt_id}"]`).waitFor();return data;}
  async function shot(view,name){await view.dialog.evaluate(el=>{el.scrollTop=0;});const d=await view.dialog.evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}));assert.ok(d.scroll<=d.client+2);const file=path.join(out,name);await view.dialog.screenshot({path:file});screenshots.push(file);}
  let g=await openShop(gm,thoradin),p=await openShop(player,thoradin);await p.offers.getByRole('button',{name:'Vender',exact:true}).click();
  const form=g.commerce.locator('details.commerce-setup').filter({has:g.page.locator('summary',{hasText:'Avaliação individual'})});await form.locator(':scope > summary').click();
  await form.getByLabel('Item para oferta individual').selectOption('compendium:arma-corpo-espada-longa');await form.getByLabel('Preço da oferta individual').fill('1.25');await form.getByRole('button',{name:'Definir oferta',exact:true}).click();
  const offer=p.offers.locator('.commerce-offers article').filter({has:p.page.getByText('Espada usada do ensaio',{exact:true})});await offer.getByRole('button').first().click();const sale=await confirm(p);assert.equal(sale.total_copper,125);assert.equal(sale.stock_instance.condition.bonus_remaining,1);assert.equal(sale.stock_instance.charges_current,originalUsedItem.charges_current);assert.equal(sale.stock_instance.charges_max,originalUsedItem.charges_max);
  checks.push('GM individual offer visible to owner without refresh','sale credits exactly final appraised price','charges and corrosion preserved in acquired object');
  const acquire=g.commerce.getByText('Objetos adquiridos para avaliação',{exact:true});await acquire.waitFor({state:'attached'});
  await shot(p,'individual-sale-player-390.png');await close(p);await close(g);
  p=await openShop(player,guild);g=await openShop(gm,guild);await p.offers.getByRole('button',{name:'Serviços',exact:true}).click();await p.offers.getByRole('button',{name:/^Curar Ferimentos Leves/}).click();const heal=await confirm(p);assert.equal(heal.total_copper,3000);assert.ok(heal.service_effect.healing_applied>0);await p.commerce.getByText(/PV 1 →/).waitFor();checks.push('reviewed healing paid at book tariff','native HP effect and dice visible');
  await shot(p,'magic-service-player-390.png');
  const npc=g.offers.locator('details.commerce-npc');await npc.locator('summary').click();await npc.getByRole('button',{name:'Abrir ficha de Klhauss',exact:true}).click();
  const dialog=gm.page.getByRole('dialog',{name:'Ficha de Klhauss',exact:true});await dialog.waitFor();await dialog.getByText(/Rank S · Nv\. 10/).waitFor();
  const spell=dialog.getByRole('button',{name:/^(Conjurar|Mirar) Dardos Místicos/});await spell.waitFor();assert.match(await spell.innerText(),/3\/3/);
  assert.equal(await dialog.getByRole('button',{name:'Executar · JP e dano na hora',exact:true}).count(),0);
  const panel=dialog.getByRole('region',{name:'Ataques de Klhauss',exact:true});
  if((await spell.innerText()).startsWith('Conjurar')){
    await dialog.getByLabel('Alvo de Klhauss',{exact:true}).selectOption('token:'+enemy.id);
    for(const name of ['Espada longa +2','Arco longo +1']){
      await panel.locator('article').filter({has:gm.page.getByText(name,{exact:true})}).getByRole('button',{name:'Atacar · rolar acerto e dano',exact:true}).click();
      await panel.getByRole('button',{name:'Confirmar resultado e aplicar dano',exact:true}).click();await panel.getByText(/Resultado confirmado\. Vida:/).waitFor();
    }
    checks.push('both configured NPC weapon attacks resolve and confirm through native engine');
  }
  if((await spell.innerText()).startsWith('Conjurar')){await dialog.getByLabel('Alvo de Klhauss',{exact:true}).selectOption('token:'+enemy.id);await spell.click();}
  else{await spell.click();await gm.page.locator(`[data-grid-token="${enemy.id}"]`).click();await gm.page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();}
  await dialog.getByRole('button',{name:/^(Conjurar|Mirar) Dardos Místicos.*2\/3/}).waitFor();checks.push('Conclave opens native Rank S warrior-mage sheet','NPC spell button consumes exactly one daily use');
  const touch=dialog.getByRole('button',{name:/^(Conjurar|Mirar) Toque Chocante/});assert.match(await touch.innerText(),/3\/3/);
  if((await touch.innerText()).startsWith('Conjurar')){await touch.click();await dialog.getByRole('button',{name:/^Conjurar Toque Chocante.*2\/3/}).waitFor();checks.push('second NPC spell has independent daily use counter');}
  await shot({dialog},'klhauss-gm-sheet.png');await dialog.getByRole('button',{name:'Voltar ao Conclave',exact:true}).click();await gm.page.getByRole('dialog',{name:'Local Conclave dos Errantes',exact:true}).waitFor();checks.push('return to Conclave works');
  await player.page.reload();await player.page.locator('.app-shell.authenticated').waitFor();assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks,screenshots,visual_acceptance:'pending_agent_image_review',production_modified:false}));
 }catch(error){await gm?.page.screenshot({path:path.join(out,'failure-gm.png'),timeout:5000}).catch(()=>{});await player?.page.screenshot({path:path.join(out,'failure-player.png'),timeout:5000}).catch(()=>{});console.error(JSON.stringify({status:'FAIL',reason:error.message,evidence:out}));throw error;}
 finally{clearTimeout(deadline);await player?.ctx.close();await gm?.ctx.close();await browser?.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
