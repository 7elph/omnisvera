const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const jsx=(type,props)=>({type,props}),walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props?.children)]:[];
function load(file,imports={}){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:m.exports,module:m,require:id=>imports[id]||{jsx,jsxs:jsx}});return m.exports;}
test('hemomancy has two halves and active icon without a duplicated blood cost',()=>{
 const {default:Card}=load('src/components/HemomancyCard.tsx',{'./SpellCard':{default:'SpellCard'},'./SheetSection':{default:'SheetSection'},'./HemomancyWeaponIcon':{default:'WeaponIcon'}});
 const tree=walk(Card({options:[],value:'foice',onChange(){},blood:20,activeWeapon:{weapon:'foice',name:'Foice de Sangue'}}));
 assert.equal(tree.filter(n=>n.props?.className==='workspace-hemomancy-halves').length,1);
 assert.equal(tree.filter(n=>n.props?.['aria-label']==='Arma ativa').length,1);
 assert.ok(!JSON.stringify(tree).includes('Sangue disponível'));
});
test('reflection pins and web area derive only from current authoritative effects',()=>{
 const {default:Map}=load('src/components/MapSpellEffects.tsx',{'../api':{mediaUrlFromVaultPath:p=>p}});
 const grid={cols:20,rows:20,cell_size_m:1.5,origin_x:0,origin_y:0};
 const effects=[{id:'web',target_id:'dorn7',target_type:'character',web_area:{map_id:'arena',x_m:3,y_m:6,width_m:3,height_m:3}},{id:'images',spell:'reflexos',target_id:'dorn7',target_type:'character',images_remaining:3}];
 const tree=walk(Map({grid,mapId:'arena',effects,tokens:[{id:'dorn',character_id:'dorn7',map_id:'arena',grid_position:{cell_x:5,cell_y:6},image_path:'dorn.png'}],characters:[]}));
 assert.equal(tree.filter(n=>n.type==='image').length,3);
 const area=tree.find(n=>n.props?.['aria-label']==='Área de Teia');assert.equal(area.props.width,10);assert.equal(area.props.x,10);
 assert.equal(walk(Map({grid,mapId:'another',effects,tokens:[],characters:[]})).filter(n=>n.type==='image'||n.type==='rect').length,0);
});
test('combat details default collapsed on player/compact sheets and lightning text stays out of sheet',()=>{
 const source=fs.readFileSync('src/components/CombatEncounterPanel.tsx','utf8');assert.ok(source.includes("open={mode==='gm'&&!compact?true:undefined}"));
 const sheet=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');assert.ok(!sheet.includes('{multiOutcome && <p'));assert.ok(sheet.includes("heldSpec.weapon==='arco'?'ranged':'melee'"));
});
test('critical failure summary exposes self damage without reopening a modal',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts');const result=attackOutcomeText({result:'miss',damage_total:0,hp_before:10,hp_after:10,breakdown:{fumble_result:{damage:6,hp_before:20,hp_after:14}}});
 assert.match(result.summary,/Falha crítica.*6/);assert.match(result.details,/20 → 14/);
});
test('critical details explicitly distinguish base multiplier from flat bonuses',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts');
 const result=attackOutcomeText({result:'hit',damage_total:11,damage_formula:'1d6+2',breakdown:{strikes:[{d20:20,result:'hit',attack_total:25,damage_total:11,critical:true,critical_multiplier:3}]}});
 assert.match(result.summary,/Crítico/);assert.match(result.details,/Crítico x3: somente dados base/);
});
