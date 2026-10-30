// Native built UI against the isolated CF-01 loopback server only.
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os'),{randomUUID}=require('node:crypto');
async function main(){
  const {chromium,request}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
  const base='http://127.0.0.1:8871',output=fs.mkdtempSync(path.join(os.tmpdir(),'omnisvera-map-management-'));
  const api=await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':'cf01-local-gm'}});
  assert.equal((await (await api.get('/health')).json()).access_mode,'gm');
  const state=await (await api.get('/combat/effects')).json();
  if(state.encounter?.active)assert.ok((await api.post('/gm/combat/effects',{data:{request_id:randomUUID(),expected_version:state.version,action:'end',payload:{}}})).ok());
  const browser=await chromium.launch({channel:'msedge',headless:true});const errors=[];
  try{
    const context=await browser.newContext({viewport:{width:1440,height:1000}});
    await context.addInitScript(()=>{localStorage.setItem('omnisvera_access_token','cf01-local-gm');localStorage.setItem('omnisvera_access_mode','gm');});
    const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/media/**',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960"><rect width="1280" height="960" fill="#202530"/></svg>'}));
    await page.goto(base);await page.locator('.app-shell.authenticated').waitFor({timeout:30000});
    const nav=page.getByRole('navigation',{name:'Navegação principal'});
    await nav.getByRole('button',{name:/Mesa$/}).click();
    await page.locator('.logical-map-grid').waitFor({timeout:30000});
    assert.equal(await page.locator('.workspace-map-management').count(),0);
    assert.equal(await page.locator('.workspace-map-panel .workspace-map-upload').count(),0);
    const maps=await (await api.get('/workspace/maps')).json();
    const quickTarget=maps.find(map=>map.title==='S7 · Maré Baixa');assert.ok(quickTarget);
    const selector=page.getByRole('combobox',{name:'Mapa ativo',exact:true});
    await selector.waitFor();assert.ok(await selector.isVisible());
    await selector.selectOption(quickTarget.id);
    await page.waitForFunction(()=>document.querySelector('.workspace-map-panel h2')?.textContent.includes('Maré Baixa'));
    assert.equal(await selector.inputValue(),quickTarget.id);
    assert.equal((await (await api.get('/workspace')).json()).map.id,quickTarget.id);
    await page.reload();await selector.waitFor();assert.equal(await selector.inputValue(),quickTarget.id);
    await nav.getByRole('button',{name:/Mapas$/}).click();
    const manager=page.getByRole('region',{name:'Gerenciamento de mapas'});
    await manager.waitFor();await manager.getByRole('searchbox',{name:'Buscar mapas'}).fill('S7');
    await page.waitForFunction(()=>document.querySelectorAll('.workspace-map-library-list article').length===6);
    const target=manager.locator('.workspace-map-library-list article').filter({hasText:'Conclave'});
    if(!await target.getByText(/Em uso/).count()){
      await target.getByRole('button',{name:'Abrir',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.workspace-map-panel h2')?.textContent.includes('Conclave'));
    }
    await manager.getByRole('searchbox',{name:'Buscar mapas'}).fill('');
    const file=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGZkAAAAASUVORK5CYII=','base64');
    for(let i=1;i<=2;i++){
      const name=`Map manager smoke ${Date.now()} ${i}`;
      await manager.getByRole('textbox',{name:'Nome da imagem'}).fill(name);
      await manager.locator('input[type=file]').setInputFiles({name:'same-image.png',mimeType:'image/png',buffer:file});
      await manager.getByRole('button',{name:'Salvar na biblioteca',exact:true}).click();
      await manager.getByRole('status').filter({hasText:`Imagem salva: ${name}`}).waitFor({timeout:30000});
      await manager.locator('.workspace-map-library-list article').filter({hasText:name}).waitFor({timeout:15000});
      assert.equal(await manager.locator('input[type=file]').inputValue(),'');
      assert.equal(await manager.getByRole('textbox',{name:'Nome da imagem'}).inputValue(),'');
    }
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await selector.scrollIntoViewIfNeeded();assert.ok(await selector.isVisible());
    assert.ok((await selector.boundingBox()).width<390);
    await manager.getByRole('searchbox',{name:'Buscar mapas'}).fill('S7');
    const row=manager.locator('.workspace-map-library-list article').last();await row.scrollIntoViewIfNeeded();
    assert.ok(await row.getByRole('button',{name:'Abrir',exact:true}).isVisible());
    const dims=await manager.locator('.workspace-map-library-list').evaluate(e=>({height:e.clientHeight,scroll:e.scrollHeight,width:e.getBoundingClientRect().width}));
    assert.ok(dims.height>0&&dims.width<390);
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    // A stalled character catalog cannot prevent the independent map list opening.
    await page.route('**/characters',()=>{});await page.reload();
    await page.locator('.app-shell.authenticated').waitFor({timeout:30000});
    await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Mapas$/}).click();
    await page.locator('.workspace-map-library-list article').first().waitFor({timeout:15000});
    assert.deepEqual(errors,[]);
    console.log('QUICK_MAP_SELECTOR=PASS; MAP_SWITCH_PERSISTENCE=PASS; MOBILE_SELECTOR=PASS; MAP_MANAGEMENT=PASS; MESA_CLEAN=PASS; SEARCH_OPEN=PASS; TWO_UPLOADS=PASS; MOBILE_LIST=PASS; STALLED_CHARACTER_INDEPENDENCE=PASS; SCREENSHOTS='+output);
  }finally{await browser.close();await api.dispose();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
