const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const f=JSON.parse(fs.readFileSync(process.env.COMPANION3_FIXTURE,'utf8'));assert.equal(f.synthetic,true);
 const base=process.env.COMPANION3_URL;assert.equal(new URL(base).hostname,'127.0.0.1');
 const report={status:'RUNNING',checks:[],errors:[]};
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-unsafe-swiftshader']});
 const gm=await request.newContext({baseURL:'http://127.0.0.1:8891',extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-morthak'}});
 const call=async(api,method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json()};
 try{
  // The synthetic sheet starts uninitialized; match existing campaign sheets
  // before checking that grid/placement preserve the established resources.
  await call(gm,'get','/characters/morthak?read_only=false');
  const before=await call(player,'get','/workspace');assert.equal(before.map.id,f.public_map);
  assert.equal(before.map.grid,undefined);assert.equal(before.tokens.some(t=>t.character_id==='morthak'),false);
  const sheet=await call(player,'get','/characters/morthak?read_only=true');assert.ok(sheet.state);
  const context=await browser.newContext({viewport:{width:844,height:390},isMobile:true,hasTouch:true});const page=await context.newPage();
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Invalid call/.test(m.text()))report.errors.push(m.text())});
  const ready=page.waitForResponse(r=>r.url().includes('/characters/morthak?read_only=true')&&r.status()===200,{timeout:60000});
  await page.goto(base+'/#token=cf01-local-morthak');await page.locator('#loading').waitFor({state:'detached',timeout:90000});await ready;
  await page.waitForTimeout(500);await page.screenshot({path:path.join(f.directory,'login-missing-map-pin.png')});
  await page.touchscreen.tap(38,108);await page.waitForTimeout(400);await page.screenshot({path:path.join(f.directory,'login-sheet-still-available.png')});
  await page.keyboard.press('Escape');
  await call(gm,'post','/workspace/maps/'+encodeURIComponent(f.public_map)+'/grid',
   {request_id:'fixture-login-grid',expected_version:0,cols:32,rows:24,cell_size_m:1,origin_x:0,origin_y:0,distance_rule:'chebyshev'});
  const placed=page.waitForResponse(async r=>{
   if(!r.url().endsWith('/workspace')||r.status()!==200)return false;
   try{return (await r.json()).tokens.some(t=>t.character_id==='morthak'&&t.grid_position)}catch{return false}
  },{timeout:30000});
  const pin=await call(gm,'post','/gm/workspace/tokens',{token_type:'character',character_id:'morthak',name:'Morthak',map_id:f.public_map,
   latitude:100*5.5/24,longitude:100*16.5/32,visible_to_players:true});
  await placed;await page.waitForTimeout(700);await page.screenshot({path:path.join(f.directory,'login-recovered-without-refresh.png')});
  const move=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
  await page.touchscreen.tap(370,221);const moved=await move;assert.equal(moved.status(),200);assert.equal(moved.request().postDataJSON().token_id,pin.id);
  await page.waitForTimeout(700);await page.screenshot({path:path.join(f.directory,'login-recovered-movement.png')});
  const master=await call(gm,'get','/workspace');assert.equal(master.map.id,f.private_map);
  const after=await call(player,'get','/characters/morthak?read_only=true');
  for(const key of ['current_hp','maximum_hp','resources','coins','conditions'])assert.deepEqual(after.state[key],sheet.state[key]);
  assert.deepEqual(after.inventory,sheet.inventory);
  const maps=await call(player,'get','/workspace/maps');assert.equal(maps.some(m=>m.id===f.private_map),false);
  assert.deepEqual(report.errors,[]);report.status='PASS';
  report.checks.push('private GM map remains private; player receives public legacy map',
   'missing grid/pin produces guidance and leaves own sheet available',
   'native grid and placement recover the sprite and camera without refreshing',
   'Morthak player then moves only his own token; HP, resources, coins and inventory preserved');
 }finally{
  await browser.close();await gm.dispose();await player.dispose();
  fs.writeFileSync(path.join(f.directory,'login-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1});
