// Native four-actor fixture only. Created NPCs are disposable; no player HP is edited.
const assert=require('node:assert/strict'),path=require('node:path'),{randomUUID}=require('node:crypto');
module.exports=async function({browser,api,base,out,screenshots,checks}){
 assert.equal(base,'http://127.0.0.1:8871');
 const call=async(method,url,data)=>{const r=await api.fetch(url,{method,data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('GET',url),post=(url,data)=>call('POST',url,data);
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const health=await get('/health');assert.match(health.database_path,/Temp/i);
 if((await get('/combat/effects')).encounter?.active)await command('end');
 let ws=await get('/workspace');const mapId=ws.map.id;
 await post(`/workspace/maps/${encodeURIComponent(mapId)}/grid`,{request_id:randomUUID(),expected_version:ws.map.grid?.version||0,cols:40,rows:40,cell_size_m:1.5});
 const catalog=(await get('/gm/workspace/monster-catalog')).monsters;
 async function create(id,name){const source=catalog.find(m=>m.id===id);assert.ok(source);return post('/gm/workspace/tokens',{token_type:'monster',name,map_id:mapId,current_hp:1000,maximum_hp:1000,visible_to_players:true,sheet:{...source,source:{monster_id:id}}});}
 const dragon=await create('dragao-dourado','Ensaio Dragão'),troll=await create('troll','Ensaio Troll'),immune=await create('dragao-dourado','Ensaio Imune'),outside=await create('goblin','Ensaio Fora');
 async function positionAll(){
  ws=await get('/workspace');
  for(const [unit,x,y] of [[dragon,4,4],[troll,14,4],[immune,22,4],[outside,14,20]]){
   const token=ws.tokens.find(t=>t.id===unit.id);
   await post(`/workspace/maps/${encodeURIComponent(mapId)}/move`,{request_id:randomUUID(),token_id:unit.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:ws.map.grid.version});
  }
 }
 for(const [iteration,width] of [1440,390].entries()){
  if((await get('/combat/effects')).encounter?.active)await command('end');
  await positionAll();
  await command('start',{map_id:mapId,battle_mode:true,participants:[dragon,troll,immune,outside].map((t,i)=>({target_type:'token',target_id:t.id,name:t.name,initiative:40-i*10}))});
  const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
  const observer=await browser.newContext({viewport:{width:390,height:900}});
  let inspectedPage;
  try{
   for(const ctx of [context,observer])await ctx.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','dorn7');});
   const page=await context.newPage(),second=await observer.newPage();inspectedPage=page;page.setDefaultTimeout(20000);
   await Promise.all([page.goto(base),second.goto(base)]);
   for(const p of [page,second]){
    await p.locator('.app-shell.authenticated').waitFor();
    await p.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();
    await p.locator('button[data-character="dorn7"]').click();
    // Workspace and combat arrive independently. Wait for the native collapsed
    // controls before opening them; otherwise this loop can run on an empty DOM.
    await p.locator('.workspace-combat-content > summary').first().waitFor();
   }
   for(const summary of await page.locator('.workspace-combat-content > summary:visible').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();
   const panel=page.getByRole('region',{name:'Ataques de Ensaio Dragão',exact:true});await panel.waitFor();
   const card=panel.locator('article').filter({has:page.locator('strong').filter({hasText:/^Baforada$/})});
   let posts=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/gm/combat/effects')&&r.postDataJSON()?.action==='monster_breath')posts++;});
   await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
   await page.locator(`[data-grid-token="${troll.id}"]`).click();
   let dialog=page.getByRole('dialog',{name:'Confirmar alvo'});await dialog.waitFor();
   const text=await dialog.innerText();assert.ok(text.includes(troll.name)&&text.includes(immune.name)&&!text.includes(outside.name));
   assert.ok(await page.locator('.targeting-cross-cell').count()>1);
   await dialog.getByRole('button',{name:'Não',exact:true}).click();assert.equal(posts,0);
   await page.locator('.targeting-overlay').waitFor({state:'hidden'});
   const before=(await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp;
   await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
   await page.locator(`[data-grid-token="${troll.id}"]`).click();
   dialog=page.getByRole('dialog',{name:'Confirmar alvo'});await dialog.waitFor();
   const shot=path.join(out,`monster-breath-${width}.png`);await page.screenshot({path:shot});screenshots.push(shot);
   const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/gm/combat/effects')&&r.request().postDataJSON()?.action==='monster_breath');
   await dialog.getByRole('button',{name:'Sim',exact:true}).click();const confirmed=await response;assert.equal(confirmed.status(),200);
   const body=confirmed.request().postDataJSON(),receipt=await confirmed.json(),result=receipt.protocol_result;
   assert.equal(posts,1);assert.equal(result.results.length,2);assert.equal(result.uses_remaining,2-iteration);
   assert.ok(result.damage_total>=11&&result.damage_total<=110);
   const trollResult=result.results.find(r=>r.target_id===troll.id),immuneResult=result.results.find(r=>r.target_id===immune.id);
   assert.equal(trollResult.damage_rolled,result.damage_total);assert.equal(immuneResult.damage_dealt,0);
   const after=(await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp;assert.equal(after,before-trollResult.damage_dealt);
   const logEntry=page.locator('.workspace-timeline article').filter({hasText:`${dragon.name} usou Baforada`}).first();
   await logEntry.getByRole('button',{name:'Ver resultado',exact:true}).click();
   const detail=page.getByRole('dialog',{name:`Resultado: ${dragon.name} usou Baforada`,exact:true});
   await detail.waitFor();const detailText=await detail.innerText();
   assert.ok(detailText.includes('Dano rolado (11d10)')&&detailText.includes(troll.name)&&detailText.includes(immune.name));
   assert.ok(!detailText.includes('target_id')&&!detailText.includes('monster_runtime'));
   const resultShot=path.join(out,`monster-result-${width}.png`);await page.screenshot({path:resultShot});screenshots.push(resultShot);
   await detail.getByRole('button',{name:'Fechar descrição',exact:true}).click();
   assert.equal((await get('/workspace')).tokens.find(t=>t.id===outside.id).current_hp,1000);
   await post('/gm/combat/effects',body);assert.equal((await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp,after);
   await second.waitForFunction(({id,hp})=>document.querySelector(`[data-grid-token="${id}"]`)?.textContent?.includes(`${hp}/1000`),{id:troll.id,hp:after});
   await second.reload();await second.waitForFunction(({id,hp})=>document.querySelector(`[data-grid-token="${id}"]`)?.textContent?.includes(`${hp}/1000`),{id:troll.id,hp:after});
   await command('next_turn');assert.equal((await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp,after,'Fire wounds cannot regenerate');
   await call('PATCH','/gm/workspace/tokens/'+encodeURIComponent(troll.id),{current_hp:after-2});
   for(let n=0;n<4;n++)await command('next_turn');
   assert.equal((await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp,after-1,'Regenerate exactly one ordinary HP before its turn');
   for(let n=0;n<4;n++)await command('next_turn');
   assert.equal((await get('/workspace')).tokens.find(t=>t.id===troll.id).current_hp,after,'Ordinary wounds heal; fire damage remains before the next viewport case');
   checks.push(`Monster breath ${width}: real card/grid/one confirmation, cancellation, shared roll and per-target JP, immunity, cone exclusion, retry, second page/reload and regeneration`);
  }catch(error){
   if(inspectedPage){const shot=path.join(out,`monster-breath-failure-${width}.png`);await inspectedPage.screenshot({path:shot});console.error(JSON.stringify({screenshot:shot,alerts:await inspectedPage.getByRole('alert').allTextContents()}));}
   throw error;
  }finally{await context.close();await observer.close();}
 }
 await command('end');
};
