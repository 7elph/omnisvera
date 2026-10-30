const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
function inventoryLists(equipped){
 const fragment=source.slice(source.indexOf('  const resourceItem ='),source.indexOf('  const equippedItems ='));
 const inventory=[{item_title:'Pulseira de Vinhas',equipped,usable:true},{item_title:'Moeda Misteriosa',equipped:true},{item_title:'Poção de HP',usable:true}];
 const code=ts.transpileModule(fragment+'\n({consumables,carriedItems})',{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText;
 return vm.runInNewContext(code,{definition:{id:'vezemir'},character:{inventory},isConsumable:item=>!!item.usable});
}
test('bracelet always remains in inventory and appears in Resources only when equipped',()=>{
 for(const equipped of [false,true]){
  const lists=inventoryLists(equipped);
  assert.ok(lists.carriedItems.some(item=>item.item_title==='Pulseira de Vinhas'));
  assert.ok(lists.carriedItems.some(item=>item.item_title==='Moeda Misteriosa'));
  assert.equal(lists.consumables.some(item=>item.item_title==='Pulseira de Vinhas'),equipped);
  assert.ok(lists.consumables.some(item=>item.item_title==='Poção de HP'));
 }
});
test('resource control cannot equip/store bracelet; strength detail button is not rendered',()=>{
 const control=fs.readFileSync('src/components/VineBraceletControl.tsx','utf8');
 assert.ok(!control.includes('onToggleEquipment'));assert.ok(!control.includes('Guardar'));
 assert.ok(source.includes("definition?.id !== 'vezemir' && ATTRIBUTES.some"));
 assert.ok(source.includes('workspace-equip-menu'),'Inventory keeps existing equip/store controls');
});
