from dataclasses import replace
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import sqlite3

from fastapi.testclient import TestClient
from app import main


class CharacterNotesTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "notes.sqlite3"
        settings = replace(main.settings, database_path=self.db, master_token="test-gm", player_token="test-generic",
            player_profiles={name: {"token": f"test-{name}", "character_path": f"Characters/{name}.md"}
                             for name in ("varkh", "raziel")})
        self.settings_patch = patch.object(main, "settings", settings)
        self.settings_patch.start(); self.addCleanup(self.settings_patch.stop)
        self.ids_patch = patch.object(main, "_character_ids", return_value=["varkh", "raziel"])
        self.ids_patch.start(); self.addCleanup(self.ids_patch.stop)
        # No lifespan: all storage is temporary; do not initialize the live campaign.
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def read(self, actor="varkh", character="varkh"):
        return self.client.get(f"/characters/{character}/notes", headers={"X-Omnisvera-Token": f"test-{actor}"})

    def write(self, content="Pista de teste", version=0, actor="varkh", character="varkh", **extra):
        return self.client.put(f"/characters/{character}/notes", headers={"X-Omnisvera-Token": f"test-{actor}"},
                               json={"content": content, "version": version, **extra})

    def test_empty_notes_and_persisted_unicode(self):
        self.assertEqual(self.read().json()["version"], 0)
        text = "Pista do Odran\n• conferir o frasco amanhã 🧪"
        saved = self.write(text).json()
        self.assertEqual(saved["version"], 1)
        self.assertEqual(self.read().json(), saved)
        self.assertEqual(saved["content"], text)
        self.assertIsNotNone(saved["updated_at"])
        self.assertEqual(self.read().headers["cache-control"], "private, no-store")

    def test_other_player_and_generic_token_cannot_read_or_write(self):
        for actor in ("raziel", "generic"):
            self.assertEqual(self.read(actor).status_code, 403)
            self.assertEqual(self.write(actor=actor).status_code, 403)

    def test_missing_or_invalid_token(self):
        self.assertEqual(self.client.get("/characters/varkh/notes").status_code, 401)
        self.assertEqual(self.read("invalid").status_code, 401)

    def test_master_access_and_character_isolation(self):
        self.assertEqual(self.write(actor="gm").status_code, 200)
        self.assertEqual(self.read("gm").json()["content"], "Pista de teste")
        self.assertEqual(self.read("raziel", "raziel").json()["content"], "")

    def test_unknown_character(self):
        self.assertEqual(self.read("gm", "unknown").status_code, 404)
        self.assertEqual(self.write(actor="gm", character="unknown").status_code, 404)

    def test_lost_response_retry_does_not_duplicate_or_increment(self):
        saved = self.write().json()
        self.assertEqual(self.write().json(), saved)

    def test_stale_device_cannot_overwrite(self):
        self.write("one")
        self.assertEqual(self.write("stale", version=0).status_code, 409)
        self.assertEqual(self.read().json()["content"], "one")
        self.assertEqual(self.write("two", version=1).json()["version"], 2)

    def test_clear_is_persisted(self):
        self.write()
        self.assertEqual(self.write("", version=1).status_code, 200)
        self.assertEqual(self.read().json()["content"], "")

    def test_limit_and_forged_identity_rejected(self):
        for payload in ({"content": "a" * 12001}, {"version": -1}, {"content": 123}, {"actor": "gm"}):
            response = self.client.put("/characters/varkh/notes", headers={"X-Omnisvera-Token": "test-varkh"},
                                       json={"content": "test", "version": 0, **payload})
            self.assertEqual(response.status_code, 422)

    def test_no_public_ledger_or_character_state_copy(self):
        self.write("private fixture text")
        with closing(sqlite3.connect(self.db)) as connection:
            tables = {row[0] for row in connection.execute("select name from sqlite_master where type='table'")}
        self.assertEqual(tables, {"character_notes"})
