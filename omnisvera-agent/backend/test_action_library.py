from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.action_library import describe_action, execute_action


class ActionLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "library.db"
        from app.character_play import init_character_play
        from app.character_creation import init_character_creation
        from app.dice_rolls import init_dice_rolls
        from app.session_workspace import init_session_workspace
        from app.session_ledger import init_session_ledger
        from app.combat import init_combat
        from app.combat_effects import init_effects
        init_character_play(self.db)
        init_character_creation(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        init_combat(self.db)
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                (json.dumps({"current_hp": 30, "maximum_hp": 30}),))
            connection.execute(
                "INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at)"
                " VALUES('vezemir', 'p', 'Vezemir', ?, 'now')",
                (json.dumps({"attributes": {"dexterity": 14}, "character_class": {"saving_throw": 14}}),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir', '{}', 'now')")
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('gob1', 'monster', 'Goblin', 12, 12, ?, 'now', 'now')",
                (json.dumps({"saving_throw": 10, "spellcaster_level":1, "armor_class": 12,
                             "attacks": [{"name": "Adaga", "damage": "1d4", "bonus": 2}],
                             "abilities": ["Baforada de teste: 1 vez por combate, 6 metros, 2d6 de dano, JPD reduz"]}),))
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('gob2', 'monster', 'Goblin B', 9, 9, ?, 'now', 'now')",
                (json.dumps({"saving_throw": 8, "armor_class": 11, "attacks": [], "abilities": []}),))

    def test_describe_spell_blocks(self) -> None:
        action = describe_action(self.db, "spell:arcana-bola-de-fogo")
        self.assertEqual(action["kind"], "spell")
        kinds = [block["type"] for block in action["blocks"]]
        self.assertEqual(kinds, ["save", "damage", "manual"])
        self.assertEqual(action["blocks"][0]["jp"], "JPD")
        self.assertTrue(action["executable"])

    def test_describe_monster_attack_and_usable(self) -> None:
        attack = describe_action(self.db, "monster:vampiro:attack:0")
        self.assertEqual(attack["kind"], "attack")
        self.assertTrue(attack["executable"])
        self.assertEqual(attack["blocks"][0], {"type": "attack", "bonus": 10, "count": 1})
        usable = describe_action(self.db, "monster:golem-de-ferro:ability:Baforada de gás")
        self.assertEqual(usable["kind"], "usable")
        self.assertTrue(usable["executable"])
        passive = describe_action(self.db, "monster:vampiro:ability:Regeneração")
        self.assertEqual(passive["kind"], "passive")
        self.assertFalse(passive["executable"])

    def test_describe_technique_points_to_handler(self) -> None:
        action = describe_action(self.db, "technique:vezemir:forca-arcana")
        self.assertEqual(action["owner"], {"type": "character", "id": "vezemir"})
        self.assertFalse(action["executable"])
        self.assertIn("/characters/vezemir/techniques/", action["execute"]["endpoint"])
        self.assertTrue(any(block["type"] == "resource" for block in action["blocks"]))

    def test_execute_token_attack_hits_and_applies(self) -> None:
        outcome = execute_action(self.db, "token:gob1:attack:0",
                                 targets=[{"type": "token", "id": "gob2"}], roll_mode="digital")
        resolution = outcome["result"]
        self.assertIn(resolution["result"], ("hit", "miss"))
        with closing(sqlite3.connect(self.db)) as connection:
            hp = int(connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='gob2'").fetchone()[0])
        if resolution["result"] == "hit":
            self.assertLess(hp, 9)
        else:
            self.assertEqual(hp, 9)

    def test_execute_token_usable(self) -> None:
        outcome = execute_action(self.db, "token:gob1:ability:Baforada de teste",
                                 targets=[{"type": "character", "id": "vezemir"}],
                                 roll_mode="physical", d20=[1])
        self.assertFalse(outcome["result"]["results"][0]["save"]["success"])
        self.assertGreater(outcome["result"]["results"][0]["damage_dealt"], 0)

    def test_execute_spell_through_library(self) -> None:
        outcome = execute_action(self.db, "spell:arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                                 targets=[{"type": "character", "id": "vezemir"}], roll_mode="digital")
        self.assertEqual(outcome["action"]["kind"], "spell")
        self.assertEqual(len(outcome["result"]["results"]), 1)

    def test_unknown_refs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            describe_action(self.db, "nope")
        with self.assertRaises(ValueError):
            describe_action(self.db, "monster:vampiro:attack:99")
        with self.assertRaises(ValueError):
            execute_action(self.db, "monster:vampiro:attack:0", targets=[{"type": "character", "id": "vezemir"}])

    def test_colon_token_ids_parse(self) -> None:
        from app.action_library import parse_action_ref
        self.assertEqual(parse_action_ref("token:monster:abc123:attack:0"), ("token", "monster:abc123", "attack", "0"))
        self.assertEqual(parse_action_ref("token:monster:abc123:ability:Baforada"),
                         ("token", "monster:abc123", "ability", "Baforada"))
        self.assertEqual(parse_action_ref("monster:vampiro:ability:Olhar Encantador"),
                         ("monster", "vampiro", "ability", "Olhar Encantador"))
        self.assertEqual(parse_action_ref("spell:arcana-bola-de-fogo"), ("spell", "arcana-bola-de-fogo", "", ""))
        self.assertEqual(parse_action_ref("technique:vezemir:forca-arcana"), ("technique", "vezemir", "", "forca-arcana"))
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('monster:colon:id', 'monster', 'Lich', 40, 40, ?, 'now', 'now')",
                (json.dumps({"saving_throw": 10, "spellcaster_level": 1, "attacks": [{"name": "Toque", "damage": "1d10", "bonus": 8}],
                             "abilities": []}),))
        action = describe_action(self.db, "token:monster:colon:id:attack:0")
        self.assertEqual(action["owner"], {"type": "token", "id": "monster:colon:id"})
        self.assertTrue(action["executable"])


if __name__ == "__main__":
    unittest.main()
