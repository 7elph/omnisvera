// Built UI, disposable CF-01 database only. No production credentials.
const assert = require('node:assert/strict');
const { chromium } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES] }));
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1000}});
    await context.addInitScript(() => {
      localStorage.setItem('omnisvera_access_token','cf01-local-gm');
      localStorage.setItem('omnisvera_access_mode','gm');
    });
    const page = await context.newPage();
    const errors=[]; page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:8871');
    const nav=page.getByRole('navigation',{name:'Navegação principal'});
    await nav.getByRole('button',{name:/NPCs$/}).click();
    await page.getByRole('heading',{name:'NPCs e criaturas'}).waitFor();
    await page.getByText('CONTROLES DE NPCs E PINS',{exact:true}).waitFor();
    await nav.getByRole('button',{name:/Sessão$/}).click();
    await page.getByRole('button',{name:'Ver sessão',exact:true}).first().click();
    if (await page.getByRole('button',{name:'Iniciar sessão',exact:true}).isDisabled()) {
      await page.getByRole('button',{name:'Finalizar sessão',exact:true}).click();
      await page.getByText('Sessão finalizada. Estado salvo.',{exact:true}).first().waitFor();
    }
    await page.getByRole('button',{name:'Iniciar sessão',exact:true}).click();
    await page.waitForFunction(() => [...document.querySelectorAll('button')].some(b=>b.textContent==='Iniciar sessão' && b.disabled));
    const finish=page.getByRole('button',{name:'Finalizar sessão',exact:true});
    await finish.click();
    await page.waitForFunction(() => [...document.querySelectorAll('button')].some(b=>b.textContent==='Finalizar sessão' && b.disabled));
    await page.reload();
    await nav.getByRole('button',{name:/Mapas$/}).click();
    // Existing fixture has logical grid and positioned tokens.
    const token=page.locator('[data-grid-sized="true"]').first();
    await token.waitFor();
    await page.waitForFunction(() => {const image=document.querySelector('.workspace-map-stage > img'); return image?.complete && image.naturalWidth>0;});
    async function verifySize() {
      const metrics=await token.evaluate(el=>{
        const stage=el.closest('.workspace-map-stage'), r=el.getBoundingClientRect(), s=stage.getBoundingClientRect();
        return {width:r.width,height:r.height,expectedW:s.width*parseFloat(el.style.width)/100,expectedH:s.height*parseFloat(el.style.height)/100};
      });
      assert.ok(Math.abs(metrics.width-metrics.expectedW)<1,JSON.stringify(metrics));
      assert.ok(Math.abs(metrics.height-metrics.expectedH)<1,JSON.stringify(metrics));
    }
    await verifySize();
    await page.getByRole('button',{name:'Aumentar zoom',exact:true}).click();
    await verifySize();
    await page.setViewportSize({width:390,height:844});
    await verifySize();
    await nav.getByRole('button',{name:/NPCs$/}).click();
    await page.getByRole('heading',{name:'NPCs e criaturas'}).waitFor();
    assert.deepEqual(errors,[]);
    console.log('PASS: NPC sidebar; session start/end and reload; token footprint at desktop/zoom/mobile; no JS errors.');
  } finally { await browser.close(); }
})().catch(e=>{ console.error(e); process.exitCode=1; });
