// Native action cards -> grid -> Yes/No -> auto-apply. TEMP fixture only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8'));assert.ok(evidence.run_id.startsWith('simulation-'));
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 assert.ok(path.resolve(health.vault_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[],calls=[];
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-grid-flow-ui-'));
 try{
  for(const [actor,action,resource,cost] of [['morthak','Toque Sombrio','toque_sombrio',1],['raziel','Arma de Sangue','reserva_de_sangue',2],['vezemir','Corpo a corpo',null,0],['dorn7','Corpo a corpo',null,0]]){
   if((await get('/combat/effects')).encounter?.active)await command('end');
   await post(`/characters/${actor}/actions`,{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture'});
   assert.ok((await api.patch('/gm/workspace/tokens/'+evidence.enemy_id,{data:{maximum_hp:500,current_hp:500}})).ok());
   let workspace=await get('/workspace?map_id='+encodeURIComponent(evidence.map_id));
   // Copy only the current public Session 7 map into the disposable vault; never edit the original.
   const asset=workspace.map.image_path,repo=path.resolve(__dirname,'../../..');
   assert.match(asset,/^zz_media\/session7\/[^/]+\.(jpg|png|svg)$/i);
   const original=path.resolve(repo,asset),copy=path.resolve(health.vault_path,asset);
   assert.ok(copy.startsWith(path.resolve(health.vault_path)+path.sep));assert.ok(fs.existsSync(original));
   fs.mkdirSync(path.dirname(copy),{recursive:true});fs.copyFileSync(original,copy);
   if(!workspace.map.grid)await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/grid`,{request_id:randomUUID(),expected_version:0,cols:20,rows:20,cell_size_m:1.5});
   const roster={map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:actor,initiative:30},{target_type:'token',target_id:evidence.enemy_id,initiative:1}]};
   await command('start',roster);await command('end');
   workspace=await get('/workspace?map_id='+encodeURIComponent(evidence.map_id));
   const grid=workspace.map.grid,enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id).grid_position,token=workspace.tokens.find(t=>t.character_id===actor),pos=token.grid_position;
   // A corpse fixture may share the enemy's original cell. Separate it; do not force-click through it.
   for(const body of workspace.tokens.filter(t=>t.current_hp===0 && t.grid_position && t.grid_position.cell_x===enemy.cell_x && t.grid_position.cell_y===enemy.cell_y)){
    const p=body.grid_position;
    await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:body.id,mode:'GM_REPOSITION',path:[[p.cell_x,p.cell_y],[Math.max(0,p.cell_x-3),Math.max(0,p.cell_y-3)]],expected_position_version:p.version,expected_grid_version:grid.version});
   }
   await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[pos.cell_x,pos.cell_y],[Math.max(0,enemy.cell_x-1),enemy.cell_y]],expected_position_version:pos.version,expected_grid_version:grid.version});
   await command('start',roster);
   const role=actor==='dorn7'?'gm':actor,width=actor==='vezemir'||actor==='dorn7'?1440:390;
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST')calls.push({url:r.url(),body:r.postDataJSON()});});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator(`button[data-character="${actor}"]`).click();
   if(actor==='raziel'){await page.locator('.workspace-sheet-section > summary').filter({hasText:'Hemomancia'}).click();await page.getByLabel('Forma da Hemomancia',{exact:true}).selectOption('arma-de-sangue');}
   const card=page.locator('article').filter({has:page.getByRole('button',{name:action,exact:true})}).first();
   await page.waitForFunction(()=>{const img=document.querySelector('.workspace-map-stage > img');return img?.complete&&img.naturalWidth>0;});
   assert.ok((await page.locator('.workspace-map-stage').boundingBox()).height>200,'Real map must not collapse');
   assert.equal(await card.getByRole('combobox',{name:/Alvo/}).count(),0);
   const before=await get('/characters/'+actor),hp=(await get('/workspace')).tokens.find(t=>t.id===evidence.enemy_id).current_hp;
   const aim=async()=>{assert.equal(await card.locator('button[data-card-command]').isVisible(),false);await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();const overlay=await page.locator('.targeting-overlay').boundingBox(),stage=await page.locator('.workspace-map-stage').boundingBox();assert.ok(Math.abs(overlay.width-stage.width)<2);assert.ok(Math.abs(overlay.height-stage.height)<2);await page.locator(`[data-grid-token="${evidence.enemy_id}"]`).click();await page.getByRole('dialog',{name:'Confirmar alvo'}).waitFor();};
   await aim();assert.equal((await get('/workspace')).tokens.find(t=>t.id===evidence.enemy_id).current_hp,hp);
   if(actor==='morthak'){
    await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Não',exact:true}).click();
    assert.equal((await get('/characters/'+actor)).state.resources.find(r=>r.key===resource).current,before.state.resources.find(r=>r.key===resource).current);await aim();
   }
   await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
   const result=page.getByRole('status',{name:'Último resultado'});await result.waitFor();
   assert.equal(await page.getByRole('dialog',{name:/Resolução d[ao]/}).count(),0);
   await result.getByRole('button',{name:'Ver resultado',exact:true}).click();
   const details=page.getByRole('dialog',{name:/^Resultado:/});await details.waitFor();
   assert.match(await details.innerText(),/PV:|Dano calculado/);
   await details.getByRole('button',{name:'Fechar descrição'}).click();
   if(resource)assert.equal((await get('/characters/'+actor)).state.resources.find(r=>r.key===resource).current,before.state.resources.find(r=>r.key===resource).current-cost);
   const after=(await get('/workspace')).tokens.find(t=>t.id===evidence.enemy_id).current_hp;assert.ok(after<=hp);
   await page.screenshot({path:path.join(output,actor+'.png'),fullPage:false});await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal((await get('/workspace')).tokens.find(t=>t.id===evidence.enemy_id).current_hp,after);
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   assert.equal(await page.getByRole('dialog',{name:/Resolução d[ao]/}).count(),0);
   const log=page.locator('.workspace-timeline');
   await log.getByRole('button',{name:'Ver resultado',exact:true}).first().click();
   const saved=page.getByRole('dialog',{name:/^Resultado:/});await saved.waitFor();
   assert.ok((await saved.innerText()).length>30);
   await saved.getByRole('button',{name:'Fechar descrição'}).click();
   checks.push({actor,width,yes_no:true,auto_applied:true,reload:true});await context.close();
  }
  await command('end');assert.deepEqual(errors,[]);assert.equal(calls.filter(c=>c.url.endsWith('/toque-sombrio')).length,1);
  const action_coverage=checks.map(({actor})=>({actor,key:actor==='morthak'?'ability:toque-sombrio':actor==='raziel'?'ability:arma-de-sangue':'attack:melee',verified_checks:['ui']}));
  console.log(JSON.stringify({status:'PASS',checks,action_coverage,screenshots:output,production_modified:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
