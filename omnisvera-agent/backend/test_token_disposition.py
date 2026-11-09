"""Companion 3.0: GM disposition marker on creature pins (merge-only, GM-only)."""
import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.access import AccessContext
from app.session_workspace import init_session_workspace, save_workspace_token


class TokenDispositionTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / 'disposition.sqlite3'
        init_session_workspace(self.db)
        self.pin = save_workspace_token(self.db, token_type='monster', name='Klhauss', latitude=10, longitude=10,
                                        sheet={'attacks': [{'name': 'Soco', 'damage': '1d4'}], 'description': 'NPC'})
        patcher = patch.object(main, 'settings', replace(main.settings, database_path=self.db))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def sheet(self):
        with closing(sqlite3.connect(self.db)) as db:
            return json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (self.pin['id'],)).fetchone()[0])

    def patch(self, body, mode='gm'):
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode=mode)
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)
        return self.client.patch('/gm/workspace/tokens/' + self.pin['id'] + '/disposition', json=body)

    def test_merge_keeps_the_rest_of_the_sheet(self):
        response = self.patch({'disposition': 'neutral'})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual({'attacks': [{'name': 'Soco', 'damage': '1d4'}], 'description': 'NPC', 'disposition': 'neutral'}, self.sheet())
        self.assertEqual(200, self.patch({'disposition': None}).status_code)
        self.assertNotIn('disposition', self.sheet())

    def test_invalid_value_and_extra_fields_are_rejected(self):
        self.assertEqual(422, self.patch({'disposition': 'friend'}).status_code)
        self.assertEqual(422, self.patch({'disposition': 'ally', 'current_hp': 0}).status_code)
        self.assertNotIn('disposition', self.sheet())

    def test_unknown_pin_is_404(self):
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode='gm')
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)
        self.assertEqual(404, self.client.patch('/gm/workspace/tokens/absent/disposition', json={'disposition': 'ally'}).status_code)


if __name__ == '__main__':
    unittest.main()
