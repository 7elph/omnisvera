import json,sqlite3,unittest
from contextlib import closing
from unittest.mock import patch
import test_dorn_approved_pack as fixtures

class ActiveDispelTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.DornApprovedPackTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.db=self.f.path;self.map,self.mine=self.f.grid();self.victim=self.f.fixture.enemy['id']
    def web(self):
        return self.f.cast('teia',targets=[{'type':'token','id':self.victim}])['protocol_result']['results'][0]['effect']
    def test_grid_occupant_preview_resolves_web_parent(self):
        from app.spell_effect_runtime import dispel_preview
        from app.combat_effects import effect_snapshot
        effect=self.web()
        with closing(sqlite3.connect(self.db)) as db:
            preview=dispel_preview(db,effect_snapshot(db),self.victim)
        self.assertEqual([e['id'] for e in preview['effects']],[effect['id']])
        self.assertEqual(preview['effects'][0]['kind'],'area')
    def test_dispel_derived_web_removes_area_and_all_occupants_with_one_cost(self):
        from app.combat_effects import readeffects
        effect=self.web();derived=next(e for e in readeffects(self.db)['effects'] if e.get('web_parent_id')==effect['id'])
        with patch('app.dorn_spells.roll_formula',return_value={'total':20}):
            result=self.f.cast('dissipar-magia',effect_id=derived['id'],target_token_id=self.victim)
        self.assertTrue(result['protocol_result']['results'][0]['success'])
        self.assertFalse(any(e.get('spell')=='teia' for e in result['effects']))
    def test_area_range_is_not_caster_self_range(self):
        effect=self.web()
        with closing(sqlite3.connect(self.db)) as db,db:
            effect['web_area']['x_m']=10000
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        before=self.f.fixture.resource('dissipar_magia')
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'alcance'):
                self.f.cast('dissipar-magia',effect_id=effect['id'])
        dice.assert_not_called();self.assertEqual(self.f.fixture.resource('dissipar_magia'),before)
    def test_wrong_pin_cannot_select_other_entities_effect(self):
        effect=self.web()
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'alvo'):
                self.f.cast('dissipar-magia',effect_id=effect['id'],target_token_id=self.mine)
        dice.assert_not_called()

    def test_moved_target_preview_rejects_before_roll_or_cost(self):
        from app.combat_effects import effect_snapshot
        from app.spell_effect_runtime import dispel_preview
        effect=self.web()
        with closing(sqlite3.connect(self.db)) as db,db:
            preview=dispel_preview(db,effect_snapshot(db),self.victim)
            db.execute('UPDATE session_workspace_entity_positions SET cell_y=cell_y+1,version=version+1 WHERE token_id=?',(self.victim,))
        before=self.f.fixture.resource('dissipar_magia')
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'mudaram'):
                self.f.cast('dissipar-magia',effect_id=effect['id'],target_token_id=self.victim,target_fingerprint=preview['fingerprint'])
        dice.assert_not_called();self.assertEqual(self.f.fixture.resource('dissipar_magia'),before)

    def test_two_magic_effects_are_listed_as_two_choices_and_not_an_arbitrary_first(self):
        from app.combat_effects import effect_snapshot
        from app.spell_effect_runtime import dispel_preview
        from app.necromancer_spells import add_effect
        web=self.web()
        with closing(sqlite3.connect(self.db)) as db,db:
            buff=add_effect(db,{'type':'token','id':self.victim},'Força Arcana','test','now',magic_type='arcane',spell_circle=2,caster_level=3)
            preview=dispel_preview(db,effect_snapshot(db),self.victim)
        self.assertEqual({e['id'] for e in preview['effects']},{web['id'],buff['id']})

    def test_resisted_dispel_keeps_area_spends_once_and_replays_one_roll(self):
        from app.combat_effects import effect_snapshot,effect_command,readeffects
        from app.spell_effect_runtime import dispel_preview
        effect=self.web()
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter={'active':True,'battle_mode':True,'map_id':self.map,'turn_index':0,
              'participants':[{'target_type':'character','target_id':'dorn7','name':'Dorn'},{'target_type':'token','target_id':self.victim,'name':'Alvo'}]}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps(encounter),))
            preview=dispel_preview(db,effect_snapshot(db),self.victim)
        args=dict(actor_id='master',actor_role='gm',request_id='resisted-dispel-retry',expected_version=preview['version'],action='dorn_spell_cast',
            payload={'spell_id':'dissipar-magia','effect_id':effect['id'],'target_token_id':self.victim,'target_fingerprint':preview['fingerprint']})
        with patch('app.dorn_spells.roll_formula',return_value={'total':1}) as dice:
            first=effect_command(self.db,**args);second=effect_command(self.db,**args)
        self.assertEqual(first,second);self.assertEqual(dice.call_count,1)
        self.assertFalse(first['protocol_result']['results'][0]['success'])
        self.assertEqual(self.f.fixture.resource('dissipar_magia'),0)
        self.assertTrue(first['encounter']['action_committed'])
        self.assertTrue(any(e['id']==effect['id'] for e in readeffects(self.db)['effects']))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='spell_resolution'").fetchone()[0],1)

    def test_grid_highlight_uses_reachable_area_not_the_occupant_center(self):
        from app.action_range import ring_for_action
        effect=self.web()
        with closing(sqlite3.connect(self.db)) as db,db:
            effect['web_area']['x_m']=24
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=17 WHERE token_id=?',(self.victim,))
        ring=ring_for_action(self.db,ref='technique:dorn7:dissipar-magia',attacker_token_id=self.mine,map_id=self.map,attacker_character_id='dorn7')
        victim=next(e for e in ring['targets'] if e['id']==self.victim)
        self.assertTrue(victim['valid']);self.assertEqual(victim['meters'],18)

    def test_reflexos_contract_and_cast_use_approved_ninety_percent(self):
        from app.action_library import native_action_contract
        contract=native_action_contract('technique:dorn7:reflexos',5)
        self.assertEqual(contract['resolution']['intercept_chance_percent'],90)
        with patch('app.dorn_spells.roll_formula',return_value={'total':1}):effect=self.f.cast('reflexos')['effects'][0]
        self.assertEqual(effect['intercept_chance_percent'],90)
        from app.dorn_spell_pack import redirect_hits
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spell_pack.roll_formula',return_value={'total':9}):
            damage,detail=redirect_hits(db,'character','dorn7',[{'result':'hit','damage_total':4}],'now')
        self.assertEqual(damage,0);self.assertTrue(detail['rolls'][0]['intercepted'])

class TargetTurnDotTests(unittest.TestCase):
    def setUp(self):
        import test_spell_engine as fixture
        fixture.SpellEngineTests.setUp(self)
        from app.combat_effects import init_effects
        from app.necromancer_spells import add_effect
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            add_effect(db,{'type':'character','id':'vezemir'},'Toque Sombrio','Morthak','now',dot_hp=True,necro_spell='toque-sombrio')
        self.p={'target_type':'character','target_id':'vezemir','name':'Vezemir'}
    def test_repeated_hook_same_victim_turn_rolls_only_once(self):
        from app.necromancer_spells import touch_turn
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.necromancer_spells.roll_formula',return_value={'total':1}) as roll:
            for request in ['hook-1','hook-2']:
                touch_turn(db,self.p,'now',request,encounter={'started_at':'fight','turn_sequence':7})
            hp=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])['current_hp']
        self.assertEqual(roll.call_count,1);self.assertEqual(hp,29)
