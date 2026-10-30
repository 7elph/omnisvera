// Hydrated production card components, real stylesheet and original art; no operational API.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
  const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
  const catalog=JSON.parse(fs.readFileSync('../backend/app/data/spell_images.json','utf8'));
  const images=Object.fromEntries(['misseis-magicos','levitacao','escuridao','relampago'].map(id=>[id,catalog[id]]));
  const names=['Mísseis Mágicos','Levitação','Escuridão','Relâmpago'];
  const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`
    import React,{useState} from 'react';import{createRoot}from'react-dom/client';
    import Card from './src/components/SpellCard';import Missile from './src/components/SpellTargetControl';
    const images=${JSON.stringify(images)},names=${JSON.stringify(names)};
    function App(){const[target,setTarget]=useState(''),[uses,setUses]=useState(1);return <main className="unified-workspace"><section className="workspace-action-catalog"><header>MAGIAS · DORN-7</header>{Object.entries(images).map(([id,image],i)=>{const heading=<button className="workspace-ability-name"><img src={'https://fixture.test/'+image} alt={names[i]}/>{names[i]}</button>,summary=<><small>{i===0?'1':i===3?'3':'2'}º círculo</small><b>{i===0?uses:1}/1</b></>;return i===0?<Missile key={id} heading={heading} summary={summary} targets={[{id:'wolf',name:'Lobo'}]} targetId={target} disabled={!uses} onSelect={setTarget} onUse={()=>setUses(0)}/>:<Card key={id} heading={heading} summary={summary}><button>Usar</button></Card>})}</section></main>}
    createRoot(document.getElementById('root')).render(<App/>);`}});
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'spell-images-visual-'));
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
    const page=await browser.newPage({viewport:{width,height}});
    await page.route('https://fixture.test/**',route=>route.fulfill({contentType:'image/png',body:fs.readFileSync(path.join('..','..',decodeURI(new URL(route.request().url()).pathname)))}));
    await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css','utf8')}\nbody{margin:0;background:#101315;color:#ddd}main{max-width:440px;padding:12px;box-sizing:border-box}</style></head><body><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
    await page.getByAltText('Relâmpago').waitFor();
    await page.waitForFunction(()=>[...document.images].length===4&&[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    assert.deepEqual(await page.locator('img').evaluateAll(nodes=>nodes.map(n=>[n.getBoundingClientRect().width,n.getBoundingClientRect().height])),[[27,27],[27,27],[27,27],[27,27]]);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),name+' overflow');
    assert.ok(await page.getByRole('button',{name:'Usar',exact:true}).first().isDisabled());
    const selectBox=await page.getByLabel('Alvo de Mísseis Mágicos').boundingBox(),useBox=await page.getByRole('button',{name:'Usar',exact:true}).first().boundingBox();
    assert.ok(useBox.x>=selectBox.x+selectBox.width-1&&Math.abs(useBox.y-selectBox.y)<2,name+' target and use beside each other');
    await page.getByLabel('Alvo de Mísseis Mágicos').selectOption('wolf');
    await page.getByRole('button',{name:'Usar',exact:true}).first().click();
    await page.getByText('0/1',{exact:true}).waitFor();
    assert.ok(await page.getByRole('button',{name:'Usar',exact:true}).first().isDisabled());
    await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
    console.log(name+' PASS: original images, 27px icons, target/use controls, no horizontal overflow');await page.close();
  }}finally{await browser.close();}console.log('SCREENSHOTS='+output);
}main().catch(e=>{console.error(e);process.exitCode=1});
