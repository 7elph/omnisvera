// Native fixture only: real UI + committed/lost response + page reload + receipt replay.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,timeout:15000,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const response=await api[method](url,{data});assert.ok(response.ok(),`${response.status()} ${url}: ${await response.text()}`);return response.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data),patch=(url,data)=>call('patch',url,data);
 const health=await get('/health');
 for(const key of ['database_path','vault_path'])assert.ok(path.resolve(health[key]).toLowerCase().startsWith((path.resolve(os.tmpdir())+path.sep).toLowerCase()));
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-catalog-recovery-')),checks=[],errors=[],owned=[];
 const evidence={status:'RUNNING',production_modified:false,screenshots:output,checks};
 let browser,map,oldMap;
 const timer=setTimeout(()=>{console.error('Catalogue smoke reached 285-second deadline');process.exit(1);},285000);timer.unref();
 try{
  const combat=await get('/combat/effects');
  if(combat.encounter?.active)await post('/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
  oldMap=(await get('/workspace')).map;
  map=await post('/gm/workspace/map',{title:'ENSAIO catálogo e recovery',filename:'fixture.png',content_type:'image/png',visible_to_players:true,
   data_base64:'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg=='});
  await patch('/gm/workspace/maps/active',{map_id:map.id});
  await post(`/workspace/maps/${encodeURIComponent(map.id)}/grid`,{request_id:randomUUID(),expected_version:0,cols:20,rows:20,cell_size_m:1.5});
  const healer=await post('/gm/workspace/tokens',{token_type:'monster',map_id:map.id,name:'Conjurador TEMP',latitude:27.5,longitude:22.5,
   visible_to_players:true,current_hp:20,maximum_hp:20,sheet:{spellcaster_level:5,category:'Humanoide'}});owned.push(healer.id);
  const patient=await post('/gm/workspace/tokens',{token_type:'monster',map_id:map.id,name:'Paciente TEMP',latitude:27.5,longitude:27.5,
   visible_to_players:true,current_hp:10,maximum_hp:40,sheet:{category:'Humanoide'}});owned.push(patient.id);
  const hero=await post('/gm/workspace/tokens',{token_type:'character',character_id:'vezemir',map_id:map.id,name:'Vezemir TEMP',latitude:27.5,longitude:32.5,visible_to_players:true});owned.push(hero.id);
  browser=await chromium.launch({channel:'msedge',headless:true});
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','dorn7');});
   const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
   const open=async(restoring=false)=>{
    await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/NPCs$/}).click();
    const tools=page.locator('aside[aria-label="Controles de NPCs"] > details');
    await tools.waitFor();if(await tools.getAttribute('open')===null)await tools.locator(':scope > summary').click();
    const summary=tools.locator('summary').filter({hasText:'GRIMÓRIO E COMPÊNDIOS'});
    const details=summary.locator('..');
    if(await details.getAttribute('open')===null)await summary.click();
    const panel=details.locator('section.workspace-monster-catalog').first();
    if(!restoring)await panel.getByRole('combobox',{name:'Tradição',exact:true}).selectOption('divina');
    return panel;
   };
   const select=async(panel,suffix)=>{
    await panel.getByRole('combobox',{name:'Magia do grimório',exact:true}).selectOption('divina-curar-ferimentos-'+suffix+'-r');
    await panel.getByRole('combobox',{name:'Conjurador',exact:true}).selectOption('token:'+healer.id);
    await panel.getByRole('combobox',{name:/Alvo de/}).selectOption('token:'+patient.id);
    assert.equal(await panel.getByPlaceholder('d20 físico (opcional)').count(),0,'Healing never requests an irrelevant save die');
   };
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   let panel=await open();
   for(const suffix of ['leves','graves','criticos']){
    await patch('/gm/workspace/tokens/'+encodeURIComponent(patient.id),{current_hp:10});
    await select(panel,suffix);
    const ids=[];let lose=suffix==='leves',actual;
    const pattern=`**/gm/compendium/spells/divina-curar-ferimentos-${suffix}-r/cast`;
    await page.route(pattern,async route=>{
     try{
      ids.push(route.request().postDataJSON().request_id);
      // Retry only ECONNRESET once, with the identical idempotent request body.
      const response=await route.fetch({maxRetries:1});assert.equal(response.status(),200);actual=await response.json();
      if(lose){lose=false;await route.abort('failed');}else await route.fulfill({response});
     }catch(error){errors.push(error.message);await route.abort('failed');}
    });
    await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
    if(suffix==='leves'){
     await panel.getByText(/Failed to fetch|Falha ao conjurar|fetch/i).waitFor();
     assert.ok(actual?.results[0]?.healing_applied>0);const after=actual.results[0].hp.after;
     await page.reload();await page.locator('.app-shell.authenticated').waitFor();panel=await open(true);
     await page.waitForFunction(id=>[...document.querySelectorAll('select[aria-label="Magia do grimório"]')].some(el=>el.checkVisibility()&&el.value===id),'divina-curar-ferimentos-leves-r');
     assert.equal(await panel.getByRole('combobox',{name:'Conjurador',exact:true}).inputValue(),'token:'+healer.id);
     assert.equal(await panel.getByRole('combobox',{name:/Alvo de/}).inputValue(),'token:'+patient.id);
     assert.equal(ids.length,1,'Reload must not resend a mutation automatically');
     await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
     await panel.getByRole('status').filter({hasText:/cura/}).waitFor();
     assert.equal(ids.length,2);assert.equal(ids[0],ids[1],'The confirmed but lost action retains its ID after reload');
     const token=(await get('/workspace')).tokens.find(token=>token.id===patient.id);assert.equal(token.current_hp,after);
     checks.push({width,key:'reload_replay',request_id:ids[0],hp_after:after});
    }else{
     await panel.getByRole('status').filter({hasText:/cura/}).waitFor();assert.equal(ids.length,1);
    }
    assert.equal(actual.results[0].damage_dealt,0);assert.ok(actual.results[0].range.checked);
    assert.equal(actual.results[0].hp.after,Math.min(40,10+actual.results[0].healing_rolled));
    assert.equal(await page.evaluate(()=>Object.keys(sessionStorage).filter(key=>key.startsWith('omnisvera:command:v1:')).length),0);
    const preview=panel.locator('article.workspace-monster-catalog-preview');
    const layout=await preview.evaluate(el=>{const [text,controls]=el.children,box=el.getBoundingClientRect(),a=text.getBoundingClientRect(),b=controls.getBoundingClientRect();return {fullWidth:a.width>=box.width*.8,separate:a.bottom<=b.top+1,overflow:text.scrollWidth>text.clientWidth+1};});
    assert.ok(layout.fullWidth&&layout.separate&&!layout.overflow,'Spell description uses full width without overlapping controls');
    await preview.screenshot({path:path.join(output,`healing-${suffix}-${width}.png`)});
    checks.push({width,key:'heal_'+suffix,healing:actual.results[0].healing_applied,rolled:actual.results[0].healing_rolled});
    await page.unroute(pattern);
   }
   await post('/characters/vezemir/actions',{request_id:randomUUID(),action:'add_condition',payload:{condition:'Paralisia'}});
   await panel.getByRole('combobox',{name:'Magia do grimório',exact:true}).selectOption('divina-remover-paralisia');
   await panel.getByRole('combobox',{name:'Conjurador',exact:true}).selectOption('token:'+healer.id);
   await panel.getByRole('combobox',{name:/Alvo de/}).selectOption('vezemir');
   assert.equal(await panel.getByPlaceholder('d20 físico (opcional)').count(),0);
   const conditionResponse=page.waitForResponse(response=>response.url().includes('/divina-remover-paralisia/cast')&&response.request().method()==='POST');
   await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
   const conditionReply=await conditionResponse;assert.equal(conditionReply.status(),200,await conditionReply.text());
   await panel.getByRole('status').filter({hasText:/removido: Paralisia/}).waitFor();
   assert.ok(!(await get('/characters/vezemir?read_only=true')).state.conditions.includes('Paralisia'));
   await panel.locator('article.workspace-monster-catalog-preview').screenshot({path:path.join(output,`condition-cure-${width}.png`)});
   checks.push({width,key:'condition_cure'});
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();
   await page.locator('button[data-character="dorn7"]').click();const sheet=page.locator('.workspace-character-panel');await sheet.locator('.workspace-character-identity').waitFor();
   const spells=sheet.locator('details').filter({has:page.locator('summary').filter({hasText:'MAGIAS'})}).first();
   if(await spells.count() && await spells.getAttribute('open')===null)await spells.locator('summary').first().click();
   for(const fragment of ['relampago_','/adaga.png']){
    const image=sheet.locator(`img[src*="${fragment}"]`).first();await image.waitFor();
    await image.evaluate(img=>img.complete&&img.naturalWidth>0?null:new Promise((resolve,reject)=>{img.addEventListener('load',resolve,{once:true});img.addEventListener('error',()=>reject(Error('Dorn image failed')),{once:true});}));
    assert.ok(await image.evaluate(img=>img.complete&&img.naturalWidth>0),fragment);
   }
   await sheet.screenshot({path:path.join(output,`dorn-art-${width}.png`)});checks.push({width,key:'dorn_images_loaded'});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),'No horizontal page overflow');
   await context.close();
  }
  assert.deepEqual(errors,[]);evidence.status='PASS';console.log(JSON.stringify(evidence));
 }catch(error){evidence.status='FAIL';evidence.error=error.message;throw error;}finally{
  clearTimeout(timer);await browser?.close();
  for(const id of owned)await api.delete('/gm/workspace/tokens/'+encodeURIComponent(id));
  if(oldMap?.id)await patch('/gm/workspace/maps/active',{map_id:oldMap.id});
  if(map?.id)await api.delete('/gm/workspace/maps/'+encodeURIComponent(map.id));
  await api.dispose();fs.writeFileSync(path.join(output,'evidence.json'),JSON.stringify(evidence,null,2));
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
