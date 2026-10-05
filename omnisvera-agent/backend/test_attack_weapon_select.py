from __future__ import annotations

import unittest

import test_combat as fixture
from app.character_play import available_attack_weapons
from app.combat import resolve_attack
from app.session_workspace import save_workspace_token


def _weapon(path, title, slot="", damage="1d6", equipped=True):
    return {
        "item_path": path, "item_title": title, "item_type": "Arma",
        "quantity": 1, "equipped": equipped, "equipment_slot": slot,
        "damage_formula": damage, "effect_rules": [],
    }


class AttackWeaponSelectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixture.CombatAttackResolutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.db = self.fixture.database
        self.token = save_workspace_token(self.db, token_type="monster", name="Lobo",
            latitude=50, longitude=50, current_hp=18, maximum_hp=18, sheet={"armor_class": 10})
        self.target = {"type": "token", "id": self.token["id"], "name": "Lobo",
                       "armor_class": 10, "current_hp": 18}

    def resolve(self, inventory, attack_id="melee", **kwargs):
        definition = dict(self.fixture.definition)
        args = dict(request_id="weapon-test-001", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="vezemir", requested_by_role="player", definition=definition,
            inventory=inventory, attack_id=attack_id, target=dict(self.target),
            roll_mode="physical", physical_d20=15, rng=fixture.SequenceRng(4))
        args.update(kwargs)
        return resolve_attack(self.db, **args)[0]

    def test_candidates_prefer_slotted_then_legacy(self):
        inv = [_weapon("Items/Espada curta.md", "Espada curta", "", "1d6"),
               _weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6")]
        paths = [i["item_path"] for i in available_attack_weapons(inv, "melee")]
        self.assertEqual(["Items/Grisalma.md", "Items/Espada curta.md"], paths)

    def test_shields_excluded_and_ranged_separated(self):
        shield = _weapon("Items/Muralha de Dorn.md", "Muralha de Dorn", "Corpo a corpo", "1d6")
        shield["item_type"] = "Escudo"
        inv = [shield, _weapon("Items/Arco curto.md", "Arco curto", "", "1d6")]
        self.assertEqual([], available_attack_weapons(inv, "melee"))
        self.assertEqual(["Items/Arco curto.md"],
                         [i["item_path"] for i in available_attack_weapons(inv, "ranged")])

    def test_usable_items_never_become_weapons(self):
        potion = _weapon("session-item:11", "Poção de HP", "", "1d4")
        potion["usable"] = True
        inv = [potion, _weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6")]
        self.assertEqual(["Items/Grisalma.md"],
                         [i["item_path"] for i in available_attack_weapons(inv, "melee")])
        self.assertEqual([],
                         [i["item_path"] for i in available_attack_weapons([potion], "melee")])

    def test_throwing_relic_available_ranged(self):
        inv = [_weapon("Items/Adagas de Espectro Fantasma.md", "Adagas", "Corpo a corpo", "1d4")]
        self.assertEqual(["Items/Adagas de Espectro Fantasma.md"],
                         [i["item_path"] for i in available_attack_weapons(inv, "ranged")])

    def test_explicit_weapon_overrides_damage(self):
        inv = [_weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6"),
               _weapon("Items/Espada curta.md", "Espada curta", "", "1d6")]
        record = self.resolve(inv, weapon_item_path="Items/Espada curta.md")
        self.assertEqual("Items/Espada curta.md",
                         record["breakdown"]["attack"]["weapon_item_path"])
        self.assertIn("1d6", record["breakdown"]["damage"]["effective_formula"])

    def test_default_preserves_auto_pick(self):
        inv = [_weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6"),
               _weapon("Items/Espada curta.md", "Espada curta", "", "1d6")]
        record = self.resolve(inv)
        self.assertEqual(self.fixture.definition["attacks"][0]["weapon_item_path"],
                         record["breakdown"]["attack"]["weapon_item_path"])

    def test_invalid_weapon_rejected(self):
        inv = [_weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6")]
        with self.assertRaises(ValueError):
            self.resolve(inv, request_id="weapon-test-002",
                         weapon_item_path="Items/Espada curta.md")
        with self.assertRaises(ValueError):
            self.resolve(inv, request_id="weapon-test-003",
                         weapon_item_path="Items/Arco curto.md")

    def test_replay_with_different_weapon_rejected(self):
        inv = [_weapon("Items/Grisalma.md", "Grisalma", "Corpo a corpo", "2d6"),
               _weapon("Items/Espada curta.md", "Espada curta", "", "1d6")]
        first = self.resolve(inv, request_id="weapon-test-004",
                             weapon_item_path="Items/Espada curta.md")
        again = self.resolve(inv, request_id="weapon-test-004",
                             weapon_item_path="Items/Espada curta.md")
        self.assertEqual(first["resolution_id"], again["resolution_id"])
        with self.assertRaises(ValueError):
            self.resolve(inv, request_id="weapon-test-004",
                         weapon_item_path="Items/Grisalma.md")


if __name__ == "__main__":
    unittest.main()
