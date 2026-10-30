const { test } = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), ts = require('typescript');
const moduleUnderTest = { exports: {} }, jsx = (type, props) => ({ type, props });
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/ActiveEffectIcons.tsx', 'utf8'), {
 compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX }
}).outputText, { module: moduleUnderTest, exports: moduleUnderTest.exports, require: id => id === '../api'
 ? { mediaUrlFromVaultPath: p => p } : id === './SessionActionArt' ? { ActionArt: 'ActionArt' } : { jsx, jsxs: jsx } });
const { activeIcons, default: Component } = moduleUnderTest.exports;
const effect = { effect_id: 'e1', target_type: 'character', target_id: 'vezemir', duration: 'rounds', rounds: 3,
 card: { id: 'speed', name: 'Velocidade', image_path: 'speed.jpg', description: 'Descrição' } };
test('only authoritative active effects render; historical actions cannot keep an icon alive', () => {
 assert.equal(activeIcons({ active_effect_icons: [effect] }, 'vezemir').length, 1);
 assert.equal(activeIcons({ active_effect_icons: [] }, 'vezemir').length, 0);
 assert.equal(activeIcons({ active_effect_icons: [{ ...effect, rounds: 0 }] }, 'vezemir').length, 0);
 assert.equal(activeIcons({ active_effect_icons: [effect] }, 'raziel').length, 0);
 assert.equal(activeIcons({ active_effect_icons: [{ ...effect, target_type: 'token' }] }, 'vezemir').length, 0);
 assert.equal(activeIcons({ active_effect_icons: [effect, { ...effect, effect_id: 'e2' }] }, 'vezemir').length, 1);
});
test('fictional time, next attack and removal snapshots do not depend on encounter history', () => {
 assert.equal(activeIcons({ active_effect_icons: [{ ...effect, duration: 'fictional_time', remaining_seconds: 0 }] }, 'vezemir').length, 0);
 assert.equal(activeIcons({ active_effect_icons: [{ ...effect, duration: 'next_attack', rounds: null }] }, 'vezemir').length, 1);
 assert.equal(Component({ state: { active_effect_icons: [] }, targetId: 'vezemir' }), null);
});
test('combat icons remain noninteractive; compact party header leaves status in the sheet', () => {
 const value = Component({ state: { active_effect_icons: [effect] }, targetId: 'vezemir', interactive: false });
 assert.equal(value.props.children[0].props.children[0].type, 'img');
 assert.equal(value.props.children[0].props.children[0].props.src, 'speed.jpg');
 assert.equal(value.props.children[0].props.children[1].props.children,3);
 const encounter = fs.readFileSync('src/components/CombatEncounterPanel.tsx', 'utf8');
 assert.ok(encounter.includes('<ActiveEffectIcons state={state} targetId={p.target_id}'));
 assert.ok(!encounter.includes('combatActionCards('));
 const workspace = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
 assert.ok(workspace.includes('<PartyMemberSummary'));
 assert.ok(!workspace.includes('targetId={item.id} interactive={false}'));
});

test('badges prefer target turns and never invent turns for fictional time',()=>{
 const badge=e=>Component({state:{active_effect_icons:[e]},targetId:'vezemir'}).props.children[0].props.children[1];
 assert.equal(badge({...effect,turns_remaining:2}).props.children,2);
 assert.equal(badge({...effect,duration:'fictional_time',rounds:null,remaining_seconds:600}),false);
});
