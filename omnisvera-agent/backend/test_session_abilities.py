from __future__ import annotations

import unittest
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.character_play import (
    apply_character_action,
    build_character_definition,
    init_character_play,
    load_session_abilities,
    seed_session_ability_resources,
)
from app.player_inventory import init_player_inventory, upsert_inventory
from app.dice_rolls import resolve_character_roll


def by_name(profile_id: str) -> dict[str, dict]:
    return {entry["name"]: entry for entry in load_session_abilities(profile_id)}


class SessionAbilityCatalogTests(unittest.TestCase):
    def test_cloak_and_leather_armor_add_two_non_stacking_points_to_sheet_ac(self) -> None:
        sheet = {"steps": [{"key": "armor", "fields": {"armor_class": 14}}]}
        note = {"title": "Raziel", "frontmatter": {}, "content": ""}
        inventory = [
            {"item_path": "Items/manto.md", "item_title": "Manto Primordial", "item_type": "Manto", "quantity": 1, "equipped": True},
            {"item_path": "Items/couro.md", "item_title": "Armadura de couro", "item_type": "Armadura leve", "quantity": 1, "equipped": True},
        ]
        defenses = build_character_definition(profile_id="raziel", note=note, sheet=sheet, inventory=inventory)["defenses"]
        self.assertEqual(defenses["base_armor_class"], 14)
        self.assertEqual(defenses["armor_class"], 16)
        self.assertEqual(defenses["armor_modifier"], 2)
        self.assertEqual(defenses["armor_modifier_source"]["value"], 2)

    def test_plate_armor_does_not_duplicate_ac_already_recorded_on_sheet(self) -> None:
        sheet = {"steps": [{"key": "armor", "fields": {"armor_class": 22}}]}
        note = {"title": "Vezemir", "frontmatter": {}, "content": ""}
        inventory = [{"item_path": "Items/placas.md", "item_title": "Armadura de placas", "item_type": "Armadura pesada", "quantity": 1, "equipped": True}]
        defenses = build_character_definition(profile_id="vezemir", note=note, sheet=sheet, inventory=inventory)["defenses"]
        self.assertEqual(defenses["base_armor_class"], 22)
        self.assertEqual(defenses["armor_class"], 22)
        self.assertEqual(defenses["armor_modifier"], 6)
        self.assertEqual(defenses["armor_modifier_source"]["item_title"], "Armadura de placas")
        self.assertTrue(defenses["armor_modifier_source"]["included_in_sheet"])

    def test_equipped_item_rules_modify_attributes_ac_and_abilities(self) -> None:
        sheet = {
            "steps": [
                {"key": "attributes", "fields": {"strength": 10, "dexterity": 12}},
                {"key": "armor", "fields": {"armor_class": 13}},
                {"key": "attacks", "fields": {"melee_bonus": 0}},
                {"key": "character_class", "fields": {"hit_points": 10}},
            ]
        }
        note = {"title": "Varkh", "frontmatter": {}, "content": ""}
        inventory = [{
            "item_path": "session-item:99", "item_title": "Manto Rúnico", "item_type": "Manto",
            "quantity": 1, "equipped": True,
            "effect_rules": [
                {"id": "strength", "trigger": "while_equipped", "kind": "attribute_bonus", "target": "strength", "value": 2},
                {"id": "armor", "trigger": "while_equipped", "kind": "armor_class_bonus", "target": "", "value": 2},
                {"id": "sight", "trigger": "while_equipped", "kind": "grant_ability", "target": "Visão Arcana", "value": 0, "label": "Enxerga runas ocultas."},
                {"id": "attack", "trigger": "while_equipped", "kind": "attack_bonus", "target": "melee", "value": 1},
                {"id": "hp", "trigger": "while_equipped", "kind": "maximum_hp_bonus", "target": "", "value": 3},
                {"id": "skill", "trigger": "while_equipped", "kind": "skill_bonus", "target": "Percepção", "value": 2},
                {"id": "fire", "trigger": "while_equipped", "kind": "resistance", "target": "fogo", "value": 0},
            ],
        }]
        definition = build_character_definition(profile_id="varkh", note=note, sheet=sheet, inventory=inventory)
        self.assertEqual(definition["base_attributes"]["strength"], 10)
        self.assertEqual(definition["attributes"]["strength"], 12)
        self.assertEqual(definition["defenses"]["base_armor_class"], 13)
        self.assertEqual(definition["defenses"]["armor_class"], 15)
        self.assertEqual(definition["defenses"]["armor_modifier"], 2)
        self.assertIn("Visão Arcana", {ability["name"] for ability in definition["session_abilities"]})
        self.assertEqual(definition["attacks"][0]["attack_bonus"], 1)
        self.assertEqual(definition["progression"]["maximum_hp_modifier"], 3)
        self.assertEqual(definition["item_effects"]["skill_modifiers"]["Percepção"], 2)
        self.assertEqual(definition["item_effects"]["resistances"], ["fogo"])

    def test_combat_definition_binds_weapon_damage_and_support_items_to_attack(self) -> None:
        sheet = {"steps": [{"key": "attacks", "fields": {"melee_bonus": 2, "ranged_bonus": 1}}]}
        note = {"title": "Morthak", "frontmatter": {}, "content": ""}
        inventory = [
            {
                "item_path": "session-item:staff", "item_title": "Cajado de Morthak", "item_type": "Arma",
                "quantity": 1, "equipped": True, "equipment_slot": "Corpo a corpo", "damage_formula": "1d6",
                "thumbnail": "zz_media/staff.png", "effect_rules": [],
            },
            {
                "item_path": "session-item:ring", "item_title": "Anel de Precisão", "item_type": "Acessório",
                "quantity": 1, "equipped": True, "equipment_slot": "Acessório", "cover": "zz_media/ring.png",
                "effect_rules": [
                    {"id": "attack", "trigger": "while_equipped", "kind": "attack_bonus", "target": "melee", "value": 1},
                    {"id": "damage", "trigger": "while_equipped", "kind": "damage_bonus", "target": "melee", "value": 2},
                ],
            },
        ]
        definition = build_character_definition(profile_id="morthak", note=note, sheet=sheet, inventory=inventory)
        melee = next(attack for attack in definition["attacks"] if attack["id"] == "melee")
        ranged = next(attack for attack in definition["attacks"] if attack["id"] == "ranged")
        self.assertEqual(melee["attack_bonus"], 3)
        self.assertEqual(melee["damage"], "1d6+2")
        self.assertEqual(melee["weapon_item_path"], "session-item:staff")
        self.assertEqual([(item["item_path"], item["role"]) for item in melee["equipment"]], [
            ("session-item:staff", "weapon"), ("session-item:ring", "support"),
        ])
        self.assertIsNone(ranged["weapon_item_path"])
        self.assertEqual(ranged["equipment"], [])
        self.assertEqual(resolve_character_roll(definition, inventory, "attack", "melee").formula, "1d20+3")
        self.assertEqual(resolve_character_roll(definition, inventory, "damage", "session-item:staff").formula, "1d6+2")

    def test_non_stacking_item_rules_use_the_largest_modifier(self) -> None:
        sheet = {"steps": [{"key": "attributes", "fields": {"strength": 10}}]}
        note = {"title": "Teste", "frontmatter": {}, "content": ""}
        inventory = [
            {"item_path": "one", "item_title": "Um", "quantity": 1, "equipped": True, "effect_rules": [{"id": "a", "trigger": "while_equipped", "kind": "attribute_bonus", "target": "strength", "value": 2, "stacking": "non_stack"}]},
            {"item_path": "two", "item_title": "Dois", "quantity": 1, "equipped": True, "effect_rules": [{"id": "b", "trigger": "while_equipped", "kind": "attribute_bonus", "target": "strength", "value": 4, "stacking": "non_stack"}]},
        ]
        definition = build_character_definition(profile_id="test", note=note, sheet=sheet, inventory=inventory)
        self.assertEqual(definition["attributes"]["strength"], 14)

    def test_item_charges_can_be_spent_and_restore_on_inn_rest(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "companion.sqlite3"
            init_character_play(database_path)
            init_player_inventory(database_path)
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)", ("test", json.dumps({"current_hp": 5, "maximum_hp": 5, "temporary_hp": 0, "conditions": [], "resources": []}), "2026-08-21T00:00:00+00:00"))
            upsert_inventory(database_path, profile_id="test", item_path="relic", item_title="Relíquia", quantity=1, equipped=True, notes=None, charges_current=3, charges_max=3, recharge="inn_rest")
            apply_character_action(database_path, character_id="test", actor_id="test", actor_role="player", action="change_charges", payload={"item_path": "relic", "charges": 2})
            self.assertEqual(upsert_inventory(database_path, profile_id="test", item_path="relic", item_title="Relíquia", quantity=1, equipped=True, notes=None)["charges_current"], 2)
            apply_character_action(database_path, character_id="test", actor_id="master", actor_role="gm", action="rest_at_inn", payload={})
            self.assertEqual(upsert_inventory(database_path, profile_id="test", item_path="relic", item_title="Relíquia", quantity=1, equipped=True, notes=None)["charges_current"], 3)

    def test_each_character_receives_only_their_catalog(self) -> None:
        expected = {
            "raziel": {
                "Reserva de Sangue", "Regeneração Vampírica", "Lâmina de Sangue", "Marca Rubra",
                "Fome de Sangue", "Mordida", "Caixão", "Medo", "Forma da Noite",
                "Sentido do Sangue", "Fotossensibilidade", "Cura Vampírica Invertida",
            },
            "varkh": {"Manipulação de Elementos", "Transmutação"},
            "vezemir": {"Força Arcana", "Velocidade"},
            "morthak": {
                "Mísseis Mágicos", "Adaga de Osso", "Levantar um Esqueleto", "Animar Mortos",
                "Não-Vida Consciente", "Memória Fraturada", "Chamado Necromântico", "Ossos sem Carne",
                "Corpo Quebradiço", "Cura Antinatural", "Repouso Imóvel", "Afastar Mortos-Vivos",
            },
        }
        catalogs = {profile_id: set(by_name(profile_id)) for profile_id in expected}
        shared_names = {"Não-Vida Consciente"}
        for profile_id, required in expected.items():
            self.assertTrue(required <= catalogs[profile_id])
            foreign_required = set().union(*(names for other, names in expected.items() if other != profile_id))
            self.assertFalse((catalogs[profile_id] & foreign_required) - shared_names)

    def test_morthak_spells_preserve_campaign_circles_and_source_boundaries(self) -> None:
        spells = by_name("morthak")
        self.assertEqual(spells["Mísseis Mágicos"]["circle"], 1)
        self.assertEqual(spells["Adaga de Osso"]["kind"], "attack")
        self.assertNotIn("circle", spells["Adaga de Osso"])
        self.assertEqual(spells["Levantar um Esqueleto"]["circle"], 2)
        self.assertEqual(spells["Animar Mortos"]["circle"], 3)
        self.assertEqual(spells["Mísseis Mágicos"]["mechanics_status"], "structured")
        self.assertIn("1d4 + 1", spells["Mísseis Mágicos"]["description"])
        self.assertIn("10 metros + 3 metros por nível", spells["Mísseis Mágicos"]["description"])
        self.assertEqual(spells["Adaga de Osso"]["mechanics_status"], "partial")
        self.assertIn("Ataque básico", spells["Adaga de Osso"]["description"])
        self.assertEqual(spells["Levantar um Esqueleto"]["mechanics_status"], "partial")
        self.assertIn("Nenhuma regra com esse nome foi localizada", spells["Levantar um Esqueleto"]["description"])
        self.assertEqual(spells["Animar Mortos"]["mechanics_status"], "partial")
        self.assertIn("5º círculo", spells["Animar Mortos"]["description"])
        self.assertIn("3º círculo", spells["Animar Mortos"]["description"])

    def test_prompt_only_varkh_powers_remain_mechanically_partial(self) -> None:
        powers = by_name("varkh")
        for name in ("Manipulação de Elementos", "Transmutação"):
            self.assertEqual(powers[name]["mechanics_status"], "partial")
            self.assertTrue(powers[name]["description"])

    def test_canonical_numbers_only_appear_where_the_source_has_them(self) -> None:
        raziel = by_name("raziel")
        morthak = by_name("morthak")
        vezemir = by_name("vezemir")
        self.assertIn("1d4", raziel["Mordida"]["description"])
        self.assertIn("1d4", raziel["Lâmina de Sangue"]["description"])
        self.assertIn("1d6", raziel["Fotossensibilidade"]["description"])
        self.assertIn("+2", morthak["Ossos sem Carne"]["description"])
        self.assertIn("metade dos PV", morthak["Cura Antinatural"]["description"])
        self.assertIn("1d6 + nível", vezemir["Força Arcana"]["description"])
        self.assertIn("1d4 + nível", vezemir["Velocidade"]["description"])

    def test_campaign_use_counters_are_structured_as_resources(self) -> None:
        expected = {
            "raziel": {"reserva_de_sangue": 5, "forma_da_noite": 3},
            "morthak": {"misseis_magicos": 3},
            "vezemir": {"forca_arcana": 1, "velocidade": 1},
        }
        for profile_id, counters in expected.items():
            resources = {entry["key"]: entry for entry in seed_session_ability_resources(profile_id)}
            self.assertEqual({key: resources[key]["maximum"] for key in counters}, counters)
            self.assertTrue(all(resources[key]["recharge"] == "inn_rest" for key in counters))

    def test_inn_rest_restores_hp_conditions_and_all_resources(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "companion.sqlite3"
            init_character_play(database_path)
            initial = {
                "current_hp": 2,
                "maximum_hp": 12,
                "temporary_hp": 4,
                "conditions": ["Envenenado", "Caído"],
                "resources": [
                    {"key": "magias_de_1o_circulo", "label": "Magias de 1º círculo", "current": 0, "maximum": 1},
                    {"key": "misseis_magicos", "label": "Mísseis Mágicos · usos", "current": 0, "maximum": 3},
                    {"key": "mana", "label": "Mana", "current": 1, "maximum": 6},
                ],
                "coins": 10,
                "location": "Nimalis",
                "session_notes": "",
            }
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute(
                    "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                    ("morthak", json.dumps(initial, ensure_ascii=False), "2026-08-15T00:00:00+00:00"),
                )
            apply_character_action(
                database_path,
                character_id="morthak",
                actor_id="master",
                actor_role="gm",
                action="rest_at_inn",
                payload={},
            )
            with closing(sqlite3.connect(database_path)) as connection:
                state = json.loads(connection.execute(
                    "SELECT state_json FROM character_states WHERE profile_id='morthak'"
                ).fetchone()[0])
            self.assertEqual(state["current_hp"], 12)
            self.assertEqual(state["temporary_hp"], 0)
            self.assertEqual(state["conditions"], [])
            self.assertEqual([resource["current"] for resource in state["resources"]], [1, 3, 6])


if __name__ == "__main__":
    unittest.main()
