from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scene_play import create_scene, get_scene, publish_scene_event, scene_view, update_scene


class ScenePreparationTests(unittest.TestCase):
    def test_scene_persists_map_camera_and_editable_checklist(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "scene.sqlite3"
            scene, created = create_scene(
                database,
                request_id="scene-preparation-1",
                campaign_id="omnisvera",
                title="Cripta do vampiro",
                location_name="Ruínas",
                created_by="master",
                image_path="zz_media/maps/cripta.png",
                map_id="map:cripta",
                checklist={"map": True, "pins": False, "opening": True},
                map_zoom=2.2,
                map_scroll_left=0.35,
                map_scroll_top=0.6,
            )

            self.assertTrue(created)
            self.assertEqual("map:cripta", scene["map_id"])
            self.assertEqual({"map": True, "pins": False, "opening": True}, scene["checklist"])
            self.assertEqual(2.2, scene["map_zoom"])

            updated = update_scene(
                database,
                int(scene["id"]),
                expected_version=int(scene["version"]),
                fields={"checklist": {"map": True, "pins": True, "treasure": True}, "map_zoom": 2.8},
            )
            self.assertEqual({"map": True, "pins": True, "treasure": True}, updated["checklist"])
            self.assertEqual(2.8, updated["map_zoom"])

            player_view = scene_view(database, int(scene["id"]), access_mode="player", profile_id="vezemir")
            self.assertIsNone(player_view, "rascunhos continuam privados")

    def test_publication_is_idempotent_and_stays_a_single_scene_event(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "scene.sqlite3"
            scene, _ = create_scene(
                database,
                request_id="scene-publication-1",
                campaign_id="omnisvera",
                title="Salão do relicário",
                location_name="Ruínas",
                created_by="master",
            )

            first, first_created = publish_scene_event(
                database,
                scene_id=int(scene["id"]),
                request_id="publish-treasure-1",
                publication_type="treasure",
                actor_id="master",
                title="Tesouro revelado",
                public_text="Um relicário de prata surge sob os escombros.",
            )
            repeated, repeated_created = publish_scene_event(
                database,
                scene_id=int(scene["id"]),
                request_id="publish-treasure-1",
                publication_type="treasure",
                actor_id="master",
                title="Texto reenviado",
                public_text="Este texto não deve gerar outro evento.",
            )

            self.assertTrue(first_created)
            self.assertFalse(repeated_created)
            self.assertEqual(first["id"], repeated["id"])
            self.assertEqual("Tesouro revelado", repeated["title"])
            loaded = get_scene(database, int(scene["id"]))
            self.assertIsNotNone(loaded)

    def test_rejects_unknown_checklist_item(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "scene.sqlite3"
            with self.assertRaisesRegex(ValueError, "checklist"):
                create_scene(
                    database,
                    request_id="scene-invalid-checklist",
                    campaign_id="omnisvera",
                    title="Cena inválida",
                    location_name="Lugar",
                    created_by="master",
                    checklist={"campo_inventado": True},
                )


if __name__ == "__main__":
    unittest.main()
