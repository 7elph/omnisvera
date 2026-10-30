"""Reproduce two requests deriving a buff on opposite sides of its first commit."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from threading import Barrier, Event, Lock
from unittest import TestCase
from unittest.mock import patch

from app import main
from app.access import AccessContext
from app.combat_effects import effect_command, init_effects, readeffects, replay_technique_effect
import test_combat as fixtures


class VezemirBuffConcurrencyTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.CombatAttackResolutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.path = self.fixture.database
        init_effects(self.path)
        with closing(sqlite3.connect(self.path)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state['resources'] = [{'key':'forca_arcana','current':1,'maximum':1}]
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))

    def test_no_matching_receipt_preserves_original_failure_and_resource(self):
        with patch.object(main, 'settings', replace(main.settings, database_path=self.path)), \
             patch.object(main, '_playable_character', return_value={'definition':{'level':5,'attributes':{'strength':14}}}), \
             patch('app.combat_effects.replay_technique_effect', return_value=None), \
             patch.object(main, 'effect_command', side_effect=ValueError('Estado dos efeitos mudou.')):
            with self.assertRaises(main.HTTPException) as error:
                main.use_character_technique('vezemir','forca-arcana',main.TechniqueUse(request_id='missing-buff-receipt'),AccessContext(mode='gm'))
            self.assertEqual(400,error.exception.status_code)
            self.assertEqual('Estado dos efeitos mudou.',error.exception.detail)
        self.assertEqual([],readeffects(self.path)['effects'])

    def test_receipt_for_another_source_or_actor_is_never_accepted(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)',('wrong-buff-receipt',json.dumps(['master','apply',{'source':'Velocidade (Vezemir)','target_type':'character','target_id':'vezemir'},None]),'{}'))
        with self.assertRaisesRegex(ValueError,'outro conteúdo'):
            replay_technique_effect(self.path,actor_id='master',request_id='wrong-buff-receipt',source='Força Arcana (Vezemir)',target_id='vezemir')
        with self.assertRaisesRegex(ValueError,'outro conteúdo'):
            replay_technique_effect(self.path,actor_id='other-player',request_id='wrong-buff-receipt',source='Velocidade (Vezemir)',target_id='vezemir')

    def test_concurrent_retry_recovers_receipt_after_derived_strength_changes(self):
        early = Barrier(2)
        committed, mutex = Event(), Lock()
        calls = {'lookup':0,'sheet':0}

        def lookup(*args, **kwargs):
            with mutex:
                calls['lookup'] += 1
                ordinal = calls['lookup']
            result = replay_technique_effect(*args, **kwargs)
            if ordinal <= 2:
                self.assertIsNone(result)
                early.wait(timeout=4)
            return result

        def sheet(*args):
            with mutex:
                calls['sheet'] += 1
                ordinal = calls['sheet']
            if ordinal == 2:
                self.assertTrue(committed.wait(4))
            bonus = sum(e.get('modifiers',{}).get('strength_bonus',0) for e in readeffects(self.path)['effects'])
            return {'definition':{'level':5,'attributes':{'strength':14+bonus}}}

        def execute(*args, **kwargs):
            result = effect_command(*args, **kwargs)
            committed.set()
            return result

        with patch.object(main, 'settings', replace(main.settings, database_path=self.path)), \
             patch.object(main, '_playable_character', side_effect=sheet), \
             patch('app.combat_effects.replay_technique_effect', side_effect=lookup), \
             patch.object(main, 'effect_command', side_effect=execute), \
             patch('app.combat_effects.roll_formula', return_value={'total':8,'individual_results':[3]}) as dice:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _:main.use_character_technique('vezemir','forca-arcana',main.TechniqueUse(request_id='same-buff-concurrent'),AccessContext(mode='gm')), range(2)))
            self.assertEqual(results[0], results[1])
            self.assertEqual(1, dice.call_count)
        effects = readeffects(self.path)['effects']
        self.assertEqual(1, len(effects))
        self.assertEqual(2, effects[0]['modifiers']['strength_bonus'])
        with closing(sqlite3.connect(self.path)) as db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(0, state['resources'][0]['current'])
            self.assertEqual(1, db.execute("SELECT count(*) FROM combat_effect_commands WHERE request_id='same-buff-concurrent'").fetchone()[0])
