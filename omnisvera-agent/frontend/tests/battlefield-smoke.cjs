// Native buttons, fixed local credentials and disposable fixture only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base='http://127.0.0.1:8875',output=fs.mkdtempSync(path.join(os.tmpdir(),'battlefield-ui-evidence-'));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}}),browser=await chromium.launch({channel:'msedge',headless:true}),errors=[];
 const get=async(route)=>{const r=await api.get(route);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(route,data)=>{const r=await api.post(route,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const command=async(action,payload={})=>post('/gm/combat/effects',{action,payload,request_id:randomUUID(),expected_version:(await get('/combat/effects')).version});
 const open=async(role,actor,width=1440)=>{
  const context=await browser.newContext({viewport:{width,height:1000}});await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');},{role});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.route('**/media/**',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960"><rect width="1280" height="960" fill="#202530"/></svg>'}));
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator(`button[data-character="${actor}"]`).click();await page.locator('.workspace-character-identity').waitFor();return page;
 };
 try{
  if((await get('/combat/effects')).encounter?.active)await command('end');
  assert.ok((await api.patch('/gm/workspace/table-mode',{data:{table_mode:'physical'}})).ok());
  for(const actor of ['vezemir','morthak','dorn7'])await post('/characters/'+actor+'/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID()});
  const w=await get('/workspace'),mapId=w.map.id;assert.ok(w.map.grid);
  const foe=await post('/gm/workspace/tokens',{token_type:'monster',name:'Cadáver de ensaio',image_path:'zz_media/fixture-original.jpg',map_id:mapId,latitude:50,longitude:50,visible_to_players:true,current_hp:1,maximum_hp:1,sheet:{armor_class:1,saving_throw:99}});
  const holder=(await get('/characters/vezemir')).inventory.find(i=>i.item_title==='Pulseira de Vinhas');assert.ok(holder);
  if(!holder.equipped)await post('/characters/vezemir/actions',{action:'equip_item',payload:{item_path:holder.item_path,equipment_slot:'Acessório'},request_id:randomUUID()});
  const pins=await get('/workspace');const max=pins.map.grid;
  const coords=[[Math.min(4,max.cols-3),Math.min(4,max.rows-3)],[Math.min(5,max.cols-2),Math.min(5,max.rows-2)]];
  for(const [id,xy] of [['vezemir',coords[0]],['morthak',coords[1]],[foe.id,[coords[0][0]+1,coords[0][1]]]]){
   let token=pins.tokens.find(t=>t.character_id===id||t.id===id);
   if(!token)token=await post('/gm/workspace/tokens',{token_type:'character',character_id:id,name:id,map_id:mapId,latitude:50,longitude:50,visible_to_players:true});
   const snapshot=await get('/workspace'),current=snapshot.tokens.find(t=>t.id===token.id);
   await post('/workspace/maps/'+mapId+'/move',{token_id:current.id,mode:'GM_REPOSITION',path:[[current.grid_position.cell_x,current.grid_position.cell_y],xy],expected_position_version:current.grid_position.version,expected_grid_version:snapshot.map.grid.version,request_id:randomUUID()});
  }
  await command('start',{map_id:mapId,battle_mode:true,participants:[{target_type:'character',target_id:'vezemir',name:'Vezemir',initiative:20},{target_type:'character',target_id:'morthak',name:'Morthak',initiative:15},{target_type:'token',target_id:foe.id,name:foe.name,initiative:1}]});
  const owner=await open('vezemir','vezemir',390);
  for(const name of ['Visão no escuro','Detecção de portas escondidas','Descanso élfico'])assert.ok(await owner.getByRole('button',{name,exact:true}).count());
  const bracelet=owner.locator('article').filter({has:owner.getByLabel('Alvo da Pulseira de Vinhas',{exact:true})});await bracelet.getByLabel('Alvo da Pulseira de Vinhas',{exact:true}).selectOption(foe.id);await bracelet.getByRole('button',{name:'Usar',exact:true}).click();
  await owner.waitForFunction(()=>document.querySelector('.workspace-resource-catalog')?.textContent.includes('1/2'));
  const budget=(await get('/combat/effects')).encounter;assert.ok(budget.consumable_used);assert.ok(!budget.action_committed);
  await owner.screenshot({path:path.join(output,'vines-mobile.png')});
  const attack=await post('/characters/vezemir/attacks/resolve',{request_id:randomUUID(),attack_id:'melee',target_type:'token',target_id:foe.id,roll_mode:'physical',d20:20});
  assert.equal(attack.breakdown.attack.tactical_bonus,2);await post('/combat/attacks/'+attack.resolution_id+'/confirm',{});
  const dead=(await get('/workspace')).tokens.find(t=>t.id===foe.id);assert.ok(dead.sheet.corpse&&dead.sheet.reanimation_allowed);assert.ok(!(await get('/combat/effects')).encounter.participants.some(p=>p.target_id===foe.id));
  await command('next_turn');const necro=await open('morthak','morthak');
  const body=necro.locator(`[data-grid-token="${foe.id}"]`);await body.waitFor();assert.equal(await body.locator('img').count(),0);assert.ok((await body.innerText()).includes('Cadáver'));
  assert.ok(await necro.locator('.workspace-pin-diagonal-bonus').count());await necro.screenshot({path:path.join(output,'corpse-and-diagonal.png')});
  const reanimate=necro.locator('article').filter({has:necro.getByLabel('Alvo de Animar Mortos',{exact:true})});await reanimate.getByLabel('Alvo de Animar Mortos',{exact:true}).selectOption(foe.id);await reanimate.getByRole('button',{name:'Usar',exact:true}).click();
  await body.waitFor({state:'detached'});
  const raised=(await get('/workspace')).tokens.find(t=>t.sheet.summon?.corpse_id===foe.id);assert.ok(raised&&raised.id!==foe.id&&raised.current_hp>0);
  await necro.reload();await necro.locator(`[data-grid-token="${raised.id}"]`).waitFor();assert.equal(await necro.locator(`[data-grid-token="${foe.id}"]`).count(),0);
  await command('end');assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',vines_then_attack:true,corpse_icon:true,new_reanimated_pin:true,diagonal_two:true,racial_passives:true,reload:true,mobile:true,screenshots:output}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
