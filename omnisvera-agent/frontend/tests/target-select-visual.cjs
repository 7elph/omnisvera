const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
 const{chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 const attack=source.slice(source.indexOf('  const attackTargetControl ='),source.indexOf('  const requiredItemForAbility ='));
 const ability=source.slice(source.indexOf('  const abilityTargetControl ='),source.indexOf('  const attackSection ='));
 const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{loader:'tsx',resolveDir:process.cwd(),contents:`
 import React,{useState}from'react';import{createRoot}from'react-dom/client';import TargetSelect from './src/components/TargetSelect';
 function App(){const[attackTargetById,setAttackTargetById]=useState({}),[attackPhysicalD20ById,setAttackPhysicalD20ById]=useState({}),[techniqueModeById,setTechniqueModeById]=useState({}),[used,setUsed]=useState('');
 const definition={attacks:[{id:'melee',name:'Corpo a corpo'}]},state={resources:[]},busy='',selectedId='raziel',battleState={},defaultAttackRollMode='physical';
 const attackTargets=[{id:'wolf',name:'Lobo',token_type:'monster',current_hp:8}],battleMapTokens=[...attackTargets,{id:'corpse',name:'Cadáver autorizado',token_type:'monster',current_hp:0,sheet:{reanimation_allowed:true}},{id:'pending',name:'Cadáver pendente',token_type:'monster',current_hp:0,sheet:{}}];
 const abilityResource=()=>({current:3,maximum:5}),combatActionBlock=()=>'',setAimedAttackId=()=>{},useAbility=(a,t)=>setUsed(a.id+':'+t.id);
 ${attack}
 ${ability}
 return <main><section className="workspace-action-catalog workspace-attack-catalog"><header>ATAQUES</header><article><span>Corpo a corpo</span><div className="workspace-inline-actions">{attackTargetControl('melee')}<button>Atacar</button></div></article></section><section className="workspace-action-catalog"><header>HABILIDADES</header>{[{id:'mordida',name:'Mordida'},{id:'lamina-de-sangue',name:'Lâmina de Sangue'},{id:'animar-mortos',name:'Animar Mortos'}].map(a=><article key={a.id}><span><button className="workspace-ability-name">{a.name}</button></span>{abilityTargetControl(a)}</article>)}</section><output>{used}</output></main>}
 createRoot(document.getElementById('root')).render(<App/>);`}});
 const browser=await chromium.launch({channel:'msedge',headless:true}),folder=fs.mkdtempSync(path.join(os.tmpdir(),'target-select-qa-'));
 try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
 const page=await browser.newPage({viewport:{width,height}});await page.setContent(`<html><head><style>${fs.readFileSync('src/styles.css','utf8')}body{margin:0;background:#101315;color:#ddd}main{max-width:360px;padding:12px}</style></head><body><div id="root"></div><script>${bundle.outputFiles[0].text}</script></body></html>`);
 await page.getByLabel('Alvo de Corpo a corpo').selectOption('wolf');assert.equal(await page.getByLabel('Alvo de Mordida').inputValue(),'');
 await page.getByLabel('Alvo de Mordida').selectOption('wolf');assert.equal(await page.locator('output').textContent(),'');await page.getByLabel('d20 físico de Mordida').fill('15');
 const bite=page.locator('article').filter({has:page.getByLabel('Alvo de Mordida')});await bite.getByRole('button',{name:'Usar',exact:true}).click();assert.equal(await page.locator('output').textContent(),'mordida:wolf');
 await page.getByLabel('Alvo de Mordida').selectOption('');assert.ok(await bite.getByRole('button',{name:'Usar',exact:true}).isDisabled());
 assert.ok(await page.getByLabel('Alvo de Animar Mortos').locator('option[value=pending]').isDisabled());await page.getByLabel('Alvo de Animar Mortos').selectOption('corpse');
 const corpse=page.locator('article').filter({has:page.getByLabel('Alvo de Animar Mortos')});await corpse.getByRole('button',{name:'Usar',exact:true}).click();assert.equal(await page.locator('output').textContent(),'animar-mortos:corpse');
 for(const select of await page.locator('.workspace-target-select').all()){
  const box=await select.boundingBox();assert.ok(box.width>60);assert.equal(await select.locator('xpath=ancestor::article').count(),1);
  const button=await select.locator('xpath=ancestor::article').getByRole('button',{name:/^(Usar|Atacar)$/}).boundingBox();
  assert.ok(button.x>=box.x+box.width-1,'action beside target');assert.ok(Math.abs(button.y-box.y)<2,'action same row');
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(folder,name+'.png'),fullPage:true});console.log(name+' PASS actual attack/ability selectors: local to card, isolated choices, selection does not execute, physical die, corpse authorization, clear, no overflow');await page.close();
 }}finally{await browser.close();}console.log('SCREENSHOTS='+folder);
}main().catch(e=>{console.error(e);process.exitCode=1});
