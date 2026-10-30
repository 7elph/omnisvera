"""Contracts for the lossless, source-backed bestiary compiler."""
import copy
import unittest

from app.monster_actions import classify_ability
from app.monster_catalog import load_monster_catalog


class MonsterRulesTests(unittest.TestCase):
    def test_ability_text_is_never_truncated_or_reformatted(self):
        text = ("Regra com espaços  e\nquebras. " * 100) + "EXCEÇÃO FINAL"
        self.assertEqual(classify_ability("Regeneração", text)["description"], text)

    def test_chance_duration_and_images_are_not_damage(self):
        for text in ("JPS nega; dorme por 2d6 rodadas.",
                     "1d6 imagens; JPD nega.", "1d6 de chance de causar dano."):
            with self.subTest(text=text):
                self.assertNotIn("reference_dice", classify_ability("Sopro", text))

    def test_explicit_damage_ignores_earlier_duration(self):
        ability = classify_ability("Sopro", "Dura 1d4 rodadas; causa 2d6+3 de dano. JPD reduz à metade.")
        self.assertEqual(ability.get("reference_dice"), "2d6+3")

    def test_all_catalog_text_survives_with_revision_and_provenance(self):
        from app.monster_rules import compile_monster_rules
        catalog = load_monster_catalog()
        for monster in catalog["monsters"]:
            original = copy.deepcopy(monster)
            result = compile_monster_rules(monster, catalog["catalog"])
            with self.subTest(monster=monster["id"]):
                self.assertEqual(result["source_record"], monster)
                self.assertEqual(monster, original)
                self.assertEqual(len(result["revision"]), 64)
                self.assertEqual(result["source"]["license"], "CC BY-SA 4.0")
                self.assertEqual(result, compile_monster_rules(monster, catalog["catalog"]))
                for i, ability in enumerate(monster.get("abilities", [])):
                    rule = next(r for r in result["rules"] if r["source_pointer"] == f"/abilities/{i}")
                    self.assertEqual(rule["text"], ability["description"])
                    self.assertEqual("".join(c["text"] for c in rule["clauses"]), rule["text"])
                    for clause in rule["clauses"]:
                        self.assertEqual(clause["text"], rule["text"][clause["start"]:clause["end"]])

    def test_passive_is_not_misrepresented_as_automatically_applied(self):
        from app.monster_rules import compile_monster_rules
        catalog = load_monster_catalog()
        troll = next(m for m in catalog["monsters"] if m["id"] == "troll")
        result = compile_monster_rules(troll, catalog["catalog"])
        rule = next(r for r in result["rules"] if r["name"] == "Regeneração")
        self.assertEqual(rule["execution"]["status"], "partial")
        self.assertTrue(rule["execution"]["gaps"])
        self.assertIn("regeneration", [c["kind"] for c in rule["clauses"]])

    def test_art_link_does_not_claim_uploaded_unique_art(self):
        from app.monster_rules import compile_monster_rules
        catalog = load_monster_catalog()
        goblin = next(m for m in catalog["monsters"] if m["id"] == "goblin")
        art = compile_monster_rules(goblin, catalog["catalog"])["art"]
        self.assertEqual(art["origin"], "external_catalog")
        self.assertFalse(art["user_upload_verified"])
        self.assertIsNone(art["unique_portrait_verified"])

    def test_unknown_future_fields_are_preserved(self):
        from app.monster_rules import compile_monster_rules
        monster = {"id": "future", "name": "Futuro", "lore": "Texto integral", "future": {"rule": "não perder"}, "abilities": []}
        self.assertEqual(compile_monster_rules(monster, {})["source_record"], monster)
