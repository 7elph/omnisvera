const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
test('inventory shows remaining projectiles across packs, preserving ordinary item quantities',()=>{
 const source=fs.readFileSync('src/components/InventoryItemIcon.tsx','utf8'),start=source.indexOf('export function inventoryQuantity(');assert.ok(start>=0);
 const fn=source.slice(start,source.indexOf('\n}',start)+2),exports={};
 vm.runInNewContext(ts.transpileModule(fn,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports});
 const quantity=exports.inventoryQuantity;
 assert.equal(quantity({quantity:1,charges_current:19,charges_max:20,mechanics:{family:'ammunition'}}),19);
 assert.equal(quantity({quantity:3,charges_current:6,charges_max:20,mechanics:{family:'ammunition'}}),46);
 assert.equal(quantity({quantity:2,charges_current:null,charges_max:20,mechanics:{family:'ammunition'}}),40);
 assert.equal(quantity({quantity:0,charges_current:0,charges_max:20,mechanics:{family:'ammunition'}}),0);
 assert.equal(quantity({quantity:2,charges_current:6,charges_max:20,mechanics:{}}),2);
});
