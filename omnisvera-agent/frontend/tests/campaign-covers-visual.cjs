const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const esbuild = require('esbuild');

async function main() {
  const { chromium } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
  const attachment = '../.codex-remote-attachments/01a0264b-3fde-70c2-96f4-88b90861f3ea/e392d0d6-da9c-4da7-bdc4-e980b2e82805';
  const files = ['1-1000208213.jpg', '2-1000208220.jpg', '3-1000208221.jpg', '4-1000208258.jpg', '5-1000208292.jpg'];
  const sessions = Array.from({ length: 6 }, (_, index) => {
    const number = 6 - index;
    return { id: number, session_number: number, title: `Sessão ${number}`, status: 'completed',
      image_path: number <= 5 ? files[number - 1] : null, public_summary: `Resumo público da sessão ${number}.` };
  });
  const bundle = await esbuild.build({ write: false, bundle: true, format: 'iife', jsx: 'automatic',
    plugins: [{ name: 'public-session-fixture', setup(build) {
      build.onResolve({ filter: /^\.\.\/api$/ }, () => ({ path: 'api', namespace: 'fixture' }));
      build.onResolve({ filter: /^\.\/(ConclaveHub|MasterAssetPanel)$/ }, () => ({ path: 'panel', namespace: 'fixture' }));
      build.onLoad({ filter: /.*/, namespace: 'fixture' }, ({ path: fixture }) => ({ loader: 'js', contents: fixture === 'panel'
        ? 'export default function Panel(){return null}'
        : `export const listCampaignSessions=async()=>${JSON.stringify(sessions)};
          export const getActiveScene=async()=>null,listContracts=async()=>[],listPlayableCharacters=async()=>[];
          export const getCurrentOperationalContract=()=>null,mediaUrlFromVaultPath=p=>'/media/'+p;
          export const updateGameSessionMetadata=()=>{},uploadGameSessionImage=()=>{};` }));
    } }], stdin: { resolveDir: process.cwd(), loader: 'tsx', contents: `
      import React from 'react';import{createRoot}from'react-dom/client';import Page from './src/pages/CampaignMemoryPage';
      createRoot(document.getElementById('root')).render(<main className="session-workspace unified-workspace campaign-memory-surface campaign-memory-history"><Page mode="player" view="history" onViewChange={()=>{}}/></main>);` } });
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'campaign-covers-'));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      await page.route('**/media/**', route => route.fulfill({ contentType: 'image/jpeg', body: fs.readFileSync(path.join(attachment, path.basename(new URL(route.request().url()).pathname))) }));
      await page.route('http://fixture.test/', route => route.fulfill({ contentType: 'text/html', body: '<html></html>' }));
      await page.goto('http://fixture.test');
      await page.setContent(`<style>${fs.readFileSync('src/styles.css', 'utf8')} body{background:#101315;margin:0}</style><div id="root"></div><script>${bundle.outputFiles[0].text}</script>`);
      await page.getByRole('button', { name: 'Ver sessão' }).first().waitFor();
      assert.equal(await page.getByRole('button', { name: 'Ver sessão' }).count(), 6);
      await page.waitForFunction(() => [...document.images].every(image => image.complete && image.naturalWidth));
      assert.equal(await page.locator('.campaign-session-image img').count(), 5);
      assert.ok(await page.locator('.campaign-session-image img').evaluateAll(images => images.every(image => getComputedStyle(image).objectFit === 'contain')));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}: overflow`);
      await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
      await page.locator('.campaign-session-grid > article').nth(2).scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(output, `${name}-cover-4.png`), fullPage: true });
      await page.getByRole('button', { name: 'Ver sessão' }).last().click();
      await page.locator('.campaign-detail-hero h1').waitFor();
      assert.equal(await page.locator('.campaign-detail-hero h1').innerText(), 'Sessão 1');
      console.log(`${name} PASS: six sessions, five complete covers, session 1 accessible, no overflow`);
      await page.close();
    }
  } finally { await browser.close(); }
  console.log(`SCREENSHOTS=${output}`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
