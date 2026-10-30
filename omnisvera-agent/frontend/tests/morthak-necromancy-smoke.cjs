// Current built cards and native commands, existing verified TEMP runner only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}}),owner=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-morthak'}});
 const call=async(method,url,data,client=api)=>{const reply=await client[method](url,{data});assert.ok(reply.ok(),await reply.text());return reply.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data);
 const health=await get('/health');assert.equal(path.resolve(health.database_path),path.join(path.dirname(file),'simulation.sqlite3'));
 const act=(action,payload={})=>post('/characters/morthak/actions',{request_id:randomUUID(),action,payload,reason:'Somente fixture de necromancia'});
 const command=async(action,payload={},request_id=randomUUID())=>post('/gm/combat/effects',{request_id,action,payload,expected_version:(await get('/combat/effects')).version});
 const batch=process.env.OMNISVERA_QA_NECROMANCY_BATCH||'first';assert.ok(['first','summons','high'].includes(batch));
 const cases=batch==='first'?[['touch',390,'morthak'],['fear',1440,'gm']]:batch==='summons'?[['summons',390,'morthak']]:[['clones',1440,'gm'],['death',390,'morthak']];
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],action_coverage=[],observed=[],out=fs.mkdtempSync(path.join(os.tmpdir(),'morthak-necromancy-ui-'));
 console.log('EVIDENCE necromancy '+out);
 const resource=(sheet,key)=>sheet.state.resources.find(r=>r.key===key).current;
 const aliveSummons=workspace=>workspace.tokens.filter(t=>t.current_hp>0&&t.sheet?.summon?.caster==='morthak');
 try{for(const [kind,width,role]of cases){
  console.log('RUN necromancy '+kind);
  if((await get('/combat/effects')).encounter?.active)await command('end');
  await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
  for(const token of aliveSummons(await get('/workspace')))if(token.sheet.summon.technique!=='clonagem')await post('/characters/morthak/techniques/dispensar-invocacao',{request_id:randomUUID(),target_type:'token',target_id:token.id});
  await act('rest_at_inn');
  let workspace=await get('/workspace'),grid=workspace.map.grid,mine=workspace.tokens.find(t=>t.character_id==='morthak'),enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
  assert.ok(grid&&mine?.grid_position&&enemy?.grid_position);
  for(const token of workspace.tokens)if(token.id!==mine.id&&token.id!==enemy.id&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});
  await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{visible_to_players:true,current_hp:500,maximum_hp:500,sheet:{...enemy.sheet,armor_class:1,hit_dice:'1',has_blood:true,is_undead:false,is_construct:false,attributes:{strength:10,dexterity:10,constitution:10,wisdom:10}}});
  const position=async(token,x,y=5)=>post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,y]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});
  await position(mine,4);await position(enemy,5);
  let seededFragment=false;
  if(kind==='clones'&&!(await get('/characters/morthak')).inventory.some(i=>i.item_title==='Fragmento de Cristal Arcano'&&i.quantity>0)){
   const fragment=(await get('/gm/workspace/items')).find(i=>i.name==='Fragmento de Cristal Arcano');assert.ok(fragment,'Persisted component catalog required, never invent an item');
   await post('/gm/workspace/items/grant',{character_id:'morthak',item_id:fragment.id,quantity:1,notes:'Somente fixture: 1 componente consumível para Clonagem'});seededFragment=true;
  }
  let preparedCorpse;
  if(kind==='summons'){
   const corpse=await post('/gm/workspace/tokens',{token_type:'monster',name:'Cadáver exclusivo do ensaio '+randomUUID(),map_id:evidence.map_id,visible_to_players:true,latitude:50,longitude:50,current_hp:0,maximum_hp:12,sheet:{armor_class:10,hit_dice:'1',reanimation_allowed:true}});
   const placed=(await get('/workspace')).tokens.find(t=>t.id===corpse.id);assert.ok(placed.sheet.corpse);assert.equal(placed.sheet.marker,'☠');await position(placed,4,6);preparedCorpse=placed;
  }
  await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'morthak',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1}]});
  const before=await get('/characters/morthak'),context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','morthak');},{role});
  const page=await context.newPage(),sent=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname.startsWith('/characters/morthak/techniques/'))sent.push({url:new URL(r.url()).pathname,body:r.postDataJSON()});});
  const open=async(reload=false)=>{
   if(reload)await page.reload();else await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator('button[data-character="morthak"]').click();
   const section=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Magias$/})});if(!await section.evaluate(el=>el.open))await section.locator(':scope > summary').click();return section;
  };
  const section=await open(),name=id=>before.definition.session_abilities.find(a=>a.id===id).name;
  const card=id=>section.locator('article.workspace-spell-card').filter({has:page.getByRole('button',{name:name(id),exact:true})});
  const click=async id=>{await card(id).locator('button[data-card-command]:enabled').waitFor({state:'attached'});await card(id).click({position:{x:8,y:8}});};
  const response=predicate=>{const p=page.waitForResponse(r=>r.request().method()==='POST'&&predicate(new URL(r.url()).pathname,r.request().postDataJSON()));void p.catch(()=>{});return p;};
  const closeToken=async()=>{const dialog=page.getByRole('dialog',{name:/^Ficha de /});await dialog.waitFor();await dialog.screenshot({path:path.join(out,kind+'-controlled-unit-'+width+'.png')});await dialog.getByRole('button',{name:'Fechar ficha',exact:true}).click();};
  const target=async(id,tokenId,yes=true)=>{await click(id);await page.locator('.targeting-overlay').waitFor();await page.locator(`[data-grid-token="${tokenId}"]`).click();await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:yes?'Sim':'Não',exact:true}).click();};
  const area=async(id,yes=true)=>{await click(id);const dialog=page.getByRole('dialog',{name:'Confirmar alvo'});await dialog.waitFor();if(id==='magia-da-morte')assert.match(await dialog.innerText(),/inclusive aliados/);if(yes)await page.screenshot({path:path.join(out,kind+'-confirmation-'+width+'.png')});await dialog.getByRole('button',{name:yes?'Sim':'Não',exact:true}).click();};
  const cast=async(id,action)=>{const pending=response(url=>url.endsWith('/techniques/'+id));await action();const reply=await pending;assert.ok(reply.ok(),await reply.text());return reply.json();};
  const replay=async id=>{const request=sent.find(r=>r.url.endsWith('/techniques/'+id));return call('post',request.url,request.body,role==='gm'?api:owner);};
  const ownTurn=async()=>{for(let i=0;i<12;i++){const e=(await get('/combat/effects')).encounter,p=e.participants[e.turn_index];if(p.target_id==='morthak')return;await command('next_turn');}assert.fail('Morthak did not regain the native turn');};
  const cover=id=>action_coverage.push({actor:'morthak',key:'ability:'+id,verified_checks:['ui']});
  if(kind==='touch'){
   await target('toque-sombrio',enemy.id,false);assert.equal(resource(await get('/characters/morthak'),'toque_sombrio'),resource(before,'toque_sombrio'));assert.equal(sent.length,0);
   const result=await cast('toque-sombrio',()=>target('toque-sombrio',enemy.id));
   assert.deepEqual(await replay('toque-sombrio'),result);
   assert.equal(result.damage_formula,'1d4');assert.equal(resource(await get('/characters/morthak'),'toque_sombrio'),resource(before,'toque_sombrio')-1);
   assert.equal(sent.filter(r=>r.url.endsWith('/techniques/toque-sombrio')).length,1);assert.ok(result.confirmed);
   if(result.result==='hit'){
    assert.ok((await get('/combat/effects')).effects.some(e=>e.target_id===enemy.id&&e.dot_hp));
    const first=await command('next_turn',{},'touch-tick-'+randomUUID());assert.ok(first.encounter.active);
    const log=await get('/workspace/ledger');assert.ok(log.some(e=>e.source_type==='touch_dot'),'Target turn produces the existing DOT ledger roll');
   }
   observed.push({kind,result:result.result,damage:result.damage_total});cover('toque-sombrio');
  }else if(kind==='fear'){
   const ring=await get('/gm/grid/range?'+new URLSearchParams({ref:'technique:morthak:aterrorizar',map_id:evidence.map_id,attacker_character_id:'morthak'}));assert.equal(ring.range_m,9+3*before.definition.level);
   const result=await cast('aterrorizar',()=>area('aterrorizar'));assert.deepEqual(await replay('aterrorizar'),result);
   const protocol=result.protocol_result;assert.ok(protocol.duration_turns>=6&&protocol.duration_turns<=11);
   assert.equal(resource(await get('/characters/morthak'),'aterrorrizar'),resource(before,'aterrorrizar')-1);
   const applied=protocol.results.filter(r=>r.effect);observed.push({kind,affected:applied.length,duration:protocol.duration_turns});
   if(applied.length){for(let i=0;i<2*protocol.duration_turns;i++)await command('next_turn');assert.ok(!(await get('/combat/effects')).effects.some(e=>e.target_id===enemy.id&&e.necro_spell==='aterrorrizar'));}
   cover('aterrorizar');
  }else if(kind==='summons'){
   const id='levantar-um-esqueleto',first=await cast(id,()=>click(id));await closeToken();const skeleton=first.token;
   assert.ok((await get('/workspace')).tokens.find(t=>t.id===skeleton.id).grid_position);assert.equal(resource(await get('/characters/morthak'),'levantar_um_esqueleto'),resource(before,'levantar_um_esqueleto')-1);
   assert.deepEqual(await replay(id),first);
   const reused=await cast(id,()=>click(id));await closeToken();assert.equal(reused.token.id,skeleton.id);assert.equal(reused.existing,true);
   assert.equal(resource(await get('/characters/morthak'),'levantar_um_esqueleto'),resource(before,'levantar_um_esqueleto')-1);
   await command('next_turn');await ownTurn();
   const corpse=preparedCorpse;assert.ok(corpse);
   await open(true);await page.locator(`[data-grid-token="${corpse.id}"] .workspace-pin-corpse-label`).waitFor();
   const animated=await cast('animar-mortos',()=>target('animar-mortos',corpse.id));await closeToken();assert.ok((await get('/workspace')).tokens.find(t=>t.id===animated.token.id).grid_position);assert.notEqual(animated.token.id,corpse.id);
   assert.equal(resource(await get('/characters/morthak'),'animar_mortos'),resource(before,'animar_mortos')-1);
   const live=aliveSummons(await get('/workspace'));assert.ok(live.some(t=>t.id===skeleton.id)&&live.some(t=>t.id===animated.token.id));
   assert.equal(live.filter(t=>t.sheet.summon.technique==='levantar-esqueleto').length,1);
   const reuse=await cast(id,()=>click(id));assert.equal(reuse.token.id,skeleton.id);
   const dialog=page.getByRole('dialog',{name:/^Ficha de /});await dialog.waitFor();const controls=dialog.locator('.workspace-summon-controls');if(!await controls.evaluate(el=>el.open))await controls.locator('summary').click();
   page.once('dialog',d=>d.accept());const dismissed=response(url=>url.endsWith('/techniques/dispensar-invocacao'));await controls.getByRole('button',{name:'Dispensar',exact:true}).click();const dismissal=await dismissed;assert.ok(dismissal.ok(),await dismissal.text());await dialog.getByRole('button',{name:'Fechar ficha',exact:true}).click();
   const after=(await get('/workspace')).tokens.find(t=>t.id===skeleton.id);assert.ok(after.sheet.summon.dismissed);assert.ok(!after.sheet.corpse);
   assert.equal(resource(await get('/characters/morthak'),'levantar_um_esqueleto'),resource(before,'levantar_um_esqueleto')-1);
   await open(true);assert.equal(await page.locator(`[data-grid-token="${skeleton.id}"]`).count(),0,'Dismissed unit must not return as a corpse pin');
   cover(id);cover('animar-mortos');
  }else if(kind==='clones'){
   const fragments=s=>s.inventory.filter(i=>i.item_title==='Fragmento de Cristal Arcano').reduce((sum,i)=>sum+i.quantity,0);
   const result=await cast('clonagem',()=>area('clonagem'));assert.deepEqual(await replay('clonagem'),result);
   assert.equal(fragments(await get('/characters/morthak')),fragments(before)-1);assert.equal(resource(await get('/characters/morthak'),'clonagem'),resource(before,'clonagem')-1);
   const clones=()=>get('/workspace').then(w=>w.tokens.filter(t=>t.sheet?.summon?.technique==='clonagem'));assert.equal((await clones()).length,0,'One-round execution must not spawn immediately in combat');
   await command('next_turn');await ownTurn();const units=await clones();assert.equal(units.length,2);assert.ok(units.every(t=>t.grid_position&&t.maximum_hp===Math.max(1,Math.floor(before.state.maximum_hp/4))));
   await open(true);assert.equal((await clones()).length,2);
   await card('clonagem').locator('button[data-card-command]').filter({hasText:'Encerrar concentração'}).waitFor({state:'attached'});
   await cast('clonagem',()=>click('clonagem'));assert.equal((await clones()).length,0);assert.equal(fragments(await get('/characters/morthak')),fragments(before)-1);
   observed.push({kind,test_only_fragment:seededFragment});cover('clonagem');
  }else{
   await area('magia-da-morte',false);assert.equal(sent.length,0);assert.equal((await get('/characters/morthak')).state.current_hp,before.state.current_hp);
   const result=await cast('magia-da-morte',()=>area('magia-da-morte'));assert.deepEqual(await replay('magia-da-morte'),result);
   const after=await get('/characters/morthak');assert.equal(after.state.current_hp,Math.floor(before.state.current_hp/10));assert.equal(resource(after,'magia_da_morte'),resource(before,'magia_da_morte')-1);
   assert.ok(result.protocol_result.results.length>0);observed.push({kind,hp_after:after.state.current_hp});cover('magia-da-morte');
  }
  const persisted=await get('/characters/morthak');await open(true);assert.deepEqual((await get('/characters/morthak')).state,persisted.state);
  await section.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,kind+'-'+width+'.png')});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await context.close();
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',batch,action_coverage,observed,screenshots:out}));
 }catch(error){for(const context of browser.contexts())for(const page of context.pages()){
  console.log('CARD_STATE '+JSON.stringify(await page.locator('article.workspace-spell-card').evaluateAll(cards=>cards.map(card=>({name:card.querySelector('.workspace-ability-name')?.textContent,disabled:card.querySelector('button[data-card-command]')?.disabled}))).catch(()=>[])));
  await page.screenshot({path:path.join(out,'failure-'+batch+'.png')}).catch(()=>{});
 }throw error;
 }finally{await browser.close();await api.dispose();await owner.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1});
