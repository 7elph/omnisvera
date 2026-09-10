from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.asset_generation import (
    init_asset_generation,
    queue_missing_assets,
    scan_eligible_gaps,
    list_jobs,
    get_job,
)
from app.prompt_builder import build_prompt
from app.cloudflare_provider import MockProvider


def _setup_db(db: Path):
    # Create minimal schema for eligible gaps
    import sqlite3
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE IF NOT EXISTS scenes (id INTEGER PRIMARY KEY, title TEXT, location_name TEXT, public_description TEXT, objective TEXT, image_path TEXT, status TEXT)")
    conn.execute("INSERT INTO scenes (id, title, location_name, public_description, objective, image_path, status) VALUES (4, 'Próximo Encontro', 'Ruinas Novas', 'Descrição pública', 'Descobrir mais', NULL, 'active')")
    conn.execute("CREATE TABLE IF NOT EXISTS game_sessions (id INTEGER PRIMARY KEY, title TEXT, public_summary TEXT, image_path TEXT, status TEXT)")
    for i, title in enumerate(["Sessão 1", "Sessão 2", "Sessão 3", "Sessão 4"], start=1):
        conn.execute("INSERT INTO game_sessions (id, title, public_summary, image_path, status) VALUES (?,?,?,?,?)", (i, title, f"Resumo {title}", None, "completed"))
    conn.execute("CREATE TABLE IF NOT EXISTS session_custom_items (id INTEGER PRIMARY KEY, name TEXT, item_type TEXT, description TEXT, image_path TEXT)")
    conn.execute("INSERT INTO session_custom_items (id, name, item_type, description, image_path) VALUES (7, 'Anel Rúnico', 'Anel', 'Anel com runas', NULL)")
    conn.execute("INSERT INTO session_custom_items (id, name, item_type, description, image_path) VALUES (8, 'Moeda Misteriosa', 'Moeda', 'Moeda estranha', NULL)")
    conn.execute("INSERT INTO session_custom_items (id, name, item_type, description, image_path) VALUES (9, 'Escama Dracônica', 'Material', 'Escama', NULL)")
    conn.execute("INSERT INTO session_custom_items (id, name, item_type, description, image_path) VALUES (10, 'Espada Comum', 'Arma', 'Espada', NULL)")
    conn.commit()
    conn.close()
    # Also need other tables for init_asset_generation to work (it creates its own)
    init_asset_generation(db)


class AssetGenerationTests(unittest.TestCase):
    def test_eligible_gaps_found(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            gaps = scan_eligible_gaps(db)
            # Should find scene 1 + 4 sessions 4 + 3 special items 3 + 2 potions = 10
            # Espada Comum should be ignored (not eligible)
            asset_types = [g["asset_type"] for g in gaps]
            self.assertIn("scene_cover", asset_types)
            self.assertEqual(asset_types.count("session_cover"), 4)
            self.assertEqual(asset_types.count("item_art"), 3)
            # potions: only if files missing, they will be counted. In temp vault, they are missing, so 2
            self.assertIn("potion_hp", asset_types)
            self.assertIn("potion_mp", asset_types)
            # Total 1+4+3+2 =10
            self.assertEqual(len(gaps), 10)

    def test_missing_eligible_queued(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            queued = queue_missing_assets(db)
            self.assertEqual(len(queued), 10)
            jobs = list_jobs(db)
            self.assertEqual(len(jobs), 10)
            for job in jobs:
                self.assertEqual(job["status"], "queued")

    def test_missing_not_eligible_ignored(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            # Add a non-eligible item: Endro-like NPC should not be queued
            # Our scan only looks at scenes/sessions/special items/potions, so NPC not in gaps
            gaps = scan_eligible_gaps(db)
            # Ensure Espada Comum not in gaps
            names = [g["display_name"] for g in gaps]
            self.assertNotIn("Espada Comum", names)
            self.assertNotIn("Endro", names)

    def test_asset_existing_not_queued(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            # Make one session already have image
            conn = sqlite3.connect(db)
            conn.execute("UPDATE game_sessions SET image_path='zz_media/covers/exist.png' WHERE id=1")
            conn.commit()
            conn.close()
            gaps = scan_eligible_gaps(db)
            # Now only 3 sessions + 1 scene + 3 items +2 potions =9
            self.assertEqual(len(gaps), 9)
            # Also test manual asset protection: if scene already has image, it should not be queued even if job exists
            # Queue, then try to bind
            from app.asset_generation import bind_asset_to_entity, update_job_status
            queue_missing_assets(db)
            # Find a job for scene 4
            jobs = list_jobs(db)
            scene_job = next(j for j in jobs if j["entity_type"] == "scene")
            # Try to bind but scene already has no image, so it would bind; but if we set image_path manually, bind should not overwrite
            # Set scene image_path to manual
            conn = sqlite3.connect(db)
            conn.execute("UPDATE scenes SET image_path='zz_media/manual.png' WHERE id=4")
            conn.commit()
            conn.close()
            # Try bind
            bind_asset_to_entity(scene_job, "zz_media/generated/new.png", db)
            conn = sqlite3.connect(db)
            cur = conn.execute("SELECT image_path FROM scenes WHERE id=4")
            self.assertEqual(cur.fetchone()[0], "zz_media/manual.png")
            conn.close()

    def test_prompt_uses_canonical_data(self):
        prompt = build_prompt("scene_cover", "omnisvera.scene.v1", {"title": "Próximo Encontro", "location_name": "Ruinas", "public_description": "Desc", "objective": "Obj"})
        self.assertIn("Próximo Encontro", prompt)
        self.assertIn("Ruinas", prompt)
        self.assertIn("Desc", prompt)
        self.assertIn("dark medieval high fantasy", prompt.lower())  # style preset value
        # For potion
        prompt_hp = build_prompt("potion_hp", "omnisvera.potion.v1", {"potion_type": "potion_hp"})
        self.assertIn("healing potion", prompt_hp.lower())
        prompt_mp = build_prompt("potion_mp", "omnisvera.potion.v1", {"potion_type": "potion_mp"})
        self.assertIn("mana potion", prompt_mp.lower())

    def test_dedup(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            q1 = queue_missing_assets(db)
            self.assertEqual(len(q1), 10)
            q2 = queue_missing_assets(db)
            self.assertEqual(len(q2), 0)  # no new, deduped
            # After changing source data, should create new with different hash
            conn = sqlite3.connect(db)
            conn.execute("UPDATE scenes SET title='Próximo Encontro ALTERADO' WHERE id=4")
            conn.commit()
            conn.close()
            gaps = scan_eligible_gaps(db)
            # Find scene gap with new hash
            q3 = queue_missing_assets(db)
            # Should queue one more (the altered scene)
            self.assertEqual(len(q3), 1)

    def test_provider_failure_not_break(self):
        provider = MockProvider(fail=True)
        with self.assertRaises(RuntimeError):
            provider.generate("test", Path("/tmp/test.png"))
        # Ensure queue still works
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            queued = queue_missing_assets(db)
            self.assertEqual(len(queued), 10)

    def test_master_ui_status(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            queue_missing_assets(db)
            from app.main import settings as main_settings
            from dataclasses import replace
            import app.asset_generation as ag
            import app.asset_api as api
            test_settings = replace(main_settings, database_path=db, master_token="test-gm", player_token="test-player", player_profiles={})
            with patch.object(main, "settings", test_settings), patch.object(ag, "get_settings", return_value=test_settings), patch.object(api, "get_settings", return_value=test_settings) if hasattr(api, "get_settings") else patch.object(main, "settings", test_settings):
                # Also patch config
                import app.config as cfg
                with patch.object(cfg, "get_settings", return_value=test_settings):
                    client = TestClient(main.app)
                    try:
                        # List jobs
                        res = client.get("/gm/assets/jobs", headers={"X-Omnisvera-Token": "test-gm"})
                        self.assertEqual(200, res.status_code)
                        self.assertEqual(10, len(res.json()))
                        # Scan
                        res2 = client.post("/gm/assets/scan", headers={"X-Omnisvera-Token": "test-gm"})
                        self.assertEqual(200, res2.status_code)
                        self.assertIn("gaps_found", res2.json())
                    finally:
                        client.close()

    def test_ready_binds_correctly(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _setup_db(db)
            queued = queue_missing_assets(db)
            job = next(j for j in queued if j["entity_type"] == "session_custom_item")
            # Simulate generation ready
            from app.asset_generation import update_job_status, bind_asset_to_entity
            update_job_status(job["id"], "generating", database_path=db)
            # Mock generate
            provider = MockProvider()
            out = Path(tmp) / "generated.png"
            provider.generate("prompt", out)
            self.assertTrue(out.exists())
            update_job_status(job["id"], "ready", image_path="zz_media/ui/icons/uploads/generated_item_7.png", database_path=db)
            bind_asset_to_entity(job, "zz_media/ui/icons/uploads/generated_item_7.png", db)
            conn = sqlite3.connect(db)
            cur = conn.execute("SELECT image_path FROM session_custom_items WHERE id=?", (int(job["entity_id"]),))
            self.assertEqual(cur.fetchone()[0], "zz_media/ui/icons/uploads/generated_item_7.png")
            conn.close()
