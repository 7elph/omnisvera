from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.session_workspace import (
    get_session_item_by_path,
    get_workspace_fog,
    get_workspace_snapshot,
    heartbeat_workspace,
    init_session_workspace,
    record_workspace_message,
    save_session_item,
    save_workspace_token,
    set_workspace_map,
    update_workspace_fog,
    update_workspace_token_position,
)


class SessionWorkspaceTests(unittest.TestCase):
    def test_map_messages_and_presence_share_one_snapshot(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            init_session_workspace(database)
            set_workspace_map(database, title="Nimalis", image_path="zz_media/maps/nimalis.png")
            record_workspace_message(
                database,
                actor_id="raziel",
                actor_name="Raziel",
                actor_role="player",
                character_id="raziel",
                text="Eu examino a porta.",
            )
            heartbeat_workspace(
                database,
                actor_id="raziel",
                actor_name="Raziel",
                actor_role="player",
                character_id="raziel",
            )
            snapshot = get_workspace_snapshot(database)
            self.assertEqual(snapshot["map"]["title"], "Nimalis")
            self.assertEqual(snapshot["messages"][0]["text"], "Eu examino a porta.")
            self.assertTrue(snapshot["presence"][0]["online"])

    def test_tokens_items_and_positions_survive_reinitialization(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            token = save_workspace_token(
                database, token_type="character", character_id="morthak", name="Morthak",
                latitude=42.5, longitude=19.25, color="#a987e8",
            )
            moved = update_workspace_token_position(
                database, token_id=token["id"], latitude=55.5, longitude=66.75,
            )
            item = save_session_item(
                database, name="Poção de Mana", item_type="consumível", description="Recupera mana.",
                effects=["+1 MP"], usable=True,
            )
            init_session_workspace(database)
            snapshot = get_workspace_snapshot(database)
            self.assertEqual(snapshot["tokens"][0]["latitude"], 55.5)
            self.assertEqual(snapshot["tokens"][0]["longitude"], 66.75)
            self.assertEqual(moved["name"], "Morthak")
            self.assertEqual(get_session_item_by_path(database, item["item_path"])["name"], "Poção de Mana")

    def test_fog_persists_and_hides_unrevealed_tokens_from_players(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            visible = save_workspace_token(
                database, token_type="monster", name="Visível", latitude=2, longitude=2,
            )
            hidden = save_workspace_token(
                database, token_type="monster", name="Oculto", latitude=80, longitude=80,
            )
            layer = update_workspace_fog(
                database, layer="exploration", enabled=True, revealed_cells=["0:0"],
            )
            self.assertTrue(layer["enabled"])
            self.assertEqual(get_workspace_fog(database)["exploration"]["revealed_cells"], ["0:0"])
            player_snapshot = get_workspace_snapshot(database)
            gm_snapshot = get_workspace_snapshot(database, is_gm=True)
            self.assertEqual([token["id"] for token in player_snapshot["tokens"]], [visible["id"]])
            self.assertEqual({token["id"] for token in gm_snapshot["tokens"]}, {visible["id"], hidden["id"]})


if __name__ == "__main__":
    unittest.main()
