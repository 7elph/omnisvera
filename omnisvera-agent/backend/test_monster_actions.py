from __future__ import annotations

import unittest

from app.monster_actions import build_action_map, classify_ability, link_spell, parse_attack_entry, parse_spellcasting
from app.monster_catalog import get_catalog_monster, load_monster_catalog


def _catalog_abilities(monster_id: str) -> list:
    monster = get_catalog_monster(monster_id)
    assert monster is not None
    return [(ability.get("name") or "", ability.get("description") or "") for ability in monster.get("abilities") or []]


class MonsterActionMapTests(unittest.TestCase):
    def test_vampire_attack_ready_with_rider_and_gaze_usable(self) -> None:
        monster = get_catalog_monster("vampiro")
        assert monster is not None
        action_map = build_action_map(monster["name"], monster["attacks"], _catalog_abilities("vampiro"))
        attack = action_map["attacks"][0]
        self.assertEqual(attack["status"], "ready")
        self.assertEqual(attack["dice"], "1d10")
        self.assertEqual(attack["riders"], ["Dreno"])
        gaze = next(ability for ability in action_map["active_abilities"] if ability["name"] == "Olhar Encantador")
        self.assertEqual(gaze["save"], "JPS")
        self.assertTrue(any(entry["name"] == "Regeneração" for entry in action_map["passive_abilities"]))
        self.assertEqual(action_map["summary"]["attacks_incomplete"], 0)

    def test_cultist_named_spells_link_to_grimoire(self) -> None:
        monster = get_catalog_monster("cultista")
        assert monster is not None
        action_map = build_action_map(monster["name"], monster["attacks"], _catalog_abilities("cultista"))
        self.assertEqual(len(action_map["spellcasting"]), 1)
        casting = action_map["spellcasting"][0]["spellcasting"]
        linked = {entry["mentioned_as"]: [link["id"] for link in entry["links"]] for entry in casting["named_spells"]}
        self.assertIn("divina-santuario", linked.get("Santuário", []))
        self.assertTrue(any("escuridao" in link for link in linked.get("Escuridão", [])))
        self.assertTrue(any("curar-ferimentos-leves-r" in link for link in linked.get("Causar Ferimentos", [])))

    def test_giant_weapon_bonus_parsed_and_flagged_for_master(self) -> None:
        monster = get_catalog_monster("gigante-da-colina")
        assert monster is not None
        action_map = build_action_map(monster["name"], monster["attacks"], _catalog_abilities("gigante-da-colina"))
        attack = action_map["attacks"][0]
        self.assertEqual(attack["status"], "incomplete")
        self.assertEqual(attack["damage_bonus"], 6)
        self.assertEqual(attack["bonus"], 11)
        self.assertTrue(action_map["blockers"])

    def test_storm_giant_lists_all_three_daily_spells(self) -> None:
        action_map = build_action_map("Gigante da Tempestade", [], _catalog_abilities("gigante-da-tempestade"))
        casting = action_map["spellcasting"][0]["spellcasting"]
        mentioned = {entry["mentioned_as"] for entry in casting["named_spells"]}
        self.assertTrue({"Levitação", "Relâmpago", "Convocar Relâmpagos"} <= mentioned)
        self.assertIn("3 vezes", action_map["spellcasting"][0].get("frequency", ""))

    def test_dragon_casts_by_level_without_invented_circle_cap(self) -> None:
        casting = parse_spellcasting("um Dragão Azul pode conjurar magias como se fosse um Mago de 7º nível.")
        self.assertEqual(casting["caster_level"], 7)
        self.assertEqual(casting["tradition"], "arcana")
        self.assertEqual(casting["named_spells"], [])

    def test_iron_golem_breath_is_usable_with_reference_damage(self) -> None:
        action_map = build_action_map("Golem de Ferro", [], _catalog_abilities("golem-de-ferro"))
        breath = next(ability for ability in action_map["active_abilities"] if ability["name"] == "Baforada de gás")
        self.assertEqual(breath["save"], "JPD")
        self.assertEqual(breath["reference_dice"], "3d6")
        self.assertEqual(breath["range_m"], 6)

    def test_custom_npc_freeform_sheet_maps_the_same_way(self) -> None:
        action_map = build_action_map(
            "Capitão Rourke",
            [{"name": "Sabre", "damage": "1d8+2", "bonus": "+5", "notes": "ataque preciso"}],
            ["Sopro de pólvora: 1 vez por combate, cone de 5 metros, 2d6 de dano, JPD reduz",
             "Casca-grossa: imune a veneno e medo"],
        )
        self.assertEqual(action_map["attacks"][0]["status"], "ready")
        breath = action_map["active_abilities"][0]
        self.assertEqual((breath["save"], breath["range_m"], breath["reference_dice"]), ("JPD", 5, "2d6"))
        self.assertEqual(action_map["passive_abilities"][0]["name"], "Casca-grossa")
        self.assertEqual(action_map["summary"]["blockers"], 0)

    def test_catalog_wide_counts_never_silently_drop_entries(self) -> None:
        catalog = load_monster_catalog()
        total_attacks = total_incomplete = total_active = total_casting = 0
        monsters_without_attacks = 0
        for monster in catalog["monsters"]:
            action_map = build_action_map(
                monster["name"], monster.get("attacks") or [],
                [(ability.get("name") or "", ability.get("description") or "") for ability in monster.get("abilities") or []])
            total_attacks += action_map["summary"]["attacks"]
            total_incomplete += action_map["summary"]["attacks_incomplete"]
            total_active += action_map["summary"]["active_abilities"]
            total_casting += action_map["summary"]["spellcasting"]
            if action_map["summary"]["attacks"] == 0:
                monsters_without_attacks += 1
            mapped = (len(action_map["attacks"]) + len(action_map["active_abilities"])
                      + len(action_map["passive_abilities"]) + len(action_map["spellcasting"]))
            source = len(monster.get("attacks") or []) + len(monster.get("abilities") or [])
            self.assertEqual(mapped, source, monster["id"])
        self.assertEqual(total_attacks, 365)
        # 14 missing bonuses recovered from explicit public d20 formulas;
        # seven numeric attacks became ready; two condition-only attacks now have native JP/clock handlers.
        self.assertEqual(total_incomplete, 34)
        self.assertEqual(monsters_without_attacks, 8)
        self.assertGreater(total_active, 100)
        self.assertGreater(total_casting, 20)

    def test_link_spell_returns_empty_without_inventing(self) -> None:
        self.assertEqual(link_spell("Magia Inexistente Xyz"), [])
        self.assertEqual(classify_ability("Imunidades", "imune a veneno, sono e medo")["kind"], "passive")

    def test_lich_maps_touch_paralysis_aura_and_level_casting(self) -> None:
        monster = get_catalog_monster("lich")
        assert monster is not None
        action_map = build_action_map(monster["name"], monster["attacks"], _catalog_abilities("lich"))
        self.assertEqual(len(action_map["attacks"]), 1)
        self.assertEqual(action_map["attacks"][0]["riders"], ["Paralisia"])
        paralysis = next(ability for ability in action_map["active_abilities"] if ability["name"] == "Paralisia")
        self.assertEqual(paralysis["save"], "JPC")
        aura = next(ability for ability in action_map["active_abilities"] if ability["name"] == "Aura Aterrorizante")
        self.assertIsNone(aura.get("save"))
        casting = next(ability for ability in action_map["spellcasting"] if ability["name"] == "Magias")
        self.assertEqual(casting["spellcasting"]["caster_level"], 15)
        self.assertEqual(casting["spellcasting"]["tradition"], "arcana")

    def test_treant_animates_plants_as_usable(self) -> None:
        monster = get_catalog_monster("treant")
        assert monster is not None
        action_map = build_action_map(monster["name"], monster["attacks"], _catalog_abilities("treant"))
        self.assertEqual(action_map["attacks"][0]["count"], 2)
        animate = next(ability for ability in action_map["active_abilities"] if ability["name"] == "Animar Plantas")
        self.assertEqual(animate["range_m"], 20)


if __name__ == "__main__":
    unittest.main()
