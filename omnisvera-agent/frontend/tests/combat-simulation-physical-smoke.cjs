// Native built UI against the guarded disposable simulation, NEVER production.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
 const evidencePath=path.resolve(process.env.OMNISVERA_SIMULATION_EVIDENCE||'');
 assert.ok(evidencePath.startsWith(path.resolve(os.tmpdir())+path.sep),'Evidence must belong to the temporary simulation');
 const evidence=JSON.parse(fs.readFileSync(evidencePath,'utf8'));
 assert.ok(evidence.run_id.startsWith('simulation-'));
 const base=process.env.OMNISVERA_SHEET_QA_URL||'http://127.0.0.1:8871',api={};
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 for(const role of ['gm','vezemir','morthak','raziel'])api[role]=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-'+role}});
 const get=async(role,url)=>{const r=await api[role].get(url);assert.ok(r.ok(),url);return r.json();};
 const post=async(role,url,data)=>{const r=await api[role].post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const browser=await chromium.launch({channel:'msedge',headless:true}),errors=[],calls=[],screens=[];
 const command=async(action,payload={})=>post('gm','/gm/combat/effects',{request_id:'physical-smoke-'+randomUUID(),expected_version:(await get('gm','/combat/effects')).version,action,payload});
 try{
  const workspace=await get('gm','/workspace');assert.ok(workspace.tokens.some(t=>t.id===evidence.enemy_id&&t.name===evidence.enemy_name),'Fixture marker missing');
  assert.equal(workspace.table_mode,'physical');
  for(const actor of ['vezemir','morthak','raziel']){
   const gm=await get('gm','/characters/'+actor),owner=await get(actor,'/characters/'+actor);
   for(const key of ['level','attributes','attacks','defenses','session_abilities'])assert.deepEqual(owner.definition[key],gm.definition[key],actor+' '+key);
   assert.deepEqual(owner.state,gm.state,actor+' state');
   assert.deepEqual(owner.inventory,gm.inventory,actor+' inventory');
  }
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-physical-ui-'));
  async function open(role,actor,width=1440){
   const context=await browser.newContext({viewport:{width,height:width===390?844:1000}});
   await context.addInitScript(({role,actor})=>{localStorage.setItem('omnisvera_access_token','cf01-local-'+role);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');localStorage.setItem('omnisvera_selected_character',actor);},{role,actor});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/techniques/'))calls.push({role,url:r.url(),body:r.postDataJSON()});});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:role==='gm'?/Mesa$/:/Ficha$/}).click();
   const actorName=(await get('gm','/characters/'+actor)).definition.name;
   await page.getByRole('button',{name:'Abrir ficha de '+actorName,exact:true}).click();
   await page.locator('.workspace-character-identity').waitFor();
   return page;
  }
  async function reloadSheet(page){
   await page.reload();await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
   await page.locator('.workspace-character-identity').waitFor();
  }
  const gm=await open('gm','morthak'),owner=await open('morthak','morthak',390);
  const prepare=async page=>{
   await page.locator('article.workspace-spell-card').filter({hasText:'Toque Sombrio'}).getByRole('button',{name:'Preparar magia'}).click();
   const panel=page.getByRole('region',{name:'Conjuração de Necromante'});
   await panel.getByLabel(evidence.enemy_name,{exact:true}).check();
   await panel.getByLabel('d20 físico de Toque Sombrio').fill('15');
   assert.equal(await panel.getByRole('button',{name:'Conjurar',exact:true}).isEnabled(),true);
   return panel;
  };
  await prepare(gm);const panel=await prepare(owner);
  for(const [name,page] of [['gm',gm],['owner-mobile',owner]]){const file=path.join(output,name+'-physical-touch.png');await page.screenshot({path:file,fullPage:true});screens.push(file);}
  const before=await get('morthak','/characters/morthak');
  await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
  const preview=owner.getByRole('dialog',{name:'Resolução do ataque'});await preview.waitFor();
  await preview.getByRole('button',{name:/Confirmar/}).click();await preview.getByRole('button',{name:'Concluído',exact:true}).waitFor();
  await preview.getByRole('button',{name:'Fechar resolução'}).click();
  const after=await get('morthak','/characters/morthak');
  const counter=s=>s.state.resources.find(r=>r.key==='toque_sombrio').current;
  assert.equal(counter(after),counter(before)-1);
  const touch=calls.filter(c=>c.url.endsWith('/toque-sombrio'));assert.equal(touch.length,1);assert.equal(touch[0].body.d20,15);assert.equal(touch[0].body.roll_mode,'physical');
  // An accepted command must appear on the other client without refreshing it.
  await gm.waitForFunction(()=>document.querySelector('[aria-label="Conjuração de Necromante"]')?.textContent.includes('Uso diário: 0/1'));
  await command('end');
  await post('gm','/characters/raziel/actions',{action:'rest_at_inn',payload:{},request_id:'physical-smoke-rest-'+randomUUID(),reason:'Somente fixture'});
  const restore=await api.gm.patch('/gm/workspace/tokens/'+evidence.enemy_id,{data:{current_hp:evidence.monster.average_hp}});assert.ok(restore.ok());
  await command('start',{title:'Ensaio Physical de Raziel',map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:30,name:'Raziel'},{target_type:'token',target_id:evidence.enemy_id,initiative:1,name:evidence.enemy_name}]});
  const gmRaz=await open('gm','raziel'),ownerRaz=await open('raziel','raziel',390);
  async function blade(page){
   await page.getByLabel('Forma da Hemomancia',{exact:true}).selectOption('lamina-de-sangue');
   const card=page.locator('article').filter({has:page.getByRole('combobox',{name:'Modo da Lâmina de Sangue',exact:true})});
   assert.equal(await card.count(),1);
   await card.getByRole('combobox',{name:'Alvo de Lâmina de Sangue',exact:true}).selectOption(evidence.enemy_id);
   await card.getByRole('combobox',{name:'Modo da Lâmina de Sangue',exact:true}).selectOption('ranged');
   await card.getByLabel('d20 físico de Lâmina de Sangue').fill('15');
   assert.equal(await card.getByRole('button',{name:'Usar',exact:true}).isEnabled(),true);
   return card;
  }
  const bladeGM=await blade(gmRaz);await blade(ownerRaz);
  const bloodBefore=(await get('raziel','/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current;
  await bladeGM.getByRole('button',{name:'Usar',exact:true}).click();
  const blood=gmRaz.getByRole('dialog',{name:'Resolução do ataque'});await blood.waitFor();
  await blood.getByRole('button',{name:/Confirmar/}).click();await blood.getByRole('button',{name:'Concluído',exact:true}).waitFor();
  const packets=calls.filter(c=>c.url.endsWith('/lamina-de-sangue'));assert.equal(packets.length,1);assert.equal(packets[0].body.roll_mode,'physical');assert.equal(packets[0].body.d20,15);
  assert.equal((await get('raziel','/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current,bloodBefore-packets[0].body.charges);
  await reloadSheet(ownerRaz);
  assert.equal((await get('gm','/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current,bloodBefore-packets[0].body.charges);
  await blood.getByRole('button',{name:'Fechar resolução'}).click();
  const browserResults=[];
  async function resetRaziel(){
   if((await get('gm','/combat/effects')).encounter?.active)await command('end');
   await post('gm','/characters/raziel/actions',{action:'rest_at_inn',payload:{},request_id:'approved-smoke-rest-'+randomUUID(),reason:'Somente fixture'});
   assert.ok((await api.gm.patch('/gm/workspace/tokens/'+evidence.enemy_id,{data:{current_hp:evidence.monster.average_hp}})).ok());
   await command('start',{title:'Ensaio de poderes aprovados',map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'raziel',initiative:30,name:'Raziel'},{target_type:'token',target_id:evidence.enemy_id,initiative:1,name:evidence.enemy_name}]});
   await reloadSheet(ownerRaz);
  }
  for(const [id,name,cost] of [['arma-de-sangue','Arma de Sangue',2],['garras-predatorias','Garras Predatórias',1],['investida-predatoria','Investida Predatória',2]]){
   await resetRaziel();
   await ownerRaz.getByLabel('Forma da Hemomancia',{exact:true}).selectOption(id);
   const card=ownerRaz.locator('article').filter({has:ownerRaz.getByRole('combobox',{name:'Alvo de '+name,exact:true})});
   assert.equal(await card.count(),1);
   await card.getByRole('combobox',{name:'Alvo de '+name,exact:true}).selectOption(evidence.enemy_id);
   await card.getByLabel('d20 físico de '+name).fill('15');
   await card.getByRole('button',{name:'Usar',exact:true}).click();
   const preview=ownerRaz.getByRole('dialog',{name:'Resolução do ataque'});await preview.waitFor();
   const packets=calls.filter(c=>c.url.endsWith('/'+id));assert.equal(packets.length,1);assert.equal(packets[0].body.roll_mode,'physical');assert.equal(packets[0].body.d20,15);
   await preview.getByRole('button',{name:/Confirmar/}).click();await preview.getByRole('button',{name:'Concluído',exact:true}).waitFor();
   await preview.getByRole('button',{name:'Fechar resolução'}).click();
   const current=(await get('raziel','/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current;assert.equal(current,10-cost);
   browserResults.push({id,physical_d20:15,blood_before:10,blood_after:current});
  }
  await resetRaziel();
  await ownerRaz.getByLabel('Forma da Hemomancia',{exact:true}).selectOption('sangue-defensivo');
  const shield=ownerRaz.locator('article').filter({has:ownerRaz.getByRole('button',{name:'Sangue Defensivo',exact:true})});
  const acBefore=(await get('raziel','/characters/raziel')).definition.defenses.armor_class;
  await shield.getByRole('button',{name:'Usar',exact:true}).click();
  await ownerRaz.waitForFunction(()=>!document.querySelector('.workspace-character-panel')?.textContent.includes('Poder aceito.'));
  for(let attempt=0;attempt<20;attempt++){
   if((await get('raziel','/characters/raziel')).state.resources.find(r=>r.key==='reserva_de_sangue').current===8)break;
   await ownerRaz.waitForTimeout(100);
  }
  assert.equal((await get('raziel','/characters/raziel')).definition.defenses.armor_class,acBefore+2);
  assert.equal(calls.filter(c=>c.url.endsWith('/sangue-defensivo')).length,1);
  await command('round');assert.equal((await get('raziel','/characters/raziel')).definition.defenses.armor_class,acBefore);
  browserResults.push({id:'sangue-defensivo',armor_class_bonus:2,expired:true});
  await command('end');
  await post('gm','/characters/raziel/actions',{action:'damage',payload:{amount:3},request_id:'coffin-wound-'+randomUUID(),reason:'Somente fixture'});
  await reloadSheet(ownerRaz);
  let coffin=ownerRaz.locator('article').filter({has:ownerRaz.getByRole('button',{name:'Caixão',exact:true})});
  await coffin.getByRole('button',{name:'Usar',exact:true}).click();
  await coffin.getByRole('button',{name:'Usar',exact:true}).waitFor({state:'visible'});
  for(let attempt=0;attempt<20;attempt++){
   if((await get('raziel','/characters/raziel')).state.resources.find(r=>r.key==='caixao').current===0)break;
   await ownerRaz.waitForTimeout(100);
  }
  const rested=await get('raziel','/characters/raziel');assert.equal(rested.state.current_hp,rested.state.maximum_hp);assert.equal(rested.state.resources.find(r=>r.key==='caixao').current,0);
  await reloadSheet(ownerRaz);
  coffin=ownerRaz.locator('article').filter({has:ownerRaz.getByRole('button',{name:'Caixão',exact:true})});assert.equal(await coffin.getByRole('button',{name:'Usar',exact:true}).isDisabled(),true);
  await coffin.screenshot({path:path.join(output,'coffin-mobile.png')});
  await post('gm','/characters/raziel/actions',{action:'rest_at_inn',payload:{},request_id:'coffin-gm-rest-'+randomUUID(),reason:'Somente fixture'});
  await reloadSheet(ownerRaz);
  assert.equal(await ownerRaz.locator('article').filter({has:ownerRaz.getByRole('button',{name:'Caixão',exact:true})}).getByRole('button',{name:'Usar',exact:true}).isEnabled(),true);
  browserResults.push({id:'caixao',owner_rest:true,locked_before_gm_rest:true,recharged_by_gm:true});
  // Real inventory in copied sheet: no test-only replacement for this UI case.
  const dornBefore=await get('gm','/characters/dorn7'),kitBefore=dornBefore.inventory.find(i=>i.item_title==='Kit de Reparo').quantity;
  assert.ok(kitBefore>0);
  assert.ok((await api.gm.patch('/gm/workspace/tokens/'+evidence.enemy_id,{data:{current_hp:evidence.monster.average_hp}})).ok());
  await command('start',{title:'Ensaio de Reparo e ataque',map_id:evidence.map_id,battle_mode:true,participants:[{target_type:'character',target_id:'dorn7',initiative:30,name:'Dorn'},{target_type:'token',target_id:evidence.enemy_id,initiative:1,name:evidence.enemy_name}]});
  const dornPage=await open('gm','dorn7');
  const repair=dornPage.locator('.workspace-resource-catalog article').filter({hasText:'Reparo'});
  await repair.getByRole('button',{name:'Usar',exact:true}).click();
  for(let attempt=0;attempt<20;attempt++){
   if((await get('gm','/characters/dorn7')).inventory.find(i=>i.item_title==='Kit de Reparo').quantity===kitBefore-1)break;
   await dornPage.waitForTimeout(100);
  }
  assert.equal((await get('gm','/characters/dorn7')).inventory.find(i=>i.item_title==='Kit de Reparo').quantity,kitBefore-1);
  const melee=dornPage.locator('.workspace-attack-catalog article').filter({has:dornPage.getByRole('combobox',{name:'Alvo de Corpo a corpo',exact:true})});
  await melee.getByRole('combobox',{name:'Alvo de Corpo a corpo',exact:true}).selectOption(evidence.enemy_id);
  await melee.getByLabel('Resultado físico de Corpo a corpo').fill('15');
  await melee.getByRole('button',{name:'Atacar',exact:true}).click();
  const dornPreview=dornPage.getByRole('dialog',{name:'Resolução do ataque'});await dornPreview.getByRole('button',{name:/Confirmar/}).click();await dornPreview.getByRole('button',{name:'Concluído',exact:true}).waitFor();
  browserResults.push({id:'dorn-reparo',kits_before:kitBefore,kits_after:kitBefore-1,attack_in_same_turn:true});
  await command('end');
  fs.writeFileSync(path.join(path.dirname(evidencePath),'browser-actions-evidence.json'),JSON.stringify({browserResults,technicalCalls:calls,screenshots:output},null,2));
  assert.deepEqual(errors,[]);
  console.log('PASS: GM/owner parity; Physical touch/blade/three approved blood weapons; defensive blood cost/expiry; owner Coffin locked until GM rest; Dorn consumes one kit and attacks in same turn; multiclient refresh; reload; no JS errors. SCREENSHOTS='+output);
 }finally{await browser.close();for(const client of Object.values(api))await client.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
