// Invoked inside the existing four-actor native fixture, using its owned browser.
const assert=require('node:assert/strict'),path=require('node:path');
module.exports=async function bestiaryRulesSmoke({browser,api,base,out,screenshots,checks}){
 assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(![8787,8788].includes(Number(new URL(base).port)));
 const route='/gm/compendium/monsters/dragao-dourado/actions';
 const response=await api.get(route);assert.equal(response.status(),200);
 const data=await response.json();assert.equal(data.rulebook.monster_id,'dragao-dourado');assert.equal(data.rulebook.source.license,'CC BY-SA 4.0');
 const breath=data.rulebook.rules.find(r=>r.name==='Baforada');assert.equal(breath.action_spec.damage_formula,'11d10');assert.equal(breath.execution.status,'native_breath');
 // Native fixture: Dorn is controlled by the GM; Varkh is the fourth player.
 for(const actor of ['raziel','vezemir','morthak','varkh']){
  const headers={'X-Omnisvera-Token':'cf01-local-'+actor};
  const health=await api.get('/health',{headers});assert.equal(health.status(),200);
  assert.equal((await health.json()).access_mode,'player','Check authenticated player identity before testing denial');
  const blocked=await api.get(route,{headers});
  // require_master intentionally returns 401 for every non-master credential.
  assert.equal(blocked.status(),401,`Player ${actor} cannot access private master compendium`);
  assert.ok(!('rulebook' in await blocked.json()));
 }
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:900},isMobile:width===390,hasTouch:width===390});
  try{
   await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.locator('.app-shell.authenticated').waitFor();
   await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/NPCs$/}).click();
   await page.locator('summary').filter({hasText:'Criar, editar ou revelar pins no mapa atual'}).click();
   await page.locator('summary').filter({hasText:'GRIMÓRIO E COMPÊNDIOS'}).click();
   await page.getByRole('button',{name:'Ações de monstros',exact:true}).click();
   const select=page.getByRole('combobox',{name:'Criatura do bestiário'});
   await select.locator('option[value="dragao-dourado"]').waitFor({state:'attached'});await select.selectOption('dragao-dourado');
   const book=page.getByRole('region',{name:'Regras completas de Dragão Dourado'});await book.waitFor();
   const spacing=await book.locator('header').first().evaluate(header=>{const title=header.querySelector('strong').getBoundingClientRect(),source=header.querySelector('small').getBoundingClientRect();return source.left-title.right>=4||source.top>=title.bottom;});
   assert.ok(spacing,'Source and title must have a readable gap or separate lines');
   const card=book.locator('details').filter({has:page.locator('summary strong').filter({hasText:/^Baforada$/})});await card.locator('summary').click();
   const text=await card.innerText();for(const expected of ['11d10','27 m','9 m','3/dia','Automática'])assert.ok(text.includes(expected),expected);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal page overflow');
   const shot=path.join(out,`bestiary-rules-${width}.png`);await book.screenshot({path:shot});screenshots.push(shot);
   await select.selectOption('dragao-das-sombras');const shadow=page.getByRole('region',{name:'Regras completas de Dragão das Sombras'});await shadow.waitFor();
   const shadowCard=shadow.locator('details').filter({has:page.locator('summary strong').filter({hasText:/^Baforada$/})});await shadowCard.locator('summary').click();
   assert.equal(await shadowCard.getByText('Dano',{exact:true}).count(),0);assert.ok((await shadowCard.innerText()).includes('1d6 rodadas'));
   assert.deepEqual(errors,[]);
  }finally{await context.close();}
 }
 checks.push('Bestiary: full source, explicit breath parameters, no sleep dice as damage, mobile/desktop, four player roles forbidden');
};
