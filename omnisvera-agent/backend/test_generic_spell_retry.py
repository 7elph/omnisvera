"""Discardable SQLite only: generic spell/action command receipts."""
import json
import sqlite3
import threading
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import patch

import test_spell_engine as baseline
from app.spell_engine import cast_spell, execute_token_action

class GenericSpellRetryTests(TestCase):
    setUp = baseline.SpellEngineTests.setUp
    hp = baseline.SpellEngineTests.hp
    token_hp = baseline.SpellEngineTests.token_hp

    def cast(self, request_id='spell-retry-001', **overrides):
        args=dict(spell_id='arcana-bola-de-fogo',caster_type='token',caster_id='gob1',
                  targets=[{'type':'character','id':'vezemir'}],roll_mode='physical',d20=[1],request_id=request_id)
        args.update(overrides)
        return cast_spell(self.db,**args)

    def count(self, table):
        with closing(sqlite3.connect(self.db)) as c:
            return c.execute('SELECT count(*) FROM '+table).fetchone()[0]

    def test_replay_rolls_damages_and_logs_once(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            first=self.cast();second=self.cast()
        self.assertEqual(first,second);self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)
        self.assertEqual(1,self.count('combat_effect_commands'));self.assertEqual(1,self.count('session_ledger'))

    def test_same_id_different_target_or_dice_is_rejected(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):self.cast()
        for change in ({'targets':[{'type':'token','id':'gob1'}]},{'d20':[20]}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError,'outra|outro|pertence'):
                self.cast(**change)
        self.assertEqual(26,self.hp())

    def test_replay_survives_caster_removal(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):first=self.cast()
        with closing(sqlite3.connect(self.db)) as c,c:c.execute("DELETE FROM session_workspace_tokens WHERE id='gob1'")
        with patch('app.spell_engine.roll_formula',side_effect=AssertionError('Replay rerolled')):
            self.assertEqual(first,self.cast())

    def test_replay_survives_target_removal(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):first=self.cast()
        with closing(sqlite3.connect(self.db)) as c,c:c.execute("DELETE FROM character_states WHERE profile_id='vezemir'")
        self.assertEqual(first,self.cast())

    def test_simultaneous_retry_commits_once(self):
        barrier=threading.Barrier(2)
        def call():barrier.wait(timeout=5);return self.cast()
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng,ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(lambda _:call(),range(2)))
        self.assertEqual(a,b);self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)

    def test_failed_command_does_not_reserve_id_or_damage_first_target(self):
        with self.assertRaises(ValueError):self.cast(targets=[{'type':'character','id':'vezemir'},{'type':'token','id':'missing'}],d20=[1,1])
        self.assertEqual(30,self.hp());self.assertEqual(0,self.count('combat_effect_commands'))
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):self.cast()
        self.assertEqual(26,self.hp())

    def test_ledger_failure_rolls_back_hp_and_receipt(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}),patch('app.spell_engine.append_session_ledger_event',side_effect=RuntimeError('ledger error')):
            with self.assertRaisesRegex(RuntimeError,'ledger error'):self.cast()
        self.assertEqual(30,self.hp());self.assertEqual(0,self.count('combat_effect_commands'))

    def test_monster_usable_replays_and_rejects_cross_endpoint_collision(self):
        args=dict(token_id='gob1',ability_name='Baforada de teste',targets=[{'type':'character','id':'vezemir'}],roll_mode='physical',d20=[1],request_id='usable-retry-001')
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            a=execute_token_action(self.db,**args);b=execute_token_action(self.db,**args)
        self.assertEqual(a,b);self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)
        with self.assertRaisesRegex(ValueError,'outra|outro|pertence'):self.cast(request_id='usable-retry-001')

    def test_two_distinct_commands_still_execute_independently(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            self.cast('spell-first-001');self.cast('spell-second-001')
        self.assertEqual(22,self.hp());self.assertEqual(2,rng.call_count)

    def test_legacy_call_without_id_keeps_existing_behavior(self):
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):self.cast(None);self.cast(None)
        self.assertEqual(22,self.hp());self.assertEqual(0,self.count('combat_effect_commands'))

    def test_invalid_request_id_rejected_without_writing(self):
        for value in ('', 'bad key', 'x'*121, True):
            with self.subTest(value=value),self.assertRaises(ValueError):self.cast(value)
        self.assertEqual(30,self.hp())

    def battle(self):
        from app.combat_effects import init_effects
        init_effects(self.db)
        encounter = {'active': True, 'battle_mode': True, 'map_id': 'default',
                     'participants': [{'target_type': 'token', 'target_id': 'gob1'},
                                      {'target_type': 'character', 'target_id': 'vezemir'}],
                     'turn_index': 0, 'attack_limit': 1, 'attacks_used': 0}
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',
                               (json.dumps(encounter),))

    def attacks_used(self):
        with closing(sqlite3.connect(self.db)) as connection:
            return json.loads(connection.execute(
                'SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0])['attacks_used']

    def test_retry_returns_original_result_after_turn_budget_spent(self):
        self.battle()
        with patch('app.spell_engine.roll_formula', return_value={'total': 4}) as rng:
            first = self.cast()
            second = self.cast()
            with self.assertRaises(ValueError):
                self.cast('another-command-same-turn')
        self.assertEqual(first, second)
        self.assertEqual(26, self.hp())
        self.assertEqual(1, self.attacks_used())
        self.assertEqual(1, rng.call_count)
        self.assertEqual(1, self.count('session_ledger'))

    def test_receipt_failure_rolls_back_damage_ledger_and_turn_budget(self):
        self.battle()
        with patch('app.spell_engine.roll_formula', return_value={'total': 4}), patch(
                'app.spell_engine.save_receipt', side_effect=sqlite3.OperationalError('receipt unavailable')):
            with self.assertRaisesRegex(sqlite3.OperationalError, 'receipt unavailable'):
                self.cast()
        self.assertEqual(30, self.hp())
        self.assertEqual(0, self.attacks_used())
        self.assertEqual(0, self.count('session_ledger'))
        self.assertEqual(0, self.count('combat_effect_commands'))

    def test_replay_uses_original_result_after_caster_level_changes(self):
        with patch('app.spell_engine.roll_formula', return_value={'total': 4}):
            first = self.cast()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            sheet = json.loads(connection.execute(
                "SELECT sheet_json FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0])
            sheet['spellcaster_level'] = 5
            connection.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",
                               (json.dumps(sheet),))
        with patch('app.spell_engine.roll_formula', side_effect=AssertionError('Replay rerolled')):
            self.assertEqual(first, self.cast())
        self.assertEqual(26, self.hp())
