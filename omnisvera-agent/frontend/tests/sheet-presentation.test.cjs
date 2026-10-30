const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');
const read=file=>fs.readFileSync(path.join(__dirname,'../src',file),'utf8');

function loadValue() {
  const module={exports:{}};
  const jsx=(type,props)=>({type,props});
  let failed=[];
  vm.runInNewContext(ts.transpileModule(read('components/ArmorClassValue.tsx'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
    {module,exports:module.exports,require:name=>name==='react' ? {useState:()=>[failed,next=>{failed=typeof next==='function'?next(failed):next;}]} : name==='../api' ? {mediaUrlFromVaultPath:p=>p ? `/media/${p}` : ''} : name==='../companionIconCatalog' ? {iconPathForItem:()=> 'armor-fallback.png'} : {jsx,jsxs:jsx}});
  return module.exports;
}

test('CA keeps its total and shows only the numeric bonus in green',()=>{
  const module={exports:loadValue()};
  const {default:Value,armorClassBonus}=module.exports;
  const tree=Value({defenses:{armor_class:17,unmodified_armor_class:14}});
  assert.equal(tree.props.children[0],17);
  assert.equal(tree.props.children[2].type,'span');
  assert.equal(tree.props.children[2].props['aria-label'],'Bônus de CA +3');
  assert.equal(tree.props.children[2].props.style.color,'#65d58a');
  assert.equal(armorClassBonus({armor_class:17,armor_modifier:2}),2);
  assert.equal(armorClassBonus({armor_class:14,unmodified_armor_class:14}),0);
  assert.equal(Value({defenses:undefined}).props.children[0],'—');
});

test('CA restores the equipped armor icon, preferring thumbnail then cover then catalog',()=>{
  const {default:Value}=loadValue();
  const defenses={armor_class:14,unmodified_armor_class:12,armor_modifier_source:{item_path:'armor/mantle',item_title:'Manto',value:2,kind:'armor'}};
  const item={item_path:'armor/mantle',item_title:'Manto',thumbnail:'thumb.png',cover:'cover.png',item_type:'armor'};
  const tree=Value({defenses,inventory:[{...item,item_path:'other',thumbnail:'wrong.png'},item]});
  assert.equal(tree.props.children[0],14);
  assert.equal(tree.props.children[1].type,'img');
  assert.equal(tree.props.children[1].props.src,'/media/thumb.png');
  assert.equal(tree.props.children[1].props.alt,'');
  assert.equal(tree.props.children[1].props['aria-label'],'Manto');
  assert.equal(tree.props.children[2].props['aria-label'],'Bônus de CA +2');
  assert.equal(Value({defenses,inventory:[{...item,thumbnail:null}]}).props.children[1].props.src,'/media/cover.png');
  assert.equal(Value({defenses,inventory:[]}).props.children[1].props.src,'/media/armor-fallback.png');
  assert.equal(Value({defenses:{armor_class:12},inventory:[item]}).props.children[1],undefined);
});

test('broken CA art falls back without spilling the item name over the stat',()=>{
  const {default:Value}=loadValue();
  const defenses={armor_class:22,unmodified_armor_class:20,armor_modifier_source:{item_path:'armor',item_title:'Nome de armadura muito longo',value:2}};
  const inventory=[{item_path:'armor',item_title:'Armadura',thumbnail:'missing.png'}];
  let tree=Value({defenses,inventory});
  let icon=tree.props.children[1];
  assert.equal(icon.props.alt,'','Broken image must not render a long alt label');
  assert.equal(icon.props.style.width,24);
  assert.equal(typeof icon.props.onError,'function');
  icon.props.onError();
  tree=Value({defenses,inventory});
  icon=tree.props.children[1];
  assert.equal(icon.props.src,'/media/armor-fallback.png');
  icon.props.onError();
  tree=Value({defenses,inventory});
  icon=tree.props.children[1];
  assert.equal(icon.type,'svg');
  assert.equal(icon.props['aria-label'],defenses.armor_modifier_source.item_title);
  assert.equal(icon.props.style.width,24);
  assert.equal(tree.props.children[0],22);
  assert.equal(tree.props.children[2].props['aria-label'],'Bônus de CA +2');
  const recovered=Value({defenses,inventory:[{...inventory[0],thumbnail:'available.png'}]});
  assert.equal(recovered.props.children[1].type,'img');
  assert.equal(recovered.props.children[1].props.src,'/media/available.png');
});

test('all character sheet views share CA; Mesa balances precede inventory, full sheet keeps its editor',()=>{
  const mesa=read('pages/SessionWorkspace.tsx');
  const sheet=read('pages/PlayableCharacterSheet.tsx');
  assert.ok(!mesa.includes('Detalhar CA'));
  assert.ok(!mesa.includes('armorModifierIcon'));
  assert.ok(mesa.includes('<ArmorClassValue defenses={definition?.defenses} inventory={character.inventory} />'));
  assert.ok(mesa.includes('<ArmorClassValue defenses={openCharacterDetail.definition.defenses} inventory={openCharacterDetail.inventory} />'));
  assert.ok(sheet.includes('<ArmorClassValue defenses={character.definition.defenses} inventory={character.inventory} />'));
  assert.ok(sheet.includes('<ArmorClassValue defenses={definition.defenses} inventory={character.inventory} />'));
  assert.ok(mesa.indexOf('<CurrencyCounters')<mesa.indexOf('workspace-action-catalog workspace-inventory-catalog'));
  assert.match(sheet, /tab === "inventory"[^\n]+<InventoryTab[^\n]+<CurrencyCounters/);
  const coins=read('components/CurrencyCounters.tsx');
  assert.ok(coins.includes('expanded = false'));
  assert.ok(coins.includes('aria-label="Moedas" open={expanded || undefined}'));
});
