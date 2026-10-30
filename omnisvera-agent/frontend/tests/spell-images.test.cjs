const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
test('resource cards bind approved art and dynamic counters',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  assert.ok(source.includes("a.kind === 'resource' && a.uses?.resource_key === resource.key)?.image_path"));
  assert.ok(source.includes('Disponível: ${resource.current}/${resource.maximum}'));
});
test('spell card uses compact inventory heading and summary, retaining action',()=>{
  const mod={exports:{}};const jsx=(type,props)=>({type,props});
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/SpellCard.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:()=>({jsx,jsxs:jsx})});
  const heading={image:'fixture.png',name:'Levitação'},action={type:'button'};
  const card=mod.exports.default({heading,summary:'2º círculo · 1/1',children:action});
  assert.equal(card.props.className,'workspace-spell-card');
  assert.equal(card.props.children[0].props.className,'workspace-catalog-card-heading');
  assert.equal(card.props.children[0].props.children,heading);
  assert.equal(card.props.children[1].props.className,'workspace-catalog-card-summary');
  assert.equal(card.props.children[2],action);
});
test('spell-specific art takes precedence over equipped item and uses inventory icon size',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  assert.match(source,/mediaUrlFromVaultPath\(ability.image_path\) \|\|/);
  const css=fs.readFileSync('src/styles.css','utf8');
  assert.match(css,/\.workspace-spell-card \.workspace-ability-name img \{[^}]*height: 27px;[^}]*width: 27px;/);
});
test('attack cards resolve their own ability art, including Bone Dagger',()=>{
  const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
  assert.ok(source.includes('abilities.find(ability => ability.id === attack.id)?.image_path'));
  assert.ok(source.includes('showIcon={Boolean(attackArt)} icon={attackArt ||'));
});
