const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const assert = require('node:assert/strict'), esbuild = require('esbuild');

async function main() {
  const { chromium } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  const start = source.indexOf('return <button key={item.id} type="button" data-character={item.id}');
  const end = source.indexOf('</button>;', start);
  assert.ok(start > 0 && end > start);
  // Render the actual party selector and effect component against the full CSS cascade.
  const markup = source.slice(start + 'return '.length, end + '</button>'.length);
  const bundle = await esbuild.build({ write: false, bundle: true, format: 'iife', jsx: 'automatic',
    define: { 'import.meta.env.VITE_API_BASE_URL': '""' },
    stdin: { loader: 'tsx', resolveDir: process.cwd(), contents: `
      import React from 'react'; import {createRoot} from 'react-dom/client';
      import ActiveEffectIcons from './src/components/ActiveEffectIcons';
      const item={id:'vezemir',name:'Vezemir',conditions:[],level:4,current_hp:27,maximum_hp:27};
      const mode='gm',selectable=true,gmToolsOpen=false,selectedAllyId='',npcLibraryOpen=false,selectedId='vezemir',online=true,hpPercent=100;
      const setSelectedAllyId=()=>{},setNpcLibraryOpen=()=>{},setGmToolsOpen=()=>{},setSelectedId=()=>{},selectedIdRef={current:''},characterColor=()=> '#ddd';
      const CharacterPortrait=()=> <img src="https://fixture/icon.svg" alt="Vezemir"/>;
      const effects=['Velocidade','Força Arcana','Escuridão'].map((name,i)=>({effect_id:'e'+i,target_type:'character',target_id:'vezemir',duration:'rounds',rounds:3,card:{id:'card'+i,name,image_path:'fixture.svg'}}));
      function App(){const [active,setActive]=React.useState(true);const battleState={active_effect_icons:active?effects:[]};
        return <main className="unified-workspace"><header className="party-status-header"><div className="party-status-title">Grupo</div><div className="party-status-list">${markup}</div></header><button onClick={()=>setActive(false)}>Expirar efeitos</button></main>}
      createRoot(document.getElementById('root')).render(<App/>);
    ` } });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'active-effect-header-'));
  try {
    for (const [name, width, height] of [['mobile', 390, 844], ['desktop', 1440, 900]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      const errors = []; page.on('pageerror', error => errors.push(error.message));
      await page.route('http://fixture/**', route => route.fulfill({ body: '<html></html>', contentType: 'text/html' }));
      await page.route('http://fixture/media/**', route => route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22"><rect width="22" height="22" fill="blue"/></svg>' }));
      await page.route('https://fixture/icon.svg', route => route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22"><rect width="22" height="22" fill="blue"/></svg>' }));
      await page.goto('http://fixture/');
      await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css', 'utf8')}</style></head><body><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
      const icons = page.locator('.party-status-list .workspace-active-effect-icons img');
      await icons.first().waitFor(); assert.equal(await icons.count(), 3);
      await page.waitForFunction(() => [...document.querySelectorAll('.workspace-active-effect-icons img')].every(img => img.complete && img.naturalWidth > 0));
      const boxes = await Promise.all([0, 1, 2].map(i => icons.nth(i).boundingBox()));
      boxes.forEach((box, i) => { assert.ok(Math.abs(box.y - boxes[0].y) < 1, `${name}: same horizontal row`); if (i) assert.ok(box.x >= boxes[i - 1].x + boxes[i - 1].width, `${name}: side by side`); });
      const strip = page.locator('.workspace-active-effect-icons');
      assert.equal(await strip.evaluate(el => getComputedStyle(el).display), 'flex');
      assert.equal(await strip.evaluate(el => getComputedStyle(el).flexWrap), 'nowrap');
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.deepEqual(errors, []);
      await page.screenshot({ path: path.join(folder, name + '.png') });
      await page.getByRole('button', { name: 'Expirar efeitos' }).click();
      await strip.waitFor({ state: 'detached' });
      assert.deepEqual(errors, []);
      console.log(`${name}: PASS horizontal header, three icons, expiration removes strip, no overflow`);
      await page.close();
    }
  } finally { await browser.close(); }
  console.log('SCREENSHOTS=' + folder);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
