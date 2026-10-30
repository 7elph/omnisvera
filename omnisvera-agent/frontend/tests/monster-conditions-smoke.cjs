// Native disposable four-sheet fixture; attack d20 controlled, JP/duration real.
const assert=require('node:assert/strict'),path=require('node:path'),{randomUUID}=require('node:crypto');
module.exports=async function({browser,api,base,out,screenshots,checks}){
 assert.equal(base,'http://127.0.0.1:8871');
 const call=async(method,url,data)=>{const r=await api.fetch(url,{method,data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('GET',url),post=(url,data)=>call('POST',url,data);
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const health=await get('/health');assert.match(health.database_path,/Temp/i);
 const catalog=(await get('/gm/workspace/monster-catalog')).monsters;
 async function end(){if((await get('/combat/effects')).encounter?.active)await command('end');}
 async function rest(){await post('/characters/raziel/actions',{request_id:randomUUID(),action:'rest_at_inn',payload:{}});}
 await end();await rest();let ws=await get('/workspace');const mapId=ws.map.id;
 const raz=ws.tokens.find(t=>t.character_id==='raziel');assert.ok(raz);
 async function create(id){const source=catalog.find(m=>m.id===id);assert.ok(source);return post('/gm/workspace/tokens',{
  token_type:'monster',name:'Ensaio '+source.name,map_id:mapId,current_hp:100,maximum_hp:100,visible_to_players:true,
  sheet:{...source,attacks:source.attacks.map(a=>({...a,bonus:100})),source:{monster_id:id}}
 });}
 async function move(id,x,y){ws=await get('/workspace');const token=ws.tokens.find(t=>t.id===id);return post(`/workspace/maps/${encodeURIComponent(mapId)}/move`,{
  request_id:randomUUID(),token_id:id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:ws.map.grid.version});}
 async function start(monster){await end();await rest();await move(raz.id,30,30);await move(monster.id,31,30);await command('start',{
  map_id:mapId,battle_mode:true,participants:[{target_type:'token',target_id:monster.id,name:monster.name,initiative:40},{target_type:'character',target_id:'raziel',initiative:30}]
 });}
 const player=await browser.newContext({viewport:{width:390,height:900},isMobile:true,hasTouch:true});
 await player.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-raziel');localStorage.setItem('omnisvera_access_mode','player');localStorage.setItem('omnisvera_selected_character','raziel');});
 const own=await player.newPage();own.setDefaultTimeout(15000);
 try{
  for(const [id,width,condition,label] of [['ghoul',1440,'paralyzed','Paralisia'],['cocatriz',390,'petrified','Petrificação']]){
   const monster=await create(id),context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   let page,confirmed;
   try{
    await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','dorn7');});
    await context.route(/\/gm\/combat\/tokens\/[^/]+\/attacks\/resolve$/,route=>route.continue({postData:JSON.stringify({...route.request().postDataJSON(),roll_mode:'physical',d20:15})}));
    page=await context.newPage();page.setDefaultTimeout(20000);
    for(let attempt=0;attempt<12;attempt++){
     await start(monster);await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
     await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();await page.locator('button[data-character="dorn7"]').click();
     await page.locator('.workspace-combat-content > summary').first().waitFor();
     for(const summary of await page.locator('.workspace-combat-content > summary:visible').all())if(!await summary.evaluate(el=>el.parentElement.open))await summary.click();
     const panel=page.getByRole('region',{name:'Ataques de '+monster.name,exact:true});await panel.waitFor();
     const card=panel.locator('article').filter({has:page.locator('strong').filter({hasText:id==='ghoul'?/^Mordida$/:/^Bicada$/})});
     await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();await page.locator(`[data-grid-token="${raz.id}"]`).click();
     const response=page.waitForResponse(r=>r.request().method()==='POST'&&/\/combat\/attacks\/[^/]+\/confirm$/.test(new URL(r.url()).pathname));
     await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
     const r=await response;assert.equal(r.status(),200);confirmed=await r.json();
     assert.equal(confirmed.result,'hit');const riders=confirmed.breakdown.monster_rider_results;assert.equal(riders.length,1);
     if(!riders[0].resisted)break;
    }
    assert.equal(confirmed.breakdown.monster_rider_results[0].resisted,false,'Bounded real JP attempts must produce a failed save');
    const state=await get('/combat/effects'),effect=state.effects.find(e=>e.target_id==='raziel'&&e.monster_condition===condition);assert.ok(effect);
    assert.ok(state.encounter.participants.some(p=>p.target_id==='raziel'),'Incapacity must not retire a living participant');
    const again=await post('/combat/attacks/'+confirmed.resolution_id+'/confirm');assert.deepEqual(again,confirmed);
    assert.equal((await get('/combat/effects')).effects.filter(e=>e.id===effect.id).length,1);
    await own.goto(base);await own.locator('.app-shell.authenticated').waitFor();
    await own.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();await own.locator('button[data-character="raziel"]').click();
    const status=own.getByRole('region',{name:'Status',exact:true});await status.locator(`[title^="${label} ·"]`).waitFor();
    if(condition==='paralyzed')assert.ok(await status.locator('.active-effect-turns').count());
    const pub=await own.evaluate(async()=>{const r=await fetch('/combat/effects',{headers:{'X-Omnisvera-Token':'cf01-local-raziel'}});return r.json();});
    const publicEffect=pub.effects.find(e=>e.id===effect.id);assert.ok(publicEffect);assert.equal(publicEffect.source_token_id,undefined);assert.equal(publicEffect.rider_id,undefined);
    await command('next_turn');
    const blocked=await api.post('/characters/raziel/attacks/resolve',{data:{request_id:randomUUID(),attack_id:'melee',target_type:'token',target_id:monster.id,roll_mode:'physical',d20:15,range_cells:1}});
    assert.equal(blocked.status(),400);assert.match(await blocked.text(),new RegExp(label));
    await own.reload();await own.getByRole('region',{name:'Status',exact:true}).locator(`[title^="${label} ·"]`).waitFor();
    assert.ok(await own.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    const shot=path.join(out,`monster-${condition}-${width}.png`);await own.getByRole('region',{name:'Status',exact:true}).scrollIntoViewIfNeeded();await own.screenshot({path:shot});screenshots.push(shot);
    const entry=page.locator('.workspace-timeline article').filter({hasText:`${monster.name} atacou`}).first();await entry.getByRole('button',{name:'Ver resultado',exact:true}).click();
    const detail=page.getByRole('dialog').filter({hasText:'Resultado: '+monster.name+' atacou'});await detail.waitFor();
    const text=await detail.innerText();assert.ok(text.includes(label)&&text.includes('JP')&&!text.includes('source_token_id'));
    const detailShot=path.join(out,`monster-condition-result-${width}.png`);await page.screenshot({path:detailShot});screenshots.push(detailShot);
    await end();assert.ok((await get('/combat/effects')).effects.some(e=>e.id===effect.id),'Ending combat does not cure bodily conditions');await rest();
    assert.ok(!(await get('/combat/effects')).effects.some(e=>e.id===effect.id),'Explicit full rest clears conditions');
    checks.push(`${label}: native ${width}px card/grid/confirmation, automatic JP, retry, player status/reload, action block, privacy and rest`);
   }catch(error){if(page){const shot=path.join(out,`monster-condition-failure-${width}.png`);await page.screenshot({path:shot});console.error(JSON.stringify({screenshot:shot,alerts:await page.getByRole('alert').allTextContents()}));}throw error;}
   finally{await context.close();}
  }
  const cobra=await create('cobra-venenosa');let poison;
  for(let attempt=0;attempt<12;attempt++){
   await start(cobra);const record=await post(`/gm/combat/tokens/${cobra.id}/attacks/resolve`,{request_id:randomUUID(),attack_id:'0',target_type:'character',target_id:'raziel',roll_mode:'physical',d20:15,range_cells:1});
   await post('/combat/attacks/'+record.resolution_id+'/confirm');poison=(await get('/combat/effects')).effects.find(e=>e.monster_condition==='poison_death'&&e.target_id==='raziel');if(poison)break;
  }
  assert.ok(poison);await end();const before=(await get('/characters/raziel')).state.current_hp;
  await command('dorn_spell_time',{seconds:poison.remaining_seconds-1});assert.equal((await get('/characters/raziel')).state.current_hp,before);
  const tick={request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action:'dorn_spell_time',payload:{seconds:1}};
  await post('/gm/combat/effects',tick);assert.equal((await get('/characters/raziel')).state.current_hp,0);await post('/gm/combat/effects',tick);assert.equal((await get('/characters/raziel')).state.current_hp,0);
  checks.push('Poison: actual exploration-duration roll, no early death, native clock expiry and idempotent retry');await rest();
 }finally{await end();await player.close();}
};
