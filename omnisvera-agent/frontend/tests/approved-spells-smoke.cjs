// Built sheet, native commands, isolated simulation only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const evidencePath=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(evidencePath.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(evidencePath,'utf8'));assert.ok(evidence.run_id.startsWith('simulation-'));
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const health=await get('/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 let combat=await get('/combat/effects');if(combat.encounter?.active)await post('/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
 assert.ok((await api.patch('/gm/workspace/maps/active',{data:{map_id:evidence.map_id}})).ok());
 for(const actor of ['morthak','dorn7'])await post(`/characters/${actor}/actions`,{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture: novo pacote aprovado'});
 if(!(await get('/characters/morthak')).inventory.some(i=>i.item_title==='Fragmento de Cristal Arcano'&&i.quantity>0)){
  const fragment=(await get('/gm/workspace/items')).find(i=>i.name==='Fragmento de Cristal Arcano');assert.ok(fragment,'Persisted catalog fragment required');
  await post('/gm/workspace/items/grant',{character_id:'morthak',item_id:fragment.id,quantity:1,notes:'Somente fixture: componente para testar Clonagem'});
 }
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],commands=[];
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-approved-spells-'));
 async function clickCard(page,card){await page.waitForFunction(el=>el.isConnected && !el.querySelector('button[data-card-command]')?.disabled,await card.elementHandle());await card.click({position:{x:8,y:8}});}
 async function open(role,actor,width){
  const context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST'&&(r.url().includes('/techniques/')||r.url().endsWith('/gm/combat/effects')))commands.push({url:r.url(),body:r.postDataJSON()});});
  await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
  await page.locator(`button[data-character="${actor}"]`).click();await page.locator('.workspace-character-identity').waitFor();
  const spells=page.locator('.workspace-sheet-section > summary').filter({hasText:/^Magias$/});
  if(!(await spells.evaluate(el=>el.parentElement.open)))await spells.click();return page;
 }
 try{
  const owner=await open('morthak','morthak',390),gm=await open('gm','morthak',1440);
  for(const page of [owner,gm]){
   const panel=page.locator('article.workspace-spell-card').filter({hasText:'Clonagem'});assert.equal(await panel.locator('button[data-card-command]').isEnabled(),true);
   const metrics=await panel.evaluate(el=>({width:el.clientWidth,overflow:el.scrollWidth>el.clientWidth+1}));assert.ok(metrics.width>100&&!metrics.overflow,'Single action card fits its column');
  }
  await owner.screenshot({path:path.join(output,'owner-clonagem-390.png'),fullPage:true});
  const panel=owner.locator('article.workspace-spell-card').filter({hasText:'Clonagem'});await clickCard(owner,panel);await owner.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Sim',exact:true}).click();await panel.locator('button[data-card-command]').filter({hasText:'Encerrar concentração'}).waitFor({state:'attached'});
  let tokens=(await get('/workspace')).tokens.filter(t=>t.sheet?.summon?.technique==='clonagem');assert.equal(tokens.length,2);assert.ok(tokens.every(t=>t.grid_position&&t.current_hp>0));
  await gm.locator('article.workspace-spell-card').filter({hasText:'Clonagem'}).locator('button[data-card-command]').filter({hasText:'Encerrar concentração'}).waitFor({state:'attached'});
  await owner.reload();await owner.locator('.app-shell.authenticated').waitFor();assert.equal((await get('/workspace')).tokens.filter(t=>t.sheet?.summon?.technique==='clonagem').length,2);
  await owner.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();await owner.locator('button[data-character="morthak"]').click();
  const spellsAfterReload=owner.locator('.workspace-sheet-section > summary').filter({hasText:/^Magias$/});
  if(!(await spellsAfterReload.evaluate(el=>el.parentElement.open)))await spellsAfterReload.click();
  await clickCard(owner,owner.locator('article.workspace-spell-card').filter({hasText:'Clonagem'}));
  await owner.locator('article.workspace-spell-card').filter({hasText:'Clonagem'}).locator('button[data-card-command]').filter({hasText:'Usar'}).waitFor({state:'attached'});
  assert.equal((await get('/workspace')).tokens.filter(t=>t.sheet?.summon?.technique==='clonagem').length,0);
  await clickCard(owner,owner.locator('article.workspace-spell-card').filter({hasText:'Magia da Morte'}));assert.match(await owner.getByRole('dialog',{name:'Confirmar alvo'}).innerText(),/inclusive aliados/);await owner.getByRole('dialog',{name:'Confirmar alvo'}).getByRole('button',{name:'Não',exact:true}).click();
  const dorn=await open('gm','dorn7',390);
  for(const spell of ['Reflexos','Teia','Força Arcana','Dissipar Magia'])assert.ok(await dorn.getByRole('button',{name:spell,exact:true}).count(),spell+' card');
  const card=dorn.locator('article.workspace-spell-card').filter({hasText:'Reflexos'});await clickCard(dorn,card);
  await dorn.waitForFunction(()=>document.querySelector('.workspace-log-filters')?.textContent || document.querySelector('.workspace-character-identity'));
  for(let i=0;i<30;i++){combat=await get('/combat/effects');if(combat.effects.some(e=>e.spell==='reflexos'&&e.images_remaining>=2))break;await dorn.waitForTimeout(100);}
  assert.ok(combat.effects.some(e=>e.spell==='reflexos'&&e.images_remaining>=2));
  await dorn.screenshot({path:path.join(output,'dorn-reflexos-390.png'),fullPage:true});
  assert.equal(commands.filter(c=>c.url.endsWith('/techniques/clonagem')&&c.body.mode!=='end').length,1);assert.equal(commands.filter(c=>c.body.action==='dorn_spell_cast'&&c.body.payload.spell_id==='reflexos').length,1);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['owner/GM controls','Clonagem native spawn/end','logical positions','reload','local second client','Dorn six-spell cards and Reflexos cast','mobile width'],action_coverage:[{actor:'morthak',key:'ability:clonagem',verified_checks:['ui']},{actor:'dorn7',key:'ability:reflexos',verified_checks:['ui']}],screenshots:output}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1});
