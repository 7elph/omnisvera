"""Ficha do Morthak ponta a ponta (Necromante nv5, com combate).

Mísseis, Toque Sombrio (rider + dreno), Aterrorizar (uso diário e
memorizada), invocação sobre cadáver, especialização travada e isolamento.
"""
from __future__ import annotations

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
from app.access import AccessContext
from app.character_play import apply_character_action, init_character_play
from app.character_creation import init_character_creation
from app.combat import init_combat
from app.combat_effects import init_effects
from app.dice_rolls import init_dice_rolls
from app.player_inventory import init_player_inventory
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token
from app.vault_index import init_db as init_vault_index


def _state():
    return {"current_hp": 10, "maximum_hp": 10, "temporary_hp": 0, "conditions": [],
            "resources": [{"key": "misseis_magicos", "label": "Mísseis", "current": 4, "maximum": 4, "recharge": "inn_rest"},
                          {"key": "magias_de_1o_circulo", "label": "C1", "current": 4, "maximum": 4, "recharge": "inn_rest"},
                          {"key": "toque_sombrio", "label": "Toque", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                          {"key": "aterrorrizar", "label": "Ater", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                          {"key": "levantar_um_esqueleto", "label": "Lev", "current": 1, "maximum": 1, "recharge": "inn_rest"}]}


class MorthakSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "morthak_sheet.sqlite3"
        init_character_play(self.db)
        init_character_creation(self.db)
        init_combat(self.db)
        init_effects(self.db)
        init_dice_rolls(self.db)
        init_player_inventory(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        init_vault_index(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Morthak.md", "Morthak", "[]", "character", "[]", "{}",
                 "# Morthak", "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("morthak", json.dumps(_state()), "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("morthak", "Characters/Individual/Morthak.md", "Morthak", "approved",
                 json.dumps({"attributes": {"intelligence": 20, "constitution": 10},
                             "character_class": {"level": 5, "class_name": "Mago"},
                             "attacks": {"melee_bonus": 2, "ranged_bonus": 2}}),
                 "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES(?,?,?)",
                ("morthak", json.dumps({"level": 5, "specialization": "necromante"}), "2026-09-30T00:00:00+00:00"))
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at)"
                               " VALUES(1,'default','Arena','','fixture')")
        self.ogre = save_workspace_token(self.db, token_type="monster", name="Ogro",
                                         latitude=10, longitude=10, current_hp=20, maximum_hp=20,
                                         sheet={"armor_class": 10, "saving_throw": 99, "hit_dice": 1,
                                                "attributes": {"constitution": 10, "wisdom": 10, "strength": 10}},
                                         visible_to_players=True)
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="morthak")
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        import gc as _gc
        import time as _time
        try:
            self.client.close()
        finally:
            main.app.dependency_overrides.clear()
            self._patcher.stop()
            _gc.collect()
            last_error = None
            for _ in range(25):
                try:
                    self.temporary.cleanup()
                    last_error = None
                    break
                except PermissionError as error:
                    last_error = error
                    _time.sleep(0.2)
            if last_error is not None:
                raise last_error

    def _resources(self):
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
        return {r["key"]: r for r in state["resources"]}

    def test_sheet_loads_with_necromancer_resources(self):
        response = self.client.get("/characters/morthak")
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertEqual(10, body["state"]["current_hp"])
        self.assertIn("toque_sombrio", {r["key"] for r in body["state"]["resources"]})
        self.assertIn("aterrorrizar", {r["key"] for r in body["state"]["resources"]})

    def test_misseis_hit_and_consume(self):
        response = self.client.post("/characters/morthak/attacks/resolve",
                                    json={"request_id": "sheet-mis-1", "attack_id": "misseis-magicos",
                                          "target_type": "token", "target_id": self.ogre["id"],
                                          "roll_mode": "digital"})
        self.assertEqual(200, response.status_code, response.text)
        resolution = response.json()
        confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, confirm.status_code, confirm.text)
        with closing(sqlite3.connect(self.db)) as connection:
            hp = connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                                    (self.ogre["id"],)).fetchone()[0]
        self.assertLess(hp, 20)
        self.assertLess(self._resources()["misseis_magicos"]["current"], 4)

    def test_toque_resolves_with_rider_and_confirms(self):
        response = self.client.post("/characters/morthak/techniques/toque-sombrio",
                                    json={"request_id": "sheet-toq-1", "target_type": "token",
                                          "target_id": self.ogre["id"], "position_confirmed": True,
                                          "roll_mode": "physical", "d20": 18})
        self.assertEqual(200, response.status_code, response.text)
        resolution = response.json()
        rider = (resolution.get("breakdown") or {}).get("strength_drain") or {}
        self.assertEqual({'dot_hp':True},rider)
        confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, confirm.status_code, confirm.text)
        if rider.get("dot_hp"):
            with closing(sqlite3.connect(self.db)) as connection:
                drains = [json.loads(row[0]) for row in connection.execute(
                    "SELECT data_json FROM combat_effects WHERE active=1").fetchall()]
            self.assertTrue(any(e.get("dot_hp") for e in drains))
        self.assertEqual(0, self._resources()["toque_sombrio"]["current"])

    def test_automatic_touch_confirms_once_and_replays_after_target_death(self):
        from app.spatial_grid import init_spatial
        init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Arena','fixture.svg',1,'now','now')")
            db.execute("INSERT INTO session_workspace_map_grids VALUES('default','square',20,20,1.5,0,0,'chebyshev',1,1)")
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(self.ogre['id'],))
        mine=save_workspace_token(self.db,token_type='character',character_id='morthak',name='Morthak',latitude=10,longitude=10,visible_to_players=True)
        with closing(sqlite3.connect(self.db)) as db,db:
            for identity,x in [(mine['id'],1),(self.ogre['id'],2)]:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,1,1,1,1)",(identity,x))
        body={'request_id':'automatic-touch-api-once','target_type':'token','target_id':self.ogre['id'],'mode':'automatic','roll_mode':'physical','d20':18}
        first=self.client.post('/characters/morthak/techniques/toque-sombrio',json=body)
        self.assertEqual(200,first.status_code,first.text)
        self.assertEqual('confirmed',first.json()['status']);self.assertEqual(0,first.json()['hp_after'])
        again=self.client.post('/characters/morthak/techniques/toque-sombrio',json=body)
        self.assertEqual(200,again.status_code,again.text)
        self.assertEqual(first.json()['resolution_id'],again.json()['resolution_id'])
        self.assertEqual(0,self._resources()['toque_sombrio']['current'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute("SELECT count(*) FROM combat_attack_resolutions WHERE request_id=?",(body['request_id'],)).fetchone()[0])

    def test_manual_confirmation_cannot_bypass_persisted_touch_grid(self):
        from app.spatial_grid import init_spatial
        init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Arena','fixture.svg',1,'now','now')")
            db.execute("INSERT INTO session_workspace_map_grids VALUES('default','square',20,20,1.5,0,0,'chebyshev',1,1)")
        mine=save_workspace_token(self.db,token_type='character',character_id='morthak',name='Morthak',latitude=10,longitude=10,visible_to_players=True)
        with closing(sqlite3.connect(self.db)) as db,db:
            for identity,x in [(mine['id'],1),(self.ogre['id'],5)]:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,1,1,1,1)",(identity,x))
        response=self.client.post('/characters/morthak/techniques/toque-sombrio',json={'request_id':'manual-cannot-bypass-grid','target_type':'token','target_id':self.ogre['id'],'position_confirmed':True,'roll_mode':'physical','d20':18})
        self.assertEqual(400,response.status_code,response.text)
        self.assertIn('alcance',response.text)
        self.assertEqual(1,self._resources()['toque_sombrio']['current'])

    def test_aterrorizar_daily_then_memorized(self):
        body = {"request_id": "sheet-ate-1", "target_type": "token", "target_id": self.ogre["id"],
                "position_confirmed": True, "target_distance": 5, "target_dv": 1}
        assert True
        first = self.client.post("/characters/morthak/techniques/aterrorizar", json=body)
        self.assertEqual(200, first.status_code, first.text)
        payload = first.json()
        results = (payload.get("protocol_result") or {}).get("results") or []
        self.assertTrue(any(r.get("effect") for r in results), first.text[:400])
        with closing(sqlite3.connect(self.db)) as connection:
            stored = [json.loads(row[0]) for row in connection.execute(
                "SELECT data_json FROM combat_effects WHERE active=1").fetchall()]
        terrors = [e for e in stored if e.get("difficult_tests")]
        self.assertEqual(1, len(terrors))
        self.assertGreaterEqual(terrors[0]["turns_remaining"], 6)
        self.assertEqual(0, self._resources()["aterrorrizar"]["current"])
        again = self.client.post("/characters/morthak/techniques/aterrorizar",
                                 json={**body, "request_id": "sheet-ate-2"})
        self.assertIn(again.status_code, (400, 409))
        extra = self.client.post("/characters/morthak/techniques/aterrorizar",
                                 json={**body, "request_id": "sheet-ate-3", "use_memorized": True})
        self.assertEqual(200, extra.status_code, extra.text)
        self.assertEqual(3, self._resources()["magias_de_1o_circulo"]["current"])

    def test_levatar_summons_and_animar_needs_authorized_corpse(self):
        raised = self.client.post("/characters/morthak/techniques/levantar-esqueleto",
                                  json={"request_id": "sheet-lev-1", "target_type": "token",
                                        "target_id": self.ogre["id"]})
        self.assertEqual(200, raised.status_code, raised.text)
        self.assertEqual(0, self._resources()["levantar_um_esqueleto"]["current"])
        with closing(sqlite3.connect(self.db)) as connection:
            names = [row[0] for row in connection.execute(
                "SELECT name FROM session_workspace_tokens").fetchall()]
        self.assertTrue(any("squeleto" in name.lower() or "esqueleto" in name.lower() for name in names), names)
        alive = self.client.post("/characters/morthak/techniques/animar-mortos",
                                 json={"request_id": "sheet-ani-1", "target_type": "token",
                                       "target_id": self.ogre["id"]})
        self.assertIn(alive.status_code, (400, 409))
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=0, sheet_json=? WHERE id=?",
                               (json.dumps({"armor_class": 10, "reanimation_allowed": True}), self.ogre["id"]))

    def test_specialization_locked_and_listed(self):
        options = self.client.get("/characters/morthak/specializations")
        self.assertEqual(200, options.status_code, options.text)
        body = options.json()
        self.assertEqual("necromante", body["current"])
        self.assertTrue(any(o["id"] == "necromante" and o["current"] for o in body["options"]))

    def test_owner_and_master_can_read_current_necromancer_perks_and_restrictions(self):
        owner = self.client.get('/characters/morthak/specializations').json()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='gm')
        master = self.client.get('/characters/morthak/specializations').json()
        self.assertEqual(owner, master)
        option = next(o for o in owner['options'] if o['id'] == 'necromante')
        self.assertTrue(option['benefits'], 'Necromancer benefits cannot be an empty catalogue')
        text = ' '.join(option['benefits'])
        self.assertIn('Toque Sombrio', text)
        self.assertIn('Aterrorizar', text)
        self.assertTrue(any('7º' in r for r in option['restrictions']))
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='varkh')
        self.assertEqual(403, self.client.get('/characters/morthak/specializations').status_code)

    def test_other_profile_cannot_cast(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="varkh")
        try:
            response = self.client.post("/characters/morthak/techniques/toque-sombrio",
                                        json={"request_id": "sheet-toq-x", "target_type": "token",
                                              "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 18})
        finally:
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="morthak")
        self.assertEqual(403, response.status_code)

    def test_rest_refills_daily(self):
        self.client.post("/characters/morthak/techniques/aterrorizar",
                         json={"request_id": "sheet-ate-r", "target_type": "token",
                               "target_id": self.ogre["id"], "position_confirmed": True,
                               "target_distance": 5, "target_dv": 1})
        apply_character_action(self.db, character_id="morthak", actor_id="master", actor_role="gm",
                               action="rest_at_inn", payload={}, reason="descanso geral")
        self.assertEqual(1, self._resources()["aterrorrizar"]["current"])


if __name__ == "__main__":
    unittest.main()
