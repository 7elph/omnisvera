// Real built UI + temporary CF-01 server; refuses operational/public hosts.
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const os=require('node:os');
const {randomUUID}=require('node:crypto');

async function main(){
  const base='http://127.0.0.1:8871';
  const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
  const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
  const json=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),url+': '+await r.text());return r.json();};
  const read=url=>json('get',url);
  const post=(url,data)=>json('post',url,data);
  assert.equal((await read('/health')).access_mode,'gm');
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-grid-browser-'));
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const errors=[];
  try{
    let combat=await read('/combat/effects');
    if(combat.encounter?.active) await post('/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
    const sessions=await read('/gm/sessions');
    if(!sessions.some(s=>s.status==='active')) {
      const session=await post('/gm/sessions',{request_id:randomUUID(),title:'Grid isolated rehearsal'});
      await post(`/gm/sessions/${session.id}/status`,{status:'active'});
    }
    const maps=await read('/workspace/maps');
    const session7=maps.filter(map=>map.title.startsWith('S7 ·'));
    assert.equal(session7.length,6);
    for(const map of session7){const snapshot=await read('/workspace?map_id='+encodeURIComponent(map.id));assert.equal(snapshot.map.grid.cell_size_m,1.5);assert.equal(snapshot.map.image_path,map.image_path);}
    const map=session7.find(map=>map.title.includes('arena'));
    await json('patch','/gm/workspace/maps/active',{map_id:map.id});
    let snapshot=await read('/workspace');
    const tokens=[];
    for(const id of ['vezemir','morthak','raziel']){
      let token=snapshot.tokens.find(t=>t.character_id===id);
      if(!token) token=await post('/gm/workspace/tokens',{token_type:'character',character_id:id,name:id,map_id:map.id,latitude:50,longitude:40,visible_to_players:true});
      tokens.push(token);
    }
    const npc=await post('/gm/workspace/tokens',{token_type:'monster',name:'Grid smoke NPC',map_id:map.id,latitude:40,longitude:70,current_hp:10,maximum_hp:10,visible_to_players:true,sheet:{movement:'6 m'}});
    tokens.push(npc);
    snapshot=await read('/workspace');
    for(const [index,token] of tokens.entries()){
      const position=snapshot.tokens.find(t=>t.id===token.id).grid_position;
      await post(`/workspace/maps/${encodeURIComponent(map.id)}/move`,{request_id:randomUUID(),token_id:token.id,mode:'GM_REPOSITION',path:[[position.cell_x,position.cell_y],[8+index*3,12]],expected_position_version:position.version,expected_grid_version:snapshot.map.grid.version});
    }
    // Fog remains the native system; reveal this rehearsal only.
    for(const layer of ['exploration','battle']) await post('/gm/workspace/fog',{map_id:map.id,layer,enabled:false,revealed_cells:[],mist_density:{}});
    const contexts=[];
    for(const role of ['gm','vezemir']){
      const context=await browser.newContext({viewport:role==='gm'?{width:1440,height:1000}:{width:390,height:844},isMobile:role!=='gm',hasTouch:role!=='gm'});
      await context.addInitScript(role=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');},role);
      const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
      await page.route('**/media/**',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960"><rect width="1280" height="960" fill="#202530"/></svg>'}));
      await page.goto(base);await page.locator('.app-shell.authenticated').waitFor({timeout:30000});
      const nav=page.getByRole('navigation',{name:'Navegação principal'});
      console.log('NAV',role,await nav.getByRole('button').allTextContents());
      if(role==='gm') await nav.getByRole('button',{name:/Mesa$/}).click();
      else {await page.waitForTimeout(1000);await page.evaluate(()=>window.dispatchEvent(new CustomEvent('omnisvera-open-workspace',{detail:'table'})));}
      try {await page.locator('.logical-map-grid').waitFor({timeout:30000});}
      catch(error){await page.screenshot({path:path.join(output,role+'-failed.png'),fullPage:true});console.error('GRID_LAYOUT',role,await page.locator('.workspace-map-stage').evaluateAll(items=>items.map(e=>({rect:e.getBoundingClientRect().toJSON(),parent:getComputedStyle(e.parentElement).display,img:e.querySelector('img')?.src}))),await page.locator('[role="alert"]').allTextContents(),'SCREENSHOT='+output);throw error;}
      contexts.push({role,page,context});
    }
    const gm=contexts[0].page, mobile=contexts[1].page;
    // Drag is a command, not a pixel PATCH. Wait for the actual HTTP reply.
    const id=tokens[0].id;
    if(await gm.getByRole('button',{name:'Ajustar',exact:true}).isEnabled()) await gm.getByRole('button',{name:'Ajustar',exact:true}).click();
    const pin=gm.locator(`[data-grid-token="${id}"]`);
    await pin.scrollIntoViewIfNeeded();
    snapshot=await read('/workspace');
    const position=snapshot.tokens.find(t=>t.id===id).grid_position;
    const stage=await gm.locator('.workspace-map-stage').boundingBox();
    const box=await pin.boundingBox();
    assert.ok(stage.width>0&&stage.height>0);
    assert.ok((await pin.getAttribute('class')).includes('movable'));
    const moveReply=gm.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
    await gm.mouse.move(box.x+box.width/2,box.y+box.height/2);await gm.mouse.down();
    await gm.mouse.move(stage.x+(position.cell_x+1.5)*stage.width/32,stage.y+(position.cell_y+.5)*stage.height/24,{steps:8});
    console.log('DRAG_DESTINATION',position,await gm.locator('.logical-grid-destination').evaluateAll(nodes=>nodes.map(e=>({x:e.getAttribute('x'),y:e.getAttribute('y')}))));
    if(!await gm.locator('.logical-grid-destination').count()){await gm.screenshot({path:path.join(output,'drag-failed.png'),fullPage:true});console.error('DRAG_GEOMETRY',{stage,box,position},output);}
    await gm.mouse.up();
    const reply=await moveReply;assert.ok(reply.ok(),await reply.text());
    const moved=await reply.json();assert.equal(moved.position.cell_x,position.cell_x+1);
    // A second connected client receives the native session_changed update.
    await mobile.waitForFunction(({id,x})=>document.querySelector(`[data-grid-token="${id}"]`)?.title.includes(`célula ${x},`),{id,x:moved.position.cell_x},{timeout:30000});
    console.log('REALTIME_LOCAL_TWO_CLIENTS=PASS');
    await gm.reload();await gm.locator('.logical-map-grid').waitFor({timeout:30000});
    assert.equal((await read('/workspace')).tokens.find(t=>t.id===id).grid_position.cell_x,moved.position.cell_x);
    // Mobile zoom keeps normalized position and selectable sheet.
    const before=await mobile.locator(`[data-grid-token="${id}"]`).evaluate(e=>({left:e.style.left,top:e.style.top}));
    await mobile.screenshot({path:path.join(output,'mobile-before-zoom.png'),fullPage:true});
    console.log('MOBILE_LAYOUT',await mobile.locator('.workspace-map-panel > header, .logical-token-controls').evaluateAll(nodes=>nodes.map(e=>({rect:e.getBoundingClientRect().toJSON(),height:getComputedStyle(e).height,flex:getComputedStyle(e).flex}))),output);
    await mobile.getByRole('button',{name:'Aumentar zoom',exact:true}).click();
    assert.deepEqual(await mobile.locator(`[data-grid-token="${id}"]`).evaluate(e=>({left:e.style.left,top:e.style.top})),before);
    await mobile.getByRole('combobox',{name:'Entidade no grid'}).selectOption(npc.id);
    await mobile.getByRole('button',{name:'Ficha da entidade',exact:true}).tap();
    await mobile.getByRole('dialog',{name:/Ficha de/}).waitFor();
    await mobile.getByRole('button',{name:'Fechar ficha',exact:true}).click();
    combat=await read('/combat/effects');
    await post('/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'start',payload:{map_id:map.id,title:'Grid smoke',battle_mode:true,participants:tokens.map((t,i)=>({target_type:t.character_id?'character':'token',target_id:t.character_id||t.id,initiative:20-i}))}});
    await mobile.getByText('COMBATE · Rodada 1',{exact:true}).waitFor({timeout:30000});
    await mobile.getByRole('combobox',{name:'Entidade no grid'}).selectOption(id);
    await mobile.getByRole('button',{name:'Mover uma célula →',exact:true}).waitFor({state:'visible'});
    const combatReply=mobile.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
    await mobile.getByRole('button',{name:'Mover uma célula →',exact:true}).tap();
    const response=await combatReply;assert.ok(response.ok(),await response.text());
    const firstMove=await response.json();assert.equal(firstMove.movement.spent_m,1.5);
    const maximumSteps=Math.floor(firstMove.movement.budget_m/1.5);
    for(let step=1;step<maximumSteps;step++){
      const next=mobile.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
      await mobile.getByRole('button',{name:'Mover uma célula →',exact:true}).tap();
      assert.ok((await next).ok());
    }
    const confirmedStyle=await mobile.locator(`[data-grid-token="${id}"]`).evaluate(e=>({left:e.style.left,top:e.style.top}));
    const denied=mobile.waitForResponse(r=>r.url().endsWith('/move')&&r.request().method()==='POST');
    await mobile.getByRole('button',{name:'Mover uma célula →',exact:true}).tap();
    assert.equal((await denied).status(),409);
    assert.deepEqual(await mobile.locator(`[data-grid-token="${id}"]`).evaluate(e=>({left:e.style.left,top:e.style.top})),confirmedStyle,'Rejected move preserves confirmed projection');
    await mobile.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    await gm.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('S7_MAPS=6; FOUR_ENTITIES=PASS; DRAG=PASS; RELOAD=PASS; MOBILE_ZOOM_SELECT_STEP=PASS; COMBAT_BUDGET=PASS; REJECTION_VISUAL=PASS');
    console.log('SCREENSHOTS='+output);
  } finally{await browser.close();await api.dispose();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
