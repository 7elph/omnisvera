// Isolated built frontend; read-only UI interactions, fixture credentials only.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-specialization-layout-'));
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const base=process.env.OMNISVERA_SHEET_QA_URL||'http://127.0.0.1:8871';
  assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
  await page.goto(base);
  await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('button',{name:'Abrir ficha de Vezemir',exact:true}).click();
  const section=page.locator('.workspace-identity-tags');
  await section.getByText('Especialista em Armas',{exact:true}).waitFor();
  for(const size of [{width:1440,height:1000},{width:1024,height:768},{width:390,height:844}]){
   await page.setViewportSize(size);await section.scrollIntoViewIfNeeded();
   await section.screenshot({path:path.join(output,`specialization-${size.width}.png`)});
   const metrics=await section.evaluate(el=>{
    const r=el.getBoundingClientRect(),cards=[...el.querySelectorAll(':scope > article')];
    return {overflow:el.scrollWidth>el.clientWidth+1,cards:cards.map(card=>{
      const c=card.getBoundingClientRect(),header=(card.querySelector('.workspace-specialization-heading > button') || card.querySelector('strong'))?.getBoundingClientRect();
      return {width:c.width,left:c.left-r.left,right:c.right-r.right,headerWidth:header?.width,scroll:card.scrollWidth,client:card.clientWidth};
    })};
   });
   console.log(size.width,JSON.stringify(metrics));
   assert.ok(!metrics.overflow,'Section horizontal overflow');
   for(const c of metrics.cards){assert.ok(c.right<=1&&c.left>=-1,'Card outside section');assert.ok(c.scroll<=c.client+1,'Card overflow');assert.ok(c.headerWidth>100,'Specialization heading cramped');}
  }
  await section.getByRole('button',{name:'Especialista em Armas',exact:true}).click();
  const detail=page.getByRole('dialog',{name:'Especialista em Armas',exact:true});
  await detail.waitFor();
  assert.ok((await detail.innerText()).includes('Benefícios:'));
  await detail.getByRole('button',{name:'Fechar descrição',exact:true}).click();
  assert.equal(await detail.count(),0);
  assert.deepEqual(errors,[]);console.log('PASS: desktop 1440/1024 and mobile specialization layout. SCREENSHOTS='+output);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
