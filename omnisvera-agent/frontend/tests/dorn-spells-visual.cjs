// Real hydrated product components/CSS; fixture API, never operational data.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),esbuild=require('esbuild');
async function main(){
  const {chromium}=require(require.resolve('playwright',{paths:[process.env.OMNISVERA_QA_MODULES||process.cwd()]}));
  const bundle=await esbuild.build({write:false,bundle:true,format:'iife',jsx:'automatic',stdin:{resolveDir:process.cwd(),loader:'tsx',contents:`
    import React,{useState} from 'react';import{createRoot}from'react-dom/client';
    import Controls from './src/components/DornSpellControls';import Effects from './src/components/DornSpellEffects';
    function App(){const[spell,setSpell]=useState('levitacao');const[combat,setCombat]=useState({version:1,effects:[{id:'lev',spell:'levitacao',label:'Levitação',target_id:'dorn7',remaining_seconds:1800,altitude_meters:0}],encounter:{active:false}});
      return <main className="unified-workspace"><label>Magia de teste<select value={spell} onChange={e=>setSpell(e.target.value)}><option value="levitacao">Levitação</option><option value="escuridao">Escuridão</option><option value="relampago">Relâmpago</option></select></label><Controls key={spell} spell={spell} combat={combat} tokens={[{id:'wolf',name:'Lobo fixture',token_type:'monster',current_hp:20}]} onClose={()=>{}} onChange={async()=>setCombat(c=>({...c,version:c.version+1}))}/><Effects combat={combat} onChange={async()=>setCombat(c=>({...c,version:c.version+1}))}/></main>}
    createRoot(document.getElementById('root')).render(<App/>);`},plugins:[{name:'fixture',setup(b){b.onResolve({filter:/\/api$/},()=>({path:'api',namespace:'fixture'}));b.onLoad({filter:/.*/,namespace:'fixture'},()=>({loader:'js',contents:`export const newDiceRequestId=()=>crypto.randomUUID();export async function sendCombatEffectCommand(r){return {protocol_result:{spell:r.payload.spell_id,results:[{target:'Lobo fixture',damage:6,hp_before:20,hp_after:14}]}}}` }));}}]});
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'dorn-spells-visual-'));const css=fs.readFileSync('src/styles.css','utf8');
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{for(const[name,width,height]of[['mobile',390,844],['desktop',1440,900]]){
    const page=await browser.newPage({viewport:{width,height}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.setContent(`<html><head><style>${css}\nbody{margin:0;background:#101315;color:#ddd}main{max-width:440px;padding:12px;box-sizing:border-box}</style></head><body><div id="root"></div><script>crypto.randomUUID=()=> 'fixture-'+Math.random();${bundle.outputFiles[0].text}</script></body></html>`);
    for(const spell of ['levitacao','escuridao','relampago']){
      await page.getByLabel('Magia de teste').selectOption(spell);
      assert.ok(await page.getByRole('button',{name:'Conjurar · resolver automaticamente'}).isDisabled());
      await page.getByLabel('Alvos da magia').selectOption('wolf');
      await page.getByLabel('Distância declarada (m)').fill('10');
      if(spell==='levitacao')await page.getByLabel('Peso do receptor (kg)').fill('100');
      if(spell==='relampago')await page.getByLabel('Contatos do raio · Lobo fixture').fill('2');
      await page.getByLabel('Confirmo alcance').check();await page.getByRole('button',{name:'Conjurar · resolver automaticamente'}).click();
      try { await page.getByRole('status').filter({hasText:'PV 20→14'}).waitFor({timeout:5000}); }
      catch(error){console.log(await page.locator('body').innerText());console.log(errors);throw error;}
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),name+' overflow');
      await page.screenshot({path:path.join(output,name+'-'+spell+'.png'),fullPage:true});
    }
    await page.locator('summary').click();await page.getByRole('button',{name:'Subir 2 m'}).click();await page.getByRole('button',{name:'Encerrar efeito'}).click();
    assert.deepEqual(errors,[]);console.log(name+'=PASS all three spell forms, effects controls, no horizontal overflow');await page.close();
  }}finally{await browser.close();}console.log('SCREENSHOTS='+output);
}main().catch(e=>{console.error(e);process.exitCode=1});
