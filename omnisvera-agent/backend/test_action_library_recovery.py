"""Native command IDs through the legacy aggregator, SQLite TEMP only."""
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch
import test_action_library as baseline
from app.action_library import execute_action

class LibraryRecoveryTests(TestCase):
    setUp=baseline.ActionLibraryTests.setUp

    def hp(self, actor='vezemir'):
        with closing(sqlite3.connect(self.db)) as db:
            return __import__('json').loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(actor,)).fetchone()[0])['current_hp']

    def cast(self, **overrides):
        kwargs=dict(targets=[{'type':'character','id':'vezemir'}],caster_type='token',caster_id='gob1',
                    roll_mode='physical',d20=[1],request_id='library-reload-spell-01')
        kwargs.update(overrides)
        return execute_action(self.db,'spell:arcana-bola-de-fogo',**kwargs)

    def test_spell_replay_survives_new_call_without_damage_or_roll(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            first=self.cast();second=self.cast()
        self.assertEqual(first,second);self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)

    def test_changed_target_with_same_id_is_rejected(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):self.cast()
        with self.assertRaises(ValueError):self.cast(targets=[{'type':'token','id':'gob2'}])
        self.assertEqual(26,self.hp())

    def test_usable_replays_native_receipt(self):
        kwargs=dict(targets=[{'type':'character','id':'vezemir'}],roll_mode='physical',d20=[1],request_id='library-usable-01')
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            a=execute_action(self.db,'token:gob1:ability:Baforada de teste',**kwargs)
            b=execute_action(self.db,'token:gob1:ability:Baforada de teste',**kwargs)
        self.assertEqual(a,b);self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)

    def test_token_attack_uses_existing_resolution_and_confirmation(self):
        kwargs=dict(targets=[{'type':'token','id':'gob2'}],roll_mode='physical',d20=[15],request_id='library-attack-01')
        with patch('app.combat.roll_formula',return_value={'total':2,'individual_results':[2],'modifier':0}) as rng:
            a=execute_action(self.db,'token:gob1:attack:0',**kwargs)
            b=execute_action(self.db,'token:gob1:attack:0',**kwargs)
        self.assertEqual(a,b);self.assertEqual(1,rng.call_count)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(7,db.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='gob2'").fetchone()[0])

    def test_invalid_id_fails_before_any_roll(self):
        with patch('app.spell_engine.roll_formula',side_effect=AssertionError('must not roll')):
            with self.assertRaises(ValueError):self.cast(request_id='invalid key')
