// Read-only UI acceptance on the native copied CF fixture. No operational tokens.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));assert.ok(path.resolve(health.vault_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const battle=await call('get','/combat/effects');if(battle.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:battle.version,action:'end',payload:{}});
 const maps=await call('get','/workspace/maps'),map=maps.find(m=>m.id==='official:nimalis');assert.ok(map);
 await call('patch','/gm/workspace/maps/active',{map_id:map.id});await call('patch',`/gm/workspace/maps/${encodeURIComponent(map.id)}/visibility`,{visible_to_players:true});
 const pins=await call('get','/gm/workspace/npc-tokens'),pin=pins.find(p=>p.name==='Thoradin'&&p.map_id===map.id);assert.ok(pin);
 const shops=await call('get',`/workspace/tokens/${encodeURIComponent(pin.id)}/commerce?character_id=vezemir`),shop=shops.find(m=>m.name==='Equipamentos de Thoradin');assert.ok(shop);assert.equal(shop.offers.length,37);
 const catalog={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/companionIconCatalog.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:catalog,exports:catalog.exports});
 const copyAsset=asset=>{assert.ok(asset.startsWith('zz_media/'));const source=path.resolve(__dirname,'../../..',asset),target=path.resolve(health.vault_path,asset);assert.ok(source.startsWith(path.resolve(__dirname,'../../../zz_media')+path.sep)&&target.startsWith(path.resolve(health.vault_path)+path.sep));assert.ok(fs.existsSync(source),asset);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);};
 copyAsset(map.image_path);copyAsset(pin.image_path);
 for(const offer of shop.offers){const image=catalog.exports.iconPathForItem(offer.name);assert.ok(image,offer.name);copyAsset(image);}
 const characters=await call('get','/characters'),npcs=await call('get','/npcs');
 for(const asset of [...characters.map(c=>c.portrait),...pins.map(p=>p.image_path),...npcs.map(n=>n.portrait_path)])if(asset?.startsWith('zz_media/')&&fs.existsSync(path.resolve(__dirname,'../../..',asset)))copyAsset(asset);
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-shop-header-'));
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:width===390?844:1000},isMobile:width===390,hasTouch:width===390});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','vezemir');});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   const nav=page.getByRole('navigation',{name:'Navegação principal'});await nav.getByRole('button',{name:/Mesa$/}).click();
   const header=page.locator('.party-status-header'),card=header.locator('[data-character="vezemir"]');await card.locator('.party-card-level').waitFor();
   const character=(await call('get','/characters')).find(c=>c.id==='vezemir');assert.equal(await card.locator('.party-card-level').innerText(),String(character.level));assert.equal(await card.locator('small').innerText(),character.class_name);assert.ok(!/\d+\s*\/\s*\d+/.test(await card.innerText()));
   const bar=await card.getByRole('progressbar').boundingBox(),level=await card.locator('.party-card-level').boundingBox();assert.ok(level.x>=bar.x+bar.width&&Math.abs(level.y+level.height/2-bar.y-bar.height/2)<2,'Level must sit beside the bar');
   await header.screenshot({path:path.join(output,`header-${width}.png`)});
   await nav.getByRole('button',{name:/NPCs$/}).click();const library=page.getByRole('region',{name:'NPCs do Mestre',exact:true});await library.getByRole('button',{name:'Atualizar pins',exact:true}).waitFor();await library.locator('.npc-card-list').getByRole('button',{name:/Thoradin/}).waitFor();
   const names=await library.locator('.npc-card-list button strong,.npc-reserved-entry > button:first-child strong,.workspace-npc-reference-list > button strong,.npc-pin-group > summary strong').allTextContents();
   const normalize=n=>n.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();assert.equal(new Set(names.map(normalize)).size,names.length,'One library entry per identity/group');assert.equal(names.filter(n=>normalize(n)==='thoradin').length,1);
   const lichCount=pins.filter(p=>p.name==='Lich').length;if(lichCount>1){const group=library.locator('.npc-pin-group').filter({has:page.locator('summary strong').filter({hasText:/^Lich$/})});assert.equal(await group.count(),1);await group.locator('summary').click();assert.equal(await group.getByRole('button').count(),lichCount);}
   await library.screenshot({path:path.join(output,`npc-library-${width}.png`)});
   await library.locator('.npc-card-list').getByRole('button',{name:/Thoradin/}).click();await library.getByRole('button',{name:'Abrir ficha no mapa',exact:true}).click();
   const dialog=page.getByRole('dialog',{name:'Ficha de Thoradin',exact:true}),offers=dialog.getByRole('region',{name:'Ofertas de Equipamentos de Thoradin',exact:true});await offers.waitFor();
   const images=offers.locator('img.commerce-item-image');assert.equal(await images.count(),37);await images.evaluateAll(nodes=>nodes.forEach(node=>node.loading='eager'));
   await page.waitForFunction(()=>{const images=[...document.querySelectorAll('.workspace-commerce img.commerce-item-image')];return images.length===37&&images.every(img=>img.complete&&img.naturalWidth>0&&!img.src.includes('inventario.jpg'));});
   assert.equal(await offers.getByLabel('Estoque disponível',{exact:true}).count(),37);assert.match(await offers.innerText(),/disponíveis/);
   await dialog.screenshot({path:path.join(output,`thoradin-shop-${width}.png`)});const size=await dialog.evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth}));assert.ok(size.scroll<=size.width+1);
   await context.close();
  }
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks:['37 real item images','explicit stock quantity','level beside health bar','no visible numeric HP','one NPC library entry per identity','distinct Lich instances preserved','NPC dossier opens original map sheet','desktop/mobile'],evidence:output}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
