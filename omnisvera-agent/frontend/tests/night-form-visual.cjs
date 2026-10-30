const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
 const{chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
 const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`import React,{useState}from'react';import{createRoot}from'react-dom/client';import Selector from './src/components/NightFormSelector';import Control from './src/components/NightFormControl';function App(){const[value,setValue]=useState('corvo'),[active,setActive]=useState(null),[uses,setUses]=useState(1);return <main className="unified-workspace"><section className="workspace-action-catalog"><article className="workspace-night-form-card"><span>Forma da Noite</span><b>{uses}/3</b><Control animal={active} busy={false} canActivate={uses>0} selector={<Selector value={value} onChange={setValue}/>} onActivate={()=>{setActive(value);setUses(uses-1)}} onDeactivate={()=>setActive(null)}/></article></section><p role="status">Selecionado: {value}</p></main>}createRoot(document.getElementById('root')).render(<App/>);`},plugins:[{name:'fixture',setup(b){b.onResolve({filter:/\/api$/},()=>({path:'api',namespace:'fixture'}));b.onLoad({filter:/.*/,namespace:'fixture'},()=>({loader:'js',contents:`export const mediaUrlFromVaultPath=p=>'http://fixture/'+p;`}));}}]});
 const browser=await chromium.launch({channel:'msedge',headless:true});const folder=fs.mkdtempSync(path.join(os.tmpdir(),'night-form-visual-'));
 try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
  const page=await browser.newPage({viewport:{width,height}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('http://fixture/**',route=>{const file=path.resolve('..','..',new URL(route.request().url()).pathname.slice(1));return route.fulfill({body:fs.readFileSync(file),contentType:'image/jpeg'});});
  await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css','utf8')}\n${fs.readFileSync('src/companionTheme.css','utf8')}\nmain{max-width:336px;padding:12px}.workspace-action-catalog{grid-template-columns:repeat(2,minmax(0,1fr))!important}</style></head><body class="app-shell"><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
  await page.locator('summary').click();await page.getByRole('button',{name:'Coruja',exact:true}).waitFor();
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('img')).every(i=>i.complete&&i.naturalWidth>0));
  await page.screenshot({path:path.join(folder,name+'-open.png'),fullPage:true});
  assert.ok(await page.getByRole('group',{name:'Escolher animal da Forma da Noite'}).getByRole('button').evaluateAll(buttons=>buttons.every(button=>button.scrollWidth<=button.clientWidth+1)),'Animal image and full name fit a native half-width card');
  for(const[nameAnimal,id]of[['Coruja','coruja'],['Morcego','morcego'],['Corvo','corvo']]){
   if(!await page.locator('details').evaluate(e=>e.open))await page.locator('summary').click();
   await page.getByRole('button',{name:nameAnimal,exact:true}).click();await page.getByRole('status').filter({hasText:'Selecionado: '+id}).waitFor();assert.equal(await page.locator('details').evaluate(e=>e.open),false);
  }
  const toggle=page.getByRole('switch',{name:'Forma da Noite'});
  await toggle.click();await page.getByText('0/3',{exact:true}).waitFor();
  assert.equal(await toggle.getAttribute('aria-checked'),'true');assert.equal(await toggle.isDisabled(),false);
  await page.screenshot({path:path.join(folder,name+'-active.png'),fullPage:true});
  await toggle.click();assert.equal(await toggle.getAttribute('aria-checked'),'false');assert.equal(await toggle.isDisabled(),true);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);console.log(name+'=PASS images, animal selector, activate once, deactivate at zero uses, no overflow');await page.close();
 }}finally{await browser.close();}console.log('SCREENSHOTS='+folder);
}main().catch(e=>{console.error(e);process.exitCode=1});
