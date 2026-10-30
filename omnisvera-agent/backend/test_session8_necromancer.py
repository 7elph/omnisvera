"""Sessão 8: Necromante nv5, Toque Sombrio, Aterrorizar, testes difíceis, fogo 1d6."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.character_play import init_character_play, _connect, update_definition_overrides, load_definition_overrides
from app.combat import confirm_attack_resolution, init_combat
from app.combat_effects import apply_definition_effects, init_effects
from app.dice_rolls import init_dice_rolls, list_roll_requests
from app.session_workspace import init_session_workspace, save_workspace_token
from app.level_advancement import TABLES, XP_REQUIRED
from app.level_recalculation import recalculate
from app.session_workspace import init_session_workspace


def _definition(profile_id, class_name, level, con=10, intel=10, ba=0, jp=14, max_hp=10):
    return {"id": profile_id, "name": profile_id, "class_name": class_name, "level": level,
            "base_attributes": {"constitution": con, "intelligence": intel},
            "defenses": {"saving_throw": jp}, "progression": {"base_attack": ba, "base_maximum_hp": max_hp}}


class Session8TablesTests(TestCase):
    def test_level_five_tables_keep_campaign_scale(self):
        self.assertEqual((5, 15), TABLES["vezemir"][5])
        self.assertEqual((2, 13), TABLES["morthak"][5])
        self.assertEqual((2, 13), TABLES["dorn7"][5])
        self.assertEqual((2, 15), TABLES["raziel"][3])
        self.assertEqual((2, 14), TABLES["raziel"][4])
        self.assertEqual((2, 14), TABLES["raziel"][5])
        self.assertEqual(16000, XP_REQUIRED["vezemir"][5])
        self.assertEqual(20000, XP_REQUIRED["morthak"][5])
        self.assertEqual(20000, XP_REQUIRED["dorn7"][5])
        self.assertEqual(12000, XP_REQUIRED["raziel"][5])


class MorthakLevelFiveTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"; init_character_play(self.db)
        self.definition = _definition("morthak", "Mago", 3, con=10, intel=20, ba=1, jp=14, max_hp=10)
        with closing(_connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states VALUES(?,?,?,?)",
                       ("morthak", json.dumps({"maximum_hp": 10, "current_hp": 10, "resources": [
                           {"key": "magias_de_1o_circulo", "current": 4, "maximum": 4, "recharge": "inn_rest"},
                           {"key": "magias_de_2o_circulo", "current": 2, "maximum": 2, "recharge": "inn_rest"},
                           {"key": "misseis_magicos", "current": 4, "maximum": 4, "recharge": "inn_rest"},
                       ]}), 1, "test"))

    def edit(self, level):
        return update_definition_overrides(self.db, character_id="morthak", actor_id="master",
                                           fields={"level": level}, definition=self.definition)

    def test_advance_to_five_creates_two_pending_rolls_without_rolling(self):
        result = self.edit(5)
        self.assertEqual(5, result["level"])
        levels = sorted(p["level"] for p in result["pending_progression"])
        self.assertEqual([4, 5], levels)
        with closing(_connect(self.db)) as db:
            state = json.loads(db.execute("SELECT state_json FROM character_states").fetchone()[0])
            self.assertEqual(10, state["maximum_hp"])
            self.assertEqual(5, json.loads(db.execute(
                "SELECT data_json FROM character_definition_overrides").fetchone()[0])["level"])

    def test_level_five_grants_circles_spells_and_daily_uses(self):
        result = self.edit(5)
        self.assertEqual([4, 3, 2], [result["advancement_resources"][f"magias_de_{c}o_circulo"] for c in (1, 2, 3)])
        self.assertEqual("toque-sombrio", result["level_abilities"][0]["id"])
        self.assertEqual("aterrorizar", result["level_abilities"][1]["id"])
        self.assertEqual(1, result["advancement_resources"]["toque_sombrio"])
        self.assertEqual(1, result["advancement_resources"]["aterrorrizar"])
        with closing(_connect(self.db)) as db:
            resources = {r["key"]: r for r in json.loads(db.execute(
                "SELECT state_json FROM character_states").fetchone()[0])["resources"]}
        self.assertEqual(1, resources["toque_sombrio"]["current"])
        self.assertEqual(1, resources["aterrorrizar"]["current"])
        # Existing uses are never refilled by the level edit.
        self.assertEqual(4, resources["magias_de_1o_circulo"]["current"])

    def test_repeated_edit_does_not_duplicate_pending_rolls(self):
        self.edit(5)
        self.definition.update(level=5)
        result = self.edit(5)
        self.assertEqual(2, len(result["pending_progression"]))
        from app.dice_rolls import list_roll_requests
        self.assertEqual(2, len(list_roll_requests(self.db)))


class RazielContractTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"; init_character_play(self.db)
        self.definition = _definition("raziel", "Hemomante", 2, con=12, ba=1, jp=15, max_hp=16)
        with closing(_connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states VALUES(?,?,?,?)",
                       ("raziel", json.dumps({"maximum_hp": 16, "current_hp": 16, "resources": [
                           {"key": "reserva_de_sangue", "current": 10, "maximum": 10, "recharge": "inn_rest"}]}), 1, "test"))

    def test_table_contract_advances_without_invented_numbers(self):
        update_definition_overrides(self.db, character_id="raziel", actor_id="master", fields={
            "progression_contract": {"die": 8, "source": "Classes/Hemomante.md, tabela de mesa",
                                     "levels": {1: [1, 15], 2: [1, 15], 3: [2, 15], 4: [2, 14], 5: [2, 14]}}})
        result = update_definition_overrides(self.db, character_id="raziel", actor_id="master",
                                             fields={"level": 5}, definition=self.definition)
        self.assertEqual([3, 4, 5], sorted(p["level"] for p in result["pending_progression"]))
        self.assertNotIn("level_abilities", result)
        with closing(_connect(self.db)) as db:
            resources = json.loads(db.execute("SELECT state_json FROM character_states").fetchone()[0])["resources"]
        self.assertEqual(10, next(r for r in resources if r["key"] == "reserva_de_sangue")["maximum"])

    def test_invalid_contract_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Contrato"):
            update_definition_overrides(self.db, character_id="raziel", actor_id="master",
                                        fields={"progression_contract": {"die": 8, "levels": {}}})
        with self.assertRaisesRegex(ValueError, "Especialização"):
            update_definition_overrides(self.db, character_id="raziel", actor_id="master",
                                        fields={"specialization": "arquimago"})


class SpecializationFieldTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"; init_character_play(self.db)

    def test_necromancer_is_accepted_and_unknown_rejected(self):
        result = update_definition_overrides(self.db, character_id="morthak", actor_id="master",
                                             fields={"specialization": "necromante"})
        self.assertEqual("necromante", result["specialization"])
        with self.assertRaisesRegex(ValueError, "Especialização"):
            update_definition_overrides(self.db, character_id="vezemir", actor_id="master",
                                        fields={"specialization": "espadachim-do-amanhecer"})


class TouchRiderTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"
        init_character_play(self.db); init_effects(self.db)

    def test_rider_shape_and_save_record(self):
        from app.necromancer_spells import touch_rider
        victim = {"type": "token", "id": "t1", "name": "Alvo",
                  "defenses": {"saving_throw": 1}, "attributes": {"constitution": 10}}
        with closing(_connect(self.db)) as db:
            rider = touch_rider(db, victim)
        self.assertEqual({'dot_hp':True},rider)


class TouchConfirmTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"
        from app.session_ledger import init_session_ledger
        init_character_play(self.db); init_combat(self.db); init_effects(self.db)
        init_dice_rolls(self.db); init_session_workspace(self.db); init_session_ledger(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states VALUES(?,?,?,?)",
                       ("morthak", json.dumps({"maximum_hp": 10, "current_hp": 10, "resources": []}), 1, "t"))
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,current_hp,maximum_hp,sheet_json,created_at,updated_at)"
                       " VALUES(?,?,?,?,?,?,?,?,?)",
                       ("t1", "monster", "default", "Rato", 10, 10,
                        json.dumps({"armor_class": 10, "attributes": {"strength": 10}}), "t", "t"))

    def _insert_resolution(self, strength):
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        breakdown = {"strikes": [{"d20": 15}], "effects_version": 0, "effect_ids": [], "effects": [],
                     "resource_cost": None, "combat_turn": None, "attack_limit": 1,
                     "strength_drain": {"dot_hp":True},
                     "attack": {"weapon_item_path": "technique:toque-sombrio"}}
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='t1'",
                       (json.dumps({"armor_class": 10, "attributes": {"strength": strength}}),))
            db.execute("INSERT INTO combat_attack_resolutions(resolution_id,request_id,campaign_id,"
                       "actor_character_id,actor_name,requested_by_id,requested_by_role,attack_id,attack_name,"
                       "target_type,target_id,target_name,roll_mode,d20,attack_bonus,attack_total,target_ac,"
                       "result,damage_formula,damage_rolls_json,damage_modifier,damage_total,breakdown_json,"
                       "status,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       ("attack:test", "req-test", "omnisvera", "morthak", "Morthak", "morthak", "player",
                        "toque-sombrio", "Toque Sombrio", "token", "t1", "Rato", "digital", 15, 1, 16, 10,
                        "hit", "1d4", "[2]", 0, 2, json.dumps(breakdown), "pending", now.isoformat(),
                        (now.replace(year=now.year + 1)).isoformat()))

    def _effects(self):
        with closing(sqlite3.connect(self.db)) as db:
            return [json.loads(r[0]) for r in db.execute("SELECT data_json FROM combat_effects WHERE active=1")]

    def test_confirm_applies_hp_dot_without_changing_strength(self):
        self._insert_resolution(10)
        confirm_attack_resolution(self.db, resolution_id="attack:test",
                                  requested_by_id="morthak", requested_by_role="player")
        drains = [e for e in self._effects() if e.get("dot_hp")]
        self.assertEqual(1, len(drains))
        self.assertEqual({},drains[0]['modifiers'])

    def test_strength_one_no_longer_kills_target(self):
        self._insert_resolution(1)
        confirmed, applied = confirm_attack_resolution(self.db, resolution_id="attack:test",
                                                       requested_by_id="morthak", requested_by_role="player")
        self.assertTrue(applied)
        self.assertTrue(confirmed["breakdown"]["strength_drain"].get("dot_hp"))
        with closing(sqlite3.connect(self.db)) as db:
            hp = db.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='t1'").fetchone()[0]
        self.assertEqual(8, hp)


class AterrorizarTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"
        init_character_play(self.db); init_effects(self.db); init_session_workspace(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO character_definition_overrides VALUES(?,?,?)",
                       ("morthak", json.dumps({"specialization": "necromante", "level": 5}), "t"))
            db.execute("INSERT INTO character_states VALUES(?,?,?,?)",
                       ("morthak", json.dumps({"maximum_hp": 10, "current_hp": 10, "resources": [
                           {"key": "aterrorrizar", "label": "Aterrorizar", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                           {"key": "magias_de_1o_circulo", "label": "C1", "current": 1, "maximum": 4, "recharge": "inn_rest"}]}), 1, "t"))
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,current_hp,maximum_hp,sheet_json,created_at,updated_at)"
                       " VALUES(?,?,?,?,?,?,?,?,?)",
                       ("gob", "monster", "default", "Goblin", 5, 5,
                        json.dumps({"armor_class": 10, "hit_dice": 1, "attributes": {"wisdom": 10}, "saving_throw": 99}), "t", "t"))
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=1 WHERE id='gob'")

    def test_failed_save_terrifies_with_difficult_and_turns(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        with closing(sqlite3.connect(self.db)) as db:
            snapshot = effect_snapshot(db)
            result = command(db, snapshot, "necro_spell_cast",
                             {"spell_id": "aterrorizar",
                              "targets": [{"type": "token", "id": "gob", "distance_meters": 5, "dv": 1}],
                              "position_confirmed": True},
                             "2026-10-11T00:00:00+00:00", "morthak", "player")
        self.assertEqual("daily", result["cost_source"])
        self.assertEqual(0, result["resource_remaining"])
        effect = result["results"][0]["effect"]
        self.assertTrue(effect["difficult_tests"])
        self.assertGreaterEqual(effect["turns_remaining"], 6)
        self.assertLessEqual(effect["turns_remaining"], 11)

    def test_spent_daily_falls_back_to_memorized_slot(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        with closing(sqlite3.connect(self.db)) as db:
            snapshot = effect_snapshot(db)
            first = command(db, snapshot, "necro_spell_cast",
                            {"spell_id": "aterrorizar",
                             "targets": [{"type": "token", "id": "gob", "distance_meters": 5, "dv": 1}],
                             "position_confirmed": True},
                            "2026-10-11T00:00:00+00:00", "morthak", "player")
            self.assertEqual("daily", first["cost_source"])
            second = command(db, effect_snapshot(db), "necro_spell_cast",
                             {"spell_id": "aterrorizar",
                              "targets": [{"type": "token", "id": "gob", "distance_meters": 5, "dv": 1}],
                              "position_confirmed": True, "use_memorized": True},
                             "2026-10-11T00:00:01+00:00", "morthak", "player")
            self.assertEqual("memorized", second["cost_source"])
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            slot = next(r for r in state["resources"] if r["key"] == "magias_de_1o_circulo")
            self.assertEqual(0, slot["current"])

    def test_unknown_dv_is_skipped_not_invented(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,current_hp,maximum_hp,sheet_json,created_at,updated_at)"
                       " VALUES(?,?,?,?,?,?,?,?,?)",
                       ("unk", "monster", "default", "Coisa", 5, 5, "{}", "t", "t"))
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=1 WHERE id='unk'")
            snapshot = effect_snapshot(db)
            with self.assertRaisesRegex(ValueError,'DV'):
                command(db, snapshot, "necro_spell_cast",
                        {"spell_id": "aterrorizar",
                         "targets": [{"type": "token", "id": "unk", "distance_meters": 5}],
                         "position_confirmed": True},
                        "2026-10-11T00:00:00+00:00", "morthak", "player")

    def test_non_owner_is_rejected(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaises(PermissionError):
                command(db, effect_snapshot(db), "necro_spell_cast",
                        {"spell_id": "aterrorizar", "targets": [], "position_confirmed": True},
                        "2026-10-11T00:00:00+00:00", "vezemir", "player")


class GridAutoConfirmTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"
        init_character_play(self.db); init_effects(self.db); init_session_workspace(self.db)
        from app.dice_rolls import init_dice_rolls
        from app.session_ledger import init_session_ledger
        init_dice_rolls(self.db)
        init_session_ledger(self.db)
        from app.session_workspace import set_workspace_map
        from app.spatial_grid import configure_grid, init_spatial
        init_spatial(self.db)
        self.map = set_workspace_map(self.db, title="Arena", image_path="a.svg",
                                     visible_to_players=True)["id"]
        self.pin = save_workspace_token(self.db, token_type="character", name="Morthak",
                                        latitude=10, longitude=10, character_id="morthak",
                                        map_id=self.map)
        self.foe = save_workspace_token(self.db, token_type="monster", name="Rato",
                                        latitude=12, longitude=12, current_hp=5, maximum_hp=5,
                                        sheet={"armor_class": 10, "hit_dice": 1,
                                               "attributes": {"wisdom": 10},
                                               "saving_throw": 99},
                                        visible_to_players=True, map_id=self.map)
        configure_grid(self.db, actor_id="master", role="gm", request_id="grid-auto-1",
                       map_id=self.map, config=dict(cols=10, rows=10, cell_size_m=1.5))
        with closing(_connect(self.db)) as db, db:
            db.execute("INSERT INTO character_definition_overrides VALUES(?,?,?)",
                       ("morthak", json.dumps({"specialization": "necromante", "level": 5}), "t"))
            db.execute("INSERT INTO character_states VALUES(?,?,?,?)",
                       ("morthak", json.dumps({"maximum_hp": 10, "current_hp": 10, "resources": [
                           {"key": "aterrorrizar", "label": "Aterrorizar", "current": 1, "maximum": 1,
                            "recharge": "inn_rest"}]}), 1, "t"))

    def _cells(self, token_id):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute("SELECT cell_x,cell_y FROM session_workspace_entity_positions"
                              " WHERE map_id=? AND token_id=?", (self.map, token_id)).fetchone()

    def test_distance_autofill_skips_manual_checkbox(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        pin = self._cells(self.pin["id"])
        foe = self._cells(self.foe["id"])
        self.assertIsNotNone(pin)
        self.assertIsNotNone(foe)
        with closing(sqlite3.connect(self.db)) as db:
            snapshot = effect_snapshot(db)
            result = command(db, snapshot, "necro_spell_cast",
                             {"spell_id": "aterrorizar",
                              "targets": [{"type": "token", "id": self.foe["id"]}]},
                             "2026-10-12T00:00:00+00:00", "morthak", "player")
        self.assertEqual("grid", result["position"])
        self.assertEqual(0, result["resource_remaining"])

    def test_far_target_within_reach_auto_confirms(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command, grid_distance_m
        with closing(sqlite3.connect(self.db)) as db:
            far = grid_distance_m(db, "token", self.foe["id"])
        self.assertIsNotNone(far)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=9,cell_y=9"
                       " WHERE map_id=? AND token_id=?", (self.map, self.foe["id"]))
        with closing(sqlite3.connect(self.db)) as db:
            result = command(db, effect_snapshot(db), "necro_spell_cast",
                             {"spell_id": "aterrorizar", "targets": [{"type": "token", "id": self.foe["id"]}]},
                             "2026-10-12T00:00:00+00:00", "morthak", "player")
        self.assertEqual("grid", result["position"])

    def test_beyond_reach_still_needs_master(self):
        from app.combat_effects import effect_snapshot
        from app.necromancer_spells import command
        from app.spatial_grid import configure_grid
        configure_grid(self.db, actor_id="master", role="gm", request_id="grid-auto-large-1",
                       map_id=self.map, config=dict(cols=40, rows=40, cell_size_m=1.5),
                       expected_version=1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=39,cell_y=39"
                       " WHERE map_id=? AND token_id=?", (self.map, self.foe["id"]))
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaisesRegex(ValueError, "Alcance máximo"):
                command(db, effect_snapshot(db), "necro_spell_cast",
                        {"spell_id": "aterrorizar", "targets": [{"type": "token", "id": self.foe["id"]}]},
                        "2026-10-12T00:00:00+00:00", "morthak", "player")


class DifficultTestsTests(TestCase):
    def test_difficult_recomputes_attribute_modifiers(self):
        attrs = {"strength": 10, "dexterity": 8, "constitution": 10,
                 "intelligence": 10, "wisdom": 13, "charisma": 10}
        definition = {"attributes": dict(attrs), "base_attributes": dict(attrs),
                      "attribute_modifiers": {"strength": 0, "wisdom": 1},
                      "attacks": [], "defenses": {}}
        result = apply_definition_effects(definition, [{"id": "e1", "modifiers": {}, "difficult_tests": True}])
        # OD2 Difficult: -2 on the attribute value (SAB 13 -> 11).
        self.assertEqual(0, result["attribute_modifiers"]["wisdom"])
        self.assertEqual(-1, result["attribute_modifiers"]["strength"])
        self.assertEqual(["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
                         result["difficult_tests"]["attributes"])


class SpecializationApplyTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.db"
        init_character_play(self.db)
        from app.player_inventory import init_player_inventory
        init_player_inventory(self.db)
        self.definition = {"id": "vezemir", "name": "Vezemir", "class_name": "Guerreiro", "level": 5}
        with closing(_connect(self.db)) as db, db:
            db.execute("INSERT INTO character_definition_overrides VALUES(?,?,?)",
                       ("vezemir", json.dumps({"level": 5}), "t"))
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,notes,updated_at)"
                       " VALUES(?,?,?,?,?,?,?,?)",
                       ("vezemir", "Items/Grisalma.md", "Grisalma", 1, 1, "Corpo a corpo", "", "t"))

    def test_weapon_mastery_applies_with_weapon_and_is_idempotent(self):
        from app.character_play import choose_specialization, load_definition_overrides
        result = choose_specialization(self.db, character_id="vezemir", spec="guerreiro-arma",
                                       actor_id="vezemir", actor_role="player",
                                       weapon_item_path="Items/Grisalma.md", definition=self.definition)
        self.assertTrue(result["applied"])
        self.assertEqual(["maestria-em-arma"], result["abilities"])
        overrides = load_definition_overrides(self.db, "vezemir")
        self.assertEqual("guerreiro-arma", overrides["specialization"])
        self.assertEqual("Items/Grisalma.md", overrides["specialization_mastery"]["weapon_item_path"])
        again = choose_specialization(self.db, character_id="vezemir", spec="guerreiro-arma",
                                      actor_id="vezemir", actor_role="player",
                                      weapon_item_path="Items/Grisalma.md", definition=self.definition)
        self.assertFalse(again["applied"])

    def test_barbaro_paladino_and_locks(self):
        from app.character_play import choose_specialization
        result = choose_specialization(self.db, character_id="vezemir", spec="barbaro",
                                       actor_id="master", actor_role="gm", definition=self.definition)
        self.assertTrue(result["applied"])
        with self.assertRaisesRegex(ValueError, "ordeiro|alinhamento"):
            choose_specialization(self.db, character_id="vezemir", spec="paladino",
                                  actor_id="master", actor_role="gm", definition=self.definition)
        with self.assertRaisesRegex(ValueError, "incompatível"):
            choose_specialization(self.db, character_id="vezemir", spec="necromante",
                                  actor_id="master", actor_role="gm", definition=self.definition)
        dorn = {"id": "dorn7", "name": "Dorn", "class_name": "Mago", "level": 5}
        with self.assertRaisesRegex(ValueError, "reservada"):
            choose_specialization(self.db, character_id="dorn7", spec="necromante",
                                  actor_id="master", actor_role="gm", definition=dorn)
        with self.assertRaisesRegex(ValueError, "arma"):
            choose_specialization(self.db, character_id="vezemir", spec="guerreiro-arma",
                                  actor_id="master", actor_role="gm", definition=self.definition)


class SpecializationChoiceTests(TestCase):
    def test_valid_locked_and_clear_paths(self):
        from app.level_advancement import validate_specialization_choice
        self.assertEqual("necromante", validate_specialization_choice("morthak", "Mago", "necromante"))
        self.assertEqual("paladino", validate_specialization_choice("vezemir", "Guerreiro", "paladino"))
        self.assertIsNone(validate_specialization_choice("morthak", "Mago", None))
        self.assertIsNone(validate_specialization_choice("morthak", "Mago", "  "))
        with self.assertRaisesRegex(ValueError, "catálogo"):
            validate_specialization_choice("vezemir", "Guerreiro", "arquimago")
        with self.assertRaisesRegex(ValueError, "incompatível"):
            validate_specialization_choice("vezemir", "Guerreiro", "necromante")
        with self.assertRaisesRegex(ValueError, "reservada"):
            validate_specialization_choice("dorn7", "Mago", "necromante")


class DornDecompositionTests(TestCase):
    def test_base_plus_for_item_matches_table_total(self):
        from app.character_play import build_character_definition
        definition = build_character_definition(
            profile_id="dorn7",
            note={"title": "Dorn", "frontmatter": {}, "content": ""},
            sheet={"steps": [{"key": "attacks", "fields": {"melee_bonus": 2, "ranged_bonus": 2}}]},
            inventory=[{"item_path": "session-item:malha", "item_title": "Malha Rúnica",
                        "item_type": "arma", "quantity": 1, "equipped": True,
                        "equipment_slot": "Corpo a corpo", "damage_formula": "1d6+2",
                        "effect_rules": [{"id": "for", "trigger": "while_equipped", "kind": "attack_bonus",
                                          "target": "melee", "value": 2}]}],
            overrides={"advancement_base_attack": 2, "advancement_attack_delta": 0, "level": 5},
        )
        melee = next(a for a in definition["attacks"] if a["id"] == "melee")
        self.assertEqual(2, melee["base_attack_bonus"])
        self.assertEqual(4, melee["attack_bonus"])
        ranged = next(a for a in definition["attacks"] if a["id"] == "ranged")
        self.assertEqual(2, ranged["base_attack_bonus"])


class SkeletonFireTextTests(TestCase):
    def test_fire_weakness_is_1d6_without_bonus(self):
        import app.data  # noqa: F401  (package anchor)
        import json as _json
        from pathlib import Path as _Path
        catalog = _json.loads((_Path(__file__).parent / "app" / "data" / "session_abilities.json").read_text(encoding="utf-8"))
        levantar = next(a for a in catalog["characters"]["morthak"] if a["id"] == "levantar-um-esqueleto")
        self.assertIn("1d6, sem bônus", levantar["description"])
        self.assertNotIn("1d6+2", levantar["description"])
