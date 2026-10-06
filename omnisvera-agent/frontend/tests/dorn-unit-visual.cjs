// Isolated browser QA of the real component/CSS; no campaign API or tokens.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

async function main() {
  const { chromium } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
  const fixtureModule = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync('src/components/DornUnitIdentity.tsx', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  const controlsModule = { exports: {} };
  const controlsCode = ts.transpileModule(fs.readFileSync('src/components/DornProtocolControls.tsx', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  vm.runInNewContext(controlsCode, { module: controlsModule, exports: controlsModule.exports, require: id => id === '../api' ? {} : require(id) });
  vm.runInNewContext(code, { module: fixtureModule, exports: fixtureModule.exports, require: id => id === './DornProtocolControls' ? controlsModule.exports : require(id) });
  const spec = JSON.parse(fs.readFileSync('../backend/app/data/dorn7_mage2.json', 'utf8'));
  const character = { access_level: 'gm', definition: { id: 'dorn7', race: spec.sheet.race.race, abilities: { racial: spec.sheet.race.racial_abilities }, session_abilities: spec.abilities }, state: { current_hp: 9, maximum_hp: 13, conditions: [] }, inventory: spec.items.map((item, i) => ({ id: i, item_title: item.name, item_type: item.type })) };
  character.definition.session_abilities = [...spec.abilities, ...['Guarda', 'Vanguarda', 'Diagnóstico'].map((name, i) => ({id:`dorn_fixture_${i}`,name,kind:'technique',group:'Ações / Protocolos'}))];
  const combat = { version: 1, encounter: {active: true, action_committed: true, turn_index: 0, participants: [{target_type:'character',target_id:'dorn7',name:'Dorn'},{target_type:'character',target_id:'vezemir',name:'Vezemir'}]}, effects: [{id:'dorn:guard',target_type:'character',target_id:'dorn7',label:'Protocolo de Guarda',protocol:'guard',ally_id:'vezemir',until:'Início do próximo turno de Dorn',duration:'manual',rounds:null,modifiers:{}},{ id: 'test', target_type: 'character', target_id: 'dorn7', label: 'Escudo Arcano — efeito fixture', duration: 'rounds', rounds: 2, modifiers: { armor_class: 4 } }] };
  const html = renderToStaticMarkup(React.createElement(fixtureModule.exports.default, { character, combat, onProtocolChange:async()=>{}, onOpenMagic: () => {}, onInspectItem: () => {} }));
  const css = fs.readFileSync('src/styles.css', 'utf8');
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'companion-dorn-visual-'));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    for (const [name, width, height] of [['mobile', 390, 844], ['desktop', 1440, 900]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      await page.route('**/*', route => route.abort());
      await page.setContent(`<html><head><style>${css}\nbody{background:#101315;color:#ddd;margin:0}main{max-width:440px;padding:12px;box-sizing:border-box}button{color:inherit}</style></head><body><main><small>QA ISOLADO · DADOS FIXTURE</small><h2>DORN-7</h2>${html}</main></body></html>`);
      await page.screenshot({ path: path.join(output, `${name}-collapsed.png`), fullPage: true });
      for (const summary of await page.locator('.dorn-unit-identity summary').all()) await summary.click();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${name}: horizontal overflow`);
      await page.screenshot({ path: path.join(output, `${name}-expanded.png`), fullPage: true });
      assert.ok(await page.getByText('Protocolo de Guarda · ATIVO', {exact:true}).isVisible());
      assert.ok(await page.getByRole('button', {name:'Diagnosticar · rolar INT'}).isDisabled());
      assert.ok(await page.getByRole('button', {name:'Assumir Vanguarda'}).isDisabled());
      console.log(`${name.toUpperCase()}_LAYOUT=PASS`);
      await page.close();
    }
    console.log(`SCREENSHOTS=${output}`);
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
