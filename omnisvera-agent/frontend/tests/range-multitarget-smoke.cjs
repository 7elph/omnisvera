// Native GM card and multi-selection, on the MCP disposable fixture only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();},post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 if((await get('/combat/effects')).encounter?.active)await command('end');
 await post('/characters/dorn7/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture'});
 assert.ok((await api.patch('/gm/workspace/maps/active',{data:{map_id:evidence.map_id}})).ok());
 const targets=[];
 for(let i=0;i<3;i++)targets.push(await post('/gm/workspace/tokens',{token_type:'monster',map_id:evidence.map_id,name:'Alvo Relâmpago '+i,visible_to_players:true,current_hp:200,maximum_hp:200,latitude:10,longitude:10+i*5,sheet:{armor_class:10,saving_throw:20,attributes:{dexterity:10}}}));
 const roster={map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'dorn7',initiative:30},...targets.map(t=>({target_type:'token',target_id:t.id,initiative:1}))]};
 await command('start',roster);await command('end');
 let workspace=await get('/workspace?map_id='+encodeURIComponent(evidence.map_id));const grid=workspace.map.grid;
 const dorn=workspace.tokens.find(t=>t.character_id==='dorn7');assert.ok(dorn?.grid_position);
 const placements=[[dorn,[2,2]],...targets.map((t,i)=>[workspace.tokens.find(p=>p.id===t.id),[4+i,2+i]])];
 for(const [token,cell] of placements){const p=token.grid_position;await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[p.cell_x,p.cell_y],cell],expected_position_version:p.version,expected_grid_version:grid.version});}
 await command('start',roster);
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],casts=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-range-multi-ui-'));
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','dorn7');});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/gm/combat/effects')&&r.postDataJSON().payload?.grid_selection)casts.push(r.postDataJSON());});
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();
  await page.locator('button[data-character="dorn7"]').click();
  const card=page.locator('article.workspace-spell-card').filter({hasText:'Relâmpago'}),dialog=page.getByRole('dialog',{name:'Confirmar alvo'}),pin=id=>page.locator(`[data-grid-token="${id}"]`);
  await page.locator('.workspace-character-panel .workspace-combat-live').waitFor();assert.equal(await page.locator('.workspace-character-panel .workspace-combat-live').getByText(/EFEITOS E MULTIATAQUE/).count(),0);
  assert.equal(await card.locator('[data-card-command]').isVisible(),false);
  // Independent rendered client must converge; HTTP snapshot alone is not UI proof.
  const observer=await context.newPage();observer.on('pageerror',e=>errors.push(e.message));
  await observer.goto(base);await observer.locator('.app-shell.authenticated').waitFor();
  await observer.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();
  await observer.locator(`[data-grid-token="${targets[0].id}"]`).waitFor();
  await page.bringToFront();
  let releaseRange;const rangeGate=new Promise(resolve=>{releaseRange=resolve;});
  await page.route('**/gm/grid/range?*',async route=>{await rangeGate;await route.continue();});
  await card.click({position:{x:8,y:8}});await page.getByText('Abrindo alcance…',{exact:true}).waitFor();await pin(targets[0].id).click();
  assert.equal(await page.locator('.workspace-token-modal-backdrop').count(),0);releaseRange();await page.locator('.targeting-overlay').waitFor();
await page.locator('.targeting-overlay').waitFor();await page.waitForFunction(id=>document.querySelector(`[data-grid-token="${id}"]`)?.classList.contains('target-valid'),targets[0].id);await page.locator('.targeting-overlay').waitFor();await pin(targets[0].id).click();assert.equal(await dialog.count(),0);
  await page.screenshot({path:path.join(output,'range-open-1440.png')});await pin(targets[0].id).click();await dialog.getByRole('button',{name:'Deselecionar',exact:true}).click();assert.equal(await pin(targets[0].id).evaluate(e=>e.classList.contains('target-selected')),false);
  for(const t of targets)await pin(t.id).click();await dialog.getByRole('button',{name:'Sim',exact:true}).waitFor();
  assert.equal(casts.length,0);await page.screenshot({path:path.join(output,'range-selected-1440.png')});await dialog.getByRole('button',{name:'Não',exact:true}).click();assert.equal(casts.length,0);
  await page.setViewportSize({width:390,height:900});await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();await page.waitForFunction(id=>document.querySelector(`[data-grid-token="${id}"]`)?.classList.contains('target-valid'),targets[0].id);await pin(targets[0].id).click();await pin(targets[0].id).click();await dialog.getByRole('button',{name:'Terminar ação',exact:true}).waitFor();await page.screenshot({path:path.join(output,'range-finish-390.png')});await dialog.getByRole('button',{name:'Terminar ação',exact:true}).click();
  await page.locator('.workspace-spell-outcome').waitFor();assert.equal(casts.length,1);assert.equal(casts[0].payload.targets.length,1);
  assert.equal(casts[0].payload.definition_revision,'dorn-relampago-campaign-v1');
  assert.equal(casts[0].payload.map_id,evidence.map_id);assert.equal(casts[0].payload.damage,undefined);
  let state=await get('/workspace');const changed=state.tokens.find(t=>t.id===targets[0].id).current_hp;assert.ok(changed<200);assert.equal(state.tokens.find(t=>t.id===targets[1].id).current_hp,200);
  await observer.bringToFront();
  await observer.waitForFunction(({id,hp})=>document.querySelector(`[data-grid-token="${id}"]`)?.textContent?.includes(`${hp}/200`),{id:targets[0].id,hp:changed});
  await page.bringToFront();
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal((await get('/workspace')).tokens.find(t=>t.id===targets[0].id).current_hp,changed);
  await command('end');await post('/characters/dorn7/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture'});await command('start',roster);await page.reload();await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();await page.locator('button[data-character="dorn7"]').click();
  await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();await page.waitForFunction(id=>document.querySelector(`[data-grid-token="${id}"]`)?.classList.contains('target-valid'),targets[0].id);for(const t of targets)await pin(t.id).click();await dialog.getByRole('button',{name:'Sim',exact:true}).click();await page.locator('.workspace-spell-outcome').waitFor();assert.equal(casts.length,2);assert.equal(casts[1].payload.targets.length,3);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['card activation','full-map white range','GM actual battle card','three target confirmation','remove/reselect','cancel no cost','finish one','auto apply three','contract revision/map','mobile','reload','second rendered local client'],action_coverage:[{actor:'dorn7',key:'ability:relampago',verified_checks:['ui']}],screenshots:output,production_modified:false}));
 }catch(error){
  for(const [index,tab] of browser.contexts().flatMap(c=>c.pages()).entries())
   await tab.screenshot({path:path.join(output,`failure-${index}.png`),timeout:5000}).catch(()=>{});
  console.error('PRIVATE_SCREENSHOTS='+output);throw error;
 }finally{await browser.close();await command('end');await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
