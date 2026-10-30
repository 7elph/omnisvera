const {test}=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), ts=require('typescript');
const moduleUnderTest={exports:{}};
const jsx=(type,props)=>({type,props});
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/SessionActionArt.tsx','utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:moduleUnderTest,exports:moduleUnderTest.exports,require:id=>id==='../api'?{mediaUrlFromVaultPath:p=>p}:id==='./SheetDetail'?{default:'SheetDetail'}:{jsx,jsxs:jsx}});
const {combatActionCards,ActionTitle,ActionArt}=moduleUnderTest.exports;
const card={id:'spell',name:'Mísseis Mágicos',description:'Descrição aprovada',image_path:'spell.jpg'};
const entry={character_id:'vezemir',event_kind:'action',visibility:'table',created_at:'2026-10-08T12:01:00Z',action_cards:[card]};
test('combat art is public, confirmed, deduplicated and scoped to current encounter',()=>{
 const ledger=[entry,entry,{...entry,event_kind:'roll'},{...entry,visibility:'gm'},{...entry,voided_at:'now'}, {...entry,character_id:'raziel'}, {...entry,created_at:'2020-01-01T00:00:00Z'}];
 assert.equal(combatActionCards(ledger,'vezemir',true,'2026-10-08T12:00:00Z').length,1);
 assert.equal(combatActionCards(ledger,'vezemir',false,'2026-10-08T12:00:00Z').length,0);
 assert.equal(combatActionCards(ledger,'vezemir',true,'2026-10-08T13:00:00Z').length,0);
 assert.equal(combatActionCards(ledger,'vezemir',true).length,0);
});
test('same read-only sheet detail receives full art and approved description',()=>{
 const value=ActionArt({card});
 assert.equal(value.props.children.props.title,card.name);
 assert.equal(value.props.children.props.description,card.description);
 assert.equal(value.props.children.props.icon,card.image_path);
 assert.equal(value.props.children.props.onClick,undefined);
});
test('timeline name is clickable inline without changing surrounding proper names',()=>{
 const value=ActionTitle({title:'Vezemir usou Mísseis Mágicos contra Morthak',cards:[card]});
 assert.equal(value.props.children[0][0],'Vezemir usou ');
 assert.equal(value.props.children[0][2],' contra Morthak');
 assert.equal(value.props.children[0][1].props.card.name,card.name);
});
