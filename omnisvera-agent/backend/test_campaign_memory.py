from __future__ import annotations

import hashlib
import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.scene_play import (
    change_session_status,
    create_session,
    get_visible_session,
    list_sessions,
    list_visible_sessions,
    sync_historical_sessions,
    update_session_metadata,
)


class CampaignMemoryTests(unittest.TestCase):
    def _historical_manifest(self, root: Path, count: int = 4) -> Path:
        source_dir = root / ".assistant-runtime" / "campaign-sources"
        source_dir.mkdir(parents=True)
        sessions = []
        for number in range(1, count + 1):
            source = source_dir / f"session-{number:03d}-transcript.txt"
            source.write_text(f"[{number:02d}:00] evidência da sessão {number}", encoding="utf-8")
            sessions.append({
                "request_id": f"historical-session-{number:03d}-test",
                "session_number": number,
                "title": f"Sessão histórica {number}",
                "status": "completed",
                "public_summary": f"Resumo público {number}",
                "public_chronicle": f"Crônica pública {number}",
                "participants": [{"character_id": "vezemir", "name": "Vezemir"}],
                "locations": [], "missions": [], "discoveries": [], "rewards": [],
                "items_acquired": [], "world_events": [], "character_events": [],
                "open_threads": [], "tags": ["História"],
                "gm_summary": f"Nota privada {number}",
                "companion_feedback": [{"title": "Teste", "description": "Somente Mestre"}],
                "source_refs": [{
                    "path": f".assistant-runtime/campaign-sources/{source.name}",
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "evidence": [f"{number:02d}:00"],
                }],
            })
        manifest = source_dir / "session-records.json"
        manifest.write_text(json.dumps({
            "version": 1,
            "campaign_id": "omnisvera",
            "source_status": "historical_evidence_pending_canon_review",
            "sessions": sessions,
        }), encoding="utf-8")
        return manifest

    def test_historical_import_is_verified_and_idempotent(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "campaign-memory.sqlite3"
            manifest = self._historical_manifest(root)

            self.assertEqual({"created": 4, "updated": 0, "unchanged": 0}, sync_historical_sessions(database, manifest))
            self.assertEqual({"created": 0, "updated": 0, "unchanged": 4}, sync_historical_sessions(database, manifest))
            self.assertEqual([4, 3, 2, 1], [row["session_number"] for row in list_sessions(database)])

            player = get_visible_session(database, 1, access_mode="player")
            self.assertEqual("Resumo público 1", player["public_summary"])
            self.assertEqual("Vezemir", player["narrative"]["participants"][0]["name"])
            self.assertNotIn("gm_summary", player)
            self.assertNotIn("gm_analysis", player)
            self.assertNotIn("source_refs", player)

            master = get_visible_session(database, 1, access_mode="gm")
            self.assertEqual("Nota privada 1", master["gm_summary"])
            self.assertEqual("Teste", master["gm_analysis"]["companion_feedback"][0]["title"])
            self.assertEqual(64, len(master["source_refs"][0]["sha256"]))

    def test_historical_import_rejects_changed_source(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "campaign-memory.sqlite3"
            manifest = self._historical_manifest(root, count=1)
            source = root / ".assistant-runtime" / "campaign-sources" / "session-001-transcript.txt"
            source.write_text("fonte alterada", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Hash divergente"):
                sync_historical_sessions(database, manifest)
            self.assertEqual([], list_sessions(database))

    def test_historical_import_never_overwrites_master_curation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "campaign-memory.sqlite3"
            manifest = self._historical_manifest(root, count=1)
            sync_historical_sessions(database, manifest)
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute(
                    """
                    UPDATE game_sessions SET title=?,status=?,private_notes=?,image_path=?,public_summary=?,
                      public_chronicle=?,gm_summary=?,narrative_json=?,version=version+1 WHERE request_id=?
                    """,
                    (
                        "Título curado", "paused", "Nota curada", "zz_media/sessions/curada.webp",
                        "Resumo curado", "Crônica curada", "Análise curada", '{"tags":["Curado"]}',
                        "historical-session-001-test",
                    ),
                )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["sessions"][0].update({"title": "Título do manifesto", "image_path": None, "public_summary": "Texto do manifesto"})
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            self.assertEqual({"created": 0, "updated": 0, "unchanged": 1}, sync_historical_sessions(database, manifest))
            curated = list_sessions(database)[0]
            self.assertEqual("Título curado", curated["title"])
            self.assertEqual("paused", curated["status"])
            self.assertEqual("Nota curada", curated["private_notes"])
            self.assertEqual("zz_media/sessions/curada.webp", curated["image_path"])
            self.assertEqual("Resumo curado", curated["public_summary"])
            self.assertEqual("Crônica curada", curated["public_chronicle"])
            self.assertEqual("Análise curada", curated["gm_summary"])
            self.assertEqual(["Curado"], curated["narrative"]["tags"])

    def test_player_chronology_hides_planning_and_private_notes(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "campaign-memory.sqlite3"
            planned, _ = create_session(
                database,
                request_id="campaign-memory-planned",
                campaign_id="omnisvera",
                title="Emboscada secreta",
                session_number=5,
                private_notes="O traidor estará presente.",
                created_by="master",
            )
            completed, _ = create_session(
                database,
                request_id="campaign-memory-completed",
                campaign_id="omnisvera",
                title="O Vampiro",
                session_number=3,
                private_notes="Segredo do receptáculo.",
                created_by="master",
            )
            change_session_status(database, int(completed["id"]), "active")
            change_session_status(database, int(completed["id"]), "completed")

            player = list_visible_sessions(database, access_mode="player")
            self.assertEqual(["O Vampiro"], [row["title"] for row in player])
            self.assertNotIn("private_notes", player[0])
            self.assertNotIn("created_by", player[0])
            self.assertNotIn(int(planned["id"]), [row["id"] for row in player])

            master = list_visible_sessions(database, access_mode="gm")
            self.assertEqual(2, len(master))
            planned_master = next(row for row in master if row["id"] == planned["id"])
            self.assertEqual("O traidor estará presente.", planned_master["private_notes"])

    def test_master_can_update_historical_date_and_image_without_changing_narrative(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "campaign-memory-metadata.sqlite3"
            session, _ = create_session(
                database,
                request_id="campaign-memory-metadata",
                campaign_id="omnisvera",
                title="Registro antigo",
                session_number=1,
                private_notes=None,
                created_by="master",
            )
            updated = update_session_metadata(database, int(session["id"]), {
                "played_on": "2026-08-01",
                "image_path": "zz_media/sessions/uploads/sessao-1.webp",
            })
            self.assertEqual("2026-08-01", updated["started_at"])
            self.assertEqual("2026-08-01", updated["ended_at"])
            self.assertEqual("zz_media/sessions/uploads/sessao-1.webp", updated["image_path"])
            self.assertEqual(2, updated["version"])

    def test_sessions_endpoint_applies_access_boundary(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "campaign-memory-api.sqlite3"
            public, _ = create_session(
                database,
                request_id="campaign-memory-api-public",
                campaign_id="omnisvera",
                title="Asas ao Norte",
                private_notes="Informação ainda não revelada.",
                created_by="master",
            )
            change_session_status(database, int(public["id"]), "active")
            settings = replace(
                main.settings,
                database_path=database,
                master_token="test-gm",
                player_token="test-player",
                player_profiles={},
            )
            with patch.object(main, "settings", settings):
                client = TestClient(main.app)
                try:
                    player = client.get("/sessions", headers={"X-Omnisvera-Token": "test-player"})
                    master = client.get("/sessions", headers={"X-Omnisvera-Token": "test-gm"})
                    anonymous = client.get("/sessions")
                finally:
                    client.close()
            self.assertEqual(200, player.status_code)
            self.assertNotIn("private_notes", player.json()[0])
            public_record = next(row for row in master.json() if row["request_id"] == "campaign-memory-api-public")
            self.assertEqual("Informação ainda não revelada.", public_record["private_notes"])
            self.assertEqual(401, anonymous.status_code)


if __name__ == "__main__":
    unittest.main()
