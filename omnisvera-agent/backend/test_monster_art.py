from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import app.monster_catalog as monster_catalog
from app.monster_catalog import bind_monster_ai_art, get_catalog_monster, load_monster_catalog


class MonsterArtTests(unittest.TestCase):
    def test_oozejar_keeps_priority_over_ai_art(self) -> None:
        vampire = get_catalog_monster("vampiro")
        assert vampire is not None
        self.assertTrue(vampire["image_path"].endswith("vampire.webp"))
        self.assertIn("Oozejar", vampire["image_attribution"])

    def test_bind_never_overwrites_and_uses_temp_file(self) -> None:
        with TemporaryDirectory() as tmp:
            fake = Path(tmp) / "ai_art.json"
            with patch.object(monster_catalog, "AI_ART_PATH", fake):
                self.addCleanup(load_monster_catalog.cache_clear)
                self.assertTrue(bind_monster_ai_art("esfera-da-aniquilacao", "zz_media/ui/icons/approved/asset_1_x.png"))
                self.assertFalse(bind_monster_ai_art("esfera-da-aniquilacao", "zz_media/ui/icons/approved/asset_2_y.png"))
                sphere = get_catalog_monster("esfera-da-aniquilacao")
                assert sphere is not None
                self.assertEqual(sphere["image_path"], "zz_media/ui/icons/approved/asset_1_x.png")
                self.assertIn("FLUX", sphere["image_attribution"])
            load_monster_catalog.cache_clear()

    def test_bind_unknown_monster_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            with patch.object(monster_catalog, "AI_ART_PATH", Path(tmp) / "ai_art.json"):
                self.addCleanup(load_monster_catalog.cache_clear)
                with self.assertRaises(ValueError):
                    bind_monster_ai_art("nao-existe", "zz_media/x.png")

    def test_monster_prompt_uses_canonical_data(self) -> None:
        from app.prompt_builder import build_prompt
        prompt = build_prompt("monster_art", "omnisvera.monster.v1",
                              {"name": "Hidra", "category": "Besta", "size": "Grande", "habitat": "Pântano", "hit_dice": "5 a 12"})
        self.assertIn("Hidra", prompt)
        self.assertIn("Besta", prompt)
        self.assertNotIn("Ilusão", prompt)


if __name__ == "__main__":
    unittest.main()
