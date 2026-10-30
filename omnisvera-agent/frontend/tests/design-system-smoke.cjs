// Presentation-only navigation, on the existing guarded TEMP rehearsal.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const file=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');assert.ok(file.startsWith(path.resolve(os.tmpdir())+path.sep));
 const evidence=JSON.parse(fs.readFileSync(file,'utf8'));assert.ok(evidence.run_id.startsWith('simulation-'));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const response=await api.get('/health');assert.ok(response.ok());const health=await response.json();assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[];
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-design-system-'));
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');localStorage.setItem('omnisvera_selected_character','vezemir');});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   const nav=page.getByRole('navigation',{name:'Navegação principal'});
   await nav.getByRole('button',{name:/Mesa$/}).click();await page.locator('button[data-character="vezemir"]').click();
   const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-inventory-catalog article').first().waitFor();
   for(const summary of await panel.locator('.workspace-sheet-section > summary').all()){
    if(!(await summary.evaluate(el=>el.parentElement.open)))await summary.click();
   }
   const cards=await panel.locator('.workspace-action-catalog:not(.workspace-inventory-catalog) > article').evaluateAll(elements=>elements.map(el=>{
    const style=getComputedStyle(el);return {radius:style.borderTopLeftRadius,background:style.backgroundColor,width:el.clientWidth,overflow:el.scrollWidth>el.clientWidth+2};
   }));assert.ok(cards.length>5);for(const card of cards){assert.equal(card.radius,'4px');assert.equal(card.background,'rgb(23, 25, 27)');assert.ok(card.width>100&&!card.overflow,'Card content must not clip horizontally');}
   const title=panel.getByRole('button',{name:'Meio-Elfo',exact:true});await title.click();
   const dialog=page.getByRole('dialog',{name:'Meio-Elfo',exact:true});await dialog.waitFor();
   const dm=await dialog.evaluate(el=>({width:el.getBoundingClientRect().width,radius:getComputedStyle(el).borderTopLeftRadius,height:el.getBoundingClientRect().height,overflow:el.scrollWidth>el.clientWidth+2}));
   assert.equal(dm.radius,'4px');assert.ok(dm.width<=width&&!dm.overflow&&dm.height<=900);
   await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal(await title.evaluate(el=>document.activeElement===el),true,'Focus returns to the original card');
   await panel.screenshot({path:path.join(output,`ficha-${width}.png`)});
   for(const name of ['Mapas','NPCs','Sessão','Cenas']){
    await nav.getByRole('button',{name:new RegExp(name+'$')}).click();
    if(name==='Mapas')await page.getByRole('region',{name:'Biblioteca de mapas'}).waitFor();
    if(name==='NPCs')await page.getByRole('region',{name:'NPCs do Mestre'}).waitFor();
    if(name==='Sessão')await page.locator('.campaign-memory-layout:not(.campaign-memory-loading)').waitFor({timeout:45000});
    if(name==='Cenas')await page.waitForFunction(()=>{const el=document.querySelector('.scene-page');return el && !el.textContent.includes('Preparando painel de cena');},{},{timeout:45000});
    // A transition frame is not evidence of a finished layout.
    await page.waitForTimeout(350);
    const samples=await page.locator('.workspace-map-library button,.workspace-map-library input,.workspace-map-library select,.workspace-npc-reference button:not(.workspace-ability-name),.scene-page input:not([type="checkbox"]):not([type="radio"]),.scene-page select,.campaign-section input:not([type="checkbox"]):not([type="radio"])').evaluateAll(elements=>elements.filter(el=>el.getBoundingClientRect().width>0).map(el=>{
     const style=getComputedStyle(el);return {radius:style.borderTopLeftRadius,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,font:parseFloat(style.fontSize)};
    }));
    for(const sample of samples){assert.equal(sample.radius,'4px',name+' control');assert.ok(sample.font>=12&&sample.height>=36,name+' readable control');}
    await page.screenshot({path:path.join(output,`${name}-${width}.png`)});checks.push({area:name,width,controls:samples.length});
   }
   await nav.getByRole('button',{name:/Mestre$/}).click();await page.locator('.workspace-gm-drawer').first().waitFor();
   assert.ok(await page.getByRole('button',{name:/Mapas$/}).count(),'Navigation stays available while GM tools are open');
   await page.screenshot({path:path.join(output,`mestre-${width}.png`)});checks.push({area:'Ficha/diálogo/Mestre',width,cards:cards.length});
   await context.close();
  }
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-morthak');localStorage.setItem('omnisvera_access_mode','player');localStorage.setItem('omnisvera_selected_character','morthak');});
  const owner=await context.newPage();owner.on('pageerror',e=>errors.push(e.message));await owner.goto(base);await owner.locator('.app-shell.authenticated').waitFor();
  const nav=owner.getByRole('navigation',{name:'Navegação principal'});assert.equal(await nav.getByRole('button',{name:/Mestre$|Mapas$|NPCs$|Cenas$/}).count(),0,'Theme cannot expose GM tools to players');
  await nav.getByRole('button',{name:/Ficha$/}).click();await owner.locator('.workspace-character-panel').waitFor();await owner.screenshot({path:path.join(output,'jogador-390.png')});
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output,mutations:'No game actions sent by this visual script'}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1});
