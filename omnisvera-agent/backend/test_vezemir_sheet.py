"""Ficha do Vezemir ponta a ponta (modo combate incluído).

Cobre cada área da ficha via HTTP com perfil de jogador: identidade,
ataques corpo a corpo e à distância (acerto/erro, idempotência),
Força Arcana e Velocidade (uso único diário + descanso), movimento de pin,
orçamento de turno, especialização e isolamento entre perfis.
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
from app.combat import init_combat, resolve_attack
from app.combat_effects import effect_command, effect_snapshot, init_effects
from app.dice_rolls import init_dice_rolls
from app.player_inventory import init_player_inventory
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token
from app.vault_index import init_db as init_vault_index


def _state(hp=27, current=27):
    return {"current_hp": current, "maximum_hp": hp, "temporary_hp": 0, "conditions": [],
            "resources": [{"key": "forca_arcana", "label": "Força Arcana", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                          {"key": "velocidade", "label": "Velocidade", "current": 1, "maximum": 1, "recharge": "inn_rest"}]}


INVENTORY = [{"item_path": "Items/Grisalma.md", "item_title": "Grisalma", "item_type": "Arma",
              "quantity": 1, "equipped": True, "equipment_slot": "Corpo a corpo", "damage_formula": "1d6+2"}]
WEAPON_PATH = "session-item:1"


class VezemirSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "vezemir_sheet.sqlite3"
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
                ("Characters/Individual/Vezemir.md", "Vezemir", "[]", "character", "[]", "{}",
                 "# Vezemir", "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("vezemir", json.dumps(_state()), "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("vezemir", "Characters/Individual/Vezemir.md", "Vezemir", "approved",
                 json.dumps({"attributes": {"strength": 14, "dexterity": 12}, "character_class": {"level": 5, "class_name": "Guerreiro"},
                             "attacks": {"melee_bonus": 5, "ranged_bonus": 2}}),
                 "2026-09-30T00:00:00+00:00"))
            for row in INVENTORY:
                connection.execute(
                    "INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,notes,updated_at)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                     ("vezemir", WEAPON_PATH if row["item_path"] == "Items/Grisalma.md" else row["item_path"],
                      row["item_title"], 1, 1, row["equipment_slot"], "", "2026-09-30T00:00:00+00:00"))
        from app.session_workspace import save_session_item
        save_session_item(self.db, name="Grisalma", item_type="arma",
                          description="Espada 1d6+2.", effects=[], effect_rules=[],
                          mechanics={"equipment_slots": ["Corpo a corpo"], "damage_formula": "1d6+2"},
                          usable=False)
        self.ogre = save_workspace_token(self.db, token_type="monster", name="Ogro",
                                         latitude=10, longitude=10, current_hp=20, maximum_hp=20,
                                         sheet={"armor_class": 10}, visible_to_players=True)
        self.pc_token = save_workspace_token(self.db, token_type="character", name="Vezemir",
                                             latitude=11, longitude=11, character_id="vezemir",
                                             current_hp=27, maximum_hp=27)
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
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

    def _target(self):
        return {"type": "token", "id": self.ogre["id"], "armor_class": 10, "current_hp": 20}

    def _definition(self):
        return {"id": "melee", "attacks": [{"id": "melee", "name": "Espada", "attack_bonus": 7, "damage": "1d6+2",
                                            "weapon_item_path": "Items/Grisalma.md"}]}

    def _start_encounter(self):
        with closing(sqlite3.connect(self.db)) as connection:
            version = effect_snapshot(connection)["version"]
        return effect_command(self.db, actor_id="master", actor_role="gm", request_id="sheet-enc-1",
                              expected_version=version, action="start",
                              payload={"participants": [
                                  {"target_type": "character", "target_id": "vezemir", "initiative": 15},
                                  {"target_type": "token", "target_id": self.ogre["id"], "initiative": 5}]})

    # -- identidade e recursos -------------------------------------------------
    def test_sheet_loads_with_hp_resources_and_attacks(self):
        response = self.client.get("/characters/vezemir")
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertEqual(27, body["state"]["current_hp"])
        keys = {r["key"] for r in body["state"]["resources"]}
        self.assertIn("forca_arcana", keys)
        self.assertIn("velocidade", keys)
        ids = {a["id"] for a in body["definition"]["attacks"]}
        self.assertIn("melee", ids)

    # -- ataques ----------------------------------------------------------------
    def test_melee_hit_confirms_once_and_damages(self):
        resolution, created = resolve_attack(
            self.db, request_id="sheet-hit-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="vezemir", requested_by_role="player", definition=self._definition(),
            inventory=INVENTORY, attack_id="melee",
            target=self._target(), roll_mode="physical", physical_d20=18)
        self.assertTrue(created)
        first = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, first.status_code, first.text)
        after = first.json()
        self.assertTrue(after["confirmed"])
        with closing(sqlite3.connect(self.db)) as connection:
            hp = connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                                    (self.ogre["id"],)).fetchone()[0]
        self.assertLess(hp, 20)
        again = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, again.status_code)
        with closing(sqlite3.connect(self.db)) as connection:
            same = connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                                      (self.ogre["id"],)).fetchone()[0]
        self.assertEqual(hp, same)

    def test_melee_miss_applies_no_damage(self):
        resolution, _ = resolve_attack(
            self.db, request_id="sheet-miss-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="vezemir", requested_by_role="player", definition=self._definition(),
            inventory=INVENTORY, attack_id="melee",
            target=self._target(), roll_mode="physical", physical_d20=1)
        response = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, response.status_code, response.text)
        with closing(sqlite3.connect(self.db)) as connection:
            hp = connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                                    (self.ogre["id"],)).fetchone()[0]
        self.assertEqual(20, hp)

    def test_confirm_other_players_resolution_is_rejected(self):
        resolution, _ = resolve_attack(
            self.db, request_id="sheet-other-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="vezemir", requested_by_role="player", definition=self._definition(),
            inventory=INVENTORY, attack_id="melee",
            target=self._target(), roll_mode="physical", physical_d20=18)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="varkh")
        try:
            response = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        finally:
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.assertEqual(403, response.status_code)

    # -- técnicas -----------------------------------------------------------------
    def test_forca_arcana_once_per_day_then_rest_refills(self):
        first = self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        self.assertEqual(200, first.status_code, first.text)
        second = self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        self.assertIn(second.status_code, (400, 409))
        apply_character_action(self.db, character_id="vezemir", actor_id="master", actor_role="gm",
                               action="rest_at_inn", payload={}, reason="descanso geral")
        third = self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        self.assertEqual(200, third.status_code, third.text)

    def test_velocidade_and_forca_stack_as_separate_effects(self):
        self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        response = self.client.post("/characters/vezemir/techniques/velocidade", json={})
        self.assertEqual(200, response.status_code, response.text)
        effects = self.client.get("/combat/effects").json()
        sources = {e["source"] for e in effects["effects"] if e["target_id"] == "vezemir"}
        self.assertIn("Força Arcana (Vezemir)", sources)
        self.assertIn("Velocidade (Vezemir)", sources)

    # -- turno e movimento ------------------------------------------------------------
    def test_turn_budget_owner_passes_stranger_fails(self):
        snap = self._start_encounter()
        mine = self.client.post("/combat/next-turn", json={"request_id": "sheet-nt-1",
                                                            "expected_version": snap["version"],
                                                            "action": "next_turn", "payload": {}})
        self.assertEqual(200, mine.status_code, mine.text)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="varkh")
        try:
            other = self.client.post("/combat/next-turn", json={"request_id": "sheet-nt-2",
                                                                 "expected_version": mine.json()["version"],
                                                                 "action": "next_turn", "payload": {}})
        finally:
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.assertIn(other.status_code, (400, 403))

    def test_move_own_pin_ok_monster_rejected(self):
        own = self.client.patch(f"/gm/workspace/tokens/{self.pc_token['id']}/position",
                                json={"latitude": 20, "longitude": 20})
        self.assertEqual(200, own.status_code)
        monster = self.client.patch(f"/gm/workspace/tokens/{self.ogre['id']}/position",
                                    json={"latitude": 20, "longitude": 20})
        self.assertEqual(403, monster.status_code)

    # -- especialização ----------------------------------------------------------------
    def test_specialization_options_and_weapon_mastery(self):
        options = self.client.get("/characters/vezemir/specializations")
        self.assertEqual(200, options.status_code, options.text)
        by_id = {o["id"]: o for o in options.json()["options"]}
        self.assertTrue(by_id["guerreiro-arma"]["eligible"])
        self.assertFalse(by_id["paladino"]["eligible"])
        choose = self.client.post("/characters/vezemir/specialization",
                                  json={"specialization": "guerreiro-arma",
                                        "weapon_item_path": WEAPON_PATH})
        self.assertEqual(200, choose.status_code, choose.text)
        self.assertTrue(choose.json()["applied"])
        sheet = self.client.get("/characters/vezemir").json()
        melee = next(a for a in sheet["definition"]["attacks"] if a["id"] == "melee")
        self.assertEqual(7, melee["base_attack_bonus"])  # nível 5 + modificador FOR +2
        self.assertEqual(8, melee["attack_bonus"])  # fixture sem melhoria; maestria +1
        mastery=next(a for a in sheet['definition']['session_abilities'] if a['id']=='maestria-em-arma')
        self.assertIn('+1 no ataque e +1 no dano',mastery['description'])
        self.assertFalse(mastery['active'])

    # -- isolamento ----------------------------------------------------------------------
    def test_other_profile_cannot_use_vezemir_technique(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="varkh")
        try:
            response = self.client.post("/characters/vezemir/techniques/forca-arcana", json={})
        finally:
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.assertEqual(403, response.status_code)


if __name__ == "__main__":
    unittest.main()
