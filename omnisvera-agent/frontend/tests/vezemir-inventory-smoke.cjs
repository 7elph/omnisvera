// Built native UI: equip/store only in the verified disposable fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const health=await api.get('/health');assert.ok(health.ok());assert.ok(path.resolve((await health.json()).database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const get=async()=>{const r=await api.get('/characters/vezemir');assert.ok(r.ok());return r.json();};
 const before=await get(),original=before.inventory.find(i=>i.item_title==='Pulseira de Vinhas');assert.ok(original);
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'vezemir-inventory-'));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[];
 try{
  for(const [role,width] of [['gm',1440],['vezemir',390]]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','vezemir');},{role});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator('button[data-character="vezemir"]').click();
   const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
   await panel.locator('.workspace-identity-tags').getByRole('button',{name:'Especialista em Armas',exact:true}).waitFor();
   assert.equal(await panel.getByRole('button',{name:'Detalhar Força',exact:true}).count(),0);
   const inventory=panel.locator('.workspace-inventory-catalog').getByRole('button',{name:'Pulseira de Vinhas',exact:true});
   await inventory.waitFor();assert.equal(await inventory.count(),1);
   const resource=panel.locator('.workspace-resource-catalog article').filter({hasText:'Pulseira de Vinhas'});
   const dialog=page.getByRole('dialog',{name:'Informações de Pulseira de Vinhas',exact:true});
   await inventory.click();await dialog.waitFor();
   if(await dialog.getByRole('button',{name:'Guardar',exact:true}).count()){
    await dialog.getByRole('button',{name:'Guardar',exact:true}).click();await resource.waitFor({state:'detached'});
   }
   assert.equal(await resource.count(),0);
   await dialog.getByRole('button',{name:'Equipar em Acessório',exact:true}).click();await resource.waitFor();
   assert.equal(await resource.getByRole('button',{name:'Guardar',exact:true}).count(),0);
   assert.equal(await resource.getByRole('button',{name:/Equipar/}).count(),0);
   assert.equal(await resource.locator('button[data-card-command]').count(),1);
   assert.equal(await resource.locator('button[data-card-command]').isVisible(),false);
   await dialog.getByRole('button',{name:'Guardar',exact:true}).waitFor();
   await dialog.getByRole('button',{name:'Fechar informações do item',exact:true}).click();
   await page.reload();await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   await page.locator('button[data-character="vezemir"]').click();
   assert.equal((await get()).inventory.find(i=>i.item_path===original.item_path).equipped,true,'Equipment persists independently of the initially selected sheet');
   await resource.waitFor();await inventory.waitFor();
   assert.ok(await panel.evaluate(el=>el.scrollWidth<=el.clientWidth+2),'No horizontal overflow');
   await panel.screenshot({path:path.join(output,`${role}-${width}.png`)});
   await inventory.click();await dialog.waitFor();
   await dialog.getByRole('button',{name:'Guardar',exact:true}).click();await resource.waitFor({state:'detached'});await inventory.waitFor();
   await dialog.getByRole('button',{name:'Fechar informações do item',exact:true}).click();
   const after=await get(),item=after.inventory.find(i=>i.item_path===original.item_path);
   assert.equal(item.quantity,original.quantity);assert.equal(item.charges_current,original.charges_current);
   assert.equal(after.state.current_hp,before.state.current_hp);
   checks.push({role,width,equipment_cycle:'PASS',reload:'PASS',hp_quantity_charges:'unchanged'});await context.close();
  }
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output,mutations:'equipment only, TEMP fixture'}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1});
