const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');

test('coin loot has no equipment slot; magical coins keep accessory slots',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  const start=source.indexOf('function possibleEquipmentSlots(');
  const fn=source.slice(start,source.indexOf('\n}',start)+2);
  const module={exports:{}};
  vm.runInNewContext(ts.transpileModule(fn+'\nexports.slots=possibleEquipmentSlots;',{
    compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
    {module,exports:module.exports,itemLooksLikeArmor:()=>false,itemLooksLikeShield:()=>false,
     itemLooksLikeWeapon:()=>false,itemLooksLikeRangedWeapon:()=>false});
  const slots=module.exports.slots;
  assert.equal(slots({item_type:'currency',mechanics:{equipment_slots:['Acessório']}}).length,0);
  assert.equal(slots({item_title:'Moeda Misteriosa',mechanics:{equipment_slots:['Acessório']}})[0],'Acessório');
  assert.equal(slots({item_title:'Flecha x20',mechanics:{family:'ammunition',equipment_slots:[]}}).length,0);
  const legacy=fs.readFileSync('src/pages/PlayableCharacterSheet.tsx','utf8');
  assert.match(legacy,/if \(item.item_type === 'currency'\) return/);
});
