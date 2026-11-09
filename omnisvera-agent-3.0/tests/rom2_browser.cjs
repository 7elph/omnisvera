const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.env.COMPANION3_FIXTURE,'utf8'));assert.equal(fixture.synthetic,true);
 const base=process.env.COMPANION3_URL;assert.equal(new URL(base).hostname,'127.0.0.1');
 const report={checks:[],errors:[],screenshots:[]};
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-unsafe-swiftshader']});
 try {
 const gm=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
 const route='/gm/sessions/'+fixture.session_id+'/status';
 const forbidden=await player.post(route,{data:{status:'planned'}});assert.ok([401,403].includes(forbidden.status()));
 for(const status of ['planned','active','paused','active','completed']){
  const r=await gm.post(route,{data:{status}});assert.equal(r.status(),200);assert.equal((await r.json()).status,status);
 }
 const record=await player.get('/sessions/'+fixture.session_id);assert.equal(record.status(),200);assert.ok(!(await record.text()).includes('GM_PRIVATE_SESSION_COMPANION3'));
 const start=await gm.post(route,{data:{status:'active'}});assert.equal(start.status(),200);
 const selectionRoute='/gm/scenes/'+fixture.preparation_id+'/selection-on-table';
 const selection={request_id:'native-preparation-selection-once',element_ids:[fixture.preparation_elements[0]],token_ids:[fixture.preparation_pins[0]],include_map:false};
 const deniedSelection=await player.post(selectionRoute,{data:selection});assert.ok([401,403].includes(deniedSelection.status()));
 const sent=await gm.post(selectionRoute,{data:selection});assert.equal(sent.status(),200);assert.equal((await sent.json()).created,true);
 const replay=await gm.post(selectionRoute,{data:selection});assert.equal(replay.status(),200);assert.equal((await replay.json()).created,false);
 const publicScene=await player.get('/scenes/'+fixture.preparation_id);assert.equal(publicScene.status(),200);
 const visible=await publicScene.json();assert.deepEqual(visible.elements.map(e=>e.id),[fixture.preparation_elements[0]]);
 assert.ok(!JSON.stringify(visible).includes('PRIVATE_'));
 const pins=await player.get('/workspace?map_id='+encodeURIComponent(fixture.public_map));const visiblePins=(await pins.json()).tokens.map(t=>t.id);
 assert.ok(visiblePins.includes(fixture.preparation_pins[0]));assert.ok(!visiblePins.includes(fixture.preparation_pins[1]));
 const finish=await gm.post(route,{data:{status:'completed'}});assert.equal(finish.status(),200);
 report.checks.push('Selective scene publication: selected clue/pin only, private notes hidden, player denied, replay does not duplicate');
 await gm.dispose();await player.dispose();report.checks.push('GM session lifecycle persists through reviewed proxy; player denied and private notes protected');
 for(const mobile of [false,true]){
  const context=await browser.newContext({viewport:mobile?{width:844,height:390}:{width:1440,height:900},isMobile:mobile,hasTouch:mobile});
  const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
  page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Invalid call|Failed to load script/.test(m.text()))report.errors.push(m.text())});
  const loaded=page.waitForResponse(r=>r.url().includes('/characters/dorn7?read_only=true')&&r.status()===200,{timeout:90000});
  await page.goto(base+'/#token=cf01-local-gm');await page.locator('#loading').waitFor({state:'detached',timeout:90000});await loaded;
  await page.waitForTimeout(1200);
  if(!mobile){
   const moved=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST',{timeout:30000});
   for(let i=0;i<10;i++){await page.mouse.wheel(0,300);await page.waitForTimeout(40)}
   await page.mouse.click(1400,400);const response=await moved;assert.equal(response.status(),200);
   assert.equal(response.request().postDataJSON().token_id,fixture.pins.dorn7);
   assert.ok(response.request().postDataJSON().path.at(-1)[0]>70,'Dorn reaches far edge beyond old 30-cell limit');
   report.checks.push('Dorn point-and-click submits authorized movement to isolated backend; HTTP 200');
   await page.waitForTimeout(2500);
  }
  for(const [name,x,y] of [['map',0,0],['sheet',38,mobile?79:218],['editor',38,mobile?253:566]]){
   if(x){await page.keyboard.press('Escape');if(mobile)await page.touchscreen.tap(x,y);else await page.mouse.click(x,y);await page.waitForTimeout(500)}
   const file=path.join(fixture.directory,`rom2-${mobile?'mobile':'desktop'}-${name}.png`);await page.screenshot({path:file});report.screenshots.push(file);
  }
  report.checks.push(`${mobile?'mobile landscape':'desktop'}: WebGL starts, authorized Dorn data loads, drawer interactions captured`);
  await context.close();
 }
 assert.deepEqual(report.errors,[]);report.status='PASS';
 }finally{await browser.close();fs.writeFileSync(path.join(fixture.directory,'rom2-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
