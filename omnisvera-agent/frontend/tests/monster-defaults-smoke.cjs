// Native HTTP + UI, using only the MCP-managed TEMP fixture and local test credentials.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-monster-defaults-'));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const call=async(method,url,data)=>{const r=await api[method](url,{data});assert.ok(r.ok(),`${r.status()} ${url}: ${await r.text()}`);return r.json();};
 const get=url=>call('get',url),post=(url,data)=>call('post',url,data),created=[],checks=[],errors=[];
 let browser,page;
 try{
  const combat=await get('/combat/effects');
  if(combat.encounter?.active)await post('/gm/combat/effects',{request_id:randomUUID(),expected_version:combat.version,action:'end',payload:{}});
  const workspace=await get('/workspace'),catalog=await get('/gm/workspace/monster-catalog');
  const add=async(monster)=>{
   const preset=monster.encounter_defaults;
   const token=await post('/gm/workspace/tokens',{token_type:'monster',name:'ENSAIO '+monster.name,map_id:workspace.map.id,current_hp:99,maximum_hp:99,visible_to_players:true,latitude:70,longitude:70,
    sheet:{...monster,attacks:preset?.attacks||monster.attacks,abilities:(preset?.abilities||monster.abilities).map(a=>`${a.name}: ${a.description}`),source:{monster_id:monster.id},saving_throw:10}});
   created.push(token.id);return token;
  };
  const victim=await post('/gm/workspace/tokens',{token_type:'monster',name:'Alvo isolado',map_id:workspace.map.id,current_hp:9999,maximum_hp:9999,visible_to_players:true,latitude:70,longitude:72,sheet:{armor_class:1,saving_throw:10}});
  created.push(victim.id);
  let weapons=0,repertoires=0;
  for(const monster of catalog.monsters){
   const preset=monster.encounter_defaults;if(!preset)continue;
   const token=await add(monster),actions=await get(`/gm/workspace/tokens/${token.id}/actions`);
   if(preset.equipment.length||monster.id==='serpente'){
    assert.equal(actions.summary.attacks_incomplete,0,monster.id);
    const index=preset.equipment.length?monster.attacks.findIndex(a=>/^Arma(?:\s*\+\d+)?$/i.test(a.damage)):0;
    const payload={request_id:randomUUID(),attack_id:String(index),target_type:'token',target_id:victim.id,roll_mode:'physical',d20:20};
    const first=await post(`/gm/combat/tokens/${token.id}/attacks/resolve`,payload),retry=await post(`/gm/combat/tokens/${token.id}/attacks/resolve`,payload);
    assert.equal(first.resolution_id,retry.resolution_id);assert.ok(first.damage_total>0);
    const result=await post(`/combat/attacks/${first.resolution_id}/confirm`),repeat=await post(`/combat/attacks/${first.resolution_id}/confirm`);
    assert.deepEqual(result,repeat);weapons++;
   }
   if(preset.spells.length){
    const level=actions.spellcasting[0]?.spellcasting?.caster_level;assert.ok(level,monster.id);
    const linked=new Set(actions.spellcasting.flatMap(a=>(a.spellcasting?.named_spells||[]).flatMap(n=>n.links.map(s=>s.id))));
    assert.ok(preset.spells.every(s=>linked.has(s.id)),monster.id);
    const spell=preset.spells[0];
    const result=await post(`/gm/compendium/spells/${spell.id}/cast`,{caster_type:'token',caster_id:token.id,targets:[{type:'token',id:victim.id}],roll_mode:'digital'});
    const n=spell.tradition==='arcana'?Math.min(5,Math.floor((level+1)/2)):1+Math.floor((level-1)/3);
    const bonus=spell.tradition==='arcana'?n:n*Math.min(level,5);
    assert.equal(result.mechanic.damage,`${n}d4+${bonus}`);assert.ok(result.results[0].damage_dealt>0);repertoires++;
   }
  }
  assert.equal(weapons,30);assert.equal(repertoires,16);
  checks.push('29 weapon loadouts and nonvenomous snake: native HTTP resolve/confirm/retry; 16 linked repertoires each cast with real caster-level scaling');
  for(const [identity,index,effect] of [['cobra-cuspidora',0,'blinded'],['verme-da-carcaca',1,'paralyzed']]){
   const token=await add(catalog.monsters.find(m=>m.id===identity));
   const first=await post(`/gm/combat/tokens/${token.id}/attacks/resolve`,{request_id:randomUUID(),attack_id:String(index),target_type:'token',target_id:victim.id,roll_mode:'physical',d20:20});
   assert.equal(first.damage_total,0);assert.deepEqual(first.damage_rolls,[]);
   const result=await post(`/combat/attacks/${first.resolution_id}/confirm`);
   assert.equal(result.breakdown.monster_rider_results[0].effect,effect);
  }
  checks.push('Blindness and paralysis attacks resolve no fake HP dice and run their native on-hit JP');
  await require('./monster-specials-scenarios.cjs')({api,base,workspace,catalog,output,checks,created});
  for(const id of created){const r=await api.delete('/gm/workspace/tokens/'+encodeURIComponent(id));assert.ok(r.ok());}
  browser=await chromium.launch({channel:'msedge',headless:true});
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
   page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mesa$/}).click();
   for(const actor of ['vezemir','raziel','dorn7','morthak']){
    await page.locator(`[data-character="${actor}"]`).click();
    const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
    const sheet=await get('/characters/'+actor);await panel.getByRole('heading',{name:sheet.definition.name,exact:true}).waitFor();
    const metrics=await panel.locator('.workspace-identity-tags').evaluate(el=>({overflow:el.scrollWidth>el.clientWidth+2,buttons:[...el.querySelectorAll('button')].map(b=>({font:parseFloat(getComputedStyle(b.querySelector('b')).fontSize),height:b.getBoundingClientRect().height}))}));
    assert.ok(!metrics.overflow);assert.ok(metrics.buttons.every(b=>b.font>=13&&b.height<=54),JSON.stringify(metrics));
    const quick=panel.locator('.workspace-hp-quick-controls').first();
    assert.equal(await quick.locator('button').count(),3);assert.equal(await quick.locator('input').count(),1);
    assert.equal(await quick.getByText('Aplicar',{exact:true}).count(),0);
    assert.equal(await quick.getByRole('button',{name:'Confirmar PV'}).locator('svg').count(),1);
    assert.equal(await quick.locator('input').evaluate(el=>getComputedStyle(el).appearance),'textfield');
    await panel.locator('.workspace-character-identity').screenshot({path:path.join(output,`${actor}-identity-${width}.png`)});
    await panel.locator('.workspace-identity-tags button').first().click();
    const dialog=page.getByRole('dialog');await dialog.waitFor();
    const portrait=dialog.locator('img.workspace-detail-image');
    if(await portrait.count()){const box=await portrait.boundingBox();assert.ok(box.width<=130&&box.height<=130);}
    assert.ok(await dialog.locator('p,.workspace-detail-content').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=14));
    await dialog.screenshot({path:path.join(output,`${actor}-identity-detail-${width}.png`)});
    await dialog.getByRole('button',{name:'Fechar descrição'}).click();
    await panel.locator('.workspace-vitals-and-controls').screenshot({path:path.join(output,`${actor}-vitals-${width}.png`)});
   }
   await page.locator('[data-character="vezemir"]').click();
   const quick=page.locator('.workspace-character-panel .workspace-hp-quick-controls').first();
   const before=(await get('/characters/vezemir')).state.current_hp;
   await quick.locator('button').first().click();
   const response=page.waitForResponse(r=>r.url().endsWith('/characters/vezemir/actions')&&r.request().method()==='POST');
   await quick.getByRole('button',{name:'Confirmar PV'}).click();assert.ok((await response).ok());
   assert.equal((await get('/characters/vezemir')).state.current_hp,before-1);
   await page.reload();await page.locator('.workspace-character-panel .workspace-character-identity').waitFor();
   assert.equal((await get('/characters/vezemir')).state.current_hp,before-1);
   await require('./monster-specials-visual.cjs')({page,api,base,workspace,catalog,output,width});
   await context.close();
  }
  checks.push('Four identities readable with compact frames; one numeric stepper and SVG confirmation; HP persists after native UI confirmation/reload at 1440/390');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output,production_modified:false,limitations:['No distinct-network or physical-mobile proof','Rust needs explicit item material/enchantment metadata; ranged reverse contact and fixed base armor CA remain assisted','Spell daily preparation limits and projectile splitting are not certified'],controlled_inputs:['Physical d20=20 through native attack API']}));
 }catch(error){if(page)await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});console.error(error.stack);console.log(JSON.stringify({status:'FAIL',checks,screenshots:output,production_modified:false}));process.exitCode=1;}
 finally{if(browser)await browser.close();await api.dispose();}
})();
