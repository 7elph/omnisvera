// Expanded per-action UI proof. All preparation and casts stay in native TEMP fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('get',url),command=async(action,payload={})=>call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const health=await get('/health');for(const key of ['database_path','vault_path'])assert.ok(path.resolve(health[key]).startsWith(path.resolve(os.tmpdir())+path.sep));
 const browser=await chromium.launch({channel:'msedge',headless:true}),output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-three-sheet-ui-')),errors=[],action_coverage=[];
 const allCases=[['vezemir','forca-arcana','Força Arcana','forca_arcana'],['vezemir','velocidade','Velocidade','velocidade'],['vezemir','frenesi','Frenesi','frenesi'],['vezemir','provocacao','Provocação','provocacao'],['morthak','aterrorizar','Aterrorizar','aterrorrizar'],['dorn7','forca-arcana','Força Arcana','dorn_forca_arcana'],['dorn7','reflexos','Reflexos','dorn_reflexos'],['dorn7','teia','Teia','dorn_teia'],['dorn7','dissipar-magia','Dissipar Magia','dorn_dissipar_magia'],['dorn7','dorn_guard','Protocolo de Guarda',null]];
 // Two fixed, disjoint halves preserve the exact ten-case union while keeping
 // each browser process below the single-script budget.
 const batches={
  first:[['vezemir','forca-arcana'],['vezemir','velocidade'],['vezemir','frenesi'],['vezemir','provocacao'],['morthak','aterrorizar']],
  second:[['dorn7','forca-arcana'],['dorn7','reflexos'],['dorn7','teia'],['dorn7','dissipar-magia'],['dorn7','dorn_guard']],
 };
 const caseKey=([actor,key])=>actor+':'+key;
 const batch=process.env.OMNISVERA_QA_THREE_SHEET_BATCH||'';
 assert.ok(!batch||Object.prototype.hasOwnProperty.call(batches,batch),'Unknown three-sheet batch');
 const batchKeys=[...batches.first,...batches.second].map(caseKey);
 assert.equal(new Set(batchKeys).size,allCases.length,'Batches must not overlap');
 assert.deepEqual(new Set(batchKeys),new Set(allCases.map(caseKey)),'Batches must preserve all cases');
 // The bounded MCP suite exercises the three repaired families; the agent can
 // run the extended batch independently without unrelated map/shop checks.
 const selectedCases=process.env.OMNISVERA_QA_EXTENDED_ACTIONS==='1'
  ?(batch?allCases.filter(c=>batches[batch].some(([actor,key])=>actor===c[0]&&key===c[1])):allCases)
  :allCases.filter(c=>c[1]==='forca-arcana'||c[1]==='aterrorizar');
 const cases=selectedCases.filter(c=>!process.env.OMNISVERA_QA_ACTION_ACTOR||c[0]===process.env.OMNISVERA_QA_ACTION_ACTOR);
 const copyAsset=asset=>{if(!asset?.startsWith('zz_media/'))return;const source=path.resolve(__dirname,'../../..',asset),target=path.resolve(health.vault_path,asset);assert.ok(source.startsWith(path.resolve(__dirname,'../../../zz_media')+path.sep)&&target.startsWith(path.resolve(health.vault_path)+path.sep));if(fs.existsSync(source)){fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);}};
 try{
  for(const [actor,key,name,resource] of cases){
   console.log('RUN '+actor+' '+key);
   if((await get('/combat/effects')).encounter?.active)await command('end');
   for(const effect of (await get('/combat/effects')).effects.filter(e=>!e.environmental))await command('remove',{id:effect.id});
   await call('post',`/characters/${actor}/actions`,{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente ensaio de ações na fixture'});
   await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
   let workspace=await get('/workspace'),grid=workspace.map.grid;assert.ok(grid);copyAsset(workspace.map.image_path);
   const mine=workspace.tokens.find(t=>t.character_id===actor),ally=workspace.tokens.find(t=>t.character_id==='vezemir');assert.ok(mine);
   const kept=new Set([mine.id,evidence.enemy_id,...(key==='dorn_guard'?[ally.id]:[])]);
   for(const token of workspace.tokens){copyAsset(token.image_path);if(!kept.has(token.id)&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});}
   for(const [token,x,y] of [[mine,4,5],[workspace.tokens.find(t=>t.id===evidence.enemy_id),5,5],...(key==='dorn_guard'?[[ally,4,6]]:[])]){
    const pos=token.grid_position;assert.ok(pos);
    await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:true});
    await call('post',`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[pos.cell_x,pos.cell_y],[x,y]],expected_position_version:pos.version,expected_grid_version:grid.version});
   }
   const enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
   await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{maximum_hp:500,current_hp:500,sheet:{...enemy.sheet,hit_dice:1,saving_throw:99,attributes:{strength:10,dexterity:10,wisdom:10}}});
   let dispelTarget;
   if(key==='dissipar-magia')dispelTarget=(await command('dorn_spell_cast',{spell_id:'forca-arcana',targets:[{type:'token',id:enemy.id}]})).protocol_result.results[0].effect.id;
   await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:actor,initiative:30},{target_type:'token',target_id:enemy.id,initiative:1},...(key==='dorn_guard'?[{target_type:'character',target_id:'vezemir',initiative:10}]:[])]});
   const before=await get('/characters/'+actor),role=actor==='dorn7'?'gm':actor;
   const context=await browser.newContext({viewport:{width:actor==='vezemir'?1440:390,height:900}});
   await context.addInitScript(({actor,role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{actor,role});
   const reads=[];
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('response',async r=>{if(new URL(r.url()).pathname==='/characters/'+actor){try{const d=await r.json();reads.push((d.state?.resources||[]).filter(x=>x.key===resource).map(x=>({key:x.key,current:x.current,maximum:x.maximum})));}catch{}}});await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator(`button[data-character="${actor}"]`).click();
   for(const summary of await page.locator('.workspace-sheet-section > summary').all())if(!(await summary.evaluate(el=>el.parentElement.open)))await summary.click();
   const card=page.locator('article').filter({has:page.getByRole('button',{name,exact:true,includeHidden:true})}).filter({has:page.locator('button[data-card-command]')}).first();
   await card.waitFor();
   if(key==='dorn_guard')assert.equal(await page.locator('article').filter({has:page.getByRole('button',{name,exact:true,includeHidden:true})}).filter({has:page.locator('button[data-card-command]')}).count(),1,'Guard must have one executable card, never a raw resource spender');
   await page.waitForFunction(el=>el?.querySelector('button[data-card-command]')&&!el.querySelector('button[data-card-command]').disabled,await card.elementHandle());
   const calls=[];page.on('request',r=>{if(r.method()==='POST'&&(r.url().includes('/techniques/')||r.url().endsWith('/gm/combat/effects')))calls.push({url:r.url(),body:r.postDataJSON()});});
   const response=page.waitForResponse(r=>r.request().method()==='POST'&&(r.url().endsWith('/techniques/'+key)||(r.url().endsWith('/gm/combat/effects')&&r.request().postDataJSON()?.action===(key==='dorn_guard'?'dorn_guard':'dorn_spell_cast'))));
   await card.click({position:{x:8,y:8}});
   // Reflexos and the approved area Guard resolve on Dorn; neither picks an ally.
   const gridPick=actor==='dorn7'&&!['reflexos','dorn_guard'].includes(key);
   if(gridPick){
    await page.locator('.targeting-overlay').waitFor();
    await page.locator(`[data-grid-token="${enemy.id}"]`).click();
   }
   const confirmation=page.getByRole('dialog',{name:'Confirmar alvo'});
   if(actor==='morthak'||gridPick){await confirmation.waitFor();await confirmation.getByRole('button',{name:'Sim',exact:true}).click();}
   let applied;
   try{applied=await response;}catch(error){
    await page.screenshot({path:path.join(output,actor+'-'+key+'-failure.png'),fullPage:false});
    console.error(JSON.stringify({actor,key,calls,card:await card.textContent().catch(()=>null),screenshot:path.join(output,actor+'-'+key+'-failure.png')}));
    throw error;
   }
   assert.ok(applied.ok(),await applied.text());const receipt=await applied.json();
   const after=await get('/characters/'+actor),effects=(await get('/combat/effects')).effects;
   if(resource){
    const remaining=after.state.resources.find(r=>r.key===resource);assert.equal(remaining.current,before.state.resources.find(r=>r.key===resource).current-1);
    // Player activation controls disappear after committing the turn. The
    // resource counter must be located independently of that now-removed button.
    const counterCard=page.locator('.workspace-character-panel article').filter({has:page.getByRole('button',{name,exact:true,includeHidden:true})}).first();
    const counter=counterCard.getByText(`${remaining.current}/${remaining.maximum}`,{exact:true});
    await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
    for(const summary of await page.locator('.workspace-sheet-section > summary').all())if(!(await summary.evaluate(el=>el.parentElement.open)))await summary.click();
    try{await counter.waitFor();}catch(error){console.error(JSON.stringify({actor,key,card:await counterCard.textContent({timeout:2000}).catch(()=>null),reads}));throw error;}
   }
   const matched=key==='forca-arcana'?effects.some(e=>e.modifiers?.strength_bonus>0):key==='velocidade'?effects.some(e=>e.modifiers?.extra_attacks===1):key==='frenesi'?effects.some(e=>e.skill==='frenesi'):key==='provocacao'?effects.some(e=>e.skill==='provocacao'):key==='aterrorizar'?effects.some(e=>e.necro_spell==='aterrorrizar'):key==='reflexos'?effects.some(e=>e.images_remaining>=2&&e.images_remaining<=5):key==='teia'?effects.some(e=>e.web_area):key==='dorn_guard'?effects.some(e=>e.protocol==='guard'&&e.target_type==='character'&&e.target_id==='dorn7'&&e.area_guard===true&&e.radius_m===9&&!e.ally_id):true;
   assert.ok(matched,name+' consequence missing');assert.equal(calls.length,1,name+' must send one activation');
   if(dispelTarget)assert.equal(effects.some(e=>e.id===dispelTarget),!receipt.protocol_result.results[0].success,'Dispel consequence must match its roll');
   await page.screenshot({path:path.join(output,actor+'-'+key+'.png'),fullPage:false});await page.reload();await page.locator('.app-shell.authenticated').waitFor();
   assert.deepEqual((await get('/characters/'+actor)).state,after.state);
   action_coverage.push({actor,key:'ability:'+key,verified_checks:['ui']});await context.close();
  }
  await command('end');assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',action_coverage,screenshots:output,production_modified:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
