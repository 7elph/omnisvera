const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const mod={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/hemomancySelection.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:mod,exports:mod.exports});
const pack={weapons:['arco','foice','marreta','escudo','lanca'].map((weapon,i)=>({weapon,name:weapon,damage:'1d8',range_m:3,invocation_cost:1,skill:{name:'ativa '+weapon,cost:weapon==='escudo'?0:1,description:'Efeito '+weapon},passive:{name:'passiva '+weapon,description:'Automática '+weapon}}))};
const entries=[...['caixao','mordida','forma-da-noite','marca-rubra','faro-de-sangue','tecnica-de-predador','marca-rubra-aprimorada'].map(id=>({id,name:id,kind:'ability',group:'Habilidades',active:true})),...['regeneracao-vampirica','medo-vampirico','corpo-predatorio'].map(id=>({id,name:id,kind:'power',group:'Poderes vampíricos',active:true})),{id:'visao',group:'Traços vampíricos'},{id:'sol',group:'Fraquezas vampíricas'}];

test('Raziel retains Marca Rubra with the other five actives plus five weapon skills, and five automatic powers',()=>{
 const before=JSON.stringify(entries),view=mod.exports.razielSheetAbilities('raziel',entries,pack);
 const actives=view.filter(a=>a.group==='Habilidades'),passives=view.filter(a=>a.group.startsWith('Passivas ·'));
 assert.deepEqual(Array.from(actives.slice(0,5),a=>a.id),['caixao','mordida','forma-da-noite','regeneracao-vampirica','marca-rubra']);
 assert.equal(actives.length,10);assert.ok(actives.every(a=>a.active));
 assert.deepEqual(Array.from(actives.slice(5),a=>a.name),pack.weapons.map(w=>w.skill.name));
 assert.equal(passives.length,5);assert.ok(passives.every(a=>!a.active&&!a.requires_target));
 assert.equal(passives.filter(a=>a.group==='Passivas · Feridas').length,3);
 assert.equal(passives.filter(a=>a.group==='Passivas · Marca').length,2);
 assert.deepEqual(Array.from(passives,a=>a.name),pack.weapons.map(w=>w.passive.name));
 assert.ok(view.some(a=>a.id==='visao'));assert.ok(view.some(a=>a.id==='sol'));
 assert.equal(JSON.stringify(entries),before,'Presentation must not mutate persisted ability definitions');
});

test('other characters and private metadata boundaries are preserved',()=>{
 assert.equal(mod.exports.razielSheetAbilities('morthak',entries,pack),entries);
 const publicView=mod.exports.razielSheetAbilities('raziel',entries,undefined);
 assert.equal(publicView.filter(a=>a.group==='Habilidades').length,5);
 assert.equal(publicView.filter(a=>a.group==='Poderes vampíricos').length,0,'Do not fabricate private skills from client constants');
});

test('skill costs one total, including invocation when switching; shield costs one',()=>{
 assert.equal(mod.exports.hemomancyBloodCost(pack,'lanca',true,'arco'),1);
 assert.equal(mod.exports.hemomancyBloodCost(pack,'lanca',true,'lanca'),1);
 assert.equal(mod.exports.hemomancyBloodCost(pack,'lanca',false,'lanca'),0);
 assert.equal(mod.exports.hemomancyBloodCost(pack,'escudo',true,'lanca'),1);
 assert.equal(mod.exports.hemomancyBloodCost(undefined,'lanca',true,''),null);
});

test('the weapon picker does not duplicate the action menu or inline skill/passive pipeline',()=>{
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.doesNotMatch(source,/Ação da arma de sangue|<HemomancyWeaponDetails/);
 assert.match(source,/razielSheetAbilities\(definition\?\.id/);
 assert.match(source,/workspace-hemomancy-skill/);
 assert.match(source,/hemomancySelection\(definition\?\.hemomancy,hemomancyChoice,false\)/);
});
