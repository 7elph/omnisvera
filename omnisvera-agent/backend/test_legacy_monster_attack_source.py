"""Prepared/custom creatures keep text provenance; no operational database."""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.combat import monster_attack_definition


class LegacyMonsterAttackSourceTests(unittest.TestCase):
    def token(self, source):
        return {'id': 'legacy-fixture', 'name': 'Vigia preparado', 'token_type': 'monster',
                'sheet': {'source': source, 'attacks': [{'name': 'Espada', 'bonus': 3, 'damage': '1d6'}]}}

    def test_text_provenance_does_not_crash_attack_resolution(self):
        for source in ['session7:operator', None, [], 17, {'monster_id': 'goblin'}]:
            with self.subTest(source=source):
                attack = monster_attack_definition(self.token(source), '0')['attacks'][0]
                self.assertEqual(attack['damage'], '1d6')
                self.assertEqual(attack['attack_bonus'], 3)

    def test_master_action_card_accepts_legacy_provenance(self):
        from app import main
        from app.action_library import _token_source
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'fixture.sqlite3'
            with closing(sqlite3.connect(database)) as db, db:
                db.execute('CREATE TABLE session_workspace_tokens(id TEXT,name TEXT,sheet_json TEXT,token_type TEXT)')
                token = self.token('session7:operator')
                db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,?,?)',
                           (token['id'], token['name'], json.dumps(token['sheet']), 'monster'))
            with patch.object(main, 'settings', SimpleNamespace(database_path=database)), patch.object(main, 'list_workspace_tokens', return_value=[token]):
                result = main.gm_get_workspace_token_actions(token['id'], SimpleNamespace(mode='gm'))
            self.assertEqual(result['attacks'][0]['status'], 'ready')
            self.assertEqual(_token_source(database, token['id'])['map']['attacks'][0]['status'], 'ready')
            self.assertEqual(token['sheet']['source'], 'session7:operator')


if __name__ == '__main__':
    unittest.main()
