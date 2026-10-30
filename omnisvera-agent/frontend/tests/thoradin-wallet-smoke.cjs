// Actual copied Thoradin/Raziel commerce through the player UI. TEMP only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.equal(base,'http://127.0.0.1:8871');
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),`${method} ${url}: ${r.status()}`);return r.json();};
 const health=await call('get','/health');
 for(const value of [health.database_path,health.vault_path])assert.ok(path.resolve(value).startsWith(path.resolve(os.tmpdir())+path.sep));
 const combat=await call('get','/combat/effects');if(combat.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
 const maps=await call('get','/workspace/maps'),map=maps.find(m=>m.id==='official:nimalis');assert.ok(map);
 await call('patch','/gm/workspace/maps/active',{map_id:map.id});
 const pins=await call('get','/gm/workspace/npc-tokens'),pin=pins.find(p=>p.name==='Thoradin'&&p.map_id===map.id);assert.ok(pin);
 const shops=await call('get',`/workspace/tokens/${encodeURIComponent(pin.id)}/commerce?character_id=raziel`),shop=shops.find(m=>m.name==='Equipamentos de Thoradin');assert.ok(shop);
 const offer=shop.offers.find(o=>/Mochila/i.test(o.name)&&o.price_copper===50&&o.quantity>0);assert.ok(offer,'Real stock must contain the backpack used to reproduce the wallet bug');
 const root=path.resolve(__dirname,'../../..'),catalog={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/companionIconCatalog.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:catalog,exports:catalog.exports});
 const assets=[map.image_path,pin.image_path,...shop.offers.map(o=>catalog.exports.iconPathForItem(o.name))];
 for(const asset of assets.filter(Boolean)){
  if(!asset.startsWith('zz_media/'))continue;
  const source=path.resolve(root,asset),target=path.resolve(health.vault_path,asset);
  assert.ok(source.startsWith(path.join(root,'zz_media')+path.sep)&&target.startsWith(path.resolve(health.vault_path)+path.sep));
  assert.ok(fs.existsSync(source),asset);fs.mkdirSync(path.dirname(target),{recursive:true});if(!fs.existsSync(target))fs.copyFileSync(source,target);
 }
 const initial=await call('get','/characters/raziel');
 for(const [currency,field,value] of [['gold','coins',105],['silver','silver_coins',25],['copper','copper_coins',0],['platinum','platinum_coins',0]])
  await call('post','/characters/raziel/actions',{action:'set_currency',payload:{currency,value,expected_balance:initial.state[field]||0},reason:'Fixture: reproduce Thoradin wallet regression',request_id:randomUUID()});
 const wallet=s=>Object.fromEntries(['coins','silver_coins','copper_coins','platinum_coins'].map(k=>[k,s[k]||0]));
 const before=await call('get','/characters/raziel'),boughtPath='compendium:kit-basico-mochila-armazena-ate-30-kg-2-kg-5-pp';
 const count=sheet=>sheet.inventory.find(i=>i.item_path===boughtPath)?.quantity||0;
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],screenshots=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-thoradin-wallet-'));
 try{
  async function open(role,width){
   const ctx=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await ctx.addInitScript(role=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','raziel');},role);
   const page=await ctx.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mapas$/:/Sessão$/}).click();
   const button=page.locator(`[data-grid-token="${pin.id}"]`);await button.scrollIntoViewIfNeeded();await button.click();
   const dialog=page.getByRole('dialog',{name:'Ficha de Thoradin',exact:true});await dialog.waitFor();
   const offers=dialog.getByRole('region',{name:`Ofertas de ${shop.name}`,exact:true});await offers.waitFor();
   return{ctx,page,dialog,offers,commerce:dialog.getByRole('region',{name:'Comércio e serviços',exact:true})};
  }
  const gm=await open('gm',1440),player=await open('raziel',390);
  const item=view=>view.offers.locator('.commerce-offers article').filter({has:view.page.getByText(offer.name,{exact:true})}).first();
  await item(player).getByRole('button').first().click();await player.commerce.getByRole('button',{name:'Cancelar',exact:true}).click();
  assert.deepEqual(wallet((await call('get','/characters/raziel')).state),wallet(before.state));
  await item(player).getByRole('button').first().click();
  const confirmation=player.commerce.getByRole('group',{name:'Confirmar negociação'});await confirmation.waitFor();
  const responsePromise=player.page.waitForResponse(r=>/\/commerce\/quotes\/[^/]+\/confirm$/.test(new URL(r.url()).pathname)&&r.request().method()==='POST');
  await confirmation.getByRole('button',{name:'Confirmar',exact:true}).click();const response=await responsePromise;assert.ok(response.ok());const receipt=await response.json();
  assert.equal(receipt.total_copper,50);assert.deepEqual(receipt.purse_after,{coins:105,silver_coins:20,copper_coins:0,platinum_coins:0});
  await player.commerce.getByRole('status').waitFor();
  await gm.page.waitForFunction(({name,stock})=>[...document.querySelectorAll('.commerce-offers article')].find(n=>n.querySelector('strong')?.textContent===name)?.querySelector('[aria-label="Estoque disponível"]')?.textContent===`${stock} disponíveis`,{name:offer.name,stock:offer.quantity-1});
  const after=await call('get','/characters/raziel');assert.equal(count(after),count(before)+1);
  const replay=await player.ctx.request.post(`${base}/commerce/quotes/${receipt.receipt_id}/confirm`,{headers:{'X-Omnisvera-Token':'cf01-local-raziel'},data:{request_id:randomUUID()}});assert.ok(replay.ok());assert.deepEqual((await replay.json()).purse_after,receipt.purse_after);
  assert.equal(count(await call('get','/characters/raziel')),count(after));
  const screen=path.join(output,'thoradin-player-390.png');await player.dialog.screenshot({path:screen});screenshots.push(screen);
  await player.page.reload();await player.page.locator('.app-shell.authenticated').waitFor();
  await player.page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
  await player.page.waitForFunction(()=>[...document.querySelectorAll('[aria-label="Prata: saldo"]')].some(n=>n.textContent==='20'));
  const walletScreen=path.join(output,'raziel-wallet-reload-390.png');await player.page.locator('.workspace-wallet').screenshot({path:walletScreen});screenshots.push(walletScreen);
  assert.deepEqual(wallet((await call('get','/characters/raziel')).state),receipt.purse_after);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',scope:'isolated_real_thoradin_raziel_wallet',checks:['cancel','native UI purchase','preserved denominations','stock realtime second local client','retry once','inventory once','reload'],screenshots,visual_acceptance:'pending_human_or_agent_image_review',production_modified:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
