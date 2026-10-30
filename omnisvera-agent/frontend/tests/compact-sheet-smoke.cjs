// Native UI + native commands. Never use the operational database or tokens.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const ts=require('typescript'),vm=require('node:vm'),catalogModule={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/companionIconCatalog.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{module:catalogModule,exports:catalogModule.exports});
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const get=async url=>{const r=await api.get(url);assert.ok(r.ok(),await r.text());return r.json();};
 const post=async(url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const health=await get('/health');
 assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 assert.ok(path.resolve(health.vault_path).startsWith(path.resolve(os.tmpdir())+path.sep));
 // Already-visible character/equipment images, copied only to the disposable fixture vault.
 const publicIcons=new Set(['zz_media/ui/icons/items/dados.jpg','zz_media/ui/icons/items/kit-basico.jpg','zz_media/ui/icons/items/armadura-de-couro.png','zz_media/ui/icons/items/inventario.jpg']);
 for(const actor of ['vezemir','morthak','raziel','dorn7']){
  const character=await get('/characters/'+actor),asset=character.definition.cover;
  assert.match(asset,/^zz_media\/characters\/(vezemir|morthak|raziel|unidade)\.(png|jpg)$/i);
  const original=path.resolve(__dirname,'../../..',asset),copy=path.resolve(health.vault_path,asset);
  assert.ok(copy.startsWith(path.resolve(health.vault_path)+path.sep));assert.ok(fs.existsSync(original));
  fs.mkdirSync(path.dirname(copy),{recursive:true});fs.copyFileSync(original,copy);
  for(const item of character.inventory){if(item.thumbnail||item.cover)publicIcons.add(item.thumbnail||item.cover);const fallback=catalogModule.exports.iconPathForItem(item.item_title,item.item_type);if(fallback)publicIcons.add(fallback);}
 }
 for(const asset of publicIcons){
  assert.match(asset,/^zz_media\//);
  const repo=path.resolve(__dirname,'../../..'),original=path.resolve(repo,asset),copy=path.resolve(health.vault_path,asset);
  assert.ok(original.startsWith(path.resolve(repo,'zz_media')+path.sep)&&copy.startsWith(path.resolve(health.vault_path,'zz_media')+path.sep));
  if(fs.existsSync(original)){fs.mkdirSync(path.dirname(copy),{recursive:true});fs.copyFileSync(original,copy);}
 }
 const command=async(action,payload={})=>post('/gm/combat/effects',{request_id:randomUUID(),expected_version:(await get('/combat/effects')).version,action,payload});
 if((await get('/combat/effects')).encounter?.active)await command('end');
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],checks=[],output=fs.mkdtempSync(path.join(os.tmpdir(),'omni-compact-sheet-'));
 try{
  for(const actor of ['vezemir','morthak','raziel','dorn7']){
   await post('/characters/'+actor+'/actions',{action:'rest_at_inn',payload:{},request_id:randomUUID(),reason:'Somente fixture: ficha compacta'});
   await command('apply',{target_type:'character',target_id:actor,label:'Velocidade',source:'Ensaio de status',duration:'rounds',rounds:3,modifiers:{attack_bonus:1}});
   const role=actor==='dorn7'?'gm':actor;
   const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
   await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
   const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();await page.locator(`button[data-character="${actor}"]`).click();
   const panel=page.locator('.workspace-character-panel');await panel.locator('.workspace-character-identity').waitFor();
   if(role==='gm'){
    for(const selected of ['morthak','vezemir','raziel','dorn7','morthak','dorn7']){
     const response=page.waitForResponse(r=>r.url().endsWith('/characters/'+selected)&&r.request().method()==='GET');
     await page.locator(`button[data-character="${selected}"]`).click();await response;
     await page.waitForFunction(id=>document.querySelector('.workspace-character-copy h2')?.textContent?.toLowerCase().includes(id==='dorn7'?'dorn':id),selected);
     const names=await panel.locator('article.workspace-spell-card > .workspace-catalog-card-heading').allTextContents();
     assert.equal(new Set(names).size,names.length,'No duplicate spell/protocol cards after character switches');
    }
   }
   const groups=panel.locator('.workspace-sheet-section');assert.ok(await groups.count()>0);
   assert.equal(await panel.locator('.workspace-sheet-section[open]').count(),0,'Groups start closed outside combat');
   await panel.locator('.workspace-status-under-vitals .workspace-active-effect-icons').waitFor();
   assert.equal(await panel.getByText('EFEITOS ATIVOS',{exact:true}).count(),0);
   assert.equal(await panel.getByText('fictional_time',{exact:true}).count(),0);
   assert.equal(await panel.getByText('Diagnóstico da Unidade',{exact:true}).count(),0);
   const jp=panel.getByRole('button',{name:'Jogar proteção',exact:true}),dice=panel.getByRole('button',{name:'Bandeja de dados',exact:true});
   for(const control of [jp,dice]){const box=await control.boundingBox();assert.ok(box.width<=46&&box.height<=46);}
   assert.equal((await jp.innerText()).trim(),'JP');assert.equal((await dice.innerText()).trim(),'');
   const header=panel.locator('.workspace-attributes > header');
   assert.equal(await header.getByRole('button').count(),3);
   const notes=header.getByRole('button',{name:'Anotações do personagem',exact:true});
   await notes.click();const noteDialog=page.getByRole('dialog',{name:'Anotações do personagem',exact:true});await noteDialog.waitFor();
   assert.equal(await noteDialog.getByRole('textbox',{name:'Anotações do personagem'}).count(),1);await page.keyboard.press('Escape');await noteDialog.waitFor({state:'detached'});
   if(role==='gm'){
    const level=panel.locator('.character-level-tools');assert.equal(await level.getByRole('button').count(),2);
    const up=await level.getByRole('button',{name:'Subir nível',exact:true}).boundingBox(),gear=await level.getByRole('button',{name:'Correção manual de nível e XP',exact:true}).boundingBox();assert.ok(Math.abs(up.y-gear.y)<2&&gear.x>up.x);
   }
   const jpBox=await jp.boundingBox(),diceBox=await dice.boundingBox(),titleBox=await header.locator(':scope > span').boundingBox();
   assert.ok(Math.abs(jpBox.y-diceBox.y)<2&&diceBox.x>jpBox.x&&jpBox.x>=titleBox.x+titleBox.width,'JP/dice must be horizontal at right of title');
   const wallet=panel.getByRole('region',{name:'Moedas',exact:true});
   assert.equal(await wallet.locator('input,select,header,summary,small').count(),0);
   assert.equal(await wallet.locator('button').count(),role==='gm'?1:0);
   if(role==='gm'){
    const balance=sheet=>Number(sheet.state.coins??0);
    const before=await get('/characters/'+actor);
    await wallet.getByRole('button',{name:'Editar moedas'}).click();
    const dialog=page.getByRole('dialog',{name:'Editar moedas',exact:true});await dialog.waitFor();
    await dialog.screenshot({path:path.join(output,actor+'-wallet-editor-390.png')});
    await dialog.getByRole('spinbutton',{name:'Ouro',exact:true}).fill(String(balance(before)+1));
    const saved=page.waitForResponse(r=>r.url().endsWith('/characters/'+actor+'/actions')&&r.request().method()==='POST');
    await dialog.getByRole('button',{name:'Aplicar Ouro',exact:true}).click();await saved;
    await page.waitForFunction(({actor,value})=>document.querySelector('.workspace-wallet [aria-label="Ouro: saldo"]')?.textContent===String(value),{actor,value:balance(before)+1});
    assert.equal(balance(await get('/characters/'+actor)),balance(before)+1,'GM edit reaches native ledger/state');
    await page.keyboard.press('Escape');await dialog.waitFor({state:'detached'});
    assert.ok((await wallet.innerText()).includes(String(balance(before)+1)));
   }
   assert.deepEqual(await wallet.locator('strong').evaluateAll(items=>items.map(el=>el.getAttribute('aria-label'))),['Cobre: saldo','Prata: saldo','Ouro: saldo','Platina: saldo']);
   assert.ok(await wallet.evaluate(el=>Boolean(el.compareDocumentPosition(document.querySelector('.workspace-inventory-catalog'))&Node.DOCUMENT_POSITION_FOLLOWING)));
   if(role==='gm'){
   const filter=page.getByRole('button',{name:'Filtros do registro',exact:true}),filters=page.getByRole('region',{name:'Filtros do registro',exact:true});
   assert.equal(await filters.count(),0);
   await filter.scrollIntoViewIfNeeded();const filterBox=await filter.boundingBox(),countBox=await page.locator('.workspace-log-tools > span').boundingBox();
   assert.ok(filterBox.width<=36&&filterBox.x+filterBox.width<=countBox.x&&Math.abs(filterBox.y+filterBox.height/2-countBox.y-countBox.height/2)<2);
   await filter.click();await filters.waitFor();await filters.getByRole('searchbox').fill('fixture-filter');
   await filter.click();assert.equal(await filters.count(),0);
   await filter.click();assert.equal(await filters.getByRole('searchbox').inputValue(),'fixture-filter');await filters.getByRole('button',{name:'Limpar filtros'}).click();await filter.click();
   }
   const sheet=await get('/characters/'+actor),loadout=panel.getByRole('region',{name:'Equipamentos atuais',exact:true});
   for(const item of sheet.inventory.filter(i=>i.equipped&&i.quantity>0))assert.equal(await loadout.getByRole('button',{name:item.item_title,exact:true}).count(),1);
   for(const item of sheet.inventory.filter(i=>i.equipped&&i.quantity>0))assert.equal((await loadout.getByRole('button',{name:item.item_title,exact:true}).innerText()).trim(),'');
   for(const icon of await panel.locator('button.workspace-item-icon').all())assert.equal(await icon.evaluate(el=>getComputedStyle(el).backgroundColor),'rgba(0, 0, 0, 0)');
   const columns=await panel.locator('.workspace-inventory-catalog').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);assert.equal(columns,6);
   assert.equal(await panel.locator('.workspace-inventory-catalog').getByRole('button',{name:'Guardar',exact:true}).count(),0);
   if(actor==='raziel'){
    assert.equal(await panel.locator('.workspace-attack-catalog').count(),1);
    assert.equal(await panel.getByRole('region',{name:'Hemomancia',exact:true}).isVisible(),false);
    await panel.locator('.workspace-sheet-section > summary').filter({hasText:'Hemomancia'}).click();
    const hemo=panel.getByRole('region',{name:'Hemomancia',exact:true}),selectors=hemo.getByRole('combobox');assert.equal(await selectors.count(),3);
    const boxes=await selectors.evaluateAll(items=>items.map(el=>el.getBoundingClientRect().y));assert.ok(Math.max(...boxes)-Math.min(...boxes)<3,'Three blood selectors stay on one row');
    await hemo.screenshot({path:path.join(output,'raziel-hemomancy-390.png')});
    await panel.locator('.workspace-sheet-section > summary').filter({hasText:'Hemomancia'}).click();
    for(const name of ['Kit básico','Armadura de couro']){const img=loadout.getByRole('button',{name,exact:true}).locator('img');await img.evaluate(el=>el.complete&&el.naturalWidth>0?true:new Promise((resolve,reject)=>{el.onload=resolve;el.onerror=reject;}));}
   }
   const art=loadout.locator('.workspace-equipment-portrait');assert.ok((await art.getAttribute('src')).includes(sheet.definition.cover));
   await art.evaluate(img=>img.complete&&img.naturalWidth>0?true:new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;}));
   assert.equal(await art.isVisible(),true);assert.equal(await art.evaluate(img=>getComputedStyle(img).objectFit),'contain');
   await loadout.screenshot({path:path.join(output,actor+'-equipment-390.png'),style:'nav[aria-label="Navegação principal"] { visibility: hidden; }'});
   await header.screenshot({path:path.join(output,actor+'-attributes-390.png')});
   await panel.locator('.workspace-character-identity').screenshot({path:path.join(output,actor+'-identity-390.png'),style:'nav[aria-label="Navegação principal"] { visibility: hidden; }'});
   await panel.locator('.workspace-inventory-catalog').screenshot({path:path.join(output,actor+'-inventory-390.png'),style:'nav[aria-label="Navegação principal"] { visibility: hidden; }'});
   const spells=panel.locator('.workspace-sheet-section > summary').filter({hasText:/^Magias$/});
   if(await spells.count()){await spells.click();await spells.locator('..').screenshot({path:path.join(output,actor+'-spells-390.png'),style:'nav[aria-label="Navegação principal"] { visibility: hidden; }'});await spells.click();}
   await wallet.screenshot({path:path.join(output,actor+'-wallet-390.png')});
   if(role==='gm')await page.locator('.workspace-timeline-panel > header').screenshot({path:path.join(output,actor+'-log-390.png')});
   const heights=await panel.locator('.workspace-inventory-catalog > article').evaluateAll(items=>items.map(el=>el.getBoundingClientRect().height));
   if(heights.length)assert.ok(heights.reduce((a,b)=>a+b,0)/heights.length<110,'Compact inventory must not retain tall cards');
   await page.screenshot({path:path.join(output,actor+'-390.png'),fullPage:true});
   if(actor==='vezemir'){
    const workspace=await get('/workspace');
    await command('start',{map_id:workspace.map.id,battle_mode:true,participants:[{target_type:'character',target_id:actor,initiative:30}]});
    await page.waitForFunction(()=>document.querySelector('.workspace-sheet-section[open]'));
    const group=panel.locator('.workspace-sheet-section[open]').first(),groupElement=await group.elementHandle();await group.locator(':scope > summary').click();
    assert.equal(await groupElement.evaluate(el=>el.open),false);
    await command('end');
   }
   if(role==='gm'){
    await page.setViewportSize({width:1440,height:900});
    const a=await jp.boundingBox(),b=await dice.boundingBox();assert.ok(Math.abs(a.y-b.y)<2&&b.x>a.x);
    assert.ok((await loadout.boundingBox()).height>150,'Equipment must keep its content height in the desktop flex column');
    await loadout.screenshot({path:path.join(output,actor+'-equipment-1440.png')});
    // Native Guard: card -> allied pin -> Yes -> enemy attack redirects without opt-in.
    const evidencePath=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE);assert.ok(evidencePath.startsWith(path.resolve(os.tmpdir())+path.sep));
    const evidence=JSON.parse(fs.readFileSync(evidencePath,'utf8'));
    let ws=await get('/workspace'),grid=ws.map.grid,dorn=ws.tokens.find(t=>t.character_id==='dorn7'),ally=ws.tokens.find(t=>t.character_id==='vezemir');
    assert.ok(grid&&dorn.grid_position&&ally.grid_position);
    const occupied=new Set(ws.tokens.filter(t=>t.id!==ally.id&&t.grid_position).map(t=>`${t.grid_position.cell_x}:${t.grid_position.cell_y}`));
    const origin=dorn.grid_position,destination=[[1,0],[-1,0],[0,1],[0,-1]].map(([x,y])=>[origin.cell_x+x,origin.cell_y+y]).find(([x,y])=>x>=0&&y>=0&&x<grid.cols&&y<grid.rows&&!occupied.has(`${x}:${y}`));assert.ok(destination);
    await post(`/workspace/maps/${encodeURIComponent(ws.map.id)}/move`,{request_id:randomUUID(),token_id:ally.id,mode:'GM_REPOSITION',path:[[ally.grid_position.cell_x,ally.grid_position.cell_y],destination],expected_position_version:ally.grid_position.version,expected_grid_version:grid.version});
    await command('start',{map_id:ws.map.id,battle_mode:true,participants:[{target_type:'character',target_id:'dorn7',initiative:30},{target_type:'character',target_id:'vezemir',initiative:20},{target_type:'token',target_id:evidence.enemy_id,initiative:1}]});
    const guard=panel.locator('.dorn-protocol-controls article').filter({has:page.getByRole('button',{name:'Protocolo de Guarda',exact:true})}).first();
    await guard.waitFor();await guard.click({position:{x:8,y:8}});await page.locator('.targeting-overlay').waitFor();
    await page.locator(`[data-grid-token="${ally.id}"]`).click();const confirm=page.getByRole('dialog',{name:'Confirmar alvo'});await confirm.waitFor();await confirm.getByRole('button',{name:'Sim',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.dorn-protocol-controls')?.textContent.includes('ATIVO'));
    const guarded=await get('/combat/effects');assert.equal(guarded.effects.find(e=>e.protocol==='guard').ally_id,'vezemir');
    await command('next_turn');await command('next_turn');
    const beforeAlly=(await get('/characters/vezemir')).state.current_hp,request_id=randomUUID();
    const attack={request_id,attack_id:'0',target_type:'character',target_id:'vezemir',roll_mode:'digital'};
    const resolution=await post(`/gm/combat/tokens/${evidence.enemy_id}/attacks/resolve`,attack);
    assert.equal(resolution.target_id,'dorn7');assert.equal(resolution.breakdown.guard_ally_id,'vezemir');
    const replay=await post(`/gm/combat/tokens/${evidence.enemy_id}/attacks/resolve`,attack);assert.equal(replay.resolution_id,resolution.resolution_id);
    await post(`/combat/attacks/${encodeURIComponent(resolution.resolution_id)}/confirm`,{});
    assert.equal((await get('/characters/vezemir')).state.current_hp,beforeAlly);
    await command('end');
   }
   checks.push({actor,width:390,collapsed:true,status:true,icon_controls:true,full_art:true,compact_filters:role==='gm'?'tested':'sheet-only view',ascending_wallet:true,loadout:true,inventory_heights:heights});await context.close();
  }
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',checks,screenshots:output,production_modified:false}));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
