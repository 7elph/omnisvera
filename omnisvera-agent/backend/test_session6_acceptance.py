"""Guards for the synthetic acceptance harness; no operational data is opened."""
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import gc
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
import session6_acceptance as acceptance


class SyntheticAcceptanceFixtureTests(unittest.TestCase):
    def test_seed_is_complete_synthetic_and_cannot_overwrite(self):
        with TemporaryDirectory() as folder:
            db = Path(folder) / 'fixture.sqlite3'
            with redirect_stdout(StringIO()):
                acceptance.seed(db)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(5, conn.execute('SELECT count(*) FROM character_sheets').fetchone()[0])
                self.assertEqual(2, conn.execute('SELECT count(*) FROM session_workspace_maps').fetchone()[0])
                self.assertTrue(all('sintético' in r[0] for r in conn.execute('SELECT content FROM notes')))
                state=json.loads(conn.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
                self.assertEqual((13, 13), (state['current_hp'], state['maximum_hp']))
                self.assertEqual(3, sum(r['maximum'] for r in state['resources']))
                self.assertEqual(1, next(r['current'] for r in state['resources'] if r['key']=='dorn_misseis_magicos'))
            before=db.read_bytes()
            with self.assertRaisesRegex(ValueError, 'replace'):
                acceptance.seed(db)
            self.assertEqual(before, db.read_bytes())
            # Existing initializers leave cyclic SQLite connections until GC on Windows.
            gc.collect()

    def test_non_temp_path_rejected_before_open(self):
        with self.assertRaisesRegex(ValueError, 'temporary'):
            acceptance.seed(Path(__file__).parent / 'forbidden-fixture.sqlite3')

    def test_scene_privacy_and_public_pc_state_remain_unchanged(self):
        from app.scene_play import create_scene, add_participant, change_scene_status, scene_view
        from app.main import _character_summary
        with TemporaryDirectory() as folder:
            db = Path(folder) / 'privacy.sqlite3'
            scene, _ = create_scene(db, request_id='s6-privacy', campaign_id='fixture',
                                   title='Cena fixture', location_name='Fixture', created_by='master',
                                   private_notes='Segredo fixture')
            add_participant(db, scene['id'], participant_type='player_character', character_id='morthak',
                            public_label='Morthak', public_status='Ferido', private_status='Segredo privado')
            self.assertIsNone(scene_view(db, scene['id'], access_mode='player', profile_id='vezemir'))
            change_scene_status(db, scene['id'], 'paused')
            player = scene_view(db, scene['id'], access_mode='player', profile_id='vezemir')
            self.assertNotIn('private_notes', player)
            self.assertNotIn('private_status', player['participants'][0])
            self.assertEqual('Ferido', player['participants'][0]['public_status'])
            gm = scene_view(db, scene['id'], access_mode='gm', profile_id=None)
            self.assertEqual('Segredo privado', gm['participants'][0]['private_status'])
            public_pc = _character_summary({'definition': {'id':'morthak', 'name':'Morthak'},
                                            'state': {'current_hp':4, 'maximum_hp':9, 'conditions':['ferido']},
                                            'access_level':'public', 'private_notes':'Não projetar'})
            self.assertEqual((4, 9, ['ferido']), (public_pc['current_hp'], public_pc['maximum_hp'], public_pc['conditions']))
            self.assertNotIn('private_notes', public_pc)
            gc.collect()
