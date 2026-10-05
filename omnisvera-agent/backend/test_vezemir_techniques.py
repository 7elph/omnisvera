"""Vezemir techniques follow the table canon (session 5):
Forca Arcana raises For (+1 per 5 possessed) so attack AND damage move
with the attribute modifier; Velocidade grants +2 CA, one extra attack
and doubled movement. Both are once per day.
"""
from __future__ import annotations

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
from app.combat import init_combat
from app.combat_effects import init_effects
from app.character_play import init_character_play
from app.character_creation import init_character_creation
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace
from app.vault_index import init_db as init_vault_index


def _vezemir_state():
    return {"current_hp": 17, "maximum_hp": 17, "temporary_hp": 0,
            "conditions": [],
            "resources": [{"key": "forca_arcana", "label": "Força Arcana — uso diário",
                           "current": 1, "maximum": 1, "recharge": "inn_rest"},
                          {"key": "velocidade", "label": "Velocidade — uso diário",
                           "current": 1, "maximum": 1, "recharge": "inn_rest"}]}


class VezemirTechniquesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "vezemir.sqlite3"
        init_character_play(self.db)
        init_character_creation(self.db)
        init_combat(self.db)
        init_effects(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        init_vault_index(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Vezemir.md", "Vezemir", "[]", "character", "[]", "{}",
                 "# Vezemir", "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("vezemir", json.dumps(_vezemir_state()), "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("vezemir", "Characters/Individual/Vezemir.md", "Vezemir", "approved",
                 json.dumps({"attributes": {"strength": 13}, "character_class": {"level": 2},
                             "attacks": {"melee_bonus": 6}}),
                 "2026-09-30T00:00:00+00:00"),
            )
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        import gc as _gc
        import time as _time
        try:
            self.client.close()
        finally:
            main.app.dependency_overrides.clear()
            self._patcher.stop()
            _gc.collect()
            last_error: Exception | None = None
            for _ in range(25):
                try:
                    self.temporary.cleanup()
                    last_error = None
                    break
                except PermissionError as error:
                    last_error = error
                    _time.sleep(0.2)
            if last_error is not None:
                raise last_error

    def test_forca_arcana_raises_strength_and_recomputes_modifier(self):
        response = self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        self.assertEqual(200, response.status_code, response.text)
        effects = response.json()["effect"]["effects"]
        data = next(e for e in effects if e["target_id"] == "vezemir")
        modifiers = data.get("modifiers") or {}
        # For 13 -> +2 (1 per 5 possessed): the engine propagates the
        # attribute raise into attack and damage via the OD modifier.
        self.assertEqual(2, modifiers.get("strength_bonus"))
        self.assertIn("13→15", data.get("label", ""))
        from app.combat_effects import apply_definition_effects
        applied = apply_definition_effects(
            {"attributes": {"strength": 13}, "attribute_modifiers": {"strength": 1}},
            [{"modifiers": modifiers}],
        )
        self.assertEqual(15, applied["attributes"]["strength"])
        self.assertEqual(2, applied["attribute_modifiers"]["strength"])

    def test_velocidade_grants_ca_extra_attack_and_movement(self):
        response = self.client.post("/characters/vezemir/techniques/velocidade", json={})
        self.assertEqual(200, response.status_code, response.text)
        effects = response.json()["effect"]["effects"]
        data = next(e for e in effects if e["target_id"] == "vezemir")
        modifiers = data.get("modifiers") or {}
        self.assertEqual(2, modifiers.get("armor_class_bonus"))
        self.assertEqual(1, modifiers.get("extra_attacks"))
        self.assertEqual(2, modifiers.get("movement_multiplier"))
        # 1d4 + level 2.
        self.assertGreaterEqual(response.json()["duration_rounds"], 3)
        self.assertLessEqual(response.json()["duration_rounds"], 6)


if __name__ == "__main__":
    unittest.main()
