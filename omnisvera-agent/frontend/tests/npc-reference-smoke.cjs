// Native HTTP and built UI on an isolated database, never operational state.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-npc-reference-'));
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const headers={'X-Omnisvera-Token':'cf01-local-gm'};
  const pinsResponse=await context.request.get('http://127.0.0.1:8871/gm/workspace/npc-tokens',{headers});
  assert.equal(pinsResponse.status(),200); const pins=await pinsResponse.json(); assert.ok(pins.length>0);
  const worldResponse=await context.request.get('http://127.0.0.1:8871/npcs',{headers});
  assert.equal(worldResponse.status(),200);let world=await worldResponse.json();
  if(!world.length){const created=await context.request.post('http://127.0.0.1:8871/gm/npcs',{headers,data:{request_id:'npc-reference-isolated-fixture',name:'NPC de ensaio isolado',visible_to_players:false,public_description:'Cola de teste',private_description:'Segredo apenas do Mestre'}}); assert.ok(created.ok());world=[await created.json()];}
  await page.goto('http://127.0.0.1:8871');await page.locator('.app-shell.authenticated').waitFor();
  await page.getByRole('button',{name:'Abrir ficha de Vezemir',exact:true}).click();
  const specialization=page.locator('.workspace-identity-tags');
  await specialization.getByText('Especialista em Armas',{exact:true}).waitFor();
  assert.equal(await specialization.getByText('Necromante',{exact:true}).count(),0);
  await page.locator('.gm-tools-tab').click();
  await page.getByRole('button',{name:/NPCs do Mestre Consultar/}).click();
  const library=page.getByRole('region',{name:'NPCs do Mestre',exact:true});await library.waitFor();
  await library.getByRole('button',{name:new RegExp(world[0].name)}).last().click();
  await library.getByRole('button',{name:'Voltar para a lista de NPCs',exact:true}).click();
  const roster=library.getByRole('region',{name:'Fichas reservadas e pins de NPCs',exact:true});
  await roster.getByRole('button',{name:/Varkh/}).click();
  await page.getByRole('button',{name:'Voltar para NPCs',exact:true}).click();
  await library.waitFor();
  await roster.getByRole('searchbox',{name:'Buscar fichas e pins'}).fill(pins[0].name);
  await roster.getByRole('button',{name:new RegExp(pins[0].name)}).first().click();
  const modal=page.getByRole('dialog',{name:`Ficha de ${pins[0].name}`,exact:true});await modal.waitFor();
  await modal.getByRole('button',{name:'Voltar para NPCs',exact:true}).click();assert.equal(await modal.count(),0);
  const after=await (await context.request.get('http://127.0.0.1:8871/gm/workspace/npc-tokens',{headers})).json();
  assert.deepEqual(after.map(t=>[t.id,t.visible_to_players,t.map_id,t.latitude,t.longitude]),pins.map(t=>[t.id,t.visible_to_players,t.map_id,t.latitude,t.longitude]));
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===390?844:1000});await library.scrollIntoViewIfNeeded();
   const dimensions=await library.evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth,children:[...el.querySelectorAll('*')].filter(n=>n.getBoundingClientRect().right>el.getBoundingClientRect().right+1).slice(0,12).map(n=>[n.tagName,n.className,n.getBoundingClientRect().width])}));console.log(width,JSON.stringify(dimensions));
   await library.screenshot({path:path.join(output,`npc-list-${width}.png`)});
   assert.ok(dimensions.scroll<=dimensions.width+1,'NPC reference must not overflow');
   await library.screenshot({path:path.join(output,`npc-list-${width}.png`)});
   await library.getByRole('button',{name:new RegExp(world[0].name)}).last().click();
   assert.ok(await library.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'NPC profile must not overflow');
   await library.screenshot({path:path.join(output,`npc-detail-${width}.png`)});
   await library.getByRole('button',{name:'Voltar para a lista de NPCs',exact:true}).click();
   await library.locator('.npc-card-list > button').last().click();
   await library.getByRole('button',{name:'Voltar para a lista de NPCs',exact:true}).click();
  }
  await library.getByRole('button',{name:'Mapas',exact:true}).click();
  await page.getByText('LOCAIS · CRIAR E PINAR RAPIDAMENTE',{exact:true}).waitFor();
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/NPCs/}).click();
  assert.equal(await page.getByText('LOCAIS · CRIAR E PINAR RAPIDAMENTE',{exact:true}).count(),0);
  assert.deepEqual(errors,[]);
  console.log('PASS: class separation, NPCs/all-map pins, read-only privacy, back navigation, locations in Maps, desktop/mobile. SCREENSHOTS='+output);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
