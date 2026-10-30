// Real built frontend and native rest commands, exclusively in the TEMP fixture.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const command=async(action,payload={})=>{const r=await api.post('/gm/combat/effects',{data:{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload}});assert.ok(r.ok(),await r.text());return r.json();};
 assert.ok(path.resolve((await get('/health')).database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 if((await get('/combat/effects')).encounter?.active)await command('end');
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-rest-toolbar-'));
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);
   await page.locator('.app-shell.authenticated').waitFor();const nav=page.getByRole('navigation',{name:'Navegação principal'});
   await nav.getByRole('button',{name:/Mesa$/}).click();const zoom=page.getByRole('button',{name:'Aumentar zoom',exact:true});await zoom.waitFor();
   const geometry=await page.locator('.workspace-map-zoom').evaluate(el=>({direction:getComputedStyle(el).flexDirection,overflow:el.scrollWidth>el.clientWidth+2,rect:el.getBoundingClientRect().toJSON(),children:[...el.children].map(c=>c.getBoundingClientRect().toJSON())}));
   assert.equal(geometry.direction,'row');assert.ok(!geometry.overflow);assert.ok(geometry.rect.height<60);
   assert.ok(Math.max(...geometry.children.map(r=>r.y))-Math.min(...geometry.children.map(r=>r.y))<20);
   assert.equal(await page.getByRole('combobox',{name:'Entidade no grid'}).count(),0);
   assert.equal(await page.getByRole('button',{name:/Mover uma célula/}).count(),0);
   assert.equal(await page.getByText('Mover no grid',{exact:true}).count(),0);
   const adjust=page.getByRole('button',{name:'Ajustar',exact:true});if(await adjust.isEnabled())await adjust.click();
   const workspace=await get('/workspace'),grid=workspace.map.grid;assert.ok(grid);
   const token=await post('/gm/workspace/tokens',{token_type:'monster',map_id:workspace.map.id,name:'Ensaio arrastar '+width,current_hp:20,maximum_hp:20,visible_to_players:true,latitude:10,longitude:80,sheet:{movement:'9 m'}});
   const pin=page.locator(`[data-grid-token="${token.id}"]`);await pin.waitFor({timeout:30000});await pin.scrollIntoViewIfNeeded();
   const position=(await get('/workspace')).tokens.find(t=>t.id===token.id).grid_position;
   const box=await pin.boundingBox(),stage=await page.locator('.workspace-map-stage').boundingBox();
   const start={x:box.x+box.width/2,y:box.y+box.height/2},end={x:start.x+stage.width/grid.cols,y:start.y};
   const reply=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
   if(width===390){
    const touch=await context.newCDPSession(page);
    await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[start]});
    for(let step=1;step<=5;step++)await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:start.x+(end.x-start.x)*step/5,y:start.y}]});
    await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await touch.detach();
   }else{await page.mouse.move(start.x,start.y);await page.mouse.down();await page.mouse.move(end.x,end.y,{steps:5});await page.mouse.up();}
   const response=await reply;assert.ok(response.ok(),await response.text());const moved=await response.json();
   assert.equal(moved.position.cell_x,position.cell_x+1);assert.equal(moved.position.cell_y,position.cell_y);
   await page.reload();await page.locator(`[data-grid-token="${token.id}"]`).waitFor();
   assert.equal((await get('/workspace')).tokens.find(t=>t.id===token.id).grid_position.cell_x,position.cell_x+1);
   if(width===390){
    const canvas=page.locator('.workspace-map-canvas'),before=await canvas.boundingBox();
    for(let i=0;i<11;i++)await page.getByRole('button',{name:'Aumentar zoom',exact:true}).click();
    const after=await canvas.boundingBox();assert.ok(Math.abs(after.height-before.height)<3,'Zoom must not grow the mobile viewport');
    const extent=await canvas.evaluate(el=>({scroll:el.scrollWidth,width:el.clientWidth,page:document.documentElement.scrollWidth,screen:innerWidth}));
    assert.ok(extent.scroll>extent.width);assert.ok(extent.page<=extent.screen+2,'Map must not widen the document');
    await page.getByRole('button',{name:'Diminuir zoom',exact:true}).click();
    await nav.getByRole('button',{name:/Mestre$/}).click();
    await page.getByRole('button',{name:/Descanso geral/}).waitFor();
    await nav.getByRole('button',{name:/Mesa$/}).click();
   }
   await page.locator('.workspace-map-panel').screenshot({path:path.join(output,`map-${width}.png`)});
   await context.close();
  }
  const actors=['vezemir','morthak','raziel','dorn7'];
  for(const [index,id] of actors.entries())await command('apply',{target_type:'character',target_id:id,label:'Velocidade',source:'Ensaio de descanso',duration:index%2?'manual':'rounds',rounds:3,modifiers:{attack_bonus:2}});
  const context=await browser.newContext({viewport:{width:390,height:900}});await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mestre$/}).click();
  const rest=page.getByRole('button',{name:/Descanso geral/});await rest.waitFor();await rest.click();
  await page.waitForFunction(()=>!document.querySelector('button.workspace-action-card:disabled')?.textContent.includes('Descanso geral'));
  await new Promise(async(resolve,reject)=>{const deadline=Date.now()+30000;while(Date.now()<deadline){if(!(await get('/combat/effects')).effects.some(e=>e.target_type==='character'&&actors.includes(e.target_id)))return resolve();await new Promise(r=>setTimeout(r,250));}reject(new Error('Full rest did not clear all character effects'));});
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();assert.equal((await get('/combat/effects')).effects.filter(e=>e.target_type==='character'&&actors.includes(e.target_id)).length,0);
  await page.screenshot({path:path.join(output,'rest-reload-390.png'),fullPage:true});assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['horizontal zoom desktop/mobile','no movement arrows or entity selector','native mouse/touch drag and reload','general rest clears four actors','reload keeps effects cleared'],screenshots:output,production_modified:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
