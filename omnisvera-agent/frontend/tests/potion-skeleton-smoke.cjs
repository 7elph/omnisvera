// Native four-actor fixture; player UI purchase/use, GM observer and cross-map summon.
// All setup changes and receipts belong to TEMP. No operational credentials.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data,context=api)=>{const r=await context[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${await r.text()}`);return r.json();};
 const health=await call('get','/health');for(const key of ['database_path','vault_path'])assert.ok(path.resolve(health[key]).startsWith(path.resolve(os.tmpdir())+path.sep));
 let battle=await call('get','/combat/effects');if(battle.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:battle.version,action:'end',payload:{}});
 const map=(await call('get','/workspace/maps')).find(m=>/nimalis/i.test(m.title));assert.ok(map,'copied Nimalis');
 await call('patch',`/gm/workspace/maps/${encodeURIComponent(map.id)}/visibility`,{visible_to_players:true});
 await call('patch','/gm/workspace/maps/active',{map_id:map.id});
 const pin=await call('post','/gm/workspace/tokens',{token_type:'location',name:'Poções do ensaio',latitude:45,longitude:45,map_id:map.id,visible_to_players:true});
 const merchant=await call('post','/gm/merchants',{name:'Poções do ensaio',location:map.title});
 await call('put',`/gm/merchants/${merchant.id}/binding`,{token_id:pin.id,enabled:true,buy_pct:50});
 const stock=await call('post',`/gm/merchants/${merchant.id}/stock`,{compendium_item_id:'campanha-pocao-hp',quantity:5,price_override_po:5});
 const before=await call('get','/characters/vezemir');
 await call('post','/characters/vezemir/actions',{action:'set_currency',payload:{currency:'gold',value:100,expected_balance:before.state.coins??0},request_id:randomUUID(),reason:'Fixture: poções'});
 await call('post','/characters/vezemir/actions',{action:'set_hp',payload:{value:1},request_id:randomUUID(),reason:'Fixture: comprovar cura'});
 const canonical='Items/Poção de HP.md',count=s=>s.inventory.filter(i=>i.item_path===canonical).reduce((sum,i)=>sum+i.quantity,0);
 const initial=await call('get','/characters/vezemir');
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],screenshots=[],out=fs.mkdtempSync(path.join(os.tmpdir(),'omni-potion-skeleton-'));
 console.log('EVIDENCE potion-skeleton '+out);
 try{
  async function open(role,width,actor='vezemir'){
   const ctx=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await ctx.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token',role==='gm'?'cf01-local-gm':'cf01-local-'+actor);localStorage.setItem('omnisvera_access_mode',role);localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
   const page=await ctx.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();return{ctx,page};
  }
  async function sheet(view,role,actor){await view.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await view.page.locator(`button[data-character="${actor}"]`).click();}
  async function activate(card){await card.locator('button[data-card-command]:enabled').waitFor({state:'attached'});await card.click({position:{x:8,y:8}});}
  async function shop(view,role){
   await view.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mapas$/:/Sessão$/}).click();
   const token=view.page.locator(`[data-grid-token="${pin.id}"]`);await token.scrollIntoViewIfNeeded();await token.click();
   const dialog=view.page.getByRole('dialog',{name:'Local '+pin.name,exact:true});await dialog.waitFor();
   const commerce=dialog.getByRole('region',{name:'Comércio e serviços',exact:true});
   const offers=dialog.getByRole('region',{name:'Ofertas de '+merchant.name,exact:true});await offers.waitFor();return{dialog,commerce,offers};
  }
  const gm=await open('gm',1440),player=await open('player',390);
  const observer=await shop(gm,'gm'),store=await shop(player,'player');
  const offer=store.offers.locator('.commerce-offers article').filter({has:player.page.getByText('Poção de HP',{exact:true})}).first();
  await offer.getByRole('button').first().click();await store.commerce.getByRole('button',{name:'Cancelar',exact:true}).click();
  assert.equal(count(await call('get','/characters/vezemir')),count(initial));
  await offer.getByRole('button').first().click();const confirmation=store.commerce.getByRole('group',{name:'Confirmar negociação'});await confirmation.waitFor();
  const buying=player.page.waitForResponse(r=>r.request().method()==='POST'&&/\/commerce\/quotes\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));
  await confirmation.getByRole('button',{name:'Confirmar',exact:true}).click();const response=await buying;assert.ok(response.ok());const receipt=await response.json();
  await gm.page.waitForFunction(()=>[...document.querySelectorAll('.commerce-offers article')].some(a=>a.querySelector('strong')?.textContent==='Poção de HP'&&a.querySelector('[aria-label="Estoque disponível"]')?.textContent==='4 disponíveis'));
  const bought=await call('get','/characters/vezemir');assert.equal(count(bought),count(initial)+1);
  const money=s=>(s.coins||0)*100+(s.silver_coins||0)*10+(s.copper_coins||0)+(s.platinum_coins||0)*1000;
  assert.equal(money(initial.state)-money(bought.state),500);
  const replay=await player.ctx.request.post(base+`/commerce/quotes/${receipt.receipt_id}/confirm`,{headers:{'X-Omnisvera-Token':'cf01-local-vezemir'},data:{request_id:randomUUID()}});assert.ok(replay.ok());assert.equal(count(await call('get','/characters/vezemir')),count(bought));
  await store.dialog.getByRole('button',{name:'Fechar local',exact:true}).click();
  await sheet(player,'player','vezemir');
  const potion=player.page.locator('.workspace-resource-catalog article').filter({has:player.page.getByRole('button',{name:'Poção de HP',exact:true})});
  await potion.waitFor();assert.equal(await potion.count(),1,'one aggregated resource, including manual/legacy flasks');
  await potion.locator(':scope > b').filter({hasText:new RegExp('^'+count(bought)+'$')}).waitFor({timeout:10000});
  assert.equal(await potion.locator(':scope > b').innerText(),String(count(bought)));
  const using=player.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/characters/vezemir/actions');
  void using.catch(()=>{});
  assert.ok(await potion.locator('button[data-card-command]').isEnabled(),'Potion use unavailable: '+await potion.locator('button[data-card-command]').getAttribute('title'));
  await activate(potion);const useReply=await using;assert.ok(useReply.ok(),await useReply.text());
  const used=await call('get','/characters/vezemir');assert.equal(count(used),count(bought)-1);assert.ok(used.state.current_hp>1&&used.state.current_hp<=5);
  const useRequest=useReply.request().postDataJSON();assert.equal(useRequest.action,'use_item');
  const useReplay=await player.ctx.request.post(base+'/characters/vezemir/actions',{headers:{'X-Omnisvera-Token':'cf01-local-vezemir'},data:useRequest});assert.ok(useReplay.ok());
  assert.equal((await call('get','/characters/vezemir')).state.current_hp,used.state.current_hp);assert.equal(count(await call('get','/characters/vezemir')),count(used));
  await potion.locator(':scope > b').filter({hasText:new RegExp('^'+count(used)+'$')}).waitFor();
  await potion.screenshot({path:path.join(out,'hp-resource-player-390.png')});screenshots.push(path.join(out,'hp-resource-player-390.png'));
  await observer.dialog.getByRole('button',{name:'Fechar local',exact:true}).click();
  await sheet(gm,'gm','vezemir');const gmPotion=gm.page.locator('.workspace-resource-catalog article').filter({has:gm.page.getByRole('button',{name:'Poção de HP',exact:true})});await gmPotion.waitFor();assert.equal(await gmPotion.count(),1);
  await gmPotion.screenshot({path:path.join(out,'hp-resource-master.png')});screenshots.push(path.join(out,'hp-resource-master.png'));
  await player.ctx.close();await gm.ctx.close();

  // Only fixture's hidden old-map skeleton is created; do not mutate its real counterpart.
  await call('post','/characters/morthak/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Fixture: nova invocação'});
  const old=await call('post','/gm/workspace/tokens',{token_type:'monster',map_id:map.id,name:'Esqueleto antigo do ensaio',latitude:50,longitude:50,current_hp:10,maximum_hp:10,visible_to_players:false,sheet:{summon:{caster:'morthak',technique:'levantar-esqueleto',duration:'week'}}});
  // Dismiss any copied active skeletons except the deliberate stale one.
  for(const token of await call('get','/gm/workspace/npc-tokens'))if(token.id!==old.id&&token.sheet?.summon?.caster==='morthak'&&token.sheet.summon.technique==='levantar-esqueleto'&&token.current_hp>0)await call('post','/characters/morthak/techniques/dispensar-invocacao',{request_id:randomUUID(),target_type:'token',target_id:token.id});
  const evidence=JSON.parse(fs.readFileSync(process.env.OMNISVERA_SIMULATION_EVIDENCE,'utf8'));
  const targetMap=(await call('get','/workspace/maps')).find(m=>m.id===evidence.map_id&&m.id!==map.id);assert.ok(targetMap,'second map with native fixture grid');
  await call('patch',`/gm/workspace/maps/${encodeURIComponent(targetMap.id)}/visibility`,{visible_to_players:true});await call('patch','/gm/workspace/maps/active',{map_id:targetMap.id});
  const morthak=await open('player',390,'morthak');await sheet(morthak,'player','morthak');
  const spells=morthak.page.locator('.workspace-sheet-section').filter({has:morthak.page.locator('summary').filter({hasText:/^Magias$/})});if(!await spells.evaluate(el=>el.open))await spells.locator(':scope > summary').click();
  const resources=s=>s.state.resources.find(r=>r.key==='levantar_um_esqueleto').current,beforeSummon=await call('get','/characters/morthak');
  const spellName=beforeSummon.definition.session_abilities.find(a=>a.id==='levantar-um-esqueleto').name;
  const card=spells.locator('article.workspace-spell-card').filter({has:morthak.page.getByRole('button',{name:spellName,exact:true})});await card.waitFor();
  const canceled=morthak.page.waitForEvent('dialog',{timeout:20000}).then(dialog=>dialog.dismiss());void canceled.catch(()=>{});
  await activate(card);await canceled;
  assert.equal(resources(await call('get','/characters/morthak')),resources(beforeSummon));
  morthak.page.once('dialog',dialog=>dialog.accept());
  const replacing=morthak.page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/techniques/levantar-um-esqueleto')&&r.request().postDataJSON()?.mode==='replace');
  void replacing.catch(()=>{});
  await activate(card);const replacedReply=await replacing;assert.ok(replacedReply.ok(),await replacedReply.text());const replaced=await replacedReply.json();
  assert.equal(replaced.replaced_token_id,old.id);assert.equal(replaced.token.map_id,targetMap.id);assert.equal(resources(await call('get','/characters/morthak')),resources(beforeSummon)-1);
  const replacementReplay=await morthak.ctx.request.post(base+'/characters/morthak/techniques/levantar-um-esqueleto',{headers:{'X-Omnisvera-Token':'cf01-local-morthak'},data:replacedReply.request().postDataJSON()});assert.ok(replacementReplay.ok());assert.equal((await replacementReplay.json()).token.id,replaced.token.id);
  const dialog=morthak.page.getByRole('dialog',{name:/^Ficha de /});await dialog.waitFor();await dialog.screenshot({path:path.join(out,'replacement-player-390.png')});screenshots.push(path.join(out,'replacement-player-390.png'));
  await morthak.page.reload();await morthak.page.locator('.app-shell.authenticated').waitFor();assert.ok((await call('get','/workspace')).tokens.some(t=>t.id===replaced.token.id));
  await morthak.ctx.close();assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['player purchase','cancel','one HP resource','1d4 heal','one physical flask','purchase/use replay','master parity','second client stock realtime','hidden old-map skeleton','replacement cancel','replacement once','reload'],screenshots,visual_acceptance:'pending_agent_image_review',production_modified:false}));
 }catch(error){let n=0;for(const context of browser.contexts())for(const page of context.pages()){try{await page.screenshot({path:path.join(out,`failure-${++n}.png`),timeout:5000,animations:'disabled'});}catch{}}throw error;}
 finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
