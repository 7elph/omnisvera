// Native browser rehearsal. Only CF-01 on loopback and TEMP evidence are allowed.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const { chromium, request } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
(async () => {
  const base = process.env.OMNISVERA_SHEET_QA_URL;
  assert.equal(base, 'http://127.0.0.1:8871');
  const out = fs.realpathSync(process.env.OMNISVERA_QA_EVIDENCE_DIR);
  assert.ok(path.relative(fs.realpathSync(os.tmpdir()), out) && !path.relative(fs.realpathSync(os.tmpdir()), out).startsWith('..'));
  const gm = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Omnisvera-Token': 'cf01-local-gm' } });
  let browser; const errors = [], screenshots = [], actors = ['vezemir','raziel','morthak','dorn7'];
  const get = async p => { const r = await gm.get(p); assert.ok(r.ok(), p + ': ' + r.status()); return r.json(); };
  try {
    const health = await get('/health');
    assert.ok(path.resolve(health.database_path).startsWith(path.resolve(os.tmpdir()) + path.sep));
    const before = {};
    for (const actor of actors) before[actor] = await get('/characters/' + actor);
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    for (const width of [1440,390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      await context.addInitScript(() => { localStorage.setItem('omnisvera_access_token','cf01-local-gm'); localStorage.setItem('omnisvera_access_mode','gm'); localStorage.setItem('omnisvera_selected_character','morthak'); });
      const page = await context.newPage(); page.on('pageerror', e => errors.push(e.message)); page.setDefaultTimeout(45000);
      await page.goto(base); await page.locator('.app-shell.authenticated').waitFor();
      await page.getByRole('navigation',{name:'Navegação principal'}).getByRole('button',{name:/Cenas$/}).click();
      const panel = page.locator('details.scene-workshop');
      await panel.locator(':scope > summary').click();
      await panel.getByRole('button',{name:`Ver bloco ${width === 1440 ? 1 : 2}`,exact:true}).click();
      await panel.getByRole('button',{name:'Revisar e guardar em cena',exact:true}).click();
      await panel.getByLabel('Cena de destino').selectOption({label:'Oficina QA privada · draft'});
      if (width === 1440) {
        await panel.getByRole('button',{name:'Cancelar',exact:true}).click();
        assert.equal((await get('/gm/ai-workshop/jobs/1')).status,'awaiting_approval');
        await panel.getByRole('button',{name:'Revisar e guardar em cena',exact:true}).click();
        await panel.getByLabel('Cena de destino').selectOption({label:'Oficina QA privada · draft'});
      }
      if (width === 1440) {
        await panel.getByRole('button',{name:'Confirmar importação',exact:true}).click();
        await panel.getByText(/Revisão registrada/).waitFor();
      }
      assert.ok(await panel.locator('.scene-workshop-queues .scene-element > div').first().evaluate(e => e.getBoundingClientRect().width >= 100), 'card text column too narrow');
      const shot = path.join(out, `workshop-${width}.png`); await page.screenshot({path:shot,fullPage:true}); screenshots.push(shot);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2), 'horizontal overflow');
      await context.close();
    }
    const detail = await get('/gm/ai-workshop/jobs/1'); assert.equal(detail.status,'completed'); assert.ok(detail.review.element_ids.length > 1);
    for (const role of ['morthak','vezemir','raziel']) {
      const player = await request.newContext({baseURL:base,extraHTTPHeaders:{'X-Omnisvera-Token':`cf01-local-${role}`}});
      assert.equal((await player.get('/gm/ai-workshop')).status(),401);
      assert.equal((await player.get('/gm/ai-workshop/jobs/1')).status(),401);
      assert.equal((await player.post('/gm/ai-workshop/jobs/1/review',{data:{}})).status(),401);
      await player.dispose();
    }
    for (const actor of actors) assert.deepEqual(await get('/characters/'+actor),before[actor],actor+' changed');
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'workshop-report.json'),JSON.stringify({verdict:'PASS',actors,checks:['native GM review','cancel without write','long private import','desktop and mobile','three players denied','four sheets unchanged'],screenshots,visual_acceptance:'PENDING'},null,2));
    console.log('PASS: private workshop native browser rehearsal');
  } finally { if(browser) await browser.close(); await gm.dispose(); }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
