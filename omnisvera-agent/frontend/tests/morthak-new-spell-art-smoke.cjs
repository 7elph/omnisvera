// Read-only built sheet, original supplied images, disposable fixture only.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const health=await api.get('/health');assert.ok(health.ok());assert.ok(path.resolve((await health.json()).database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const entries=[['clonagem','Clonagem'],['magia-da-morte','Magia da Morte'],['toque-sombrio','Toque Sombrio'],['aterrorizar','Aterrorizar']];
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'morthak-new-spell-art-'));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[];
 try{
  for(const [role,width] of [['gm',1440],['morthak',390]]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(({role})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character','morthak');},{role});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   await page.locator('button[data-character="morthak"]').click();
   const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
   const spells=panel.locator('.workspace-sheet-section > summary').filter({hasText:/^Magias$/});
   if(!(await spells.evaluate(el=>el.parentElement.open)))await spells.click();
   for(const [id,title] of entries){
    const trigger=panel.getByRole('button',{name:title,exact:true});await trigger.waitFor();
    const icon=trigger.locator('img');await icon.waitFor();
    await icon.evaluate(el=>el.complete&&el.naturalWidth>0?Promise.resolve():new Promise((resolve,reject)=>{el.onload=resolve;el.onerror=()=>reject(new Error('Icon did not load'));}));
    assert.ok((await icon.getAttribute('src')).endsWith(`/companion-assets/morthak-${id}.jpg`));
    const size=await icon.boundingBox();assert.equal(size.width,27);assert.equal(size.height,27);
    await trigger.click({modifiers:['Shift']});const dialog=page.getByRole('dialog',{name:title,exact:true});await dialog.waitFor();
    const image=dialog.locator('.workspace-detail-image');await image.waitFor();
    await image.evaluate(el=>el.complete&&el.naturalWidth>0?Promise.resolve():new Promise((resolve,reject)=>{el.onload=resolve;el.onerror=()=>reject(new Error('Full image did not load'));}));
    assert.ok((await image.getAttribute('src')).endsWith(`/companion-assets/morthak-${id}.jpg`));
    assert.ok(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth+2),'No horizontal overflow');
    await dialog.screenshot({path:path.join(output,`${role}-${id}.png`)});
    await dialog.getByRole('button',{name:'Fechar descrição',exact:true}).click();
    checks.push({role,width,id,icon:27,image:'loaded'});
   }
   await panel.screenshot({path:path.join(output,`${role}-sheet.png`)});await context.close();
  }
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output,mutations:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1});
