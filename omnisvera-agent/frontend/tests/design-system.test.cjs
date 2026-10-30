const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props?.children),...walk(v.props?.heading)]:[];
test('one final theme covers shared cards, controls, dialogs and every Companion area',()=>{
 const main=fs.readFileSync('src/main.tsx','utf8');assert.ok(main.indexOf('./companionTheme.css')>main.indexOf('./styles.css'));
 const css=fs.readFileSync('src/companionTheme.css','utf8');
 for(const selector of ['workspace-spell-card','workspace-inventory-catalog','workspace-map-library-list','npc-memory-list','scene-section','campaign-section','workspace-item-modal','workspace-ability-detail','focus-visible'])assert.ok(css.includes(selector),selector);
 assert.ok(css.includes('button:not(:is(.workspace-map-token'));assert.ok(css.includes('input:not([type="checkbox"])'));assert.ok(css.includes('prefers-reduced-motion'));
 // Existing native confirmation needs two narrowly scoped overrides against legacy form styles.
 const withoutDispel=css.replace(/\.workspace-dispel-options (?:label\.workspace-inline-actions|input\[type="radio"\])\s*\{[^}]*\}/g,'');
 assert.equal(withoutDispel.includes('!important'),false,'No broad priority war with grid/fog/zoom outside the scoped dispel choices');
});
test('Dorn and Necromancer controls reuse the inventory-style control card',()=>{
 for(const file of ['DornSpellControls','NecromancerSpellControls'])assert.ok(fs.readFileSync(`src/components/${file}.tsx`,'utf8').includes('ActionControlCard'));
});
test('shared control card preserves region, title, close and original action children',()=>{
 const mod={exports:{}};const jsx=(type,props)=>({type,props});
 vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/ActionControlCard.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:()=>({jsx,jsxs:jsx,default:'shared-component'})});
 let closed=0;const tree=mod.exports.default({title:'Reflexos',label:'Conjuração do Tomo Arcano',description:'Só consulta',onClose:()=>closed++,children:jsx('button',{children:'Conjurar'})});
 assert.equal(tree.type,'section');assert.equal(tree.props['aria-label'],'Conjuração do Tomo Arcano');
 const nodes=walk(tree);assert.ok(nodes.some(n=>n.props?.children==='Conjurar'));
 nodes.find(n=>n.props?.['aria-label']==='Fechar controle').props.onClick();assert.equal(closed,1);
});
