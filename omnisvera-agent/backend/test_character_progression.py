from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import sqlite3

from fastapi.testclient import TestClient
from app import main
from app.character_play import build_character_definition, load_definition_overrides, update_definition_overrides


class CharacterProgressionTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "progression.sqlite3"

    def save(self, fields):
        return update_definition_overrides(self.db, character_id="varkh", actor_id="master", fields=fields)

    def test_level_and_xp_persist_and_build_without_changing_vault_or_hp(self):
        self.save({"level": 3, "experience": 1250})
        definition = build_character_definition(profile_id="varkh",
            note={"title": "Varkh", "frontmatter": {}, "content": ""},
            sheet={"steps": []}, inventory=[], overrides=load_definition_overrides(self.db, "varkh"))
        self.assertEqual(3, definition["level"])
        self.assertEqual(1250, definition["progression"]["experience"])
        self.save({"experience": 0})
        self.assertEqual(0, load_definition_overrides(self.db, "varkh")["experience"])
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM character_states").fetchone()[0])

    def test_invalid_or_forged_fields_do_not_partially_update(self):
        self.save({"level": 2, "experience": 50})
        for fields in ({"level": 3, "experience": -1}, {"experience": 1.5}, {"experience": True},
                       {"experience": "100"}, {"level": 1.5}, {"level": True},
                       {"level": 0}, {"level": 21}, {"experience": 2147483648},
                       {"progression": {"experience": 2}}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.save(fields)
        self.assertEqual({"level": 2, "experience": 50}, load_definition_overrides(self.db, "varkh"))

    def test_player_cannot_use_gm_progression_endpoint(self):
        settings = replace(main.settings, database_path=self.db, master_token="test-master", player_token="test-player")
        with patch.object(main, "settings", settings), patch.object(main, "update_definition_overrides") as write:
            with closing(TestClient(main.app)) as client:
                for token in ("test-player", "invalid"):
                    response = client.patch("/gm/characters/varkh/definition",
                        headers={"X-Omnisvera-Token": token}, json={"fields": {"level": 3, "experience": 100}})
                    self.assertEqual(401, response.status_code)
            write.assert_not_called()
