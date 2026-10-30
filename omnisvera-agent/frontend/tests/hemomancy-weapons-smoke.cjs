// Built client, native grid/receipts/realtime, TEMP fixture only. Never production.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8')),base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data);
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],action_coverage=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-hemomancy-ui-'));
 try{
  const batch=process.env.OMNISVERA_QA_HEMOMANCY_BATCH||'first';assert.ok(['first','second'].includes(batch));
  const cases=batch==='first'?[['arco',false,390,'raziel'],['arco',true,1440,'gm'],['foice',true,390,'raziel']]:[['marreta',true,1440,'gm'],['lanca',true,390,'raziel'],['escudo',false,390,'raziel']];
  for(const [weapon,skill,width,role] of cases){
   console.log('RUN hemomancy '+weapon+(skill?' skill':' basic'));
   if((await get('/combat/effects')).encounter?.active)await command('end');
   await post('/characters/raziel/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture de Hemomancia'});
   await call('patch','/gm/workspace/maps/active',{map_id:evidence.map_id});
   let workspace=await get('/workspace'),grid=workspace.map.grid,mine=workspace.tokens.find(t=>t.character_id==='raziel'),enemy=workspace.tokens.find(t=>t.id===evidence.enemy_id);
   assert.ok(grid&&mine?.grid_position&&enemy?.grid_position);
   for(const token of workspace.tokens)if(token.id!==mine.id&&token.id!==enemy.id&&token.visible_to_players)await call('patch','/gm/workspace/tokens/'+encodeURIComponent(token.id),{visible_to_players:false});
   await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{visible_to_players:true,current_hp:500,maximum_hp:500,sheet:{...enemy.sheet,armor_class:1,has_blood:true}});
   for(const [token,x] of [[mine,4],[enemy,5]])await post(`/workspace/maps/${encodeURIComponent(evidence.map_id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[token.grid_position.cell_x,token.grid_position.cell_y],[x,5]],expected_position_version:token.grid_position.version,expected_grid_version:grid.version});
   await command('start',{map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:20},{target_type:'token',target_id:enemy.id,initiative:1}]});
   let before=await get('/characters/raziel');const pack=before.definition.hemomancy,spec=pack.weapons.find(w=>w.weapon===weapon);
   assert.deepEqual(pack.weapons.map(w=>w.weapon),['arco','foice','marreta','escudo','lanca']);
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','raziel');},{role});
   const page=await context.newPage(),casts=[];page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/techniques/hemomancia-'))casts.push(r.url());});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   await page.locator('button[data-character="raziel"]').click();
   const section=page.locator('.workspace-sheet-section').filter({has:page.locator('.workspace-hemomancy')});
   if(!await section.evaluate(el=>el.open))await section.locator(':scope > summary').click();
   const weaponCard=page.locator('.workspace-hemomancy-card');await weaponCard.waitFor();
   await weaponCard.getByLabel('Arma da Hemomancia').selectOption(skill||weapon==='escudo'?'arco':weapon);
   assert.equal(await weaponCard.locator('select').count(),1,'Hemomancia only selects the weapon');
   assert.equal(await weaponCard.locator('.workspace-hemomancy-pipeline').count(),0);
   const activeSection=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Habilidades$/})});
   const powerSection=page.locator('.workspace-sheet-section').filter({has:page.locator('summary').filter({hasText:/^Poderes vampíricos$/i})});
   for(const group of [activeSection,powerSection])if(!await group.evaluate(el=>el.open))await group.locator(':scope > summary').click();
   assert.equal(await activeSection.locator('.workspace-ability-name').count(),10);
   assert.equal(await activeSection.locator('.workspace-hemomancy-skill').count(),5);
   for(const name of ['Caixão','Mordida','Forma da Noite','Regeneração Vampírica','Marca Rubra'])assert.equal(await activeSection.getByRole('button',{name,exact:true}).count(),1);
   for(const name of ['Marca Rubra aprimorada','Faro de Sangue','Técnica de Predador','Corpo Predatório','Medo'])assert.equal(await activeSection.getByRole('button',{name,exact:true}).count(),0);
   assert.equal(await powerSection.locator('.workspace-ability-name').count(),5);
   const markCard=activeSection.locator('article').filter({has:page.getByRole('button',{name:'Marca Rubra',exact:true})});
   const blood=value=>value.state.resources.find(r=>r.key==='reserva_de_sangue').current;
   const maximum=before.state.resources.find(r=>r.key==='reserva_de_sangue').maximum;
   assert.equal(await markCard.locator('b').innerText(),`${blood(before)}/${maximum}`,'Marca Rubra shows the persisted blood pool, not invented daily uses');
   assert.equal(await powerSection.locator('button[data-card-command]').count(),0,'Passives never have activation commands');
   await powerSection.getByRole('button',{name:spec.passive.name,exact:true}).click();
   await page.getByRole('dialog',{name:spec.passive.name,exact:true}).waitFor();
   await page.getByRole('button',{name:'Fechar descrição',exact:true}).click();
   assert.equal(await page.locator('.targeting-overlay').count(),0,'Reading a passive must not activate the grid');
   assert.equal(casts.length,0);
   if(weapon==='arco'){
    await call('patch','/gm/workspace/tokens/'+encodeURIComponent(enemy.id),{current_hp:499});
    const sentMark=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/marca-rubra'));
    await markCard.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
    await page.locator(`[data-grid-token="${enemy.id}"]`).click();
    await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
    const marked=await sentMark;assert.ok(marked.ok(),await marked.text());
    const afterMark=await get('/characters/raziel');assert.equal(blood(afterMark),blood(before)-1);
    await page.waitForFunction(({expected})=>Array.from(document.querySelectorAll('article')).some(el=>el.querySelector('button.workspace-ability-name')?.textContent?.trim()==='Marca Rubra'&&el.querySelector('b')?.textContent===expected),{expected:`${blood(afterMark)}/${maximum}`});
    before=afterMark;
    action_coverage.push({actor:'raziel',key:'ability:marca-rubra',verified_checks:['ui']});
   }
   const card=skill||weapon==='escudo'?activeSection.locator('.workspace-hemomancy-skill').filter({has:page.getByRole('button',{name:spec.skill.name,exact:true})}):weaponCard;
   assert.equal(await card.locator('button[data-card-command]').count(),1);
   assert.ok(await card.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'Card must fit desktop/mobile');
   if(weapon==='arco'&&!skill){await activeSection.screenshot({path:path.join(output,'habilidades-'+width+'.png')});await powerSection.screenshot({path:path.join(output,'poderes-'+width+'.png')});}
   // A second real client observes native ledger/realtime without an explicit reload.
   let observer,changed;
   const expected=blood(before)-spec.invocation_cost-(skill?spec.skill.cost:0);
   if(weapon==='arco'&&!skill){
    observer=await context.newPage();await observer.goto(base);await observer.locator('.app-shell.authenticated').waitFor();
    await card.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
    await page.locator(`[data-grid-token="${enemy.id}"]`).click();
    await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Não',exact:true}).click();
    assert.equal(blood(await get('/characters/raziel')),blood(before),'Cancel never spends');
   }
   const commandId=`hemomancia-${weapon}${skill?'-habilidade':''}`;
   // The mark's counter can render before the complete overview refresh ends.
   // Wait for the actual command to be actionable before clicking its card.
   await page.waitForFunction(button=>button&&!button.disabled,await card.locator('button[data-card-command]').elementHandle());
   await card.click({trial:true}); // Command buttons are intentionally hidden on clickable cards.
   const sent=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/techniques/'+commandId));
   const confirmed=weapon==='escudo'?null:page.waitForResponse(r=>r.request().method()==='POST'&&/\/combat\/attacks\/.*\/confirm$/.test(new URL(r.url()).pathname));
   void sent.catch(()=>{});if(confirmed)void confirmed.catch(()=>{});
   await card.click({position:{x:8,y:8}});
   if(weapon!=='escudo'){
    await page.locator('.targeting-overlay').waitFor();await page.locator(`[data-grid-token="${enemy.id}"]`).click();
    // Measure propagation only after target selection/cancellation is complete.
    // Slow viewport rendering is not time spent waiting for the confirmed action.
    if(observer)changed=observer.waitForResponse(async r=>{if(new URL(r.url()).pathname!=='/characters/raziel')return false;try{return blood(await r.json())===expected;}catch{return false;}},{timeout:30000});
    await page.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();
   }
   const reply=await sent;assert.ok(reply.ok(),await reply.text());
   if(weapon==='arco'&&skill){const resolved=await reply.json(),base=before.definition.attacks.find(a=>a.id==='ranged');assert.equal(resolved.attack_bonus,(base.base_attack_bonus??base.attack_bonus)+(base.effect_attack_bonus||0)+2,'Tiro uses the native Marca Rubra bonus');}
   if(confirmed){const result=await confirmed;assert.ok(result.ok(),await result.text());
    if(weapon==='lanca'&&skill){
     const resolved=await result.json();assert.equal(resolved.breakdown.hemomancy.skill_damage,'1d4');
     if(resolved.result==='hit'){assert.match(resolved.damage_formula,/1d8\+1d4/);assert.equal(resolved.damage_total,resolved.damage_rolls.reduce((a,b)=>a+b,0)+resolved.damage_modifier);}
     else {assert.equal(resolved.damage_total,0);assert.equal(resolved.damage_rolls.length,0);}
    }
   }
   if(changed)await changed;
   const after=await get('/characters/raziel');assert.equal(blood(after),expected);
   assert.equal(casts.length,1,'One card confirmation must send one technique command');
   const effects=(await get('/combat/effects')).effects;
   assert.ok(effects.some(e=>e.hemomancy_kind===(weapon==='escudo'?'shield':'weapon')&&(weapon==='escudo'||e.weapon===weapon)));
   await card.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,weapon+(skill?'-skill':'')+'-'+width+'.png'),fullPage:false});
   await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal(blood(await get('/characters/raziel')),expected);
   action_coverage.push({actor:'raziel',key:'ability:'+commandId,verified_checks:['ui']});await context.close();
  }
  await command('end');assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',action_coverage,screenshots:output,production_modified:false,multi_client:'local browser pages only'}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
