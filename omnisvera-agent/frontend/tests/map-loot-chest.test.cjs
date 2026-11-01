const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const mod={exports:{}},jsx=(type,props)=>({type,props});
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/MapLootChest.tsx','utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}
}).outputText,{module:mod,exports:mod.exports,require:id=>id.endsWith('.css')?{}:{jsx,jsxs:jsx}});
const {canCollectMapLoot,default:Chest}=mod.exports;
const corpse={id:'body',token_type:'monster',name:'Orc',current_hp:0,sheet:{treasure:'Q (G)'}};
test('chest is limited to uncollected carried loot, not living units, summons or lairs',()=>{
 assert.equal(canCollectMapLoot(corpse),true);
 for(const token of [{...corpse,current_hp:1},{...corpse,token_type:'character'},...[
  {loot_collected:true},{summon:{caster:'mage'}},{reanimated_by:'mage'},{disintegrated:true},{treasure:'(G)'},{treasure:'-'}
 ].map(sheet=>({...corpse,sheet:{...corpse.sheet,...sheet}}))])assert.equal(canCollectMapLoot(token),false);
});
test('chest has an accessible label, logical projected position, and one direct collection event',()=>{
 let calls=0,stopped=0;
 const button=Chest({token:corpse,left:25,top:40,disabled:false,onCollect:()=>calls++});
 assert.equal(button.type,'button');assert.equal(button.props['aria-label'],'Saquear espólio de Orc');
 assert.equal(button.props.style.left,'25%');assert.equal(button.props.style.top,'40%');
 button.props.onClick({stopPropagation:()=>stopped++});assert.equal(calls,1);assert.equal(stopped,1);
 assert.equal(Chest({token:{...corpse,current_hp:1}}),null);
});
