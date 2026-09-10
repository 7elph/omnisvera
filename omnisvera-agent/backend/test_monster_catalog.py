from __future__ import annotations

import unittest
from pathlib import Path

from app.monster_catalog import get_catalog_monster, list_monster_catalog, load_monster_art_manifest, load_monster_catalog


class MonsterCatalogTests(unittest.TestCase):
    def test_official_srd_catalog_contains_all_255_monsters(self) -> None:
        catalog = load_monster_catalog()
        self.assertEqual(catalog["count"], 255)
        self.assertEqual(len(catalog["monsters"]), 255)
        self.assertEqual(catalog["catalog"]["license"], "CC BY-SA 4.0")

    def test_vampire_preserves_combat_mechanics_and_source(self) -> None:
        vampire = get_catalog_monster("vampiro")
        self.assertIsNotNone(vampire)
        assert vampire is not None
        self.assertEqual(vampire["average_hp"], 55)
        self.assertEqual(vampire["hit_points"], "55")
        self.assertEqual(vampire["armor_class"], 18)
        self.assertEqual(vampire["saving_throw"], 13)
        self.assertEqual(vampire["morale"], 12)
        self.assertEqual(vampire["attacks"][0]["bonus"], 10)
        self.assertEqual(vampire["attacks"][0]["damage"], "1d10 + Dreno")
        self.assertTrue(any(ability["name"] == "Regeneração" for ability in vampire["abilities"]))
        self.assertEqual(vampire["source_url"], "https://olddragon.com.br/monstros/vampiro")
        self.assertEqual(
            vampire["image_path"],
            "zz_media/ui/icons/monsters/illustrated-bestiary/vampire.webp",
        )
        self.assertEqual(vampire["image_license"], "CC BY-SA 4.0")

    def test_search_is_accent_insensitive_and_keeps_catalog_total(self) -> None:
        result = list_monster_catalog(query="vibora")
        self.assertEqual(result["total"], 255)
        self.assertTrue(any(monster["name"] == "Víbora Gigante" for monster in result["monsters"]))
        self.assertEqual(result["count"], len(result["monsters"]))

    def test_variable_and_special_hit_points_are_not_invented(self) -> None:
        hydra = get_catalog_monster("hidra")
        sphere = get_catalog_monster("esfera-da-aniquilacao")
        assert hydra is not None and sphere is not None
        self.assertEqual(hydra["hit_dice"], "5 a 12")
        self.assertEqual(hydra["hit_points"], "25 a 60")
        self.assertIsNone(hydra["average_hp"])
        self.assertEqual(sphere["hit_points"], "Especial")
        self.assertIsNone(sphere["average_hp"])

    def test_art_manifest_only_points_to_packaged_derivatives(self) -> None:
        manifest = load_monster_art_manifest()
        media_root = Path(__file__).resolve().parents[2] / "zz_media" / "ui" / "icons" / "monsters" / "illustrated-bestiary"
        self.assertGreaterEqual(len(manifest["mappings"]), 100)
        for monster_id, art_id in manifest["mappings"].items():
            self.assertIsNotNone(get_catalog_monster(monster_id), monster_id)
            self.assertTrue((media_root / f"{art_id}.webp").is_file(), art_id)

    def test_list_reports_image_coverage_without_hiding_unmatched_monsters(self) -> None:
        result = list_monster_catalog()
        self.assertEqual(result["total"], 255)
        self.assertGreaterEqual(result["image_count"], 100)
        self.assertLess(result["image_count"], result["total"])
        self.assertEqual(result["art_collection"]["creator"], "Oozejar")


if __name__ == "__main__":
    unittest.main()
