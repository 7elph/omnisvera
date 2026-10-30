// Built client/native commands only, using the existing runner's TEMP fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const owner=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
 const call=async(method,url,data,client=api)=>{const r=await client[method](url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data);
 const act=(action,payload={})=>post('/characters/raziel/actions',{action,payload,request_id:randomUUID(),reason:'Somente fixture vampírica'});
 const command=async(action,payload={})=>post('/gm/combat/effects',{action,payload,request_id:randomUUID(),expected_version:(await get('/combat/effects')).version});
 const health=await get('/health');assert.equal(path.resolve(health.database_path),path.join(path.dirname(file),'simulation.sqlite3'));
 const batch=process.env.OMNISVERA_QA_VAMPIRIC_BATCH||'first';assert.ok(['first','second'].includes(batch));
 const cases=batch==='first'?[['regen',1440,'gm'],['bite',390,'raziel']]:[['coffin',390,'raziel'],['night',1440,'gm']];
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],action_coverage=[],observed=[],out=fs.mkdtempSync(path.join(os.tmpdir(),'raziel-vampiric-ui-'));
 const blood=s=>s.state.resources.find(r=>r.key==='reserva_de_sangue').current;
 const uses=(s,key)=>s.state.resources.find(r=>r.key===key).current;
 try{for(const [kind,width,role] of cases){
  console.log('RUN vampiric '+kind);
  if((await get('/combat/effects')).encounter?.active)await command('end');
  await act('rest_at_inn');await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
  const workspace=await get('/workspace'),grid=workspace.map.grid,mine=workspace.tokens.find(t=>t.character_id==='raziel'),enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
  assert.ok(grid&&mine?.grid_position&&enemy?.grid_position);
  for(const token of workspace.tokens)if(token.id!==mine.id&&token.id!==enemy.id&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});
  await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{visible_to_players:true,current_hp:500,maximum_hp:500,sheet:{...enemy.sheet,armor_class:1,has_blood:true}});
  for(const [token,x]of [[mine,4],[enemy,5]])await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,5]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});
  if(kind==='regen'||kind==='bite'){
   await act('damage',{amount:5});
   await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1}]});
  }
  if(kind==='coffin'){
   await act('damage',{amount:5});await act('add_condition',{condition:'Condição apenas de ensaio'});
   await act('consume_resource',{resource_key:'reserva_de_sangue',amount:2});
  }
  const before=await get('/characters/raziel'),context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','raziel');},{role});
  const page=await context.newPage(),sent=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST'&&/\/characters\/raziel\/(techniques\/|actions$)/.test(new URL(r.url()).pathname))sent.push({url:new URL(r.url()).pathname,body:r.postDataJSON()});});
  const open=async()=>{
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   await page.locator('button[data-character="raziel"]').click();
   const group=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Habilidades$/})});
   if(!await group.evaluate(el=>el.open))await group.locator(':scope > summary').click();return group;
  };
  const section=await open(),card=name=>section.locator('article').filter({has:page.getByRole('button',{name,exact:true})});
  const useCard=async name=>{await page.waitForFunction(el=>el&&!el.disabled,await card(name).locator('button[data-card-command]').elementHandle());await card(name).click({position:{x:8,y:8}});};
  const response=predicate=>{const p=page.waitForResponse(r=>r.request().method()==='POST'&&predicate(new URL(r.url()).pathname,r.request().postDataJSON()));void p.catch(()=>{});return p;};
  let key;
  if(kind==='regen'){
   const pending=response(url=>url.endsWith('/techniques/regeneracao-vampirica'));
   await useCard('Regeneração Vampírica');const reply=await pending;assert.ok(reply.ok(),await reply.text());const result=await reply.json(),after=await get('/characters/raziel');
   assert.equal(blood(after),blood(before)-1);assert.ok(result.heal_roll>=1&&result.heal_roll<=4);
   assert.equal(after.state.current_hp,Math.min(before.state.maximum_hp,before.state.current_hp+result.heal_roll));
   assert.ok((await get('/combat/effects')).encounter.action_committed);
   const request=sent.find(r=>r.url.endsWith('/techniques/regeneracao-vampirica'));
   assert.deepEqual(await call('post',request.url,request.body,role==='gm'?api:owner),result);assert.equal(blood(await get('/characters/raziel')),blood(after));
   key='regeneracao-vampirica';observed.push({kind,heal_roll:result.heal_roll});
  }else if(kind==='bite'){
   const preview=response(url=>url.endsWith('/techniques/mordida')),confirmed=response(url=>/^\/combat\/attacks\/[^/]+\/confirm$/.test(url));
   await useCard('Mordida');await page.locator('.targeting-overlay').waitFor();await page.locator(`[data-grid-token="${enemy.id}"]`).click();
   await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
   const attack=await preview;assert.ok(attack.ok(),await attack.text());const reply=await confirmed;assert.ok(reply.ok(),await reply.text());const result=await reply.json();
   assert.equal(before.definition.level,5);assert.equal(result.damage_formula,'1d6');
   const after=await get('/characters/raziel'),victim=(await get('/workspace')).tokens.find(t=>t.id===enemy.id);
   assert.equal(victim.current_hp,result.hp_after);assert.equal(result.hp_before-result.hp_after,result.breakdown.drain_result.drained);
   assert.equal(after.state.current_hp,Math.min(before.state.maximum_hp,before.state.current_hp+result.breakdown.drain_result.drained));
   assert.equal(blood(after),blood(before));assert.ok(result.confirmed);
   key='mordida';observed.push({kind,result:result.result,damage:result.damage_total});
  }else if(kind==='coffin'){
   const pending=response((url,body)=>url==='/characters/raziel/actions'&&body.action==='rest_in_coffin');
   await useCard('Caixão');const reply=await pending;assert.ok(reply.ok(),await reply.text());let after=await get('/characters/raziel');
   assert.equal(after.state.current_hp,after.state.maximum_hp);assert.deepEqual(after.state.conditions,[]);assert.equal(uses(after,'caixao'),0);
   assert.equal(blood(after),after.state.resources.find(r=>r.key==='reserva_de_sangue').maximum);
   const request=sent.find(r=>r.body.action==='rest_in_coffin');await call('post',request.url,request.body,owner);
   assert.equal(uses(await get('/characters/raziel'),'caixao'),0);
   const denied=await owner.post(request.url,{data:{...request.body,request_id:randomUUID()}});assert.equal(denied.status(),400);
   await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal(uses(await get('/characters/raziel'),'caixao'),0);
   await act('rest_at_inn');assert.equal(uses(await get('/characters/raziel'),'caixao'),1);key='caixao';
  }else{
   const selector=page.getByLabel('Animal da Forma da Noite',{exact:true});assert.equal(await selector.locator('img').count(),0);
   await selector.click();const chooser=page.getByRole('group',{name:'Escolher animal da Forma da Noite'});await chooser.waitFor();
   await chooser.locator('img').evaluateAll(images=>Promise.all(images.map(img=>img.decode())));
   assert.ok(await chooser.getByRole('button').evaluateAll(buttons=>buttons.every(button=>button.scrollWidth<=button.clientWidth+1)),'Animal pictures and full names must fit the compact card');
   await chooser.screenshot({path:path.join(out,'night-selector-'+width+'.png')});
   await chooser.getByRole('button',{name:'Coruja',exact:true}).click();assert.equal(await chooser.isVisible(),false);
   const pending=response((url,body)=>url==='/characters/raziel/actions'&&body.action==='consume_resource');
   await page.getByRole('switch',{name:'Forma da Noite',exact:true}).click();const reply=await pending;assert.ok(reply.ok(),await reply.text());let after=await get('/characters/raziel');
   assert.equal(after.state.animal_form,'coruja');assert.equal(after.state.current_hp,1);assert.equal(after.definition.defenses.armor_class,14);assert.equal(after.definition.defenses.saving_throw,4);
   assert.equal(uses(after,'forma_da_noite'),uses(before,'forma_da_noite')-1);
   await page.getByRole('switch',{name:'Forma da Noite',exact:true,checked:true}).waitFor();
   await page.screenshot({path:path.join(out,'night-active-'+width+'.png')});
   const denied=await owner.post('/characters/raziel/techniques/regeneracao-vampirica',{data:{request_id:randomUUID()}});assert.equal(denied.status(),400);
   await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal((await get('/characters/raziel')).state.animal_form,'coruja');
   const normal=after.state.normal_current_hp;assert.equal(typeof normal,'number');
   await act('damage',{amount:5});after=await get('/characters/raziel');assert.ok(!after.state.animal_form);assert.equal(after.state.current_hp,Math.max(0,normal-4));
   assert.equal(uses(after,'forma_da_noite'),uses(before,'forma_da_noite')-1);key='forma-da-noite';
  }
  const matching=sent.filter(r=>kind==='regen'?r.url.endsWith('/techniques/regeneracao-vampirica'):kind==='bite'?r.url.endsWith('/techniques/mordida'):r.body.action===(kind==='coffin'?'rest_in_coffin':'consume_resource'));
  assert.equal(matching.length,1,'One UI use sends one command');
  const persisted=await get('/characters/raziel');await open();assert.deepEqual((await get('/characters/raziel')).state,persisted.state);
  await card({regen:'Regeneração Vampírica',bite:'Mordida',coffin:'Caixão',night:'Forma da Noite'}[kind]).scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,kind+'-'+width+'.png')});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');
  action_coverage.push({actor:'raziel',key:'ability:'+key,verified_checks:['ui']});await context.close();
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',batch,action_coverage,observed,screenshots:out}));
 }finally{await browser.close();await api.dispose();await owner.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1});
