from __future__ import annotations

import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.character_play import apply_character_action, init_character_play
from app.combat_effects import effect_command, init_effects
from app.contract_play import current_operational_contract
from app.dice_rolls import create_roll, init_dice_rolls
from app.scene_play import (
    change_scene_status,
    change_session_status,
    create_scene,
    create_session,
    get_scene,
    init_scene_play,
)
from app.session_ledger import append_session_ledger_event, init_session_ledger
from app.session_workspace import (
    get_workspace_snapshot,
    init_session_workspace,
    list_workspace_maps,
    set_active_workspace_map,
    set_workspace_map,
)


class SessionCoherenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "coherence.sqlite3"
        init_scene_play(self.database)
        init_character_play(self.database)
        init_dice_rolls(self.database)
        init_session_workspace(self.database)
        init_session_ledger(self.database)
        init_effects(self.database)

    def _session(self, suffix: str, campaign_id: str = "omnisvera") -> dict:
        return create_session(
            self.database,
            request_id=f"coherence-session-{suffix}",
            campaign_id=campaign_id,
            title=f"Sessão {suffix}",
            created_by="master",
        )[0]

    def _character(self, profile_id: str = "vezemir") -> None:
        state = {
            "current_hp": 10,
            "maximum_hp": 10,
            "temporary_hp": 0,
            "conditions": [],
            "resources": [],
        }
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                (profile_id, json.dumps(state), "2026-08-31T00:00:00+00:00"),
            )

    def test_only_one_session_can_be_active_and_concurrent_activation_is_safe(self) -> None:
        first, second = self._session("first"), self._session("second", "outra-campanha")

        def activate(session_id: int) -> str:
            try:
                change_session_status(self.database, session_id, "active")
                return "active"
            except ValueError:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(activate, [int(first["id"]), int(second["id"])]))
        self.assertEqual(["active", "rejected"], sorted(results))
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM game_sessions WHERE status='active'").fetchone()[0])

    def test_scene_cannot_be_activated_without_an_active_session(self) -> None:
        scene, _ = create_scene(
            self.database,
            request_id="coherence-scene-without-session",
            campaign_id="omnisvera",
            title="Cena preparada",
            location_name="Nimalis",
            created_by="master",
        )

        with self.assertRaisesRegex(ValueError, "Inicie uma sessão"):
            change_scene_status(self.database, int(scene["id"]), "active")
        self.assertEqual("draft", get_scene(self.database, int(scene["id"]))["status"])

    def test_pausing_or_completing_a_session_pauses_its_active_scene(self) -> None:
        for index, final_status in enumerate(("paused", "completed"), start=1):
            with self.subTest(final_status=final_status):
                session = self._session(f"close-{index}")
                change_session_status(self.database, int(session["id"]), "active")
                scene, _ = create_scene(
                    self.database,
                    request_id=f"coherence-close-scene-{index}",
                    campaign_id="omnisvera",
                    title=f"Cena {index}",
                    location_name="Ruínas",
                    created_by="master",
                )
                change_scene_status(self.database, int(scene["id"]), "active")

                change_session_status(self.database, int(session["id"]), final_status)

                self.assertEqual("paused", get_scene(self.database, int(scene["id"]))["status"])

    def test_open_on_table_without_active_session_does_not_switch_maps(self) -> None:
        waiting_map = set_workspace_map(
            self.database,
            title="Mapa de espera",
            image_path="maps/espera.png",
            visible_to_players=True,
        )
        prepared_map = set_workspace_map(
            self.database,
            title="Mapa privado",
            image_path="maps/privado.png",
            visible_to_players=False,
        )
        set_active_workspace_map(self.database, waiting_map["id"])
        scene, _ = create_scene(
            self.database,
            request_id="coherence-open-without-session",
            campaign_id="omnisvera",
            title="Cena ainda fechada",
            location_name="Ruínas",
            created_by="master",
            map_id=prepared_map["id"],
        )
        settings = replace(
            main.settings,
            database_path=self.database,
            master_token="test-gm",
            player_token="test-player",
            player_profiles={},
        )

        with patch.object(main, "settings", settings):
            client = TestClient(main.app)
            try:
                response = client.post(
                    f"/gm/scenes/{scene['id']}/open-on-table",
                    headers={"X-Omnisvera-Token": "test-gm"},
                    json={"request_id": "open-without-session"},
                )
            finally:
                client.close()

        self.assertEqual(400, response.status_code)
        self.assertIn("Inicie uma sessão", response.json()["detail"])
        self.assertEqual(waiting_map["id"], get_workspace_snapshot(self.database, is_gm=True)["map"]["id"])
        stored_private_map = next(item for item in list_workspace_maps(self.database) if item["id"] == prepared_map["id"])
        self.assertFalse(stored_private_map["visible_to_players"])

    def test_open_on_table_reveals_map_sanitizes_player_scene_and_is_idempotent(self) -> None:
        session = self._session("open-table")
        change_session_status(self.database, int(session["id"]), "active")
        waiting_map = set_workspace_map(
            self.database,
            title="Mapa de espera",
            image_path="maps/espera.png",
            visible_to_players=True,
        )
        prepared_map = set_workspace_map(
            self.database,
            title="Mapa secreto da cena",
            image_path="maps/cena.png",
            visible_to_players=False,
        )
        set_active_workspace_map(self.database, waiting_map["id"])
        scene, _ = create_scene(
            self.database,
            request_id="coherence-open-table-scene",
            campaign_id="omnisvera",
            title="Salão oculto",
            location_name="Ruínas",
            location_source="gm://local-secreto",
            public_description="O salão se abre diante do grupo.",
            private_notes="Há uma criatura atrás da porta.",
            created_by="master",
            map_id=prepared_map["id"],
        )
        settings = replace(
            main.settings,
            database_path=self.database,
            master_token="test-gm",
            player_token="test-player",
            player_profiles={},
        )
        headers = {"X-Omnisvera-Token": "test-gm"}
        payload = {"request_id": "coherence-open-repeat"}

        with patch.object(main, "settings", settings):
            client = TestClient(main.app)
            try:
                first = client.post(f"/gm/scenes/{scene['id']}/open-on-table", headers=headers, json=payload)
                repeated = client.post(f"/gm/scenes/{scene['id']}/open-on-table", headers=headers, json=payload)
                player_scene = client.get("/scenes/active", headers={"X-Omnisvera-Token": "test-player"})
                player_workspace = client.get("/workspace", headers={"X-Omnisvera-Token": "test-player"})
            finally:
                client.close()

        self.assertEqual(200, first.status_code)
        self.assertTrue(first.json()["created"])
        self.assertEqual(200, repeated.status_code)
        self.assertFalse(repeated.json()["created"])
        self.assertEqual(first.json()["event"]["id"], repeated.json()["event"]["id"])

        self.assertEqual(200, player_scene.status_code)
        public_scene = player_scene.json()
        self.assertEqual(scene["id"], public_scene["id"])
        for private_key in ("location_source", "request_id", "created_by", "private_notes"):
            self.assertNotIn(private_key, public_scene)

        self.assertEqual(200, player_workspace.status_code)
        self.assertEqual(prepared_map["id"], player_workspace.json()["map"]["id"])
        self.assertEqual(prepared_map["id"], player_workspace.json()["active_map_id"])
        self.assertTrue(player_workspace.json()["map"]["visible_to_players"])
        stored_prepared_map = next(item for item in list_workspace_maps(self.database) if item["id"] == prepared_map["id"])
        self.assertTrue(stored_prepared_map["visible_to_players"])

        with closing(sqlite3.connect(self.database)) as connection:
            publications = connection.execute(
                "SELECT COUNT(*) FROM scene_events WHERE event_key=?",
                ("scene-publication:coherence-open-repeat",),
            ).fetchone()[0]
            messages = connection.execute(
                "SELECT COUNT(*) FROM session_workspace_messages WHERE text LIKE ?",
                ("Salão oculto:%",),
            ).fetchone()[0]
        self.assertEqual(1, publications)
        self.assertEqual(1, messages)

    def test_future_character_roll_and_ledger_records_receive_game_session_id(self) -> None:
        session = self._session("events")
        change_session_status(self.database, int(session["id"]), "active")
        self._character()
        action = apply_character_action(
            self.database,
            character_id="vezemir",
            actor_id="master",
            actor_role="gm",
            action="damage",
            payload={"amount": 1},
            reason="Armadilha",
            session_id="legacy-scene-77",
        )
        roll, _ = create_roll(
            self.database,
            request_id="coherence-roll-active",
            campaign_id="omnisvera",
            actor_id="master",
            actor_role="gm",
            roll_type="free",
            label="Teste",
            formula="1d20",
            visibility="gm",
            rng=lambda *_: 10,
        )
        with closing(sqlite3.connect(self.database)) as connection, connection:
            ledger_id = append_session_ledger_event(
                connection,
                source_type="coherence_test",
                source_id="ledger-active",
                event_kind="state",
                actor_id="master",
                actor_name="Mestre",
                actor_role="gm",
                character_id=None,
                title="Fato da sessão",
                detail=None,
                created_at="2026-08-31T00:00:00+00:00",
            )
            character_row = connection.execute(
                "SELECT session_id,game_session_id FROM character_events WHERE id=?", (action["event_id"],)
            ).fetchone()
            ledger_rows = connection.execute(
                "SELECT game_session_id FROM session_ledger WHERE id IN (?,?) ORDER BY id",
                (ledger_id, ledger_id),
            ).fetchall()
        self.assertEqual("legacy-scene-77", character_row[0])
        self.assertEqual(session["id"], character_row[1])
        self.assertEqual(session["id"], roll["game_session_id"])
        self.assertEqual(session["id"], ledger_rows[0][0])

    def test_no_active_session_does_not_invent_context(self) -> None:
        self._character()
        action = apply_character_action(
            self.database,
            character_id="vezemir",
            actor_id="master",
            actor_role="gm",
            action="damage",
            payload={"amount": 1},
            session_id="historical-session-unresolved",
        )
        roll, _ = create_roll(
            self.database,
            request_id="coherence-roll-no-session",
            campaign_id="omnisvera",
            actor_id="master",
            actor_role="gm",
            roll_type="free",
            label="Sem sessão",
            formula="1d20",
            visibility="gm",
            rng=lambda *_: 10,
        )
        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute(
                "SELECT session_id,game_session_id FROM character_events WHERE id=?", (action["event_id"],)
            ).fetchone()
        self.assertEqual("historical-session-unresolved", row[0])
        self.assertIsNone(row[1])
        self.assertIsNone(roll["game_session_id"])

    def test_scene_and_combat_preserve_explicit_operational_context(self) -> None:
        session = self._session("scene")
        change_session_status(self.database, int(session["id"]), "active")
        scene, _ = create_scene(
            self.database,
            request_id="coherence-scene-active",
            campaign_id="omnisvera",
            title="Posto abandonado",
            location_name="Earthropo",
            created_by="master",
        )
        self.assertEqual(session["id"], scene["session_id"])
        activated = change_scene_status(self.database, int(scene["id"]), "active")
        self.assertEqual(session["id"], activated["session_id"])

        started = effect_command(
            self.database,
            actor_id="master",
            actor_role="gm",
            request_id="coherence-combat-start",
            expected_version=0,
            action="start",
            payload={
                "map_id": "official:earthropo",
                "title": "Emboscada",
                "game_session_id": int(session["id"]),
                "scene_id": int(scene["id"]),
                "participants": [{"target_type": "character", "target_id": "vezemir", "name": "Vezemir", "initiative": 10}],
            },
        )
        self.assertEqual(session["id"], started["encounter"]["game_session_id"])
        self.assertEqual(scene["id"], started["encounter"]["scene_id"])
        updated = effect_command(
            self.database,
            actor_id="master",
            actor_role="gm",
            request_id="coherence-combat-initiative",
            expected_version=started["version"],
            action="initiative",
            payload={"participants": [{"target_type": "character", "target_id": "vezemir", "name": "Vezemir", "initiative": 12}]},
        )
        self.assertEqual(session["id"], updated["encounter"]["game_session_id"])
        self.assertEqual(scene["id"], updated["encounter"]["scene_id"])

    def test_contract_state_is_the_operational_mission_source(self) -> None:
        published = {"id": 1, "status": "published", "title": "Disponível"}
        accepted = {"id": 2, "status": "accepted", "title": "Aceita"}
        active = {"id": 3, "status": "active", "title": "Ativa"}
        self.assertIsNone(current_operational_contract([published]))
        self.assertEqual(active, current_operational_contract([published, accepted, active]))
        self.assertEqual(accepted, current_operational_contract([published, accepted]))


if __name__ == "__main__":
    unittest.main()
