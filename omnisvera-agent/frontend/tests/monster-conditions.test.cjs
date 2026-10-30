const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function load(file){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:m,exports:m.exports,require:()=>({})});return m.exports;}

test('paralysis and petrification block actions and consumables without consuming a turn',()=>{
 const {combatActionBlock,consumableActionBlock}=load('src/components/combatActionAvailability.ts');
 for(const kind of ['paralyzed','petrified']){
  const state={effects:[{target_id:'raziel',monster_condition:kind,blocks_actions:true,label:'Paralisia'}],encounter:{active:true,battle_mode:true,participants:[{target_id:'raziel'}],turn_index:0}};
  assert.match(combatActionBlock(state,'raziel',10),/Paralisia/);assert.match(consumableActionBlock(state,'raziel',10),/Paralisia/);
  assert.equal(state.encounter.action_committed,undefined);
  assert.doesNotMatch(combatActionBlock(state,'vezemir',10),/Paralisia/);
  state.effects=[];assert.equal(combatActionBlock(state,'raziel',10),'');
 }
});

test('result exposes JP, real damage and original time units without internal fields',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts');
 const text=attackOutcomeText({result:'hit',damage_total:8,hp_before:30,hp_after:22,breakdown:{
  damage_defenses:{damage_before_defenses:8,damage_after_defenses:0},
  monster_rider_results:[{name:'Paralisia',effect:'paralyzed',save:{total:2,target:14},resisted:false,remaining_seconds:1200,duration_unit:'turns',rider_id:'hidden-id'},
   {name:'Veneno',effect:'poison_damage',save:{total:20,target:14},resisted:true,damage_dealt:3}]
 }});
 assert.match(text.details,/JP 2\/14.*falhou.*2 turno\(s\) de exploração/);
 assert.match(text.details,/Veneno.*dano adicional 3/);assert.match(text.details,/Defesas: 8 → 0/);
 assert.doesNotMatch(text.details,/hidden-id|rider_id|monster_condition/);
});

test('gaze and gas results show condition or immunity without pretending they caused HP damage',()=>{
 const {monsterBreathOutcomeText}=load('src/attackOutcome.ts');
 const text=monsterBreathOutcomeText({results:[
  {target:'Raziel',damage_dealt:0,resisted:false,condition:{name:'Petrificação',effect:'petrified',effect_id:'test-only',duration_unit:'permanent'},save:{total:2,target:14}},
  {target:'Cocatriz',damage_dealt:0,resisted:false,condition:{name:'Petrificação',effect:'petrified',immune:'Imunidade à petrificação'}}
 ]});
 assert.match(text.summary,/1 condição aplicada/);assert.match(text.details,/Petrificação.*até remoção/);
 assert.match(text.details,/Cocatriz.*imune/);assert.doesNotMatch(text.details,/test-only|0 de dano|effect_id/);
});

test('poison results expose attribute loss and onset in human units',()=>{
 const {attackOutcomeText}=load('src/attackOutcome.ts');
 const text=attackOutcomeText({result:'hit',damage_total:2,hp_before:30,hp_after:28,breakdown:{monster_rider_results:[
  {name:'Veneno',effect:'poison_attribute',attribute:'constitution',attribute_before:12,attribute_after:8,save:{total:2,target:14},resisted:false},
  {name:'Veneno',effect:'delayed_condition',delay_seconds:90,duration_seconds:1200,remaining_seconds:90,duration_unit:'rounds',phase:'latent'}
 ]}});
 assert.match(text.details,/Constituição 12 → 8/);assert.match(text.details,/início em 9 rodada/);
 assert.doesNotMatch(text.details,/constitution|fictional_time|poison_spec/);
});
