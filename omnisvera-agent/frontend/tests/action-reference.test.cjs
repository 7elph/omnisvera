const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(){const module={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/actionReference.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{module,exports:module.exports});return module.exports;}
test('reference includes spells, techniques, attacks, passives and usable items from actual sheet',()=>{
 const {characterActionReference}=load();
 const rows=characterActionReference({definition:{session_abilities:[{id:'magic',name:'Mísseis Mágicos',kind:'spell',blocked:true,description:'3 + 1 equipado',uses:{resource_key:'magic',cost:1}}],attacks:[{id:'melee',name:'Grisalma',damage:'1d8',equipment:[{role:'weapon',thumbnail:'axe.jpg'},{role:'support',thumbnail:'shield.jpg'}]}],abilities:{sentidos:'Sentidos aguçados'}},state:{resources:[{key:'magic',current:0,maximum:4}]},inventory:[{item_path:'potion',item_title:'Poção',usable:true,quantity:2,description:'Cura descrita'},{item_path:'bag',item_title:'Mochila',quantity:1}]});
 assert.equal(rows.length,4);assert.equal(rows.find(r=>r.id==='magic').status,'Bloqueada na ficha');
 assert.match(rows.find(r=>r.id==='magic').description,/0\/4/);
 assert.equal(rows.find(r=>r.id==='attack:melee').image_path,'axe.jpg');
 assert.ok(rows.some(r=>r.name==='Sentidos'));assert.ok(!rows.some(r=>r.name==='Mochila'));
});
test('reference does not duplicate the same spell shown as an attack',()=>{
 const rows=load().characterActionReference({definition:{session_abilities:[{id:'bone',name:'Adaga de Osso',kind:'spell'}],attacks:[{id:'bone',name:'Adaga de Osso'}]},inventory:[]});assert.equal(rows.length,1);
});
test('generic sheet keys are presented in Portuguese without changing proper names',()=>{
 const rows=load().characterActionReference({definition:{abilities:{class:'Guerreiro',racial:'Raça',Grisalma:'Nome próprio preservado'}},inventory:[]});
 assert.equal(rows[0].name,'Classe');assert.equal(rows[1].name,'Traços raciais');assert.equal(rows[2].name,'Grisalma');
});
test('activity filters work across combat and exploration without interpreting historical actions as active effects',()=>{
 const entries=[{actorId:'morthak',actor:'Morthak',kind:'action',title:'Usou Mísseis Mágicos',cards:[{name:'Mísseis Mágicos',description:'Dano de energia'}]}, {actorId:'morthak',kind:'roll',title:'Investigação'}, {actorId:'raziel',kind:'action',title:'Mordida'}, {actorId:'morthak',kind:'message',title:'Mensagem'}];
 const {filterActivity}=load();assert.equal(filterActivity(entries,{actor:'morthak',kind:'actions',query:''}).length,2);
 assert.equal(filterActivity(entries,{actor:'morthak',kind:'actions',query:'misseis'}).length,1);
 assert.equal(filterActivity(entries,{actor:'',kind:'all',query:'energia'}).length,1);
 assert.equal(filterActivity(entries,{actor:'',kind:'all',query:''}).length,4);
});
test('consultation is lazy, read-only and uses the existing sheet detail, never commands',()=>{
 const source=fs.readFileSync('src/components/CharacterActionReference.tsx','utf8');
 assert.match(source,/getPlayableCharacter/);assert.match(source,/<SheetDetail/);
 assert.match(source,/cancelled/);assert.match(source,/Atualizar consulta/);
 assert.doesNotMatch(source,/useCharacterTechnique|resolveCharacterAttack|applyCharacterStateAction|sendCombatEffectCommand/);
 const workspace=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');
 assert.match(workspace,/actionReferenceOpen && <CharacterActionReference/);
 assert.match(workspace,/Filtrar registro por personagem/);assert.match(workspace,/Buscar no registro/);
});

test('native manifest hides retired actions and adds current hemomancy skills without claiming certification',()=>{
 const m=load(),cards=[{id:'old',name:'Antiga',category:'Habilidades',status:'Regras cadastradas',description:'Texto'},
  {id:'session-item:1',name:'Poção',category:'Itens e efeitos',status:'No inventário',description:'Cura'}];
 const manifest={character_id:'raziel',execution_approved:false,actions:[
  {ref:'technique:raziel:old',label:'Antiga',visible_on_sheet:false,automation_scope:'native',availability:{state:'available',reason:'ok'},limitations:[]},
  {ref:'technique:raziel:hemomancia-arco-habilidade',label:'Tiro do Coração',kind:'ability',automation_scope:'native',description:'Regra atual',availability:{state:'available',reason:'Validação final'},limitations:['Sem certificação completa']},
  {ref:'item:raziel:session-item:1',label:'Poção',kind:'item',automation_scope:'native',availability:{state:'unavailable',reason:'Sem estoque'},limitations:[]}]};
 const rows=m.referenceWithManifest(cards,manifest);
 assert.ok(!rows.some(r=>r.id==='old'));
 assert.equal(rows.find(r=>r.name==='Tiro do Coração').status,'Comando integrado');
 assert.match(rows.find(r=>r.name==='Tiro do Coração').description,/Sem certificação completa/);
 assert.equal(rows.find(r=>r.name==='Poção').status,'Indisponível agora');
 assert.ok(rows.every(r=>!r.status.includes('certificada')));
 assert.deepEqual(cards.map(c=>c.status),['Regras cadastradas','No inventário']);
});
test('missing manifest never promotes structured descriptions or passive records to automatic mechanics',()=>{
 const cards=[{id:'x',name:'X',status:'Regras cadastradas',category:'Habilidades',description:'Texto'}];
 assert.equal(load().referenceWithManifest(cards,null)[0].status,'Automação não verificada');
});
