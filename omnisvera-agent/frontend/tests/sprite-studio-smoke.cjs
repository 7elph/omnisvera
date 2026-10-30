// End-to-end Sprite Studio on the native TEMP fixture. Never live credentials/data.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const response=await api[method](url,{data});assert.ok(response.ok(),`${method} ${url}: ${await response.text()}`);return response.json();};
 const health=await call('get','/health');assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-sprite-studio-')),screenshots=[],errors=[],checks=[];let browser,context,page;
 const deadline=setTimeout(()=>{console.error('Sprite smoke deadline');void browser?.close().finally(()=>process.exit(1));},280000);deadline.unref();
 try{
  let combat=await call('get','/combat/effects');if(combat.encounter?.active)await call('post','/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
  const map=(await call('get','/workspace/maps')).find(m=>/nimalis/i.test(m.title));assert.ok(map);
  await call('patch',`/gm/workspace/maps/${encodeURIComponent(map.id)}/visibility`,{visible_to_players:true});await call('patch','/gm/workspace/maps/active',{map_id:map.id});
  let grid=(await call('get','/workspace')).map?.grid;
  if(!grid){const result=await call('post',`/workspace/maps/${encodeURIComponent(map.id)}/grid`,{request_id:randomUUID(),expected_version:0,cols:32,rows:24,cell_size_m:1.5,origin_x:0,origin_y:0,distance_rule:'chebyshev'});grid=result.grid;}
  const snapshot=await call('get','/workspace');let dorn=snapshot.tokens.find(t=>t.character_id==='dorn7');
  if(!dorn)dorn=await call('post','/gm/workspace/tokens',{token_type:'character',character_id:'dorn7',name:'Dorn',latitude:35,longitude:35,map_id:map.id,visible_to_players:true});
  // Keep the visual subject away from the fixture's pre-existing pile of pins.
  const placed=(await call('get','/workspace')).tokens.find(t=>t.id===dorn.id),start=placed.grid_position;
  const setupPath=[[start.cell_x,start.cell_y]];let [x,y]=setupPath[0];
  while(x!==8||y!==8){if(x!==8)x+=Math.sign(8-x);else y+=Math.sign(8-y);setupPath.push([x,y]);}
  await call('post',`/workspace/maps/${encodeURIComponent(map.id)}/move`,{request_id:randomUUID(),token_id:dorn.id,mode:'GM_REPOSITION',path:setupPath,expected_position_version:start.version,expected_grid_version:grid.version});
  const before=await call('get','/characters/dorn7');
  // Reuse installed Chrome on Windows; do not download a heavyweight test browser.
  browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'chrome':undefined});context=await browser.newContext({viewport:{width:1440,height:1100}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  page=await context.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  const nav=page.getByRole('navigation',{name:'Navegação principal'});
  async function openStudio(){await nav.getByRole('button',{name:/Mapas$/}).click();const details=page.locator('details').filter({has:page.locator('summary').filter({hasText:/^Sprite Studio$/})}).first();if(!(await details.getAttribute('open')))await details.locator('summary').first().click();await page.getByRole('region',{name:'Sprite Studio',exact:true}).waitFor();return page.getByRole('region',{name:'Sprite Studio',exact:true});}
  let studio=await openStudio();await studio.getByRole('button',{name:'Exemplo de Dorn',exact:true}).click();
  await studio.getByRole('status').filter({hasText:'Arte de teste derivada'}).waitFor();
  await studio.getByLabel('Importar PNG').setInputFiles({name:'bad.png',mimeType:'image/png',buffer:Buffer.from('invalid')});
  await studio.getByRole('alert').filter({hasText:'PNG válido'}).waitFor();
  await studio.getByLabel('Importar PNG').setInputFiles(path.resolve('public/companion-assets/sprites/dorn-demo-v1.png'));
  await page.waitForFunction(()=>document.querySelector('[aria-label="Nome do sprite"]')?.value==='dorn-demo-v1');
  await studio.getByLabel('Nome do sprite').fill('Dorn sprite ensaio');
  await studio.getByLabel('Largura do quadro',{exact:true}).fill('128');await studio.getByLabel('Altura do quadro',{exact:true}).fill('168');
  await studio.getByRole('button',{name:'Separar quadros',exact:true}).click();
  for(const n of [1,2,3,4])await studio.getByRole('button',{name:'Quadro '+n,exact:true}).click();
  await studio.getByRole('button',{name:'Usar seleção nesta animação',exact:true}).click();
  for(const n of [1,2,3,4])await studio.getByRole('button',{name:'Quadro '+n,exact:true}).click();
  await studio.getByLabel('Estado da animação').selectOption('walk_down');
  for(const n of [5,6,7,8])await studio.getByRole('button',{name:'Quadro '+n,exact:true}).click();
  await studio.getByRole('button',{name:'Usar seleção nesta animação',exact:true}).click();await studio.getByLabel('FPS',{exact:true}).fill('7');
  await studio.getByRole('button',{name:'Salvar sprite',exact:true}).click();await studio.getByRole('status').filter({hasText:'Sprite salvo'}).waitFor();
  const asset=(await call('get','/gm/sprites')).find(a=>a.name==='Dorn sprite ensaio');assert.ok(asset);assert.equal(asset.metadata.animations.walk_down.frames.length,4);
  assert.equal(asset.metadata.canvas_width,128);assert.equal(asset.metadata.canvas_height,168);
  await studio.getByLabel('Associar sprite',{exact:true}).selectOption('character:dorn7');await studio.getByRole('button',{name:'Associar',exact:true}).click();await studio.getByRole('status').filter({hasText:'associado'}).waitFor();
  let pin=page.locator(`[data-grid-token="${dorn.id}"]`),canvas=pin.locator('canvas');await canvas.waitFor();await canvas.scrollIntoViewIfNeeded();
  await page.waitForFunction(id=>{const c=document.querySelector(`[data-grid-token="${id}"] canvas`);return c?.dataset.frame!==undefined;},dorn.id);
  const frames=new Set();for(let i=0;i<7;i++){frames.add(await canvas.getAttribute('data-frame'));await page.waitForTimeout(120);}assert.ok(frames.size>1,'Idle changes real source frames');
  for(let i=0;i<10;i++)await page.getByRole('button',{name:'Aumentar zoom',exact:true}).click();
  await canvas.scrollIntoViewIfNeeded();
  await canvas.screenshot({path:path.join(output,'dorn-idle-zoom.png')});screenshots.push(path.join(output,'dorn-idle-zoom.png'));
  await page.screenshot({path:path.join(output,'dorn-map-desktop.png')});screenshots.push(path.join(output,'dorn-map-desktop.png'));
  checks.push('import sample PNG','slice and order frames','idle and walk preview','save and native binding','animated idle on real copied Nimalis');
  const ws=await call('get','/workspace');const current=ws.tokens.find(t=>t.id===dorn.id);const position=current.grid_position;assert.ok(position);
  const end=[position.cell_x,position.cell_y<grid.rows-1?position.cell_y+1:position.cell_y-1];
  const command={request_id:randomUUID(),token_id:dorn.id,mode:'GM_REPOSITION',path:[[position.cell_x,position.cell_y],end],expected_position_version:position.version,expected_grid_version:ws.map.grid.version};
  await page.evaluate(async({base,map,command})=>{const r=await fetch(base+`/workspace/maps/${encodeURIComponent(map)}/move`,{method:'POST',headers:{'X-Omnisvera-Token':'cf01-local-gm','Content-Type':'application/json'},body:JSON.stringify(command)});if(!r.ok)throw new Error(await r.text());},{base,map:map.id,command});
  await page.waitForFunction(id=>document.querySelector(`[data-grid-token="${id}"] canvas`)?.dataset.state?.startsWith('walk_'),dorn.id,{timeout:12000});
  await canvas.screenshot({path:path.join(output,'dorn-walking.png')});screenshots.push(path.join(output,'dorn-walking.png'));
  await page.waitForFunction(id=>document.querySelector(`[data-grid-token="${id}"] canvas`)?.dataset.state==='idle',dorn.id);
  const moved=(await call('get','/workspace')).tokens.find(t=>t.id===dorn.id);assert.equal(moved.grid_position.cell_y,end[1]);
  const after=await call('get','/characters/dorn7');assert.deepEqual(after.state,before.state,'Visual studio must not alter sheet');
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();studio=await openStudio();pin=page.locator(`[data-grid-token="${dorn.id}"]`);await pin.locator('canvas').waitFor();
  checks.push('confirmed native move shows walk then idle','logical position persisted','reload retains association','Dorn sheet unchanged');
  await context.close();context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-raziel');localStorage.setItem('omnisvera_access_mode','player');});
  page=await context.newPage();page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Sessão$/}).click();canvas=page.locator(`[data-grid-token="${dorn.id}"] canvas`);await canvas.waitFor();await canvas.scrollIntoViewIfNeeded();
  assert.equal(await page.getByRole('region',{name:'Sprite Studio',exact:true}).count(),0);
  const staticPins=await page.locator('.workspace-map-token:not(:has(canvas))').count();assert.ok(staticPins>0,'Other tokens retain static renderer');
  await page.screenshot({path:path.join(output,'dorn-map-player-mobile.png')});screenshots.push(path.join(output,'dorn-map-player-mobile.png'));
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),'No page horizontal overflow');
  checks.push('mobile player visible sprite','other pins static','GM studio hidden from player');
  const mobilePosition=(await call('get','/workspace')).tokens.find(t=>t.id===dorn.id).grid_position;
  for(let i=0;i<5;i++)await page.getByRole('button',{name:'Aumentar zoom',exact:true}).click();
  assert.deepEqual((await call('get','/workspace')).tokens.find(t=>t.id===dorn.id).grid_position,mobilePosition);
  await canvas.scrollIntoViewIfNeeded();await canvas.screenshot({path:path.join(output,'dorn-mobile-zoom.png')});screenshots.push(path.join(output,'dorn-mobile-zoom.png'));
  checks.push('desktop/mobile zoom preserves logical position');
  await page.route('**/workspace/sprites/**',route=>route.abort());
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Sessão$/}).click();
  await page.locator(`[data-grid-token="${dorn.id}"] img`).waitFor();
  checks.push('failed atlas fetch restores static portrait');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots,visual_acceptance:'pending_agent_image_review',production_modified:false}));
 }catch(error){if(page)await page.screenshot({path:path.join(output,'failure.png'),timeout:5000}).catch(()=>{});console.error(JSON.stringify({status:'FAIL',reason:error.message,evidence:output}));throw error;}
 finally{clearTimeout(deadline);await context?.close();await browser?.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
