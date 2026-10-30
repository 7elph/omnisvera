// Built app + disposable CF-01 database. No real-table actions or credentials.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL||'http://127.0.0.1:8872';
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
 assert.ok(![8787,8788].includes(Number(new URL(base).port)),'Never test the operational server');
 const actors=(process.env.OMNISVERA_SHEET_QA_ACTORS||'vezemir,morthak,raziel,dorn7').split(',');
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-sheet-readiness-'));
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[];
 try{
  for(const [role,actor,width] of [['gm','morthak',1440],['morthak','morthak',390],['gm','vezemir',390],['vezemir','vezemir',360],['raziel','raziel',390],['gm','dorn7',390]]){
   if(!actors.includes(actor))continue;
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.addInitScript(({role,actor})=>{
    localStorage.setItem('omnisvera_access_token','cf01-local-'+role);
    localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');
    localStorage.setItem('omnisvera_selected_character',actor);
   },{role,actor});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   await page.locator(`button[data-character="${actor}"]`).click();
   const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
   const identity=panel.locator('.workspace-character-identity');
   assert.equal(await identity.locator('.workspace-action-catalog').count(),0,'Progression must not be nested inside identity header');
   const pending=panel.getByRole('region',{name:'Progressão pendente'});
   const metrics=await pending.count()?await pending.evaluate(el=>{
    const box=el.getBoundingClientRect();return {width:box.width,overflow:el.scrollWidth>el.clientWidth+1,rows:[...el.querySelectorAll('article')].map(row=>{
     const text=row.querySelector('span').getBoundingClientRect(),button=row.querySelector('button').getBoundingClientRect(),r=row.getBoundingClientRect();
     return {width:r.width,textWidth:text.width,overlap:text.right>button.left+1&&text.top<button.bottom&&button.top<text.bottom,overflow:row.scrollWidth>row.clientWidth+1,buttonHeight:button.height};
    })};
   }):{width:0,rows:[]};
   if(metrics.rows.length)assert.ok(metrics.width>250&&!metrics.overflow,'Pending HP section has usable width');
   for(const row of metrics.rows){assert.ok(row.textWidth>100&&!row.overlap&&!row.overflow,'HP labels and roll buttons cannot overlap');assert.ok(row.buttonHeight>=36,'Touch-sized roll button');}
   if(actor==='morthak'||actor==='vezemir'){
    const specialization=panel.locator('.workspace-identity-tags');
    const title=actor==='morthak'?'Necromante':'Especialista em Armas';
    await specialization.getByRole('button',{name:title,exact:true}).waitFor();
    assert.equal(await panel.getByRole('region',{name:'Especialização',exact:true}).count(),0,'No duplicate specialization management section on the sheet');
    assert.ok(!(await specialization.innerText()).includes('Benefícios'),'Identity has only the specialization summary trigger');
    if(actor==='morthak'){
     await specialization.getByRole('button',{name:'Necromante',exact:true}).click();
     const detail=page.getByRole('dialog',{name:'Necromante',exact:true});await detail.waitFor();
     const text=await detail.innerText();assert.match(text,/Toque Sombrio/);assert.match(text,/Aterrorizar/);
     assert.equal(await detail.getByRole('button',{name:'Escolher',exact:true}).count(),0,'Summary is not a nested selection menu');
     await detail.getByRole('button',{name:'Fechar descrição',exact:true}).click();assert.equal(await detail.count(),0);
     assert.ok(await panel.getByRole('button',{name:'Toque Sombrio',exact:true}).count(),'Existing combat spell card is still accessible');
    }
   }
   if(actor==='vezemir'||actor==='raziel')assert.equal(await panel.getByRole('button',{name:'Salvar máximo',exact:true}).count(),0,'Maximum HP editor removed from the gameplay sheet');
   if(actor==='dorn7'){
    for(const name of ['Levitação','Escuridão'])assert.equal(await panel.getByRole('button',{name,exact:true}).count(),0,'Retired Dorn spell hidden');
    assert.equal(await panel.getByText(/(?:Levitação|Escuridão) · preparada/).count(),0,'Retired prepared resources hidden too');
    const guard=panel.locator('article.workspace-spell-card').filter({hasText:'Protocolo de Guarda'});
    assert.equal(await guard.locator('input[type="checkbox"]').count(),0);
    if(await guard.getByRole('button',{name:'Usar',exact:true}).count())assert.equal(await guard.getByRole('button',{name:'Ativar Guarda',exact:true}).count(),0);
    assert.equal(await panel.getByText(/Magias ativas ·/).count(),0);
   }
   await panel.screenshot({path:path.join(output,`${role}-${actor}-${width}.png`)});
   checks.push({role,actor,width,pending:metrics});await context.close();
  }
  assert.ok(checks.length,'At least one supported actor must be tested');assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
