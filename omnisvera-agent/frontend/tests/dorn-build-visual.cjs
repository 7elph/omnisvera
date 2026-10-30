// Hydrated real React components + actual product CSS. Fixture API only;
// this verifies UI interaction/layout, not a real campaign or multiclient game.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const esbuild = require('esbuild');
async function main() {
  const { chromium } = require(require.resolve('playwright', { paths: [process.env.OMNISVERA_QA_MODULES || process.cwd()] }));
  const spec = JSON.parse(fs.readFileSync('../backend/app/data/dorn7_mage3.json','utf8'));
  const fixture = { definition: {id:'dorn7',name:'Unidade DORN-7',level:3,abilities:{racial:spec.sheet.race.racial_abilities},progression:{pending_rolls:[{level:4,request_id:1,die:4,controller:'master'}]}},
    state:{current_hp:18,maximum_hp:20}, inventory:spec.items.map((item,i)=>({item_path:`fixture:${i}`,item_title:item.name,damage_formula:item.damage,description:item.description})) };
  const bundled = await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`
    import React, { useState } from 'react'; import { createRoot } from 'react-dom/client';
    import DornDetails from './src/components/DornConstructDetails';
    import Protocols from './src/components/DornProtocolControls';
    import Pending from './src/components/PendingLevelRolls';
    const fixture=${JSON.stringify(fixture)};
    function App(){const [combat,setCombat]=useState({version:1,effects:[],encounter:{active:false,participants:[]}});
      const [character,setCharacter]=useState(fixture);
      return <main className="unified-workspace"><h2>Unidade DORN-7 · QA fixture</h2><p>PV 18/20 · CA 11</p>
      <section className="workspace-action-catalog"><header>AÇÕES / PROTOCOLOS</header><Protocols combat={combat} onChange={async s=>setCombat(s)}/></section>
      <DornDetails character={character} combat={combat}/><Pending character={character} canOperate onApplied={async()=>setCharacter({...character,definition:{...character.definition,progression:{pending_rolls:[]}}})}/></main>}
    createRoot(document.getElementById('root')).render(<App/>);`},plugins:[{name:'fixture-api',setup(build){
    build.onResolve({filter:/\/api$/},()=>({path:'api',namespace:'fixture'}));
    build.onLoad({filter:/.*/,namespace:'fixture'},()=>({loader:'js',contents:`
      let sequence=0; export const newDiceRequestId=()=> 'fixture-'+(++sequence); export const mediaUrlFromVaultPath=path=>'/media/'+path;
      export async function completeRollRequest(){return {total:3};}
      export async function sendCombatEffectCommand(request){return {version:request.expected_version+1,encounter:{active:false,participants:[]},effects:request.action==='dorn_vanguard'&&request.payload.enabled?[{id:'vanguard',target_id:'dorn7',target_type:'character',protocol:'vanguard',label:'Protocolo de Vanguarda',duration:'scene'}]:[],protocol_result:request.action==='dorn_diagnose'?{total:15,difficulty:12,outcome:'success'}:undefined};}
    `}));}}]});
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'dorn-build-qa-'));
  const css=fs.readFileSync('src/styles.css','utf8');
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try { for(const [name,width,height] of [['mobile',390,844],['desktop',1440,900]]){
    const page=await browser.newPage({viewport:{width,height}});
    await page.route('**/media/**',route=>{const file=route.request().url().split('/media/')[1];route.fulfill({contentType:file.endsWith('.png')?'image/png':'image/jpeg',body:fs.readFileSync(path.resolve('..','..',file))});});
    await page.route('http://fixture.local/',route=>route.fulfill({contentType:'text/html',body:'<html><body></body></html>'}));
    await page.goto('http://fixture.local/');
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.setContent(`<html><head><style>${css}\nbody{margin:0;background:#101315;color:#ddd}main{max-width:440px;padding:12px;box-sizing:border-box}main p{font-size:.75rem}</style></head><body><div id="root"></div><script>${bundled.outputFiles[0].text}</script></body></html>`);
    await page.getByRole('button',{name:'Assumir Vanguarda'}).click();
    await page.getByText('Protocolo de Vanguarda · ATIVO',{exact:true}).waitFor();
    await page.screenshot({path:path.join(output,`${name}-collapsed.png`),fullPage:true});
    for(const summary of await page.locator('summary').all())await summary.click();
    await page.getByRole('button',{name:'Desativar Vanguarda'}).click();
    await page.getByRole('button',{name:'Assumir Vanguarda'}).waitFor();
    assert.equal(await page.getByText('Diagnóstico da Unidade').count(),0);
    assert.equal(await page.locator('.dorn-protocol-controls > .workspace-spell-card').count(),2);
    assert.equal(await page.locator('section').filter({has:page.getByText('TRAÇOS DE CONSTRUCTO',{exact:true})}).locator('.workspace-spell-card').count(),3);
    await page.getByRole('button',{name:'Mente Artificial',exact:true}).click();
    await page.getByRole('dialog',{name:'Mente Artificial'}).waitFor();
    assert.equal(await page.locator('.workspace-detail-image').count(),1);
    await page.waitForFunction(()=>{const image=document.querySelector('.workspace-detail-image');return image?.complete&&image.naturalWidth>0;});
    await page.getByRole('button',{name:'Fechar descrição'}).click();
    for(const title of ['Protocolo de Guarda','Protocolo de Vanguarda','Forma Imutável','Corpo Artificial']){
      await page.getByRole('button',{name:title,exact:true}).click();
      await page.getByRole('dialog',{name:title}).waitFor();
      await page.waitForFunction(()=>{const image=document.querySelector('.workspace-detail-image');return image?.complete&&image.naturalWidth>0;});
      await page.getByRole('button',{name:'Fechar descrição'}).click();
    }
    for(const removed of ['Posição permite interposição','Exploração · até desativar ou encerrar cena','gastar ação'])assert.equal(await page.getByText(removed,{exact:true}).count(),0);
    await page.getByRole('button',{name:'Rolar PV',exact:true}).click();
    await page.getByRole('button',{name:'Rolar PV',exact:true}).waitFor({state:'detached'});
    assert.ok(await page.locator('article.workspace-spell-card').filter({hasText:'Protocolo de Guarda'}).getByRole('button',{name:'Usar',exact:true}).isDisabled());
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),`${name}: horizontal overflow`);
    assert.deepEqual(errors,[]);
    await page.screenshot({path:path.join(output,`${name}-expanded.png`),fullPage:true});
    console.log(`${name}=PASS hydrated protocol/roll/details interaction; no horizontal overflow`);await page.close();
  }}finally{await browser.close();}
  console.log(`SCREENSHOTS=${output}`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
