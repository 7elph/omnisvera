// Fixed encounter acceptance, called only by the native TEMP preparation smoke.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{randomUUID}=require('node:crypto');
const ARENA='map:83ccd7972a084a30',PARTY=['vezemir','raziel','morthak','dorn7'];
const ENEMIES=['monster:fb4139d296724b7584a8027b69789019','monster:d13d377b55f945ed819a279ccc8b4930','monster:22fc72b962b64769b157c67e153feb59','monster:e5be7ae3bd7147f3b37e660669cdd6cb'];
function pathToward(start,destination,budget){
 const result=[start.slice()];let [x,y]=start;
 for(let i=0;i<budget&&Math.max(Math.abs(x-destination[0]),Math.abs(y-destination[1]))>1;i++){
  x+=Math.sign(destination[0]-x);y+=Math.sign(destination[1]-y);result.push([x,y]);
 }
 return result;
}
async function runTodayEncounter({api,browser,base,output}){
 assert.equal(base,'http://127.0.0.1:8871');
 const call=async(method,url,data,client=api)=>{const r=await client.fetch(new URL(url,base).href,{method,data});assert.ok(r.ok(),`${url}: ${r.status()} ${await r.text()}`);return r.json();};
 const get=(url,client)=>call('GET',url,undefined,client),post=(url,data,client)=>call('POST',url,data,client);
 const health=await get('/health');for(const p of [health.database_path,health.vault_path])assert.ok(path.resolve(p).startsWith(path.resolve(os.tmpdir())+path.sep));
 const command=async(action,payload={})=>post(action==='next_turn'?'/combat/next-turn':'/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 if((await get('/combat/effects')).encounter?.active)await command('end');
 for(const actor of PARTY)await post(`/characters/${actor}/actions`,{request_id:randomUUID(),action:'rest_at_inn',payload:{},reason:'Somente fixture: ensaio do encontro preparado'});
 await call('PATCH','/gm/workspace/table-mode',{table_mode:'digital'});
 await call('PATCH','/gm/workspace/maps/active',{map_id:ARENA});
 const initial=await get('/workspace'),grid=initial.map.grid;
 assert.ok(grid&&grid.cell_size_m===1.5);
 const prepared=initial.tokens.filter(t=>ENEMIES.includes(t.id));assert.equal(prepared.length,4);
 assert.ok(prepared.every(t=>t.name.startsWith('PREP')&&t.sheet.attacks.length>0&&[7,14].includes(t.maximum_hp)));
 // The earlier generic API case changes the disposable arena. Restore its
 // production preparation coordinates, never the production database itself.
 const starts={vezemir:[14,22],raziel:[15,22],morthak:[16,22],dorn7:[17,22],
  [ENEMIES[0]]:[12,8],[ENEMIES[1]]:[19,8],[ENEMIES[2]]:[12,13],[ENEMIES[3]]:[22,13]};
 for(const t of initial.tokens){
  const key=t.character_id||t.id,keep=PARTY.includes(key)||ENEMIES.includes(key);
  await call('PATCH',`/gm/workspace/tokens/${encodeURIComponent(t.id)}`,{visible_to_players:keep,...(ENEMIES.includes(t.id)?{current_hp:t.maximum_hp}:{})});
  if(keep){const p=t.grid_position;assert.ok(p);await post(`/workspace/maps/${ARENA}/move`,{request_id:randomUUID(),token_id:t.id,mode:'GM_REPOSITION',path:[[p.cell_x,p.cell_y],starts[key]],expected_position_version:p.version,expected_grid_version:grid.version});}
 }
 // Real profiles, HP, armour and damage. Initiative is declared for this
 // rehearsal, not a random initiative or a canonical outcome for the session.
 await command('start',{title:'QA TEMP · carga da Âncora',map_id:ARENA,battle_mode:true,participants:[
  ...ENEMIES.map((id,i)=>({target_type:'token',target_id:id,initiative:30-i})),
  ...PARTY.map((id,i)=>({target_type:'character',target_id:id,initiative:20-i}))]});
 const clients=[],errors=[],screenshots=[],actions=[],moves=[],frames={};
 try{
  for(const [actor,width] of [['dorn7',1440],['vezemir',390],['raziel',390],['morthak',390]]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390,
    extraHTTPHeaders:{'X-Omnisvera-Token':actor==='dorn7'?'cf01-local-gm':'cf01-local-'+actor}});
   await context.addInitScript(({actor})=>{localStorage.setItem('omnisvera_access_token',actor==='dorn7'?'cf01-local-gm':'cf01-local-'+actor);localStorage.setItem('omnisvera_access_mode',actor==='dorn7'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{actor});
   const page=await context.newPage();page.setDefaultTimeout(15000);frames[actor]=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('websocket',socket=>socket.on('framereceived',({payload})=>{try{const msg=JSON.parse(String(payload));if(['connected','session_changed'].includes(msg.type))frames[actor].push(msg.type);}catch{}}));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:actor==='dorn7'?/Mesa$/:/Ficha$/}).click();
   await page.locator(`button[data-character="${actor}"]`).click();await page.locator('.workspace-combat-live').waitFor();
   const shot=path.join(output,`encounter-start-${actor}-${width}.png`);await page.screenshot({path:shot,fullPage:true});screenshots.push(shot);
   clients.push({actor,context,page});
  }
  const hpBefore={};for(const actor of PARTY)hpBefore[actor]=(await get('/characters/'+actor)).state.current_hp;
  for(let turn=0;turn<56;turn++){
   const state=await get('/combat/effects'),e=state.encounter,ws=await get('/workspace');
   const liveEnemies=ws.tokens.filter(t=>ENEMIES.includes(t.id)&&t.current_hp>0);
   if(!liveEnemies.length)break;
   const current=e.participants[e.turn_index],enemy=current.target_type==='token';
   const actor=enemy?ws.tokens.find(t=>t.id===current.target_id):ws.tokens.find(t=>t.character_id===current.target_id);
   assert.ok(actor&&(!enemy||ENEMIES.includes(actor.id)),'Only today participants may take a turn');
   let targets=enemy?ws.tokens.filter(t=>PARTY.includes(t.character_id)):liveEnemies;
   const sheets={};if(enemy)for(const t of targets)sheets[t.character_id]=await get('/characters/'+t.character_id);
   targets=targets.filter(t=>!enemy||sheets[t.character_id].state.current_hp>0);assert.ok(targets.length,'Party defeated; report instead of declaring ready');
   const p=actor.grid_position,distance=t=>Math.max(Math.abs(p.cell_x-t.grid_position.cell_x),Math.abs(p.cell_y-t.grid_position.cell_y));
   targets.sort((a,b)=>distance(a)-distance(b));let target=targets[0];
   const actorSheet=enemy?null:await get('/characters/'+current.target_id);
   const movement=enemy?parseFloat(actor.sheet.movement||6):parseFloat(actorSheet.definition.movement||9);
   assert.ok(Number.isFinite(movement)&&movement>0,'Movement must come from a valid sheet value');
   const route=pathToward([p.cell_x,p.cell_y],[target.grid_position.cell_x,target.grid_position.cell_y],Math.floor(movement/grid.cell_size_m));
   if(route.length>1){
    await post(`/workspace/maps/${ARENA}/move`,{request_id:randomUUID(),token_id:actor.id,mode:'COMBAT_MOVE',path:route,expected_position_version:p.version,expected_grid_version:grid.version,expected_combat_version:state.version});
    moves.push({actor:current.target_id,cells:route.length-1});
   }
   const end=route.at(-1),q=target.grid_position;
   if(Math.max(Math.abs(end[0]-q.cell_x),Math.abs(end[1]-q.cell_y))<=1){
    const actorClient=enemy||current.target_id==='dorn7'?api:clients.find(c=>c.actor===current.target_id).context.request;
    const attack=enemy?{id:'0',attack_count:1}:actorSheet.definition.attacks.find(a=>a.id==='melee'&&a.damage&&a.weapon_item_path);
    assert.ok(attack,`${current.target_id}: basic melee attack unavailable`);
    const body={request_id:randomUUID(),attack_id:attack.id,target_type:enemy?'character':'token',target_id:enemy?target.character_id:target.id,roll_mode:'digital',attack_count:attack.attack_count||1,...(enemy?{range_cells:1}:{})};
    const url=enemy?`/gm/combat/tokens/${encodeURIComponent(actor.id)}/attacks/resolve`:`/characters/${current.target_id}/attacks/resolve`;
    const preview=await post(url,body,actorClient),confirm='/combat/attacks/'+preview.resolution_id+'/confirm';
    const result=await post(confirm,{},actorClient),retry=await post(confirm,{},actorClient);assert.deepEqual(retry,result,'Confirmation retry must not apply twice');
    assert.equal(result.hp_after,Math.max(0,result.hp_before-result.damage_total));
    actions.push({round:state.round,actor:current.target_id,target:body.target_id,d20:result.d20,damage:result.damage_total,hp_before:result.hp_before,hp_after:result.hp_after,result:result.result});
   }
   await command('next_turn');
  }
  const final=await get('/workspace');assert.ok(final.tokens.filter(t=>ENEMIES.includes(t.id)).every(t=>t.current_hp===0),'Fight did not finish within eight rounds');
  for(const actor of PARTY)assert.ok(actions.some(a=>a.actor===actor),actor+' did not execute an attack');
  assert.ok(actions.some(a=>ENEMIES.includes(a.actor)),'No prepared enemy attack executed');
  const version=(await get('/combat/effects')).version;
  for(const c of clients){
   await c.page.waitForFunction(v=>Number(document.querySelector('.workspace-combat-live')?.getAttribute('data-combat-version'))>=v,version,{timeout:20000});
   assert.ok(frames[c.actor].includes('session_changed'),c.actor+' received no realtime invalidation');
   await c.page.reload();await c.page.locator('.app-shell.authenticated').waitFor();
   const sheet=await get('/characters/'+c.actor,c.context.request);assert.ok(sheet.state.current_hp>0);
   const shot=path.join(output,`encounter-reload-${c.actor}.png`);await c.page.screenshot({path:shot,fullPage:true});screenshots.push(shot);
  }
  assert.deepEqual(errors,[]);
  const hpAfter={};for(const actor of PARTY)hpAfter[actor]=(await get('/characters/'+actor)).state.current_hp;
  await command('end');
  return {status:'PASS',mode:'digital',actors:PARTY,enemy_ids:ENEMIES,actions,moves,hp_before:hpBefore,hp_after:hpAfter,
   rounds:Math.max(...actions.map(a=>a.round)),screenshots,realtime_clients:clients.map(c=>({actor:c.actor,events:frames[c.actor].length,rendered_version:version,reload:true})),
   limits:'Four browser contexts on one host; API attacks, not card clicks. Fixed initiative, one digital run, not a balance certification. Physical phones and different networks not tested.',production_modified:false};
 }finally{for(const c of clients)await c.context.close();}
}
module.exports={pathToward,runTodayEncounter};
