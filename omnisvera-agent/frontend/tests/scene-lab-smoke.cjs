// Private proposal UI against CF-01 TEMP only. No operational credentials, publication, or proposal execution.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
function inTemp(value,allowRoot=false){
 const resolved=fs.realpathSync(value),temp=fs.realpathSync(os.tmpdir());
 const relative=path.relative(temp,resolved);
 assert.ok((relative||allowRoot)&&!relative.startsWith('..')&&!path.isAbsolute(relative),'Fixture/evidence path must remain inside OS TEMP');
 return resolved;
}
(async()=>{
 const base=process.env.OMNISVERA_SHEET_QA_URL;
 assert.equal(base,'http://127.0.0.1:8871','Only the designated isolated CF-01 listener 8871 is allowed');
 const api=await request.newContext({baseURL:base,timeout:20000,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
 const playerApi=await request.newContext({baseURL:base,timeout:20000,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-morthak'}});
 let browser;
 const errors=[],mutations=[],checks=[],screenshots=[];
 const get=async url=>{const response=await api.get(url);assert.ok(response.ok(),`${url}: ${response.status()} ${await response.text()}`);return response.json();};
 try{
  const health=await get('/health');assert.equal(health.access_mode,'gm');inTemp(health.database_path);inTemp(health.vault_path);
  const playerHealth=await playerApi.get('/health');assert.ok(playerHealth.ok());assert.equal((await playerHealth.json()).access_mode,'player');
  const output=process.env.OMNISVERA_QA_EVIDENCE_DIR?path.resolve(process.env.OMNISVERA_QA_EVIDENCE_DIR):fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-scene-lab-'));
  // Validate parent before creation as well as real target, including symlink containment.
  let parent=output;while(!fs.existsSync(parent))parent=path.dirname(parent);inTemp(parent,true);
  fs.mkdirSync(output,{recursive:true});inTemp(output);
  const suffix=randomUUID(),title=`QA privada ${suffix}`,privateMarker=`SEGREDO-LAB-${suffix}`;
  const beforeCombat=await get('/combat/effects');
  const beforeCharacter=await get('/characters/morthak');
  const created=await api.post('/gm/scenes',{data:{request_id:`lab-smoke-scene-${suffix}`,title,location_name:'Fixture isolada',private_notes:privateMarker,visibility:'gm'}});
  assert.ok(created.ok(),await created.text());const scene=await created.json();assert.ok(scene.id>0);assert.equal(scene.visibility,'gm');
  checks.push('CF-01 health confirms TEMP database/vault and public fixture credentials');
  browser=await chromium.launch({channel:'msedge',headless:true});
  async function open(role,width){
   const context=await browser.newContext({viewport:{width,height:900}});context.setDefaultTimeout(60000);
   await context.addInitScript(({role,sceneId})=>{
    localStorage.setItem('omnisvera_access_token',`cf01-local-${role}`);localStorage.setItem('omnisvera_access_mode',role==='gm'?'gm':'player');
    localStorage.setItem('omnisvera_selected_character','morthak');localStorage.setItem('omnisvera_selected_scene',String(sceneId));
   },{role,sceneId:scene.id});
   const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
   page.on('request',r=>{if(['POST','PUT'].includes(r.method())&&r.url().includes('/scene-lab/proposals/'))mutations.push({method:r.method(),url:new URL(r.url()).pathname,body:r.postDataJSON()});});
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();return{context,page};
  }
  const {context:desktop,page}=await open('gm',1440);
  await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).click();
  const lab=page.locator('details').filter({has:page.locator(':scope > summary').filter({hasText:/^Laboratório de propostas · privado$/})});
  await lab.locator(':scope > summary').click();
  await lab.getByLabel('Título da proposta').fill(`Ação QA ${suffix}`);
  await lab.getByLabel('Conteúdo JSON da proposta').fill(JSON.stringify({schema_version:1,private_marker:privateMarker,notes:'Rascunho técnico, não executável'}));
  await lab.getByRole('button',{name:'Criar proposta privada',exact:true}).click();
  await lab.getByText('Revisão 1 · Rascunho',{exact:true}).waitFor();
  let proposals=await get(`/gm/scenes/${scene.id}/lab/proposals`);assert.equal(proposals.length,1);const proposalId=proposals[0].id;
  await lab.getByText('Editar proposta técnica',{exact:true}).click();
  await lab.getByLabel('Conteúdo JSON da proposta').fill(JSON.stringify({schema_version:1,private_marker:privateMarker,notes:'Revisão dois'}));
  await lab.getByRole('button',{name:'Salvar nova revisão',exact:true}).click();await lab.getByText('Revisão 2 · Rascunho',{exact:true}).waitFor();
  await lab.getByText('Conteúdo e histórico · v2',{exact:true}).click();
  const revisionOne=lab.locator('details').filter({has:page.locator(':scope > summary').filter({hasText:/^Revisão 1 ·/})});
  await revisionOne.locator(':scope > summary').click();assert.match(await revisionOne.innerText(),/Rascunho técnico/);
  await lab.getByText('Revisão do Mestre',{exact:true}).click();await lab.getByLabel('Motivo da revisão').fill('Aprovada somente para revisão na fixture, sem execução.');
  await lab.getByRole('button',{name:'Aprovar revisão',exact:true}).click();await lab.getByText('Revisão 2 · Revisada',{exact:true}).waitFor();
  const detail=await get(`/gm/scene-lab/proposals/${proposalId}`);
  assert.equal(detail.version,2);assert.equal(detail.status,'approved');assert.equal(detail.content.notes,'Revisão dois');assert.equal(detail.evidence,null);
  assert.ok(detail.revisions.some(r=>r.version===1&&r.content.notes==='Rascunho técnico, não executável'));
  assert.ok(detail.revisions.some(r=>r.version===2));
  assert.equal(mutations.filter(m=>m.method==='PUT').length,1);assert.equal(mutations.find(m=>m.method==='PUT').body.expected_version,1);
  assert.equal(mutations.filter(m=>m.url.endsWith('/decision')).length,1);assert.equal(mutations.find(m=>m.url.endsWith('/decision')).body.expected_version,2);
  checks.push('GM creates private proposal, persists immutable revisions, views history and approves review without publishing');
  await lab.scrollIntoViewIfNeeded();const desktopShot=path.join(output,'scene-lab-desktop-1440.png');await page.screenshot({path:desktopShot,fullPage:true});screenshots.push(desktopShot);
  await page.reload();await page.locator('.app-shell.authenticated').waitFor();await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).click();
  await lab.locator(':scope > summary').click();await lab.getByRole('button',{name:new RegExp(`Ação QA ${suffix}.*v2`)}).click();await lab.getByText('Revisão 2 · Revisada',{exact:true}).waitFor();checks.push('Reload restores proposal revision and review decision');
  await page.setViewportSize({width:390,height:900});await lab.getByText('Conteúdo e histórico · v2',{exact:true}).click();await lab.scrollIntoViewIfNeeded();
  const metrics=await lab.evaluate(el=>({width:el.getBoundingClientRect().width,overflow:el.scrollWidth>el.clientWidth+2,documentOverflow:document.documentElement.scrollWidth>window.innerWidth+2,inputs:[...el.querySelectorAll('input,textarea,select')].filter(e=>e.getBoundingClientRect().width>0).map(e=>({width:e.getBoundingClientRect().width,overflow:e.getBoundingClientRect().right>window.innerWidth+2}))}));
  assert.ok(metrics.width>250&&!metrics.overflow&&!metrics.documentOverflow,'Private laboratory fits mobile width');assert.ok(metrics.inputs.every(e=>!e.overflow),'Inputs remain reachable on mobile');
  const mobileShot=path.join(output,'scene-lab-mobile-390.png');await page.screenshot({path:mobileShot,fullPage:true});screenshots.push(mobileShot);checks.push({mobile_width:390,metrics});
  const {context:ownerContext,page:owner}=await open('morthak',390);
  assert.equal(await owner.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).count(),0);
  await owner.evaluate(()=>window.dispatchEvent(new CustomEvent('omnisvera-open-workspace',{detail:'scenes'})));
  assert.equal(await owner.getByText('Laboratório de propostas · privado',{exact:true}).count(),0);
  for(const url of [`/gm/scenes/${scene.id}/lab/proposals`,`/gm/scene-lab/proposals/${proposalId}`]){const response=await playerApi.get(url);assert.ok([401,403].includes(response.status()),`Private API rejects player: ${response.status()}`);}
  const publicScenes=await playerApi.get('/scenes');assert.ok(publicScenes.ok());const publicText=await publicScenes.text();assert.ok(!publicText.includes(privateMarker)&&!publicText.includes(title));
  assert.deepEqual(await get('/combat/effects'),beforeCombat,'Proposal review cannot alter combat state');
  const afterCharacter=await get('/characters/morthak');assert.deepEqual(afterCharacter.state,beforeCharacter.state,'Proposal review cannot alter character state');assert.deepEqual(afterCharacter.inventory,beforeCharacter.inventory,'Proposal review cannot alter inventory');
  checks.push('Player cannot navigate to private laboratory or read its API; combat and character unchanged');
  assert.deepEqual(errors,[]);await ownerContext.close();await desktop.close();
  console.log(JSON.stringify({status:'PASS',scope:'isolated_private_scene_lab_ui_only',proposal_id:proposalId,scene_id:scene.id,checks,screenshots,visual_acceptance:'pending_human_or_agent_image_review',real_networks:'INCONCLUSIVE',proposal_execution:'NOT_IMPLEMENTED_NOT_TESTED'}));
 }finally{await browser?.close();await playerApi.dispose();await api.dispose();}
})().catch(error=>{console.error(error);process.exitCode=1;});
