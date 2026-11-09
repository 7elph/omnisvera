"""Companion 3.0: owner/GM read of the action manifest; never writes, never for others."""
from fastapi.testclient import TestClient

from app import main
from app.access import AccessContext
import test_action_manifest_main as base


class PlayerActionManifestTests(base.ActionManifestMainTests):
    def _get(self, access):
        main.app.dependency_overrides[main.require_any] = lambda: access
        self.addCleanup(main.app.dependency_overrides.pop, main.require_any, None)
        client = TestClient(main.app)
        self.addCleanup(client.close)
        return client.get('/characters/vezemir/action-manifest')

    def test_owner_reads_manifest_without_writing(self):
        before = self.database.read_bytes()
        response = self._get(AccessContext(mode='player', profile_id='vezemir'))
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertFalse(body['execution_approved'])
        self.assertEqual('technique:vezemir:frenesi', body['actions'][0]['ref'])
        self.assertEqual(before, self.database.read_bytes())
        self.create_state.assert_not_called()

    def test_other_player_is_refused(self):
        response = self._get(AccessContext(mode='player', profile_id='raziel'))
        self.assertEqual(403, response.status_code)

    def test_route_precedes_frontend_catchall(self):
        paths = [getattr(route, 'path', '') for route in main.app.routes]
        self.assertLess(paths.index('/characters/{profile_id}/action-manifest'), paths.index('/{full_path:path}'))




def load_tests(loader, tests, pattern):
    # Inherited scenarios already run in test_action_manifest_main; keep only these.
    import unittest
    names = [n for n in vars(PlayerActionManifestTests) if n.startswith('test_')]
    return unittest.TestSuite(PlayerActionManifestTests(n) for n in names)
