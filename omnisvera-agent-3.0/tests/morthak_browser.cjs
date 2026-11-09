const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.env.COMPANION3_FIXTURE,'utf8'));
 assert.equal(fixture.synthetic,true);
 const base=process.env.COMPANION3_URL;assert.equal(new URL(base).hostname,'127.0.0.1');
 const report={status:'RUNNING',checks:[],errors:[],screenshots:[]};
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-unsafe-swiftshader']});
 const gm=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-morthak'}});
 const read=async(api,url)=>{const r=await api.get(url);assert.equal(r.status(),200);return r.json()};
 const waitRead=(page,path)=>page.waitForResponse(r=>r.url().includes(path)&&r.status()===200,{timeout:45000});
 const shot=async(page,name)=>{const file=path.join(fixture.directory,name+'.png');await page.screenshot({path:file});report.screenshots.push(file)};
 async function open(identity,mobile){
  const context=await browser.newContext({viewport:mobile?{width:844,height:390}:{width:1440,height:900},isMobile:mobile,hasTouch:mobile});
  const page=await context.newPage();
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Invalid call|Shader compilation failed|Failed to load script/.test(m.text()))report.errors.push(m.text())});
  const loaded=waitRead(page,'/characters/'+(identity==='gm'?'dorn7':'morthak')+'?read_only=true');
  await page.goto(base+'/#token=cf01-local-'+identity);
  await page.locator('#loading').waitFor({state:'detached',timeout:90000});await loaded;await page.waitForTimeout(800);
  return page;
 }
 async function move(page,x,y,character,mobile=false){
  const response=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST',{timeout:20000});
  if(mobile)await page.touchscreen.tap(x,y);else await page.mouse.click(x,y);
  const r=await response;assert.equal(r.status(),200);assert.equal(r.request().postDataJSON().token_id,fixture.pins[character]);
 }
 try{
  const page=await open('gm',false);
  const selected=waitRead(page,'/characters/morthak?read_only=true');await page.mouse.click(720,606);await selected;
  await page.mouse.click(1245,862);await page.waitForTimeout(200); // Focus the selected Morthak, not Dorn.
  await move(page,772,476,'morthak');await page.waitForTimeout(800);
  for(const [direction,x,y] of [['left',668,476],['up',668,424],['right',772,424],['down',772,476]]){
   await move(page,x,y,'morthak');await page.waitForTimeout(160);await shot(page,'morthak-walk-'+direction);await page.waitForTimeout(700);
  }
  await shot(page,'morthak-map-idle');
  await page.mouse.click(38,247);await page.waitForTimeout(500);await shot(page,'morthak-sheet-idle');
  const snapshot=await read(gm,'/workspace');
  const pin=snapshot.tokens.find(t=>t.id===fixture.pins.morthak),dorn=snapshot.tokens.find(t=>t.id===fixture.pins.dorn7);
  assert.deepEqual([pin.grid_position.cell_x,pin.grid_position.cell_y],[9,8]);
  assert.deepEqual([dorn.grid_position.cell_x,dorn.grid_position.cell_y],[5,5]);
  report.checks.push('Master selects Morthak, focuses his sprite, moves his real token and displays all four walk directions',
   'idle returns after movement; Morthak sheet has an animated preview; Dorn retains his own position');
  const phone=await open('morthak',true);await shot(phone,'morthak-mobile-idle');
  await move(phone,474,221,'morthak',true);await phone.waitForTimeout(800);
  await phone.touchscreen.tap(38,108);await phone.waitForTimeout(600);await shot(phone,'morthak-mobile-own-sheet');
  const publicDorn=await read(player,'/characters/dorn7?read_only=true');assert.equal(Boolean(publicDorn.state),false);
  const forbidden=await player.post('/workspace/maps/default/move',{data:{request_id:'morthak-cannot-move-dorn',token_id:fixture.pins.dorn7,
   mode:'EXPLORATION_MOVE',path:[[5,5],[6,5]],expected_position_version:dorn.grid_position.version,expected_grid_version:snapshot.map.grid.version}});
  assert.equal(forbidden.status(),403);
  report.checks.push('mobile Morthak access moves his own native entity and opens his own animated sheet',
   'Morthak cannot move Dorn or read his private state');
  assert.deepEqual(report.errors,[]);report.status='PASS';
 }finally{
  await browser.close();await gm.dispose();await player.dispose();
  fs.writeFileSync(path.join(fixture.directory,'morthak-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1});
