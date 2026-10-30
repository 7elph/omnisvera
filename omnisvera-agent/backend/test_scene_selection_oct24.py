from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app import battle_mode
from app import scene_play
from app import scene_selection
from app import session_workspace
from app.combat_effects import init_effects


class SceneSelectionOct24Tests(unittest.TestCase):
    def test_replay_after_resolution_and_session_end_never_republishes(self):
        with TemporaryDirectory() as td:
            db=self._setup_db(td)
            scene,_=scene_play.create_scene(db,request_id='scene-repeat-original',campaign_id='omnisvera',title='Teste',location_name='Local',created_by='master',map_id='map:arena')
            args={'request_id':'selection-immutable-retry','include_map':True}
            first=scene_selection.open_selection(db,scene['id'],**args)
            with closing(sqlite3.connect(db)) as conn,conn:
                conn.execute("UPDATE scenes SET status='resolved' WHERE id=?",(scene['id'],))
                conn.execute("UPDATE game_sessions SET status='completed'")
            replay=scene_selection.open_selection(db,scene['id'],**args)
            self.assertFalse(replay['created']);self.assertEqual(first['event'],replay['event'])
            with closing(sqlite3.connect(db)) as conn:self.assertEqual(1,conn.execute("SELECT count(*) FROM session_ledger WHERE source_type='scene_selection'").fetchone()[0])

    def test_selected_pin_only_and_fog_preserved(self):
        with TemporaryDirectory() as td:
            db=self._setup_db(td)
            scene,_=scene_play.create_scene(db,request_id='scene-pins-selected',campaign_id='omnisvera',title='Teste',location_name='Local',created_by='master',map_id='map:arena')
            pins=[session_workspace.save_workspace_token(db,token_type='monster',map_id='map:arena',name=f'Pin {i}',latitude=20,longitude=20,visible_to_players=False) for i in (1,2)]
            scene_selection.open_selection(db,scene['id'],request_id='selection-pin-single',token_ids=[pins[0]['id']],include_map=True)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(1,conn.execute('SELECT visible_to_players FROM session_workspace_tokens WHERE id=?',(pins[0]['id'],)).fetchone()[0])
                self.assertEqual(0,conn.execute('SELECT visible_to_players FROM session_workspace_tokens WHERE id=?',(pins[1]['id'],)).fetchone()[0])

    def test_realtime_failure_rolls_back_publication_and_map(self):
        from unittest.mock import patch
        with TemporaryDirectory() as td:
            db=self._setup_db(td)
            scene,_=scene_play.create_scene(db,request_id='scene-atomic-selection',campaign_id='omnisvera',title='Teste',location_name='Local',created_by='master',map_id='map:arena')
            with patch.object(scene_selection.session_ledger,'append_session_ledger_event',side_effect=RuntimeError('fixture failure')):
                with self.assertRaises(RuntimeError):scene_selection.open_selection(db,scene['id'],request_id='selection-atomic-failure',include_map=True)
            self.assertEqual('draft',scene_play.get_scene(db,scene['id'])['status'])
            with closing(sqlite3.connect(db)) as conn:self.assertEqual('default',conn.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()[0])

    def _setup_db(self, tempdir):
        db = Path(tempdir) / "sel.sqlite3"
        scene_play.init_scene_play(db)
        session_workspace.init_session_workspace(db)
        init_effects(db)
        # create active session
        with closing(sqlite3.connect(db)) as conn, conn:
            conn.execute(
                "INSERT INTO game_sessions(request_id,campaign_id,title,status,created_by,created_at) VALUES(?,?,?,?,?,?)",
                ("sess-1", "omnisvera", "Sessao", "active", "master", "2026-10-24T00:00:00+00:00"),
            )
            conn.execute("INSERT OR REPLACE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','M','m.png','now')")
            conn.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','M','m.png',1,'now','now')")
            conn.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('map:arena','Arena','a.png',1,'now','now')")
        return db

    def test_criacao_e_selecao_parcial(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-1", campaign_id="omnisvera", title="C", location_name="L", created_by="master", map_id="map:arena")
            e1, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-1", element_type="clue", title="Pista A", status="hidden", visibility="gm", created_by="master", public_description="Desc A", private_description="Priv A")
            e2, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-2", element_type="clue", title="Pista B", status="hidden", visibility="gm", created_by="master", public_description="Desc B", private_description="Priv B")
            res = scene_selection.open_selection(db, scene["id"], request_id="req-sel-1", element_ids=[e1["id"]], token_ids=[], include_map=False)
            self.assertEqual(res["scene_id"], scene["id"])
            self.assertIsNone(res["map_id"])
            self.assertTrue(res["created"])
            with closing(sqlite3.connect(db)) as conn:
                e1r = conn.execute("SELECT visibility,public_description,private_description FROM scene_elements WHERE id=?", (e1["id"],)).fetchone()
                e2r = conn.execute("SELECT visibility,public_description,private_description FROM scene_elements WHERE id=?", (e2["id"],)).fetchone()
                self.assertEqual(e1r[0], "table")
                self.assertEqual(e2r[0], "gm")  # not revealed
            # only selected in public text
            self.assertIn("Desc A", res["event"]["public_text"])
            self.assertNotIn("Desc B", res["event"]["public_text"])
            self.assertNotIn("Priv A", res["event"]["public_text"])
            self.assertNotIn("private_description", json.dumps(res["event"]))

    def test_idempotencia_mesmo_request_mesma_intencao(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-2", campaign_id="omnisvera", title="C", location_name="L", created_by="master")
            e1, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-3", element_type="clue", title="Pista A", status="hidden", visibility="gm", created_by="master", public_description="Desc A", private_description="Priv A")
            r1 = scene_selection.open_selection(db, scene["id"], request_id="req-sel-2", element_ids=[e1["id"]], include_map=False)
            r2 = scene_selection.open_selection(db, scene["id"], request_id="req-sel-2", element_ids=[e1["id"]], include_map=False)
            self.assertTrue(r1["created"])
            self.assertFalse(r2["created"])
            self.assertEqual(r1["event"]["id"], r2["event"]["id"])
            with closing(sqlite3.connect(db)) as conn:
                cnt = conn.execute("SELECT count(*) FROM scene_events WHERE event_key=?", ("scene-selection:req-sel-2",)).fetchone()[0]
                self.assertEqual(cnt, 1)

    def test_intencao_diferente_mesmo_request_rejeita(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-3", campaign_id="omnisvera", title="C", location_name="L", created_by="master")
            e1, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-4", element_type="clue", title="Pista A", status="hidden", visibility="gm", created_by="master", public_description="Desc A", private_description="Priv A")
            scene_selection.open_selection(db, scene["id"], request_id="req-sel-3", element_ids=[e1["id"]], include_map=False)
            with self.assertRaises(ValueError):
                scene_selection.open_selection(db, scene["id"], request_id="req-sel-3", element_ids=[], include_map=False)

    def test_privacidade_nao_publica_private_description_objective_notas(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-4", campaign_id="omnisvera", title="C", location_name="L", created_by="master", objective="ObjSecreto", private_notes="NotasPriv")
            e1, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-5", element_type="clue", title="Pista A", status="hidden", visibility="gm", created_by="master", public_description="PubA", private_description="PrivA")
            res = scene_selection.open_selection(db, scene["id"], request_id="req-sel-4", element_ids=[e1["id"]], include_map=False)
            ev = res["event"]
            self.assertNotIn("PrivA", json.dumps(ev))
            self.assertNotIn("private_description", json.dumps(ev))
            self.assertNotIn("objective", json.dumps(ev))
            self.assertNotIn("private_notes", json.dumps(ev))
            player=scene_play.scene_view(db,scene['id'],access_mode='player',profile_id='raziel')
            self.assertNotIn('objective',player)
            self.assertNotIn('private_notes',player)
            # scene not dumping all elements
            with closing(sqlite3.connect(db)) as conn:
                e2c = conn.execute("SELECT count(*) FROM scene_elements WHERE scene_id=? AND visibility='table'", (scene["id"],)).fetchone()[0]
                self.assertEqual(e2c, 1)

    def test_id_estrangeiro_e_atomicidade(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-5", campaign_id="omnisvera", title="C", location_name="L", created_by="master")
            scene2, _ = scene_play.create_scene(db, request_id="scene-sel-5b", campaign_id="omnisvera", title="C2", location_name="L", created_by="master")
            e2, _ = scene_play.create_element(db, scene_id=scene2["id"], request_id="el-sel-6", element_type="clue", title="Pista X", status="hidden", visibility="gm", created_by="master", public_description="PubX", private_description="PrivX")
            with self.assertRaises(ValueError):
                scene_selection.open_selection(db, scene["id"], request_id="req-sel-5", element_ids=[e2["id"]], include_map=False)
            # nothing changed
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute("SELECT visibility FROM scene_elements WHERE id=?", (e2["id"],)).fetchone()[0], "gm")
                self.assertEqual(conn.execute("SELECT count(*) FROM scene_events WHERE event_key=?", (f"scene-selection:{scene['id']}:req-sel-5",)).fetchone()[0], 0)

    def test_sessao_faltante(self):
        with TemporaryDirectory() as td:
            db = Path(td) / "sel.sqlite3"
            scene_play.init_scene_play(db)
            session_workspace.init_session_workspace(db)
            init_effects(db)
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute("INSERT OR REPLACE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','M','m.png','now')")
                conn.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','M','m.png',1,'now','now')")
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-6", campaign_id="omnisvera", title="C", location_name="L", created_by="master")
            with self.assertRaises(ValueError):
                scene_selection.open_selection(db, scene["id"], request_id="req-sel-6", element_ids=[], include_map=False)

    def test_combate_nao_permite_trocar_mapa_mesmo_mapa_ok(self):
        with TemporaryDirectory() as td:
            db = self._setup_db(td)
            scene, _ = scene_play.create_scene(db, request_id="scene-sel-7", campaign_id="omnisvera", title="C", location_name="L", created_by="master", map_id="map:arena")
            e1, _ = scene_play.create_element(db, scene_id=scene["id"], request_id="el-sel-7", element_type="clue", title="Pista A", status="hidden", visibility="gm", created_by="master", public_description="Desc A", private_description="Priv A")
            # start combat on different map
            with closing(sqlite3.connect(db)) as conn, conn:
                import json as _j
                encounter = {"active": True, "battle_mode": True, "map_id": "default", "participants": []}
                conn.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (_j.dumps(encounter),))
            with self.assertRaises(ValueError):
                scene_selection.open_selection(db, scene["id"], request_id="req-sel-7", element_ids=[e1["id"]], include_map=True)
            # clear combat, same map
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute("UPDATE combat_effect_clock SET encounter_json='{}' WHERE id=1")
            res = scene_selection.open_selection(db, scene["id"], request_id="req-sel-8", element_ids=[e1["id"]], include_map=True)
            self.assertEqual(res["map_id"], "map:arena")


if __name__ == "__main__":
    unittest.main()
