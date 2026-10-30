// Uses only the existing isolated fixture; no gameplay commands are issued.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-action-reference-'));
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  const page=await context.newPage(),errors=[],commands=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('request',request=>{if(!['GET','HEAD'].includes(request.method())&&/\/attacks\/|\/techniques\/|\/characters\/[^/]+\/state|\/gm\/combat\/effects|\/vines/.test(request.url()))commands.push(request.url());});
  await page.goto('http://127.0.0.1:8871');await page.locator('.app-shell.authenticated').waitFor();
  await page.locator('.gm-tools-tab').click();
  await page.locator('summary').filter({hasText:'Cola de ações'}).click();
  const reference=page.getByRole('region',{name:'Cola de ações',exact:true});await reference.waitFor();
  const select=reference.getByRole('combobox',{name:'Personagem da cola de ações'});
  await select.selectOption('morthak');
  await reference.getByRole('button',{name:'Mísseis Mágicos',exact:true}).waitFor();
  const allOptions=await reference.locator('article').count();
  await reference.getByRole('searchbox',{name:'Buscar habilidade ou magia'}).fill('misseis');
  const matchingOptions=await reference.locator('article').count();assert.ok(matchingOptions>0&&matchingOptions<allOptions);
  await reference.getByRole('button',{name:'Mísseis Mágicos',exact:true}).click();
  const detail=page.getByRole('dialog',{name:'Mísseis Mágicos',exact:true});await detail.waitFor();
  assert.ok((await detail.innerText()).length>50);await detail.getByRole('button',{name:'Fechar descrição'}).click();
  await reference.getByRole('searchbox',{name:'Buscar habilidade ou magia'}).fill('');
  await select.selectOption('vezemir');
  await reference.getByRole('button',{name:'Força Arcana',exact:true}).waitFor();
  assert.equal(await reference.getByRole('button',{name:'Mísseis Mágicos',exact:true}).count(),0);
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===390?844:1000});await reference.scrollIntoViewIfNeeded();
   assert.ok(await reference.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'Reference overflow');
   await reference.screenshot({path:path.join(output,`reference-${width}.png`)});
   await reference.getByRole('button',{name:'Força Arcana',exact:true}).click();
   const ability=page.getByRole('dialog',{name:'Força Arcana',exact:true});await ability.waitFor();
   assert.ok(await ability.evaluate(el=>{const r=el.getBoundingClientRect();return r.width>200&&r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;}),'Detail outside viewport');
   await ability.screenshot({path:path.join(output,`detail-${width}.png`)});
   await ability.getByRole('button',{name:'Fechar descrição'}).click();
  }
  await select.selectOption('');assert.equal(await reference.getByText('Carregando ações…').count(),0);
   await page.getByRole('button',{name:'Filtros do registro',exact:true}).click();
   const filters=page.getByRole('region',{name:'Filtros do registro'});
  await filters.getByRole('combobox',{name:'Tipo de registro'}).selectOption('actions');
  const log=page.locator('.workspace-timeline');await log.getByRole('button',{name:'Ver resultado',exact:true}).first().waitFor();
  assert.equal(await log.locator('article.message').count(),0);
  await log.getByRole('button',{name:'Ver resultado',exact:true}).first().click();
  const result=page.getByRole('dialog',{name:/^Resultado:/});await result.waitFor();assert.ok((await result.innerText()).length>35);
  await result.getByRole('button',{name:'Fechar descrição'}).click();
  await filters.getByRole('searchbox',{name:'Buscar no registro'}).fill('sem-correspondencia-123456');
  await page.getByText('Nenhum registro corresponde aos filtros.',{exact:true}).waitFor();
  await filters.getByRole('button',{name:'Limpar filtros'}).click();assert.ok(await log.locator('article').count()>0);
  assert.deepEqual(commands,[]);assert.deepEqual(errors,[]);
  console.log('PASS: current-sheet references, search, actor switch, read-only cards, action results, filters, desktop/mobile. SCREENSHOTS='+output);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
