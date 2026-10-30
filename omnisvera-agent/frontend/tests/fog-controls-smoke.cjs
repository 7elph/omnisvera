// Only disposable loopback fixture; never operational credentials or fog.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_FOG_QA_URL||process.env.OMNISVERA_SHEET_QA_URL||'http://127.0.0.1:8874';
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const health=await (await api.get('/health')).json();assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-fog-visible-')),errors=[];
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/media/**',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960"><rect width="1280" height="960" fill="#202530"/></svg>'}));
  const openMaps=async()=>{await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mapas$/}).click();await page.locator('.workspace-fog-section').waitFor();};
  await openMaps();await page.waitForFunction(()=>document.querySelector('[aria-label="Editar fog do mapa atual"]')?.disabled===false);
  const fog=page.locator('.workspace-fog-section');
  assert.equal(await fog.getAttribute('open'),'');
  assert.ok(await fog.getByRole('button',{name:'Pintar névoa',exact:true}).isVisible());
  const metrics=await fog.evaluate(el=>({top:el.getBoundingClientRect().top,library:document.querySelector('.workspace-map-management').getBoundingClientRect().top}));
  assert.ok(metrics.top<metrics.library&&metrics.top<600,'Fog is before library in the first screen');
  await page.screenshot({path:path.join(output,'desktop.png')});
  await fog.getByRole('button',{name:'Pintar névoa',exact:true}).click();
  const overlay=page.locator('.workspace-map-fog.editor');await overlay.scrollIntoViewIfNeeded();
  const box=await overlay.boundingBox();assert.ok(box&&box.width>100);
  const savedResponse=page.waitForResponse(r=>r.url().endsWith('/gm/workspace/fog')&&['POST','PATCH'].includes(r.request().method()));
  await page.mouse.move(box.x+12,box.y+12);await page.mouse.down();await page.mouse.up();
  const response=await savedResponse;assert.ok(response.ok(),await response.text());
  const saved=await response.json();assert.ok(Object.keys(saved.mist_density).length>0);
  await openMaps();const refreshed=await (await api.get('/workspace')).json();assert.deepEqual(refreshed.fog.exploration.mist_density,saved.mist_density);
  await page.setViewportSize({width:390,height:844});await fog.scrollIntoViewIfNeeded();
  for(const name of ['Pintar névoa','Apagar névoa']){const b=fog.getByRole('button',{name,exact:true});assert.ok(await b.isVisible());const bounds=await b.boundingBox();assert.ok(bounds.x>=0&&bounds.x+bounds.width<=391);}
  await page.screenshot({path:path.join(output,'mobile.png')});
  const owner=await browser.newContext();await owner.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-morthak');localStorage.setItem('omnisvera_access_mode','player');});
  const ownerPage=await owner.newPage();await ownerPage.goto(base);await ownerPage.locator('.app-shell.authenticated').waitFor();assert.equal(await ownerPage.locator('.workspace-fog-tools').count(),0);
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',desktop:true,mobile:true,fog_save_reload:true,gm_only:true,screenshots:output}));
 }finally{await browser.close();await api.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
