const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
 const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
 const images=JSON.parse(fs.readFileSync('../backend/app/data/spell_images.json','utf8'));
 const card={id:'misseis-magicos',name:'Mísseis Mágicos',description:'Descrição aprovada da ficha. A abertura deste card não gasta recursos.',image_path:images['misseis-magicos']};
 const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',define:{'import.meta.env':'{}'},stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`
 import React from 'react';import{createRoot}from'react-dom/client';import{ActionTitle,ActionArt}from'./src/components/SessionActionArt';
 const card=${JSON.stringify(card)};createRoot(document.getElementById('root')).render(<main className="unified-workspace"><section className="workspace-combat-live"><header>Combate em andamento</header><ol><li><b>1</b><span>Vezemir<span className="workspace-turn-action-icons"><ActionArt card={card} iconOnly/></span></span></li></ol></section><div className="workspace-timeline"><article className="action"><div><i>→</i><time>09:00</time></div><section><header><strong>Vezemir</strong><small>ação</small></header><p><ActionTitle title="Vezemir usou Mísseis Mágicos contra o Lobo" cards={[card]}/></p></section></article></div></main>);`}});
 const output=fs.mkdtempSync(path.join(os.tmpdir(),'session-action-art-'));
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});
  await page.route('**/media/**',route=>route.fulfill({contentType:'image/jpeg',body:fs.readFileSync(path.join('..','..',decodeURI(new URL(route.request().url()).pathname).replace(/^\/media\//,'')))}));
  await page.route('http://fixture.test/',route=>route.fulfill({contentType:'text/html',body:'<html></html>'}));
  await page.goto('http://fixture.test');
  await page.setContent(`<style>${fs.readFileSync('src/styles.css','utf8')}\nbody{background:#101315;color:#ddd;margin:0}main{padding:12px;max-width:650px;box-sizing:border-box}</style><div id="root"></div><script>${bundle.outputFiles[0].text}</script>`);
  await page.getByRole('button',{name:card.name,exact:true}).first().waitFor();
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  assert.deepEqual(await page.locator('img').evaluateAll(nodes=>nodes.map(n=>Math.round(n.getBoundingClientRect().width))),[22,22]);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),name+' overflow');
  await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
  for(let i=0;i<2;i++){
   await page.getByRole('button',{name:card.name,exact:true}).nth(i).click();
   await page.getByRole('dialog',{name:card.name}).waitFor();
   await page.getByText(card.description,{exact:true}).waitFor();
   const dialog=await page.getByRole('dialog').boundingBox();assert.ok(dialog.width<=width);
   await page.getByRole('button',{name:'Fechar descrição'}).click();
  }
  console.log(name+' PASS: 22px art, inline names, turn icon, both read-only dialogs, no overflow');await page.close();
 }}finally{await browser.close();}console.log('SCREENSHOTS='+output);
}main().catch(e=>{console.error(e);process.exitCode=1});
