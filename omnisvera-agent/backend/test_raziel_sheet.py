"""Ficha da Raziel ponta a ponta (Hemomante, com combate).

Lâmina (cargas + consumo), Mordida (alvo vivo, anti-suicídio, cura),
regeneração, técnicas bloqueadas, especializações vazias e isolamento.
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


def _state(hp=10, maximum=16):
    return {"current_hp": hp, "maximum_hp": maximum, "temporary_hp": 0, "conditions": [],
            "resources": [{"key": "reserva_de_sangue", "label": "Reserva", "current": 5, "maximum": 10,
                           "recharge": "inn_rest"}]}


class RazielSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "raziel_sheet.sqlite3"
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
                ("Characters/Individual/Raziel.md", "Raziel", "[]", "character", "[]", "{}",
                 "# Raziel", "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("raziel", json.dumps(_state()), "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("raziel", "Characters/Individual/Raziel.md", "Raziel", "approved",
                 json.dumps({"attributes": {"strength": 10, "dexterity": 14},
                             "character_class": {"level": 2, "class_name": "Hemomante"},
                             "attacks": {"melee_bonus": 1, "ranged_bonus": 1}}),
                 "2026-09-30T00:00:00+00:00"))
        self.ogre = save_workspace_token(self.db, token_type="monster", name="Ogro",
                                         latitude=10, longitude=10, current_hp=20, maximum_hp=20,
                                         sheet={"armor_class": 10}, visible_to_players=True)
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="raziel")
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

    def _reserva(self):
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
        return next(r for r in state["resources"] if r["key"] == "reserva_de_sangue")["current"]

    def test_sheet_loads_with_blood_and_techniques(self):
        response = self.client.get("/characters/raziel")
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertEqual(5, next(r["current"] for r in body["state"]["resources"]
                                 if r["key"] == "reserva_de_sangue"))

    def test_level_five_bite_and_full_blood_reserve(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO character_definition_overrides VALUES('raziel',?,?)",(json.dumps({'level':5}),'fixture'))
            state=_state();state['resources'][0].update(current=10,maximum=10)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        sheet=self.client.get('/characters/raziel').json()
        from app.vampire_powers import bite_definition
        self.assertEqual('1d6',bite_definition(sheet['definition'])['attacks'][0]['damage'])
        response=self.client.post('/characters/raziel/techniques/lamina-de-sangue',json={'request_id':'full-reserve-001','charges':10,'target_type':'token','target_id':self.ogre['id'],'roll_mode':'digital'})
        self.assertEqual(200,response.status_code,response.text)
        self.assertEqual('10d4',response.json()['damage_formula'])

    def test_animal_profile_is_shown_and_damage_returns_with_overflow(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            state=_state();state['resources'].append({'key':'forma_da_noite','current':3,'maximum':3,'recharge':'inn_rest','label':'Forma'})
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        apply_character_action(self.db,character_id='raziel',actor_id='raziel',actor_role='player',action='consume_resource',payload={'resource_key':'forma_da_noite','amount':1,'animal':'corvo'},request_id='animal-first-001')
        sheet=self.client.get('/characters/raziel').json()
        self.assertEqual((1,1,10),(sheet['state']['current_hp'],sheet['state']['maximum_hp'],sheet['state']['normal_current_hp']))
        self.assertEqual((14,4),(sheet['definition']['defenses']['armor_class'],sheet['definition']['defenses']['saving_throw']))
        self.assertEqual([],sheet['definition']['attacks'])
        denied=self.client.post('/characters/raziel/techniques/lamina-de-sangue',json={'charges':1,'target_type':'token','target_id':self.ogre['id']})
        self.assertEqual(400,denied.status_code)
        result=apply_character_action(self.db,character_id='raziel',actor_id='master',actor_role='gm',action='damage',payload={'amount':5},request_id='animal-hit-001')
        self.assertTrue(result['night_form_returned']);self.assertEqual(4,result['overflow_damage'])
        apply_character_action(self.db,character_id='raziel',actor_id='master',actor_role='gm',action='damage',payload={'amount':5},request_id='animal-hit-001')
        normal=self.client.get('/characters/raziel').json()['state']
        self.assertEqual(6,normal['current_hp']);self.assertNotIn('animal_form',normal)

    def test_lamina_consumes_declared_charges(self):
        response = self.client.post("/characters/raziel/techniques/lamina-de-sangue",
                                    json={"request_id": "sheet-lam-1", "charges": 2,
                                          "target_type": "token", "target_id": self.ogre["id"],
                                          "roll_mode": "physical", "d20": 18})
        self.assertEqual(200, response.status_code, response.text)
        resolution = response.json()
        confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, confirm.status_code, confirm.text)
        self.assertEqual(3, self._reserva())

    def test_lamina_rejects_bad_charges(self):
        for charges, request_id in ((0, "sheet-lam-z"), (6, "sheet-lam-s")):
            response = self.client.post("/characters/raziel/techniques/lamina-de-sangue",
                                        json={"request_id": request_id, "charges": charges,
                                              "target_type": "token", "target_id": self.ogre["id"],
                                              "roll_mode": "physical", "d20": 18})
            self.assertIn(response.status_code, (400, 409, 422))
        self.assertEqual(5, self._reserva())

    def test_mordida_hits_live_target_and_heals(self):
        response = self.client.post("/characters/raziel/techniques/mordida",
                                    json={"request_id": "sheet-mor-1", "target_type": "token",
                                          "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 18})
        self.assertEqual(200, response.status_code, response.text)
        resolution = response.json()
        confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, confirm.status_code, confirm.text)
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
        self.assertGreater(state["current_hp"], 10)

    def test_mordida_rejects_dead_target_and_self(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?",
                               (self.ogre["id"],))
        dead = self.client.post("/characters/raziel/techniques/mordida",
                                json={"request_id": "sheet-mor-d", "target_type": "token",
                                      "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 18})
        self.assertIn(dead.status_code, (400, 409))
        own = self.client.post("/characters/raziel/techniques/mordida",
                               json={"request_id": "sheet-mor-s", "target_type": "character",
                                     "target_id": "raziel", "roll_mode": "physical", "d20": 18})
        self.assertIn(own.status_code, (400, 409))

    def test_regeneracao_spends_blood(self):
        response = self.client.post("/characters/raziel/techniques/regeneracao-vampirica",
                                    json={"request_id": "sheet-reg-1"})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(4, self._reserva())

    def test_garras_investida_and_arma_consume_blood(self):
        for technique, request_id, cost, damage in (("garras-predatorias", "sheet-gar-1", 1, "1d6"),
                                                    ("investida-predatoria", "sheet-inv-1", 1, "2d4"),
                                                    ("arma-de-sangue", "sheet-arm-1", 1, "1d8")):
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("UPDATE character_states SET state_json=?",
                                   (json.dumps(_state()),))
            response = self.client.post(f"/characters/raziel/techniques/{technique}",
                                        json={"request_id": request_id, "target_type": "token",
                                              "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 18})
            self.assertEqual(200, response.status_code, response.text)
            resolution = response.json()
            self.assertEqual(damage, (resolution.get("breakdown") or {}).get("damage_formula")
                             or resolution.get("damage_formula"), technique)
            confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
            self.assertEqual(200, confirm.status_code, confirm.text)
            self.assertEqual(5 - cost, self._reserva(), technique)

    def test_faro_adds_plus_one_vs_wounded(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=10 WHERE id=?",
                               (self.ogre["id"],))
        response = self.client.post("/characters/raziel/techniques/garras-predatorias",
                                    json={"request_id": "sheet-far-1", "target_type": "token",
                                          "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 10})
        self.assertEqual(200, response.status_code, response.text)
        self.assertIn("+1 Faro", response.json().get("attack_name", ""))

    def test_sangue_defensivo_shields(self):
        response = self.client.post("/characters/raziel/techniques/sangue-defensivo",
                                    json={"request_id": "sheet-esc-1"})
        self.assertEqual(200, response.status_code, response.text)
        with closing(sqlite3.connect(self.db)) as connection:
            effects = [json.loads(row[0]) for row in connection.execute(
                "SELECT data_json FROM combat_effects WHERE active=1").fetchall()]
        shields = [e for e in effects if (e.get("modifiers") or {}).get("armor_class_bonus") == 2]
        self.assertEqual(1, len(shields))
        self.assertEqual(4, self._reserva())

    def test_blocked_technique_stays_locked(self):
        response = self.client.post("/characters/raziel/techniques/marca-rubra-aprimorada",
                                    json={"request_id": "sheet-blq-1"})
        self.assertNotEqual(200, response.status_code)

    def test_no_specializations_for_hemomante(self):
        options = self.client.get("/characters/raziel/specializations")
        self.assertEqual(200, options.status_code, options.text)
        self.assertEqual([], options.json()["options"])

    def test_other_profile_cannot_drink(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="varkh")
        try:
            response = self.client.post("/characters/raziel/techniques/mordida",
                                        json={"request_id": "sheet-mor-x", "target_type": "token",
                                              "target_id": self.ogre["id"], "roll_mode": "physical", "d20": 18})
        finally:
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="raziel")
        self.assertEqual(403, response.status_code)

    def test_rest_refills_reserve(self):
        self.client.post("/characters/raziel/techniques/regeneracao-vampirica",
                         json={"request_id": "sheet-reg-r"})
        apply_character_action(self.db, character_id="raziel", actor_id="master", actor_role="gm",
                               action="rest_at_inn", payload={}, reason="descanso geral")
        self.assertEqual(10, self._reserva())


if __name__ == "__main__":
    unittest.main()
