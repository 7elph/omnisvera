const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function moduleAt(file){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports});return m.exports;}
const {selectGridTarget}=moduleAt('src/components/gridTargetSelection.ts');
test('select up to three, confirm only at capacity, never duplicate on repeated pin',()=>{
 let r=selectGridTarget([],'a',true,3);assert.equal(r.decision,'continue');
 r=selectGridTarget(r.selected,'b',true,3);assert.equal(r.decision,'continue');
 const repeat=selectGridTarget(r.selected,'a',true,3);assert.equal(repeat.decision,'repeat');assert.equal(repeat.selected.length,2);
 r=selectGridTarget(r.selected,'c',true,3);assert.equal(r.decision,'confirm');
 assert.equal(selectGridTarget(r.selected,'d',true,3).selected.length,3);
 assert.equal(selectGridTarget([],'far',false,3).selected.length,0);
 assert.equal(selectGridTarget([],'a',true,1).decision,'confirm');
});
test('card delegates exactly once and keeps selectors and disabled commands safe',()=>{
 const {activateCard}=moduleAt('src/components/cardActivation.ts');let calls=0,blocked=0;
 const command={disabled:false,click:()=>calls++},card={querySelector:()=>command};
 const target={closest:q=>q==='article'?card:null};
 const event={target,currentTarget:{contains:()=>true},preventDefault(){blocked++},stopPropagation(){}};
 activateCard(event);assert.equal(calls,1);
 command.disabled=true;activateCard(event);assert.equal(calls,1);
 command.disabled=false;target.closest=q=>q==='article'?card:q.startsWith('select')?{}:null;
 activateCard(event);assert.equal(calls,1);
 target.closest=q=>q==='article'?card:q==='button[data-card-command]'?command:null;
 activateCard(event);assert.equal(calls,1);assert.equal(blocked,2);
 event.shiftKey=true;target.closest=q=>q==='article'?card:null;activateCard(event);assert.equal(calls,1);
});
test('master gets actual compact battle card without multi-effect editor',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8'),panel=fs.readFileSync('src/components/CombatEncounterPanel.tsx','utf8');
 assert.ok(source.includes('<CombatEncounterPanel compact ledger='));
 assert.ok(panel.includes('{!compact && <CombatEffectsPanel'));
 assert.equal(source.includes('>Ficha da entidade</button>'),false);
});
