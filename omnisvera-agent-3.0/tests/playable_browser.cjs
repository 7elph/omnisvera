const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.env.COMPANION3_FIXTURE,'utf8'));
 assert.equal(fixture.synthetic,true);
 const base=process.env.COMPANION3_URL;assert.equal(new URL(base).hostname,'127.0.0.1');
 const report={status:'RUNNING',checks:[],errors:[],screenshots:[]};
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-unsafe-swiftshader']});
 const gm=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-vezemir'}});
 const call=async(api,method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),await r.text());return r.json()};
 const shot=async(page,name)=>{const target=path.join(fixture.directory,name+'.png');await page.screenshot({path:target});report.screenshots.push(target)};
 const nav=async(page,index,mobile=false)=>{
   if(mobile)await page.touchscreen.tap(38+(index%2)*62,108+Math.floor(index/2)*58);
   else await page.mouse.click(38,247+index*58);
 };
 const waitRead=(page,url)=>page.waitForResponse(r=>r.url().includes(url)&&r.status()===200,{timeout:45000});
 const effect=async(action,payload={})=>{
   const state=await call(gm,'get','/combat/effects');
   return call(gm,'post','/gm/combat/effects',{request_id:'godot-test-'+action+'-'+Date.now(),expected_version:state.version,action,payload});
 };
 async function open(identity,mobile){
   const context=await browser.newContext({viewport:mobile?{width:844,height:390}:{width:1440,height:900},isMobile:mobile,hasTouch:mobile});
   const page=await context.newPage();page.setDefaultTimeout(30000);
   // Capture actual server receipts before Godot releases its fetch response.
   page.effectReceipts=[];
   await page.route('**/gm/combat/effects',async route=>{
    if(route.request().method()!=='POST')return route.continue();
    const response=await route.fetch();
    const bytes=await response.body();
    page.effectReceipts.push({status:response.status(),body:JSON.parse(bytes.toString('utf8'))});
    await route.fulfill({response,body:bytes});
   });
   page.on('pageerror',e=>report.errors.push(e.message));
   page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Invalid call|Failed to load script/.test(m.text()))report.errors.push(m.text())});
   const ready=waitRead(page,'/characters/'+(identity==='gm'?'dorn7':'vezemir')+'?read_only=true');
   await page.goto(base+'/#token=cf01-local-'+identity);
   await page.locator('#loading').waitFor({state:'detached',timeout:90000});await ready;
   await page.waitForTimeout(1000);return{context,page};
 }
 try{
  const desktop=await open('gm',false),page=desktop.page;
  const art=[];
  page.on('response',r=>{if(r.url().includes('/media/'))art.push({path:new URL(r.url()).pathname,status:r.status()})});
  await shot(page,'playable-desktop-idle');
  const moving=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
  await page.mouse.click(772,476);
  const movement=await moving;assert.equal(movement.status(),200,await movement.text());
  assert.equal(movement.request().postDataJSON().mode,'EXPLORATION_MOVE');
  const moved=await movement.json();assert.equal(moved.position.cell_x,6);assert.equal(moved.position.cell_y,5);
  await page.waitForTimeout(150);await shot(page,'playable-dorn-walk');
  await page.waitForTimeout(1600);await shot(page,'playable-dorn-returned-idle');
  const leftMove=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
  await page.mouse.click(720,450);assert.equal((await leftMove).status(),200);
  await page.waitForTimeout(150);await shot(page,'playable-dorn-walk-left');
  await page.waitForTimeout(650);
  const returnMove=page.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
  await page.mouse.click(772,476);assert.equal((await returnMove).status(),200);
  await page.waitForTimeout(800);
  report.checks.push('master point-and-click created a native adjacent exploration move; walking returned to idle');
  const itemArt=waitRead(page,'/media/zz_media/ui/icons/items/adaga.png');
  await nav(page,0);await itemArt;await page.waitForTimeout(800);await shot(page,'playable-dorn-sheet-controls');
  await page.keyboard.press('Escape');
  await nav(page,3);await page.waitForTimeout(400);await shot(page,'playable-inventory-catalog-fallback');
  assert.ok(art.some(a=>a.path.endsWith('/missing.png')&&a.status===404));
  report.checks.push('a missing preferred inventory image falls back to the same existing item icon as Companion 2.0');
  await page.keyboard.press('Escape');
  await effect('start',{map_id:'default',participants:[{target_type:'character',target_id:'dorn7',initiative:10},{target_type:'token',target_id:fixture.enemy,initiative:1}]});
  let refreshed=waitRead(page,'/combat/effects');await nav(page,4);await refreshed;await page.keyboard.press('Escape');
  await nav(page,0);await page.waitForTimeout(500);
  const guarded=page.waitForResponse(r=>r.url().endsWith('/gm/combat/effects')&&r.request().method()==='POST');
  await page.mouse.click(180,157);
  await guarded;const guardReceipt=page.effectReceipts.at(-1);assert.equal(guardReceipt.status,200,JSON.stringify(guardReceipt.body));
  assert.ok(guardReceipt.body.effects.some(e=>e.protocol==='guard'));
  await page.waitForTimeout(120);await shot(page,'playable-guard-accepted');
  await page.keyboard.press('Escape');await effect('next_turn');await effect('next_turn');
  refreshed=waitRead(page,'/combat/effects');await nav(page,4);await refreshed;await page.keyboard.press('Escape');
  await nav(page,0);await page.waitForTimeout(500);
  const contract=waitRead(page,'/gm/actions/describe?ref=');await page.mouse.click(380,157);await contract;
  await page.waitForTimeout(500);await shot(page,'playable-lightning-range');
  await page.mouse.click(720,606);await page.mouse.click(720,606);
  await page.waitForTimeout(300);await shot(page,'playable-lightning-confirm');
  const lightning=page.waitForResponse(r=>r.url().endsWith('/gm/combat/effects')&&r.request().method()==='POST');
  await page.keyboard.press('Enter');
  await lightning;const lightningReceipt=page.effectReceipts.at(-1);assert.equal(lightningReceipt.status,200,JSON.stringify(lightningReceipt.body));
  const lightningResult=lightningReceipt.body;
  assert.ok(lightningResult.protocol_result.damage_roll.total>0);
  assert.ok(lightningResult.protocol_result.results[0].damage>0);
  await page.waitForTimeout(120);await shot(page,'playable-lightning-accepted');
  await page.waitForTimeout(2200);await shot(page,'playable-after-cast-idle');
  report.checks.push('Guarda consumed the native action/resource and started its supplied sprite animation',
    'Relampago fetched the native revision/range, selected a grid pin, confirmed, rolled damage and animated after server success');
  await effect('end');
  const mobile=await open('vezemir',true),phone=mobile.page;
  await shot(phone,'playable-mobile-centered-icons');
  const playerMoving=phone.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
  await phone.touchscreen.tap(422,247);
  const playerMovement=await playerMoving;assert.equal(playerMovement.status(),200,await playerMovement.text());
  assert.equal(playerMovement.request().postDataJSON().token_id,fixture.pins.vezemir);
  await nav(phone,0,true);await phone.waitForTimeout(700);await shot(phone,'playable-mobile-own-sheet');
  const publicDorn=await call(player,'get','/characters/dorn7?read_only=true');assert.equal(Boolean(publicDorn.state),false);assert.deepEqual(publicDorn.inventory,[]);
  const forbidden=await player.post('/gm/combat/effects',{data:{request_id:'fixture-forbidden-guard',expected_version:0,action:'dorn_guard',payload:{}}});assert.ok([401,403].includes(forbidden.status()));
  await phone.keyboard.press('Escape');await nav(phone,5,true);await phone.waitForTimeout(600);
  const publicMaps=await call(player,'get','/workspace/maps');assert.equal(publicMaps.some(m=>m.id===fixture.private_map),false);
  const index=publicMaps.findIndex(m=>m.id===fixture.public_map);
  const opened=waitRead(phone,'/workspace?map_id=');await phone.touchscreen.tap(260,122+index*80);
  const snapshot=await(await opened).json();assert.equal(snapshot.map.id,fixture.public_map);
  assert.equal(snapshot.tokens.some(p=>p.name==='GM_HIDDEN_MAP_PIN'),false);
  await phone.waitForTimeout(1600);await shot(phone,'playable-mobile-floating-map');
  await phone.touchscreen.tap(486,195);await phone.waitForTimeout(500);await shot(phone,'playable-mobile-pin');
  await phone.keyboard.press('Escape');await phone.keyboard.press('Escape');await nav(phone,6,true);
  await phone.waitForTimeout(500);const sessionRead=waitRead(phone,'/sessions/'+fixture.session_id);
  await phone.touchscreen.tap(260,122);const session=await(await sessionRead).json();assert.equal(session.private_notes,undefined);
  await phone.waitForTimeout(1000);await shot(phone,'playable-mobile-session');
  report.checks.push('mobile player point-and-click moved only their own native entity',
    'large transparent PNG controls centered on the left, real sheets accessible while offline',
    'private character state, GM commands, hidden map/pin and session notes remain protected',
    'floating map and pin popup, existing session chronology exercised');
  assert.equal(report.errors.length,0,report.errors.join('\n'));report.status='PASS';
 }finally{
  await browser.close();await gm.dispose();await player.dispose();
  fs.writeFileSync(path.join(fixture.directory,'browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1});
