// Built browser + temporary CF-01 backend. Never operational credentials/data.
const assert=require('node:assert/strict');
const {randomUUID}=require('node:crypto');
const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES]}));
(async()=>{
  const base='http://127.0.0.1:8871';
  const gm=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
  const player=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-morthak'}});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const read=async(client,url)=>{const r=await client.get(url);assert.ok(r.ok(),url);return r.json();};
  const post=async(client,url,data)=>{const r=await client.post(url,{data});assert.ok(r.ok(),await r.text());return r.json();};
  try {
    assert.equal((await read(gm,'/health')).access_mode,'gm');
    await post(gm,'/characters/morthak/actions',{action:'rest_at_inn',payload:{},reason:'Preparação da fixture descartável',request_id:'necro-smoke-rest-'+randomUUID()});
    const workspace=await read(gm,'/workspace'), name='QA necromancer '+randomUUID();
    const creature=await post(gm,'/gm/workspace/tokens',{token_type:'monster',name,map_id:workspace.map.id,
      visible_to_players:true,latitude:50,longitude:50,current_hp:50,maximum_hp:50,
      sheet:{armor_class:1,hit_dice:'1',saving_throw:99,attributes:{strength:10,constitution:10,wisdom:10}}});
    const context=await browser.newContext({viewport:{width:390,height:844}});
    await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-morthak');localStorage.setItem('omnisvera_access_mode','player');});
    const page=await context.newPage(), errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(base);
    await page.locator('.app-shell.authenticated').waitFor();
    await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Ficha$/}).click();
    await page.locator('.workspace-character-identity h2').waitFor();
    const before=await read(player,'/characters/morthak');
    assert.equal(before.definition.level,5);
    const card=title=>page.locator('article.workspace-spell-card').filter({hasText:title});
    await card('Toque Sombrio').getByRole('button',{name:'Preparar magia'}).click();
    let panel=page.getByRole('region',{name:'Conjuração de Necromante'});
    await panel.getByLabel(name,{exact:true}).check();
    await panel.getByLabel('Alvo ao alcance do toque, conferido com o Mestre').check();
    await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
    const preview=page.getByRole('dialog',{name:'Resolução do ataque'});
    await preview.waitFor();
    await preview.getByRole('button',{name:/Confirmar/}).click();
    await preview.getByRole('button',{name:'Concluído',exact:true}).waitFor();
    await preview.getByRole('button',{name:'Fechar resolução'}).click();
    const after=await read(player,'/characters/morthak');
    assert.equal(after.state.resources.find(r=>r.key==='toque_sombrio').current,0);
    await card('Aterrorizar').getByRole('button',{name:'Preparar magia'}).click();
    panel=page.getByRole('region',{name:'Conjuração de Necromante'});
    await panel.getByLabel(name,{exact:true}).check();
    await panel.getByLabel('Distância dos alvos').fill('5');
    await panel.getByLabel('Alvos no raio da magia, conferidos com o Mestre').check();
    await panel.getByRole('button',{name:'Conjurar',exact:true}).click();
    await panel.getByRole('status').filter({hasText:'aterrorizado'}).waitFor();
    let effects=await read(gm,'/combat/effects');
    assert.ok(effects.effects.some(e=>e.target_id===creature.id && e.necro_spell==='aterrorrizar'));
    const missileBefore=(await read(player,'/characters/morthak')).state.resources.find(r=>r.key==='misseis_magicos');
    await card('Mísseis Mágicos').getByLabel('Alvo de Mísseis Mágicos').selectOption(creature.id);
    await card('Mísseis Mágicos').getByRole('button',{name:'Usar',exact:true}).click();
    const missile=page.getByRole('dialog',{name:'Resolução da magia'});
    await missile.getByRole('button',{name:'Confirmar uso e aplicar dano'}).click();
    await missile.getByRole('button',{name:'Concluído',exact:true}).waitFor();
    await missile.getByRole('button',{name:'Concluído',exact:true}).click();
    const missileAfter=(await read(player,'/characters/morthak')).state.resources.find(r=>r.key==='misseis_magicos');
    assert.equal(missileAfter.current,missileBefore.current-1);
    assert.equal(missileAfter.maximum,missileBefore.maximum);
    await page.reload();
    assert.ok((await read(gm,'/combat/effects')).effects.some(e=>e.target_id===creature.id && e.necro_spell==='aterrorrizar'));
    const ledger=await read(player,'/workspace/ledger');
    assert.ok(ledger.some(e=>e.title.includes('Aterrorizar')));
    await post(gm,'/gm/combat/effects',{request_id:'necro-smoke-time-'+randomUUID(),expected_version:effects.version,action:'necro_spell_time',payload:{turns:100}});
    assert.ok(!(await read(gm,'/combat/effects')).effects.some(e=>e.target_id===creature.id && e.necro_spell==='aterrorrizar'));
    assert.deepEqual(errors,[]);
    console.log('PASS: mobile Morthak level 5; touch preview/confirmation/cost; fear cast/save/duration; missiles usable with one cost; reload; public ledger; exploration expiration.');
  } finally {await browser.close();await gm.dispose();await player.dispose();}
})().catch(e=>{console.error(e);process.exitCode=1;});
