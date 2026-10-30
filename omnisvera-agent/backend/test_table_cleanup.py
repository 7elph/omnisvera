import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from test_battle_mode import BattleModeTests
from app.combat import confirm_attack_resolution
from app.combat_effects import readeffects
from app.battle_mode import retire_defeated
from app.character_play import _save_state
from app.scene_play import init_scene_play, archive_scene, list_scenes, create_scene


class DefeatedCombatantsTests(BattleModeTests):
    def test_last_actor_defeated_closes_round_and_expires_effect(self):
        self.start()
        self.command('apply', target_type='character', target_id='vezemir', label='Teste', source='fixture', duration='rounds', rounds=1, modifiers={})
        self.command('next_turn')
        before = readeffects(self.db)['round']
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?', (self.enemy['id'],))
            retire_defeated(db, 'now')
        state = readeffects(self.db)
        self.assertEqual(before + 1, state['round'])
        self.assertFalse(state['effects'])
        self.assertEqual('vezemir', state['encounter']['participants'][0]['target_id'])

    def test_fatal_attack_removes_target_but_preserves_pin_and_current_turn(self):
        self.start()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?', (self.enemy['id'],))
        attack = self.attack('fatal-attack')
        confirm_attack_resolution(self.db, resolution_id=attack['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        encounter = readeffects(self.db)['encounter']
        self.assertEqual(['vezemir'], [p['target_id'] for p in encounter['participants']])
        self.assertTrue(encounter['action_committed'])
        with closing(sqlite3.connect(self.db)) as db:
            hp, visible, sheet = db.execute('SELECT current_hp,visible_to_players,sheet_json FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()
        self.assertEqual((0, 1), (hp, visible))
        self.assertTrue(json.loads(sheet)['combat_retired'])
        self.command('next_turn')
        self.assertEqual('vezemir', readeffects(self.db)['encounter']['participants'][0]['target_id'])

    def test_zero_hp_current_actor_passes_to_next_and_persists(self):
        self.start()
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state['current_hp'] = 0
            _save_state(db, 'vezemir', state)
        encounter = readeffects(self.db)['encounter']
        self.assertEqual(self.enemy['id'], encounter['participants'][encounter['turn_index']]['target_id'])
        self.assertFalse(encounter['action_committed'])
        with closing(sqlite3.connect(self.db)) as db, db:
            self.assertEqual([], retire_defeated(db, 'now'))
        self.command('end')


class SceneArchiveTests(unittest.TestCase):
    def test_archive_is_reversible_and_does_not_delete_scene_content(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.sqlite3'
            init_scene_play(path)
            create_scene(path, request_id='fixture-scene', campaign_id='omnisvera', title='Cena preservada', location_name='Estrada', created_by='master')
            scene_id = list_scenes(path)[0]['id']
            archive_scene(path, scene_id)
            self.assertEqual([], list_scenes(path))
            self.assertEqual('Cena preservada', list_scenes(path, include_archived=True)[0]['title'])
            archive_scene(path, scene_id, False)
            self.assertEqual(scene_id, list_scenes(path)[0]['id'])


if __name__ == '__main__':
    unittest.main()
