"""Main integration: manifests never reconcile live character state on reads."""
from contextlib import ExitStack, closing
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.access import AccessContext


class ActionManifestMainTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / 'fixture.sqlite3'
        self.saved = {'current_hp': 7, 'maximum_hp': 12, 'resources': [
            {'key': 'frenesi', 'current': 0, 'maximum': 1}], 'conditions': ['envenenado']}
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('CREATE TABLE character_states(profile_id TEXT PRIMARY KEY,state_json TEXT,version INTEGER,updated_at TEXT)')
            db.execute('INSERT INTO character_states VALUES(?,?,?,?)', ('vezemir', json.dumps(self.saved), 9, 'before'))
        self.definition = {'id': 'vezemir', 'identity_cards': {}, 'attacks': [],
                           'progression': {'maximum_hp': 100},
                           'session_abilities': [{'id': 'frenesi', 'name': 'Frenesi',
                                                  'uses': {'resource_key': 'frenesi'}}]}
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(main, 'settings', replace(main.settings, database_path=self.database)))
        self.sheet = stack.enter_context(patch.object(main, '_sheet_for_character', return_value={'character_path': 'Characters/Vezemir.md'}))
        self.sheets = stack.enter_context(patch.object(main, 'list_sheets', return_value=[
            {'profile_id': 'vezemir', 'character_path': 'Characters/Vezemir.md'}]))
        stack.enter_context(patch.object(main, 'resolve_note', return_value={'id': 1}))
        stack.enter_context(patch.object(main, 'get_note', return_value={'id': 1, 'content': ''}))
        stack.enter_context(patch.object(main, 'list_inventory', return_value=[]))
        stack.enter_context(patch.object(main, '_inventory_with_media', return_value=[]))
        stack.enter_context(patch.object(main, 'load_definition_overrides', return_value={}))
        stack.enter_context(patch.object(main, 'build_character_definition', return_value=self.definition))
        stack.enter_context(patch.object(main, 'readeffects', return_value={'effects': [], 'version': 4}))
        self.create_state = stack.enter_context(patch.object(main, 'get_or_create_state', return_value={'current_hp': 99}))

    def test_readonly_state_preserves_hp_conditions_resources_version_and_database(self):
        before = self.database.read_bytes()
        result = main._playable_character('vezemir', AccessContext(mode='gm'), read_only=True)
        self.assertEqual({**self.saved, 'version': 9, 'updated_at': 'before'}, result['state'])
        self.create_state.assert_not_called()
        self.sheet.assert_not_called()
        self.assertEqual(before, self.database.read_bytes())

    def test_missing_state_does_not_seed_or_grant_resources(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('DELETE FROM character_states')
        before = self.database.read_bytes()
        result = main._playable_character('vezemir', AccessContext(mode='gm'), read_only=True)
        self.assertIsNone(result['state'])
        self.create_state.assert_not_called()
        self.assertEqual(before, self.database.read_bytes())

    def test_existing_callers_keep_default_state_behavior(self):
        result = main._playable_character('vezemir', AccessContext(mode='gm'))
        self.assertEqual({'current_hp': 99}, result['state'])
        self.create_state.assert_called_once()

    def test_sheet_endpoint_readonly_option_never_reconciles_character_state(self):
        before=self.database.read_bytes()
        result=main.playable_character('vezemir',AccessContext(mode='gm'),read_only=True)
        self.assertEqual(7,result['state']['current_hp'])
        self.create_state.assert_not_called()
        self.assertEqual(before,self.database.read_bytes())

    def test_routers_precede_frontend_catchall_and_manifest_is_readonly(self):
        def route_paths(routes):
            for route in routes:
                included = getattr(route, 'original_router', None)
                if included is not None:
                    yield from route_paths(included.routes)
                else:
                    yield getattr(route, 'path', '')
        paths = list(route_paths(main.app.routes))
        self.assertLess(paths.index('/gm/actions/manifest/{character_id}'), paths.index('/{full_path:path}'))
        self.assertLess(paths.index('/gm/scenes/{scene_id}/lab/proposals'), paths.index('/{full_path:path}'))
        before = self.database.read_bytes()
        previous = main.app.dependency_overrides.get(main.require_master)
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode='gm')
        try:
            client = TestClient(main.app)
            self.addCleanup(client.close)
            response = client.get('/gm/actions/manifest/vezemir')
        finally:
            if previous is None: main.app.dependency_overrides.pop(main.require_master, None)
            else: main.app.dependency_overrides[main.require_master] = previous
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual('unavailable', response.json()['actions'][0]['availability']['state'])
        self.assertEqual(before, self.database.read_bytes())
        self.create_state.assert_not_called()

    def test_missing_character_returns_404_without_state_creation(self):
        self.sheet.side_effect = HTTPException(status_code=404, detail='Personagem inexistente')
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode='gm')
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)
        client = TestClient(main.app)
        self.addCleanup(client.close)
        response = client.get('/gm/actions/manifest/absent')
        self.assertEqual(404, response.status_code)
        self.create_state.assert_not_called()
        self.sheet.assert_not_called()

    def test_missing_state_manifest_reports_unknown_and_does_not_create_state(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('DELETE FROM character_states')
        before = self.database.read_bytes()
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode='gm')
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)
        client = TestClient(main.app)
        self.addCleanup(client.close)
        response = client.get('/gm/actions/manifest/vezemir')
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual('unknown', response.json()['actions'][0]['availability']['state'])
        self.assertEqual(before, self.database.read_bytes())
        self.create_state.assert_not_called()

    def test_unknown_token_returns_404_without_writing_database(self):
        before = self.database.read_bytes()
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode='gm')
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)
        client = TestClient(main.app)
        self.addCleanup(client.close)
        with patch.object(main, 'list_workspace_tokens', return_value=[]):
            response = client.get('/gm/workspace/tokens/absent/action-manifest')
        self.assertEqual(404, response.status_code)
        self.assertEqual(before, self.database.read_bytes())
