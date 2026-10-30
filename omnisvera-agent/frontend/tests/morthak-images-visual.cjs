const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
 const{chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
 const art=JSON.parse(fs.readFileSync('../backend/app/data/spell_images.json','utf8'));
 const dornItems=process.env.OMNISVERA_QA_DORN_ITEMS && {
  'Escritas Rúnicas':'zz_media/ui/icons/uploads/escritas_runicas_d049fd2221.jpg',
  'Malha Rúnica':'zz_media/ui/icons/uploads/malha_runica_05ad221463.jpg',
  'Compartimento interno':'zz_media/ui/icons/uploads/compartimento_interno_73d982feed.jpg',
  'Núcleo Rúnico':'zz_media/ui/icons/uploads/nucleo_runico_7bc0fef279.jpg',
  'Cristal de Memória danificado':'zz_media/ui/icons/uploads/cristal_de_memoria_danificado_0e0329aac8.jpg'
 };
 const profile=dornItems ? 'dorn7' : process.env.OMNISVERA_QA_RAZIEL ? 'raziel' : 'morthak';
 const ids=process.env.OMNISVERA_QA_RAZIEL_PASSIVES ? ['nao-vida-consciente-vampiro','visao-no-escuro-vampiro','imunidades-vampiricas','fotossensibilidade','cura-vampirica-invertida'] : process.env.OMNISVERA_QA_RAZIEL_TRAITS ? ['regeneracao-vampirica','fome-de-sangue','medo-vampirico','sentido-do-sangue','corpo-predatorio'] : process.env.OMNISVERA_QA_RAZIEL ? ['reserva-de-sangue','lamina-de-sangue','marca-rubra','caixao','mordida'] : process.env.OMNISVERA_QA_MORTHAK_TRAITS ? ['chamado-necromantico','ossos-sem-carne','repouso-imovel','corpo-quebradico','cura-antinatural'] : ['adaga-de-osso','levantar-um-esqueleto','nao-vida-consciente-esqueleto','animar-mortos','memoria-fraturada'];
 const entries=dornItems ? JSON.parse(fs.readFileSync('../backend/app/data/dorn7_mage3.json','utf8')).items.filter(item=>dornItems[item.name]).map(item=>({id:item.name,name:item.name,description:item.description,active:false,image:dornItems[item.name]})) : JSON.parse(fs.readFileSync('../backend/app/data/session_abilities.json','utf8')).characters[profile].filter(a=>ids.includes(a.id)).map(a=>({...a,image:art[a.id]}));
 const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`import React from'react';import{createRoot}from'react-dom/client';import Detail from './src/components/SheetDetail';import Card from './src/components/SpellCard';const entries=${JSON.stringify(entries)};createRoot(document.getElementById('root')).render(<main><section className="workspace-action-catalog"><header>${profile.toUpperCase()}</header>{entries.map(a=>a.kind==='resource'?<article key={a.id}><span><Detail title={a.name} description={a.description+' Disponível: 5/5'} icon={'http://fixture/'+a.image}/></span><b>5/5</b></article>:<Card key={a.id} heading={<Detail title={a.name} description={a.description} icon={'http://fixture/'+a.image}/>} summary={<small>{a.active===false?'Passiva':a.kind}</small>}>{a.active!==false&&<button>Usar</button>}</Card>)}</section></main>);`}});
 const browser=await chromium.launch({channel:'msedge',headless:true}),folder=fs.mkdtempSync(path.join(os.tmpdir(),'morthak-images-visual-'));
 try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});
  await page.route('http://fixture/**',route=>route.fulfill({body:fs.readFileSync(path.resolve('..','..',new URL(route.request().url()).pathname.slice(1))),contentType:'image/jpeg'}));
  await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css','utf8')}\nbody{margin:0;background:#101315;color:#ddd}main{max-width:360px;padding:12px}</style></head><body><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
  await page.getByRole('button',{name:entries[0].name,exact:true}).waitFor();await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));assert.equal(await page.locator('img').count(),5);
  for(const entry of entries){await page.getByRole('button',{name:entry.name,exact:true}).click();const dialog=page.getByRole('dialog',{name:entry.name});await dialog.waitFor();await page.waitForFunction(()=>[...document.querySelectorAll('[role=dialog] img')].every(i=>i.complete&&i.naturalWidth));assert.ok((await dialog.locator('img').getAttribute('src')).endsWith(entry.image));await page.getByRole('button',{name:'Fechar descrição'}).click();}
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(folder,name+'.png')});console.log(name+' PASS: five original images, descriptions open/close, no overflow');await page.close();
 }}finally{await browser.close();}console.log('SCREENSHOTS='+folder);
}main().catch(e=>{console.error(e);process.exitCode=1});
