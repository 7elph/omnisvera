from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.main import AccessContext
from app.session_workspace import init_session_workspace, save_workspace_token


class MasterReferenceTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'reference.sqlite3'
        init_session_workspace(self.db)
        self.settings = replace(main.settings, database_path=self.db,
                                master_token='reference-gm', player_token='reference-player')

    def test_specializations_only_match_class_and_reserved_owner(self):
        for profile, class_name, expected in [
            ('vezemir', 'Guerreiro', {'guerreiro-arma', 'barbaro', 'paladino'}),
            ('morthak', 'Mago', {'necromante'}),
            ('dorn7', 'Mago', set()), ('raziel', 'Hemomante', set()),
        ]:
            with self.subTest(profile=profile), patch.object(main, 'settings', self.settings), patch.object(
                main, '_playable_character', return_value={'definition': {'class_name': class_name, 'level': 5}}), patch.object(
                    main, '_character_access_level', return_value='owner'):
                result = main.list_specialization_options(profile, AccessContext(mode='gm'))
                self.assertEqual(expected, {row['id'] for row in result['options']})
                if profile == 'vezemir':
                    paladin = next(row for row in result['options'] if row['id'] == 'paladino')
                    self.assertFalse(paladin['eligible'])
                    self.assertTrue(any('alinhamento' in reason for reason in paladin['reasons']))

    def test_all_created_npc_tokens_are_readable_only_by_master_without_revealing(self):
        tokens = [save_workspace_token(self.db, token_type='monster', name=name,
                  latitude=10, longitude=10, map_id=map_id, visible_to_players=False,
                  sheet={'notes': 'Segredo do Mestre'}) for name, map_id in [('Maera', 'gate'), ('Serren', 'warehouse')]]
        save_workspace_token(self.db, token_type='location', name='Portão', latitude=1, longitude=1)
        with patch.object(main, 'settings', self.settings), closing(TestClient(main.app)) as client:
            gm = client.get('/gm/workspace/npc-tokens', headers={'X-Omnisvera-Token': 'reference-gm'})
            self.assertEqual(200, gm.status_code)
            self.assertEqual({row['id'] for row in tokens}, {row['id'] for row in gm.json()})
            self.assertTrue(all(not row['visible_to_players'] for row in gm.json()))
            self.assertIn(client.get('/gm/workspace/npc-tokens', headers={'X-Omnisvera-Token': 'reference-player'}).status_code, (401, 403))
            self.assertIn(client.get('/gm/workspace/npc-tokens').status_code, (401, 403))

    def test_saved_gm_sheets_remain_available_when_not_in_active_player_profiles(self):
        settings = replace(self.settings, player_profiles={'vezemir': {'character_path': 'Vezemir.md'}})
        with patch.object(main, 'settings', settings), patch.object(main, '_character_ids', return_value=['vezemir', 'dorn7', 'varkh']):
            roster = main.gm_companion_roster(AccessContext(mode='gm'))
        self.assertEqual(['dorn7', 'varkh'], roster['gm_character_ids'])
