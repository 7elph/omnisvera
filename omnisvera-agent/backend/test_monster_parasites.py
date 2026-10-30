import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_monster_conditions_runtime as fixture


class ParasiteTests(unittest.TestCase):
    setUp = fixture.MonsterConditionRuntimeTests.setUp
    hp = fixture.MonsterConditionRuntimeTests.hp
    effects = fixture.MonsterConditionRuntimeTests.effects
    record = fixture.MonsterConditionRuntimeTests.record
    setup_monster = fixture.MonsterConditionRuntimeTests.setup_monster

    def infest(self):
        from app.monster_conditions import apply_on_hit
        record = self.record('flagelo-da-podridao')
        with closing(sqlite3.connect(self.db)) as db, db, patch('app.dorn_spells.save', return_value={'success':False}):
            return apply_on_hit(db, record, 'now')

    def test_approved_rule_is_explicit_and_native_without_fake_damage(self):
        from app.combat import monster_attack_definition
        attack = monster_attack_definition(self.setup_monster('flagelo-da-podridao'), '0')['attacks'][0]
        self.assertTrue(attack['effect_only'])
        result = self.infest()
        self.assertEqual(result[0]['effect'], 'parasite')
        self.assertEqual(self.effects()[0]['campaign_rule'], 'flagelo-provisional-v1')
        self.assertEqual(self.hp(), 30)

    def test_three_victim_turns_exactly_once_each_no_stacking_or_refresh(self):
        from app.monster_parasites import turn_start
        self.infest()
        participant = {'target_type':'character','target_id':'vezemir','name':'Vezemir'}
        with closing(sqlite3.connect(self.db)) as db, db, patch('app.monster_parasites.roll_formula', return_value={'total':3,'individual_results':[3]}) as dice:
            for seq in (1,1,2,3,4):
                turn_start(db, participant, {'started_at':'fight','turn_sequence':seq}, 'now', 'request-'+str(seq))
        self.assertEqual(self.hp(), 21)
        self.assertEqual(self.effects(), [])
        self.assertEqual(dice.call_count, 3)

    def test_successful_jpc_and_repeated_contact_do_not_stack(self):
        from app.monster_conditions import apply_on_hit
        record = self.record('flagelo-da-podridao')
        with closing(sqlite3.connect(self.db)) as db, db, patch('app.dorn_spells.save', return_value={'success':True}):
            apply_on_hit(db,record,'now')
        self.assertEqual(self.effects(), [])
        self.infest(); self.infest()
        self.assertEqual(len(self.effects()), 1)

    def test_remove_is_owner_scoped_idempotent_and_spends_main_action(self):
        from app.combat_effects import effect_command, readeffects
        self.infest()
        with closing(sqlite3.connect(self.db)) as db, db:
            encounter={'active':True,'battle_mode':True,'started_at':'fight','map_id':'default','turn_sequence':1,
                'participants':[{'target_type':'character','target_id':'vezemir','name':'Vezemir'}], 'turn_index':0}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps(encounter),))
        version=readeffects(self.db)['version']
        args=dict(actor_id='raziel', actor_role='player', request_id='parasite-remove-foreign', expected_version=version, action='parasite_remove', payload={'target_type':'character','target_id':'vezemir'}, allow_player=True)
        with self.assertRaises(PermissionError):effect_command(self.db,**args)
        args.update(actor_id='vezemir',request_id='parasite-remove-own')
        first=effect_command(self.db,**args)
        self.assertEqual(effect_command(self.db,**args),first)
        self.assertTrue(first['encounter']['action_committed'])
        self.assertEqual(self.effects(),[])
        self.assertEqual(self.hp(),30)

    def test_turn_hook_is_in_native_next_turn_not_global_round(self):
        from app.combat_effects import effect_command, readeffects
        self.infest()
        with closing(sqlite3.connect(self.db)) as db,db:
            e={'active':True,'battle_mode':False,'started_at':'fight','map_id':'default','turn_sequence':1,
               'participants':[{'target_type':'token','target_id':'gob1','name':'Flagelo'},{'target_type':'character','target_id':'vezemir','name':'Vezemir'}], 'turn_index':0}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps(e),))
        with patch('app.monster_parasites.roll_formula',return_value={'total':2,'individual_results':[2]}):
            response=effect_command(self.db,actor_id='master',actor_role='gm',request_id='parasite-native-next',expected_version=readeffects(self.db)['version'],action='next_turn',payload={})
        self.assertEqual(self.hp(),28)
        self.assertEqual(response['effects'][0]['turns_remaining'],2)
