// Fixed TEMP-only acceptance: read-only gallery, then native opening/retry in the fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.equal(base,'http://127.0.0.1:8871');
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async(url,client=api)=>{const r=await client.get(url);assert.ok(r.ok(),`${url}: ${r.status()}`);return r.json();};
 const health=await get('/health');
 for(const value of [health.database_path,health.vault_path])assert.ok(path.resolve(value).startsWith(path.resolve(os.tmpdir())+path.sep));
 const scenes=(await get('/scenes')).filter(s=>/^Sexta\s*·/.test(s.title));assert.equal(scenes.length,6);
 assert.ok(scenes.every(s=>s.status==='draft'&&s.visibility==='gm'));
 const before=await get('/workspace'),combatBefore=await get('/combat/effects');
 const playerApi=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
 const publicScenes=await get('/scenes',playerApi);assert.ok(!publicScenes.some(s=>scenes.some(p=>p.id===s.id)));
 const denied=await playerApi.get(`/scenes/${scenes[0].id}`);assert.equal(denied.status(),404);
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-preparations-ui-'));
 const browser=await chromium.launch({channel:'msedge',headless:true}),screenshots=[],errors=[],writes=[];
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','morthak');});
   const page=await context.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method())&&/\/(gm\/(scenes|workspace)|characters\/[^/]+\/actions|commerce\/)/.test(new URL(r.url()).pathname))writes.push(r.url());});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).click();
   const library=page.getByRole('region',{name:'Biblioteca de preparações',exact:true});await library.waitFor();
   await library.getByRole('searchbox',{name:'Buscar',exact:true}).fill('Sexta');
   await page.waitForFunction(()=>document.querySelectorAll('.scene-library-card').length===6);
   await page.waitForFunction(()=>[...document.querySelectorAll('.scene-library-cover img')].every(i=>i.complete&&i.naturalWidth>0));
   for(const scene of scenes){
    await library.getByRole('button',{name:new RegExp(scene.title.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).click();
    const viewer=page.getByRole('region',{name:`Preparação: ${scene.title}`,exact:true});await viewer.waitFor();
    assert.equal(await viewer.locator('.scene-map-preview').count(),0,'Full map opens only on demand');
    await viewer.locator('.scene-context-content .scene-map-card .scene-asset-inspect').click();
    const mapDialog=page.locator('dialog.scene-map-dialog');await mapDialog.waitFor();
    const preview=mapDialog.getByRole('region',{name:'Prévia do mapa e pins',exact:true});await preview.waitFor();
    await page.waitForFunction(()=>{const p=document.querySelector('.scene-map-preview-surface img');return p?.complete&&p.naturalWidth>0;});
    assert.equal(await viewer.getByRole('alert').count(),0);
    const viewport=preview.locator('.scene-map-preview-viewport');const size=await viewport.boundingBox();
    await preview.getByRole('button',{name:'Ampliar prévia',exact:true}).click();
    await preview.getByRole('button',{name:'Ampliar prévia',exact:true}).click();
    const enlarged=await viewport.boundingBox();assert.ok(Math.abs(size.height-enlarged.height)<2,'Zoom must not enlarge the page viewport');
    assert.ok(enlarged.width<=width,'Map must fit the mobile panel');
    await preview.getByRole('button',{name:'Ajustar',exact:true}).click();
    await mapDialog.getByRole('button',{name:'Fechar detalhes',exact:true}).click();
    await viewer.getByRole('button',{name:/^Biblioteca ·/}).click();
    const libraryElements=viewer.getByRole('complementary',{name:'Biblioteca de elementos'});
    const card=libraryElements.locator('.scene-asset-card:not(.scene-map-card) .scene-asset-inspect').first();await card.click();
    const dialog=page.locator('dialog.scene-asset-dialog');await dialog.waitFor();
    assert.ok((await dialog.boundingBox()).width<=width);
    await dialog.getByRole('button',{name:'Fechar detalhes',exact:true}).click();
    await viewer.getByRole('button',{name:'Conteúdo público',exact:true}).click();
    assert.equal(await viewer.locator('.scene-asset-card').count(),0);
    assert.equal(await viewer.locator('.scene-map-preview').count(),0);
    await viewer.getByRole('button',{name:'Preparação',exact:true}).click();
    // Native lazy-loading: inspect every rendered image, not only the cover.
    for(const image of await viewer.locator('.scene-asset-card img').all()){
     await image.scrollIntoViewIfNeeded();
     await image.evaluate(async element=>{await element.decode();assertImage(element);function assertImage(img){if(!img.naturalWidth)throw Error('Preparation image did not decode');}});
    }
    if(scene.id===23){
     for(const label of ['Representante militar','Mestre do Conclave']){
      const npc=libraryElements.locator('.scene-asset-card').filter({hasText:label}).first();
      assert.equal(await npc.locator('img').count(),1,`Missing portrait: ${label}`);
     }
    }
    await viewer.getByRole('button',{name:'Fechar biblioteca',exact:true}).click();
    const sceneShot=path.join(output,`scene-${scene.id}-${width}.png`);
    await viewer.screenshot({path:sceneShot});screenshots.push(sceneShot);
   }
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal page overflow');
   const screenshot=path.join(output,`preparations-${width}.png`);await page.screenshot({path:screenshot,fullPage:true});screenshots.push(screenshot);
   await context.close();
  }
  assert.deepEqual(writes,[],'Inspecting a preparation must not publish, activate or move anything');
  const after=await get('/workspace');assert.equal(after.map.id,before.map.id);assert.deepEqual(after.tokens,before.tokens);
  assert.deepEqual(await get('/combat/effects'),combatBefore);assert.deepEqual(errors,[]);
  // Separate phase. API and database above are proven TEMP/8871; no live credentials.
  const command=async(method,url,data)=>{const r=await api.fetch(url,{method,data});assert.ok(r.ok(),`${url}: ${r.status()}`);return r.json();};
  const originalMaps=await get('/workspace/maps'),sessions=await get('/gm/sessions');
  let session=sessions.find(s=>s.status==='active'),createdSession=false;
  if(!session){
   session=await command('POST','/gm/sessions',{request_id:`qa-preparation-opening-${Date.now()}`,title:'QA TEMP · abertura de preparações'});
   await command('POST',`/gm/sessions/${session.id}/status`,{status:'active'});createdSession=true;
  }
  const opening_checks=[];
  for(const scene of scenes){
   const body={request_id:`qa-open-preparation-${scene.id}-${Date.now()}`};
   const result=await command('POST',`/gm/scenes/${scene.id}/open-on-table`,body);
   assert.equal(result.map.id,scene.map_id);assert.equal(result.created,true);
   const replay=await command('POST',`/gm/scenes/${scene.id}/open-on-table`,body);
   assert.equal(replay.created,false);assert.equal(replay.event.id,result.event.id);
   const publicWorkspace=await get('/workspace',playerApi);
   assert.equal(publicWorkspace.map.id,scene.map_id,'Opening must select/reveal the prepared map to a player');
   assert.ok(publicWorkspace.messages.some(m=>m.text?.includes(scene.public_description)),'Opening must reach the public session record');
   assert.ok(!JSON.stringify(publicWorkspace).includes('ELENCO DE HOJE'),'Private GM notes must stay private');
   for(const id of scene.elements.filter(e=>e.visibility==='gm').map(e=>e.id)){
    assert.ok(!publicWorkspace.messages.some(m=>m.scene_element_id===id),'Hidden clues must not be published by opening');
   }
   opening_checks.push({scene_id:scene.id,map_id:scene.map_id,player_map:true,opening_record:true,retry:true});
  }
  const encounter=await require('./today-encounter-probe.cjs').runTodayEncounter({api,browser,base,output});
  fs.writeFileSync(path.join(output,'today-encounter.json'),JSON.stringify(encounter,null,2));
  await command('PATCH','/gm/workspace/maps/active',{map_id:before.map.id});
  for(const map of originalMaps){
   if(scenes.some(s=>s.map_id===map.id))await command('PATCH',`/gm/workspace/maps/${encodeURIComponent(map.id)}/visibility`,{visible_to_players:map.visible_to_players});
  }
  if(createdSession)await command('POST',`/gm/sessions/${session.id}/status`,{status:'completed'});
  console.log(JSON.stringify({status:'PASS',scope:'isolated_preparations_desktop_mobile_and_native_opening',screenshots,opening_checks,encounter,fixture_publication:true,visual_acceptance:'pending_human_or_agent_image_review',production_modified:false}));
 }finally{await browser.close();await api.dispose();await playerApi.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
