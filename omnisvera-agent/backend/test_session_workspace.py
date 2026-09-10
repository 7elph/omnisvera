from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.session_workspace import (
    delete_session_item,
    get_session_item_by_path,
    get_workspace_fog,
    get_workspace_snapshot,
    ensure_official_workspace_maps,
    heartbeat_workspace,
    init_session_workspace,
    list_workspace_maps,
    record_workspace_message,
    save_session_item,
    session_item_inventory_holders,
    save_workspace_token,
    set_active_workspace_map,
    set_workspace_map,
    update_workspace_map_visibility,
    update_workspace_fog,
    update_workspace_token,
    update_workspace_token_position,
    update_workspace_table_mode,
)
from app.player_inventory import normalize_inventory_item_mechanics, upsert_inventory


class SessionWorkspaceTests(unittest.TestCase):
    def test_official_maps_are_added_idempotently_without_changing_active_map(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "workspace.db"
            maps = root / "zz_media" / "maps"
            maps.mkdir(parents=True)
            for filename in ("mapa_de_nimalis.png", "mapa_de_nimalia.png", "earthropo.png"):
                (maps / filename).write_bytes(b"map")
            dungeon = set_workspace_map(
                database, title="Dungeon 01", image_path="maps/dungeon.png", visible_to_players=False,
            )

            ensure_official_workspace_maps(database, root)
            ensure_official_workspace_maps(database, root)

            all_maps = list_workspace_maps(database)
            official = [item for item in all_maps if item["id"].startswith("official:")]
            self.assertEqual({item["title"] for item in official}, {"Nimalis", "Nimalia", "Earthropo"})
            self.assertTrue(all(item["visible_to_players"] for item in official))
            self.assertEqual(get_workspace_snapshot(database, is_gm=True)["map"]["id"], dungeon["id"])

    def test_table_mode_is_persisted_and_shared_in_snapshot(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            init_session_workspace(database)
            self.assertEqual(get_workspace_snapshot(database)["table_mode"], "digital")
            self.assertEqual(update_workspace_table_mode(database, "physical"), "physical")
            self.assertEqual(get_workspace_snapshot(database, is_gm=True)["table_mode"], "physical")
            self.assertEqual(get_workspace_snapshot(database, is_gm=False)["table_mode"], "physical")
            init_session_workspace(database)
            self.assertEqual(get_workspace_snapshot(database)["table_mode"], "physical")

    def test_table_mode_rejects_unknown_values(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            with self.assertRaisesRegex(ValueError, "Modo da mesa inválido"):
                update_workspace_table_mode(database, "automatic")

    def test_legacy_morthak_staff_receives_weapon_mechanics_from_backend(self) -> None:
        item = normalize_inventory_item_mechanics({
            "item_path": "session-item:3",
            "item_title": "Cajado de Morthak",
            "item_type": "Arma",
            "effects": ["1d4 de dano"],
            "mechanics": {},
        })
        self.assertEqual(item["damage_formula"], "1d4")
        self.assertEqual(item["mechanics"]["damage_formula"], "1d4")
        self.assertEqual(item["mechanics"]["equipment_slots"], ["Corpo a corpo", "À distância"])

    def test_created_and_vault_weapons_offer_both_combat_slots(self) -> None:
        weapons = [
            {
                "item_path": "session-item:10",
                "item_title": "Lâmina criada",
                "item_type": "Arma",
                "mechanics": {"equipment_slots": ["Corpo a corpo"], "damage_formula": "1d6"},
            },
            {
                "item_path": "Items/01 Armas/Arco.md",
                "item_title": "Arco",
                "item_type": "Arma à distância",
                "damage_formula": "1d6",
            },
        ]
        for weapon in weapons:
            with self.subTest(item_title=weapon["item_title"]):
                normalized = normalize_inventory_item_mechanics(weapon)
                self.assertEqual(normalized["mechanics"]["equipment_slots"], ["Corpo a corpo", "À distância"])

    def test_session_item_deletion_can_detect_inventory_holders(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            item = save_session_item(
                database, name="Grimório", item_type="item", description="",
                effects=[], usable=False,
            )
            upsert_inventory(
                database, profile_id="morthak", item_path=item["item_path"], item_title=item["name"],
                quantity=2, equipped=False, notes=None,
            )
            self.assertEqual(session_item_inventory_holders(database, item["id"]), [{"profile_id": "morthak", "quantity": 2}])
            self.assertTrue(delete_session_item(database, item["id"]))
            self.assertIsNone(get_session_item_by_path(database, item["item_path"]))

    def test_map_messages_and_presence_share_one_snapshot(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            init_session_workspace(database)
            set_workspace_map(database, title="Nimalis", image_path="zz_media/maps/nimalis.png", visible_to_players=True)
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

    def test_upload_adds_map_without_replacing_the_active_map(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            nimalis = set_workspace_map(
                database, title="Nimalis", image_path="maps/nimalis.png", visible_to_players=True,
            )
            dungeon = set_workspace_map(
                database, title="Dungeon 01", image_path="maps/dungeon.png", visible_to_players=False,
            )
            snapshot = get_workspace_snapshot(database, is_gm=True)
            self.assertEqual(snapshot["map"]["id"], nimalis["id"])
            self.assertEqual([item["id"] for item in list_workspace_maps(database)], [nimalis["id"], dungeon["id"]])
            self.assertFalse(dungeon["visible_to_players"])

    def test_players_only_list_and_open_maps_marked_visible(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            nimalis = set_workspace_map(
                database, title="Nimalis", image_path="maps/nimalis.png", visible_to_players=True,
            )
            dungeon = set_workspace_map(
                database, title="Dungeon 01", image_path="maps/dungeon.png", visible_to_players=False,
            )
            set_active_workspace_map(database, dungeon["id"])
            visible_maps = list_workspace_maps(database, visible_to_players_only=True)
            self.assertEqual([item["id"] for item in visible_maps], [nimalis["id"]])
            hidden_request = get_workspace_snapshot(database, map_id=dungeon["id"])
            self.assertEqual(hidden_request["map"]["id"], nimalis["id"])

            revealed = update_workspace_map_visibility(database, dungeon["id"], visible_to_players=True)
            self.assertIsNotNone(revealed)
            self.assertTrue(revealed["visible_to_players"])
            revealed_request = get_workspace_snapshot(database, map_id=dungeon["id"])
            self.assertEqual(revealed_request["map"]["id"], dungeon["id"])

    def test_map_tokens_remain_attached_when_another_map_is_opened(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            dungeon = set_workspace_map(
                database, title="Dungeon 01", image_path="maps/dungeon.png", visible_to_players=True,
            )
            vampire = save_workspace_token(
                database, token_type="monster", name="Vampiro", latitude=45, longitude=52,
                map_id=dungeon["id"],
            )
            nimalia = set_workspace_map(
                database, title="Nimalia", image_path="maps/nimalia.png", visible_to_players=True,
            )
            set_active_workspace_map(database, nimalia["id"])
            self.assertEqual(get_workspace_snapshot(database)["tokens"], [])
            dungeon_snapshot = get_workspace_snapshot(database, map_id=dungeon["id"])
            self.assertEqual([item["id"] for item in dungeon_snapshot["tokens"]], [vampire["id"]])

    def test_fog_is_isolated_per_map(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            dungeon = set_workspace_map(
                database, title="Dungeon 01", image_path="maps/dungeon.png", visible_to_players=True,
            )
            nimalis = set_workspace_map(
                database, title="Nimalis", image_path="maps/nimalis.png", visible_to_players=True,
            )
            update_workspace_fog(
                database, map_id=dungeon["id"], layer="exploration", enabled=True,
                revealed_cells=[], mist_density={"4:4": 1},
            )
            self.assertTrue(get_workspace_snapshot(database, map_id=dungeon["id"])["fog"]["exploration"]["enabled"])
            self.assertFalse(get_workspace_snapshot(database, map_id=nimalis["id"])["fog"]["exploration"]["enabled"])

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
                effect_rules=[{"id": "mana", "trigger": "on_use", "kind": "restore_resource", "target": "mana", "value": 1, "label": "Recupera mana"}],
                mechanics={"equipment_slots": [], "consume_mode": "charges", "charges_max": 3, "recharge": "inn_rest", "slot_limit": 1},
            )
            init_session_workspace(database)
            snapshot = get_workspace_snapshot(database)
            self.assertEqual(snapshot["tokens"][0]["latitude"], 55.5)
            self.assertEqual(snapshot["tokens"][0]["longitude"], 66.75)
            self.assertEqual(moved["name"], "Morthak")
            restored_item = get_session_item_by_path(database, item["item_path"])
            self.assertEqual(restored_item["name"], "Poção de Mana")
            self.assertEqual(restored_item["effect_rules"][0]["kind"], "restore_resource")
            self.assertEqual(restored_item["effect_rules"][0]["target"], "mana")
            self.assertEqual(restored_item["mechanics"]["charges_max"], 3)
            self.assertEqual(restored_item["mechanics"]["consume_mode"], "charges")

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
                mist_density={"25:19": 1},
            )
            self.assertTrue(layer["enabled"])
            self.assertEqual(get_workspace_fog(database)["exploration"]["revealed_cells"], ["0:0"])
            player_snapshot = get_workspace_snapshot(database)
            gm_snapshot = get_workspace_snapshot(database, is_gm=True)
            self.assertEqual([token["id"] for token in player_snapshot["tokens"]], [visible["id"]])
            self.assertEqual({token["id"] for token in gm_snapshot["tokens"]}, {visible["id"], hidden["id"]})

    def test_empty_density_layer_does_not_hide_every_player_token(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            visible = save_workspace_token(
                database, token_type="monster", name="Vampiro", latitude=50, longitude=50,
            )
            update_workspace_fog(
                database, layer="exploration", enabled=True, revealed_cells=[], mist_density={},
            )
            snapshot = get_workspace_snapshot(database)
            self.assertEqual([token["id"] for token in snapshot["tokens"]], [visible["id"]])

    def test_master_can_prepare_hidden_token_and_reveal_it_later(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            hidden = save_workspace_token(
                database, token_type="monster", name="Vampiro", latitude=50, longitude=50,
                visible_to_players=False,
            )
            self.assertEqual(get_workspace_snapshot(database)["tokens"], [])
            updated = update_workspace_token(
                database, token_id=hidden["id"], visible_to_players=True,
            )
            self.assertTrue(updated["visible_to_players"])
            self.assertEqual([token["id"] for token in get_workspace_snapshot(database)["tokens"]], [hidden["id"]])

    def test_battle_fog_density_persists_independently_from_exploration(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "workspace.db"
            update_workspace_fog(
                database, layer="exploration", enabled=True,
                revealed_cells=["1:1"], mist_density={"1:1": .25},
            )
            battle = update_workspace_fog(
                database, layer="battle", enabled=True,
                revealed_cells=["4:3"], mist_density={"4:3": 1, "5:3": .625},
            )
            init_session_workspace(database)
            fog = get_workspace_fog(database)
            self.assertTrue(battle["enabled"])
            self.assertEqual(fog["battle"]["revealed_cells"], ["4:3"])
            self.assertEqual(fog["battle"]["mist_density"], {"4:3": 1.0, "5:3": .625})
            self.assertEqual(fog["exploration"]["mist_density"], {"1:1": .25})


if __name__ == "__main__":
    unittest.main()
