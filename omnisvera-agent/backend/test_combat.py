from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from app.access import AccessContext
from app.character_play import build_character_definition, init_character_play
from app.combat import CombatExpiredError, CombatNotFoundError, confirm_attack_resolution, init_combat, resolve_attack
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger, list_session_ledger
from app.session_workspace import init_session_workspace, list_workspace_tokens, save_workspace_token


class SequenceRng:
    def __init__(self, *values: int):
        self.values = iter(values)

    def __call__(self, minimum: int, maximum: int) -> int:
        value = next(self.values)
        if not minimum <= value <= maximum:
            raise AssertionError(f"{value} is outside {minimum}..{maximum}")
        return value


class CombatAttackResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.database = Path(self.temporary.name) / "combat.sqlite3"
        init_character_play(self.database)
        init_dice_rolls(self.database)
        init_session_workspace(self.database)
        init_session_ledger(self.database)
        init_combat(self.database)
        self._insert_character("vezemir", 20, 20)
        self._insert_character("raziel", 14, 14)
        self.inventory = [
            {
                "item_path": "session-item:grisalma",
                "item_title": "Grisalma",
                "item_type": "Arma",
                "quantity": 1,
                "equipped": True,
                "equipment_slot": "Corpo a corpo",
                "damage_formula": "1d6",
                "effect_rules": [],
            },
            {
                "item_path": "session-item:ring",
                "item_title": "Anel de Precisão",
                "item_type": "Acessório",
                "quantity": 1,
                "equipped": True,
                "equipment_slot": "Acessório",
                "effect_rules": [
                    {"id": "attack", "trigger": "while_equipped", "kind": "attack_bonus", "target": "melee", "value": 1},
                    {"id": "damage", "trigger": "while_equipped", "kind": "damage_bonus", "target": "melee", "value": 2},
                ],
            },
        ]
        self.definition = build_character_definition(
            profile_id="vezemir",
            note={"title": "Vezemir", "frontmatter": {}, "content": ""},
            sheet={"steps": [{"key": "attacks", "fields": {"melee_bonus": 3}}]},
            inventory=self.inventory,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _insert_character(self, profile_id: str, current_hp: int, maximum_hp: int) -> None:
        state = {
            "current_hp": current_hp,
            "maximum_hp": maximum_hp,
            "temporary_hp": 0,
            "conditions": [],
            "resources": [],
        }
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                (profile_id, json.dumps(state), "2026-08-23T00:00:00+00:00"),
            )

    def _character_hp(self, profile_id: str) -> int:
        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id=?", (profile_id,)
            ).fetchone()
        return int(json.loads(row[0])["current_hp"])

    def _resolve(self, *, target: dict, request_id: str, roll_mode: str = "physical", d20: int | None = 15, rng=None):
        return resolve_attack(
            self.database,
            request_id=request_id,
            actor_character_id="vezemir",
            actor_name="Vezemir",
            requested_by_id="vezemir",
            requested_by_role="player",
            definition=self.definition,
            inventory=self.inventory,
            attack_id="melee",
            target=target,
            roll_mode=roll_mode,
            physical_d20=d20,
            rng=rng,
        )[0]

    def test_physical_hit_resolves_without_mutation_then_confirms_once_with_one_ledger_event(self) -> None:
        vampire = save_workspace_token(
            self.database,
            token_type="monster",
            name="Vampiro",
            latitude=50,
            longitude=50,
            current_hp=18,
            maximum_hp=18,
            sheet={"armor_class": 14},
        )
        resolution = self._resolve(
            target={"type": "token", "id": vampire["id"], "name": "Vampiro", "armor_class": 14, "current_hp": 18},
            request_id="physical-hit-1",
            rng=SequenceRng(6),
        )
        self.assertEqual(resolution["roll_mode"], "physical")
        self.assertEqual(resolution["d20"], 15)
        self.assertEqual(resolution["attack_bonus"], 4)
        self.assertEqual(resolution["attack_total"], 19)
        self.assertEqual(resolution["target_ac"], 14)
        self.assertEqual(resolution["result"], "hit")
        self.assertEqual(resolution["damage_formula"], "1d6+2")
        self.assertEqual(resolution["damage_total"], 8)
        self.assertEqual(resolution["breakdown"]["attack"], {"base_bonus": 3, "equipment_bonus": 1, "total_bonus": 4})
        self.assertEqual([item["item_title"] for item in resolution["breakdown"]["equipment"]], ["Grisalma", "Anel de Precisão"])
        self.assertEqual(list_workspace_tokens(self.database)[0]["current_hp"], 18)

        confirmed, applied = confirm_attack_resolution(
            self.database,
            resolution_id=resolution["resolution_id"],
            requested_by_id="vezemir",
            requested_by_role="player",
        )
        self.assertTrue(applied)
        self.assertEqual((confirmed["hp_before"], confirmed["hp_after"]), (18, 10))
        self.assertEqual(list_workspace_tokens(self.database)[0]["current_hp"], 10)

        repeated, applied_again = confirm_attack_resolution(
            self.database,
            resolution_id=resolution["resolution_id"],
            requested_by_id="vezemir",
            requested_by_role="player",
        )
        self.assertFalse(applied_again)
        self.assertEqual(repeated["hp_after"], 10)
        self.assertEqual(list_workspace_tokens(self.database)[0]["current_hp"], 10)
        ledger = list_session_ledger(self.database, AccessContext(mode="gm"))
        combat_entries = [item for item in ledger if item["source_type"] == "combat_action"]
        self.assertEqual(len(combat_entries), 1)
        detail = combat_entries[0]["detail"]
        self.assertEqual(detail["combat_action_id"], resolution["resolution_id"])
        self.assertEqual((detail["hp_before"], detail["hp_after"]), (18, 10))
        self.assertEqual(detail["damage_total"], 8)

    def test_miss_against_character_target_keeps_hp_and_is_logged(self) -> None:
        resolution = self._resolve(
            target={"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 18, "current_hp": 14},
            request_id="physical-miss-1",
            d20=3,
        )
        self.assertEqual(resolution["result"], "miss")
        self.assertEqual(resolution["damage_total"], 0)
        self.assertEqual(self._character_hp("raziel"), 14)
        confirmed, applied = confirm_attack_resolution(
            self.database,
            resolution_id=resolution["resolution_id"],
            requested_by_id="vezemir",
            requested_by_role="player",
        )
        self.assertTrue(applied)
        self.assertEqual((confirmed["hp_before"], confirmed["hp_after"]), (14, 14))
        self.assertEqual(self._character_hp("raziel"), 14)

    def test_digital_roll_reuses_dice_mechanism_for_attack_and_damage(self) -> None:
        resolution = self._resolve(
            target={"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 12, "current_hp": 14},
            request_id="digital-hit-1",
            roll_mode="digital",
            d20=None,
            rng=SequenceRng(10, 4),
        )
        self.assertEqual((resolution["d20"], resolution["attack_total"]), (10, 14))
        self.assertEqual(resolution["damage_total"], 6)

    def test_invalid_physical_d20_and_missing_attack_or_weapon_are_rejected(self) -> None:
        target = {"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 12, "current_hp": 14}
        for value in (0, 21, None):
            with self.subTest(d20=value), self.assertRaisesRegex(ValueError, "entre 1 e 20"):
                self._resolve(target=target, request_id=f"bad-d20-{value}", d20=value)
        with self.assertRaisesRegex(ValueError, "Ataque não encontrado"):
            resolve_attack(
                self.database, request_id="missing-attack-1", actor_character_id="vezemir", actor_name="Vezemir",
                requested_by_id="vezemir", requested_by_role="player", definition=self.definition,
                inventory=self.inventory, attack_id="missing", target=target, roll_mode="physical", physical_d20=10,
            )
        unarmed = build_character_definition(
            profile_id="vezemir", note={"title": "Vezemir", "frontmatter": {}, "content": ""},
            sheet={"steps": [{"key": "attacks", "fields": {"melee_bonus": 3}}]}, inventory=[],
        )
        with self.assertRaisesRegex(ValueError, "Equipe uma arma"):
            resolve_attack(
                self.database, request_id="missing-weapon-1", actor_character_id="vezemir", actor_name="Vezemir",
                requested_by_id="vezemir", requested_by_role="player", definition=unarmed,
                inventory=[], attack_id="melee", target=target, roll_mode="physical", physical_d20=10,
            )

    def test_permissions_and_expiration_are_enforced(self) -> None:
        target = {"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 12, "current_hp": 14}
        with self.assertRaises(PermissionError):
            resolve_attack(
                self.database, request_id="foreign-actor-1", actor_character_id="vezemir", actor_name="Vezemir",
                requested_by_id="morthak", requested_by_role="player", definition=self.definition,
                inventory=self.inventory, attack_id="melee", target=target, roll_mode="physical", physical_d20=15,
            )
        created = datetime(2026, 8, 23, tzinfo=timezone.utc)
        resolution = resolve_attack(
            self.database, request_id="permission-hit-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="vezemir", requested_by_role="player", definition=self.definition,
            inventory=self.inventory, attack_id="melee", target=target, roll_mode="physical", physical_d20=15,
            rng=SequenceRng(3), now=created,
        )[0]
        with self.assertRaises(PermissionError):
            confirm_attack_resolution(
                self.database, resolution_id=resolution["resolution_id"],
                requested_by_id="morthak", requested_by_role="player", now=created,
            )
        with self.assertRaises(CombatExpiredError):
            confirm_attack_resolution(
                self.database, resolution_id=resolution["resolution_id"],
                requested_by_id="vezemir", requested_by_role="player", now=created + timedelta(minutes=16),
            )
        self.assertEqual(self._character_hp("raziel"), 14)

    def test_gm_may_resolve_for_any_character(self) -> None:
        target = {"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 12, "current_hp": 14}
        resolution, created = resolve_attack(
            self.database, request_id="gm-attack-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="master", requested_by_role="gm", definition=self.definition,
            inventory=self.inventory, attack_id="melee", target=target, roll_mode="physical", physical_d20=15,
            rng=SequenceRng(2),
        )
        self.assertTrue(created)
        self.assertEqual(resolution["requested_by_role"], "gm")

    def test_invalid_target_dead_target_and_unknown_resolution_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Alvo inválido"):
            self._resolve(
                target={"type": "other", "id": "x", "name": "Inválido", "armor_class": 10, "current_hp": 1},
                request_id="invalid-target-1",
            )
        with self.assertRaisesRegex(ValueError, "sem HP"):
            self._resolve(
                target={"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 10, "current_hp": 0},
                request_id="dead-target-1",
            )
        with self.assertRaises(CombatNotFoundError):
            confirm_attack_resolution(
                self.database,
                resolution_id="attack:unknown",
                requested_by_id="vezemir",
                requested_by_role="player",
            )


if __name__ == "__main__":
    unittest.main()
