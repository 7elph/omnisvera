// Current action reference, native GM manifest and four actors in a verified TEMP fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(+new URL(base).port));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),`${url}: ${r.status()}`);return r.json();};
 const health=await get('/health');for(const p of [health.database_path,health.vault_path])assert.ok(path.resolve(p).startsWith(path.resolve(os.tmpdir())+path.sep));
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-action-readiness-')),screenshots=[],checks=[],errors=[],writes=[];
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
   const page=await context.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method())&&/\/(gm\/combat|characters\/[^/]+\/(actions|techniques)|combat\/attacks)/.test(new URL(r.url()).pathname))writes.push(new URL(r.url()).pathname);});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mestre$/}).click();
   await page.getByText('Cola de ações',{exact:true}).click();
   const panel=page.getByRole('region',{name:'Cola de ações',exact:true});await panel.waitFor();
   for(const actor of ['vezemir','raziel','dorn7','morthak']){
    await panel.getByRole('combobox',{name:'Personagem da cola de ações'}).selectOption(actor);
    await page.waitForFunction(()=>document.querySelector('.workspace-action-reference')?.getAttribute('aria-busy')==='false');
    assert.equal(await panel.getByRole('alert').count(),0);
    const native=await get('/gm/actions/manifest/'+actor);assert.equal(native.execution_approved,false);
    assert.ok((await panel.locator('.workspace-action-reference-list').innerText()).includes('Comando integrado'));
    if(actor==='raziel')for(const title of ['Tiro do Coração','Ceifa Rubra','Ruptura Óssea','Estocada Transfixante','Bastião Carmesim']){
     assert.equal(await panel.locator('.workspace-action-reference-list > article').filter({has:page.getByText(title,{exact:true})}).count(),1,title);
    }
    if(actor==='dorn7')for(const title of ['Levitação','Escuridão','Diagnóstico da Unidade'])assert.equal(await panel.getByText(title,{exact:true}).count(),0,title);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    const rows=panel.locator('.workspace-action-reference-list > article');
    for(const row of await rows.all())await row.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.querySelectorAll('.workspace-action-reference-list img')].every(i=>i.complete&&i.naturalWidth>0));
    await panel.scrollIntoViewIfNeeded();
    const shot=path.join(output,`${actor}-${width}.png`);await page.screenshot({path:shot});screenshots.push(shot);checks.push({actor,width,native_manifest:true,read_only:true});
   }
   await page.route('**/gm/actions/manifest/raziel',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"fixture offline"}'}));
   await panel.getByRole('combobox',{name:'Personagem da cola de ações'}).selectOption('raziel');
   await page.waitForFunction(()=>document.querySelector('.workspace-action-reference')?.getAttribute('aria-busy')==='false');
   await panel.getByText('Não foi possível verificar a automação. As descrições continuam disponíveis.',{exact:true}).waitFor();
   assert.ok((await panel.innerText()).includes('Automação não verificada'));assert.ok(!(await panel.locator('.workspace-action-reference-list').innerText()).includes('Comando integrado'));
   await page.unroute('**/gm/actions/manifest/raziel');await panel.getByRole('button',{name:'Atualizar consulta',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.workspace-action-reference')?.getAttribute('aria-busy')==='false');
   assert.ok((await panel.innerText()).includes('Tiro do Coração'));
   await context.close();
  }
  const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
  try{assert.ok([401,403].includes((await player.get('/gm/actions/manifest/raziel')).status()));}finally{await player.dispose();}
  assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
  const result={status:'PASS',scope:'four_actor_action_reference_only',checks,screenshots,manifest_failure_and_retry:true,player_manifest_denied:true,no_commands_sent:true,production_modified:false,visual_acceptance:'pending_agent_image_review'};
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
