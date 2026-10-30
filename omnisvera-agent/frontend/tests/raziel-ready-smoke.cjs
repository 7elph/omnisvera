// Native UI and disposable CF-01 server only; no production credentials/actions.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL||'http://127.0.0.1:8872';assert.match(base,/^http:\/\/127\.0\.0\.1:887[12]$/);
 const gm=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const owner=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-raziel'}});
 const get=async(api,url)=>{const r=await api.get(url);assert.ok(r.ok(),url);return r.json();};
 const post=async(api,url,data)=>{const r=await api.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
 const act=async(action,payload={})=>post(gm,'/characters/raziel/actions',{action,payload,request_id:randomUUID(),reason:'Fixture only'});
 const e=await get(gm,'/combat/effects');if(e.encounter?.active)await post(gm,'/gm/combat/effects',{action:'end',payload:{},expected_version:e.version,request_id:randomUUID()});
 await act('rest_at_inn');assert.ok((await gm.patch('/gm/workspace/table-mode',{data:{table_mode:'physical'}})).ok());
 const workspace=await get(gm,'/workspace');const target=await post(gm,'/gm/workspace/tokens',{token_type:'monster',name:'Alvo de ensaio Raziel',map_id:workspace.map.id,visible_to_players:true,latitude:50,longitude:50,current_hp:50,maximum_hp:50,sheet:{armor_class:1}});
 const browser=await chromium.launch({channel:'msedge',headless:true}),out=fs.mkdtempSync(path.join(os.tmpdir(),'raziel-ready-ui-'));
 const context=await browser.newContext({viewport:{width:390,height:844}});await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-raziel');localStorage.setItem('omnisvera_access_mode','player');});
 const page=await context.newPage(),errors=[],commands=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/attacks/resolve'))commands.push(r.postDataJSON());});
 const open=async()=>{await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();await page.locator('button[data-character="raziel"]').click();await page.locator('.workspace-character-identity').waitFor();};
 const confirm=async()=>{const modal=page.getByRole('dialog',{name:'Resolução do ataque'});await modal.waitFor();await modal.getByRole('button',{name:/Confirmar/}).click();await modal.getByRole('button',{name:'Concluído',exact:true}).waitFor();await modal.getByRole('button',{name:'Fechar resolução'}).click();};
 try{
  await open();const hemo=page.getByRole('region',{name:'Hemomancia',exact:true});assert.equal(await hemo.locator('article').count(),1);
  assert.equal(await hemo.getByLabel('Lâminas declaradas',{exact:true}).locator('option').count(),10);
  const item='item:Items/Adagas de Espectro Fantasma.md';await hemo.getByLabel('Forma da Hemomancia',{exact:true}).selectOption(item);
  await hemo.getByLabel('Modo da arma equipada',{exact:true}).selectOption('ranged');
  await hemo.getByLabel('Sangue para reforçar arma',{exact:true}).selectOption('10');
  await hemo.getByLabel('Alvo de À distância',{exact:true}).selectOption(target.id);
  await hemo.getByLabel('d20 físico da arma equipada',{exact:true}).fill('20');await hemo.getByRole('button',{name:'Atacar',exact:true}).click();
  const before=await get(owner,'/characters/raziel');assert.equal(before.state.resources.find(r=>r.key==='reserva_de_sangue').current,10,'Preview does not spend blood');
  await confirm();const after=await get(owner,'/characters/raziel');assert.equal(after.state.resources.find(r=>r.key==='reserva_de_sangue').current,0);assert.equal(commands.length,1);assert.equal(commands[0].blood_boost,10);
  await hemo.screenshot({path:path.join(out,'hemomancia-mobile.png')});
  await act('rest_at_inn');await open();
  const selector=page.getByLabel('Animal da Forma da Noite',{exact:true});assert.equal(await selector.locator('img').count(),0);
  assert.equal(await page.getByRole('group',{name:'Escolher animal da Forma da Noite'}).isVisible(),false);
  await selector.click();await page.getByRole('button',{name:'Coruja',exact:true}).click();
  await page.getByRole('switch',{name:'Forma da Noite',exact:true}).click();
  await page.getByRole('switch',{name:'Forma da Noite',exact:true}).filter({hasText:'Desativar'}).waitFor();
  const animal=await get(owner,'/characters/raziel');assert.equal(animal.state.current_hp,1);assert.equal(animal.definition.defenses.armor_class,14);assert.equal(animal.definition.defenses.saving_throw,4);
  assert.equal(animal.state.animal_form,'coruja');assert.equal(await page.getByLabel('Forma da Hemomancia',{exact:true}).isDisabled(),true);
  const denied=await owner.post('/characters/raziel/techniques/lamina-de-sangue',{data:{request_id:randomUUID(),charges:1,target_type:'token',target_id:target.id,roll_mode:'physical',d20:20}});assert.equal(denied.status(),400);
  await page.screenshot({path:path.join(out,'coruja-active-mobile.png')});
  const normalBefore=animal.state.normal_current_hp;await act('damage',{amount:5});await open();
  const returned=await get(owner,'/characters/raziel');assert.equal(returned.state.current_hp,normalBefore-4);assert.ok(!returned.state.animal_form);
  assert.equal(returned.state.resources.find(r=>r.key==='forma_da_noite').current,2);
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'PASS',blood_boost:10,one_command:true,animal_overflow:4,reload:true,screenshots:out}));
 }finally{await browser.close();await gm.dispose();await owner.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1});
