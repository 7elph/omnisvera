const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
 const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
 // Use the actual grouped ability renderer, not a separately styled replica.
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 const start=source.indexOf('{Object.entries(groupedAbilities).map(');
 const end=source.indexOf('<section className="workspace-action-catalog workspace-inventory-catalog"',start);
 assert.ok(start>0&&end>start);
 const markup=source.slice(start,end).trim();
 const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',define:{'import.meta.env.VITE_API_BASE_URL':'""'},stdin:{loader:'tsx',resolveDir:process.cwd(),contents:`
 import React from 'react';import{createRoot}from'react-dom/client';import Detail from './src/components/SheetDetail';import NightFormSelector from './src/components/NightFormSelector';import SpellCard from './src/components/SpellCard';
 const AbilityName=({ability,icon})=><Detail title={ability.name} description={ability.description} icon={icon}/>;
 const definition={id:'raziel'},state={resources:[{key:'reserva_de_sangue',current:3,maximum:5}]},busy='',canOperate=true;
 const abilities=[{id:'lamina-de-sangue',name:'Lâmina de Sangue',active:true,requires_target:true,description:'Consome a Reserva de Sangue.'},{id:'forma-da-noite',name:'Forma da Noite',active:true,image_path:'https://fixture/icon.svg'},{id:'marca-rubra',name:'Marca Rubra',active:true,requires_target:true,image_path:'https://fixture/icon.svg'},{id:'cura-vampirica-invertida',name:'Cura Vampírica Invertida',active:false}];
 const groupedAbilities={'Habilidades':abilities},techniqueModeById={},NIGHT_FORMS=[];
 const normalizedName=s=>s,mediaUrlFromVaultPath=s=>s,requiredItemForAbility=()=>null,iconPathForItem=()=>'',abilityResource=a=>a.active?state.resources[0]:null;
 const abilityTargetControl=()=> <button>Selecionar alvo</button>,setTechniqueModeById=()=>{},useAbility=()=>{};
 createRoot(document.getElementById('root')).render(<main>${markup}<section className="workspace-action-catalog"><SpellCard heading={<Detail title="Magia com contador" description="QA" icon="https://fixture/icon.svg"/>} summary={<><small>magia</small><b>3/5</b></>}><button>Usar</button></SpellCard></section></main>);`}});
 const browser=await chromium.launch({channel:'msedge',headless:true}),folder=fs.mkdtempSync(path.join(os.tmpdir(),'sheet-standard-qa-'));
 try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('http://fixture/**',route=>route.fulfill({body:'<html></html>',contentType:'text/html'}));
  await page.route('https://fixture/icon.svg',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="27" height="27"><rect width="27" height="27" fill="blue"/></svg>'}));
  await page.goto('http://fixture/');
  await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css','utf8')} body{margin:0;background:#101315;color:#ddd}main{max-width:360px;padding:12px}</style></head><body><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
  await page.waitForTimeout(200);
  assert.deepEqual(errors,[]);
  const blade=page.locator('article').filter({has:page.getByRole('button',{name:'Lâmina de Sangue',exact:true})});await blade.waitFor();
  assert.equal(await blade.locator(':scope > b').count(),0);
  const title=await blade.locator(':scope > span').boundingBox(),controls=await blade.locator('.workspace-inline-actions').boundingBox();assert.ok(controls.y>=title.y+title.height);
  assert.ok(title.width>250);
  for(const name of ['Forma da Noite','Marca Rubra','Magia com contador']){
   const card=page.locator('article').filter({has:page.getByRole('button',{name,exact:true})});
   const heading=await card.getByRole('button',{name,exact:true}).boundingBox(),counter=await card.locator('b').boundingBox();
   assert.ok(counter.x>=heading.x+heading.width-1,name+': counter beside heading');
   assert.ok(counter.y<heading.y+heading.height && counter.y+counter.height>heading.y,name+': same row');
  }
  await page.getByRole('button',{name:'Lâmina de Sangue',exact:true}).click();await page.getByRole('dialog').waitFor();await page.getByRole('button',{name:'Fechar descrição'}).click();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(folder,name+'.png')});console.log(name+' PASS actual ability renderer: no duplicated blade counter, full-width heading, controls below, dialog, no overflow');await page.close();
 }}finally{await browser.close();}console.log('SCREENSHOTS='+folder);
}main().catch(e=>{console.error(e);process.exitCode=1});
