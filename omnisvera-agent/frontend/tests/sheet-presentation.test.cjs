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
  vm.runInNewContext(ts.transpileModule(read('components/ArmorClassValue.tsx'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
    {module,exports:module.exports,require:name=>name==='../api' ? {mediaUrlFromVaultPath:p=>p ? `/media/${p}` : ''} : name==='../companionIconCatalog' ? {iconPathForItem:()=> 'armor-fallback.png'} : {jsx,jsxs:jsx}});
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
  assert.equal(tree.props.children[1].props.alt,'Manto');
  assert.equal(tree.props.children[2].props['aria-label'],'Bônus de CA +2');
  assert.equal(Value({defenses,inventory:[{...item,thumbnail:null}]}).props.children[1].props.src,'/media/cover.png');
  assert.equal(Value({defenses,inventory:[]}).props.children[1].props.src,'/media/armor-fallback.png');
  assert.equal(Value({defenses:{armor_class:12},inventory:[item]}).props.children[1],undefined);
});

test('all character sheet views share CA display and keep coins below inventory',()=>{
  const mesa=read('pages/SessionWorkspace.tsx');
  const sheet=read('pages/PlayableCharacterSheet.tsx');
  assert.ok(!mesa.includes('Detalhar CA'));
  assert.ok(!mesa.includes('armorModifierIcon'));
  assert.ok(mesa.includes('<ArmorClassValue defenses={definition?.defenses} inventory={character.inventory} />'));
  assert.ok(mesa.includes('<ArmorClassValue defenses={openCharacterDetail.definition.defenses} inventory={openCharacterDetail.inventory} />'));
  assert.ok(sheet.includes('<ArmorClassValue defenses={character.definition.defenses} inventory={character.inventory} />'));
  assert.ok(sheet.includes('<ArmorClassValue defenses={definition.defenses} inventory={character.inventory} />'));
  assert.ok(mesa.indexOf('<CurrencyCounters')>mesa.indexOf('workspace-action-catalog workspace-inventory-catalog'));
  assert.match(sheet, /tab === "inventory"[^\n]+<InventoryTab[^\n]+<CurrencyCounters/);
  const coins=read('components/CurrencyCounters.tsx');
  assert.ok(coins.includes('<details className="workspace-gm-subsection" aria-label="Moedas">'));
  assert.ok(!coins.includes('<details className="workspace-gm-subsection" aria-label="Moedas" open'));
});
