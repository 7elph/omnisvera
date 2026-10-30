from unittest import TestCase
from app.session_workspace import save_workspace_token, get_workspace_snapshot
import test_spatial_grid as grid_fixture
import test_dorn_protocols as dorn_fixture
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from app.character_play import init_character_play, apply_character_action
from app.combat_effects import effect_command, readeffects


class SimulationPinRegressionTests(TestCase):
    def test_repin_existing_character_preserves_authoritative_cell_without_trigger_conflict(self):
        fixture = grid_fixture.SpatialGridTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        before = fixture.position()
        for _ in range(2):
            repeated = save_workspace_token(fixture.db, token_type='character', character_id='vezemir',
                name='Vezemir', map_id=fixture.map, latitude=90, longitude=90)
            self.assertEqual(fixture.token['id'], repeated['id'])
        snapshot = get_workspace_snapshot(fixture.db, map_id=fixture.map, is_gm=True)
        self.assertEqual(1, len(snapshot['tokens']))
        self.assertEqual(before, fixture.position())


class SimulationRetryRegressionTests(TestCase):
    def test_night_form_concurrent_retry_consumes_once_and_rejects_changed_animal(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory)/'night.sqlite3'; init_character_play(db_path)
            state={'current_hp':10,'maximum_hp':10,'resources':[{'key':'forma_da_noite','current':3,'maximum':3}], 'conditions':[]}
            with closing(sqlite3.connect(db_path)) as db,db:
                db.execute('INSERT INTO character_states VALUES(?,?,?,?)',('raziel',json.dumps(state),1,'now'))
            args=dict(character_id='raziel',actor_id='raziel',actor_role='player',action='consume_resource',payload={'resource_key':'forma_da_noite','amount':1,'animal':'corvo'},request_id='night-replay-regression')
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _: apply_character_action(db_path,**args),range(2)))
            replay=apply_character_action(db_path,**args)
            self.assertTrue(replay['replayed'])
            self.assertEqual(1,len({r['event_id'] for r in results+[replay]}))
            with closing(sqlite3.connect(db_path)) as db:
                saved=json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])
                self.assertEqual(2,saved['resources'][0]['current']);self.assertEqual('corvo',saved['animal_form'])
                self.assertEqual(1,db.execute('SELECT count(*) FROM character_events').fetchone()[0])
            with self.assertRaisesRegex(ValueError,'outro conteúdo'):
                apply_character_action(db_path,**{**args,'payload':{**args['payload'],'animal':'morcego'}})

    def test_dorn_diagnostic_receipt_ignores_server_derived_sheet_version_not_user_input(self):
        fixture=dorn_fixture.DornProtocolTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.start()
        definition={'name':'Dorn','attributes':{'intelligence':16},'attribute_modifiers':{'intelligence':3},'effects_version':1}
        payload={'subject':'Componente do ensaio','difficulty':14,'_definition':definition}
        args=dict(actor_id='master',actor_role='gm',request_id='diagnostic-replay-regression',expected_version=readeffects(fixture.db)['version'],action='dorn_diagnose',payload=payload)
        with patch('app.dorn_protocols.roll_formula',return_value={'total':18,'individual_results':[15]}) as dice:
            first=effect_command(fixture.db,**args)
            second=effect_command(fixture.db,**{**args,'payload':{**payload,'_definition':{**definition,'effects_version':2}}})
            self.assertEqual(first,second);self.assertEqual(1,dice.call_count)
        with self.assertRaisesRegex(ValueError,'outro conteúdo'):
            effect_command(fixture.db,**{**args,'payload':{**payload,'difficulty':15}})
