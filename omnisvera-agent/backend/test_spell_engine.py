from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.spell_engine import cast_spell, derive_spell_mechanic, execute_token_action
from app.spell_catalog import get_catalog_spell


class SpellEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "engine.db"
        from app.character_play import init_character_play
        from app.character_creation import init_character_creation
        from app.dice_rolls import init_dice_rolls
        from app.session_workspace import init_session_workspace
        from app.session_ledger import init_session_ledger
        init_character_play(self.db)
        init_character_creation(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                (json.dumps({"current_hp": 30, "maximum_hp": 30, "copper_coins": 0, "silver_coins": 0,
                             "coins": 0, "platinum_coins": 0}),))
            connection.execute(
                "INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at)"
                " VALUES('vezemir', 'p', 'Vezemir', ?, 'now')",
                (json.dumps({"attributes": {"dexterity": 14, "constitution": 12, "wisdom": 10},
                             "character_class": {"saving_throw": 14}}),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir', '{\"level\":1}', 'now')")
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('gob1', 'monster', 'Goblin', 12, 12, ?, 'now', 'now')",
                (json.dumps({"saving_throw": 10,"spellcaster_level":1, "attacks": [{"name": "Adaga", "damage": "1d4", "bonus": 2}],
                             "abilities": ["Baforada de teste: 1 vez por combate, 6 metros, 2d6 de dano, JPD reduz"]}),))

    def hp(self, character_id: str = "vezemir") -> int:
        with closing(sqlite3.connect(self.db)) as connection:
            return int(json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id=?", (character_id,)).fetchone()[0])["current_hp"])

    def token_hp(self, token_id: str = "gob1") -> int:
        with closing(sqlite3.connect(self.db)) as connection:
            return int(connection.execute(
                "SELECT current_hp FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()[0])

    def test_fireball_mechanic_comes_from_text(self) -> None:
        spell = get_catalog_spell("arcana-bola-de-fogo")
        assert spell is not None
        mechanic = derive_spell_mechanic(spell)
        self.assertEqual(mechanic["save"], "JPD")
        self.assertEqual(mechanic["save_effect"], "halves")

    def test_generic_fireball_uses_explicit_caster_level_and_range(self):
        from app.spell_engine import scaled_spell_mechanic
        self.assertEqual(scaled_spell_mechanic(get_catalog_spell('arcana-bola-de-fogo'),5)['range_m'],60)
        self.assertEqual(scaled_spell_mechanic(get_catalog_spell('arcana-bola-de-fogo'),15)['damage'],'10d6')
        with closing(sqlite3.connect(self.db)) as connection,connection:
            sheet=json.loads(connection.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0])
            sheet['spellcaster_level']=5
            connection.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",(json.dumps(sheet),))
        result=cast_spell(self.db,spell_id='arcana-bola-de-fogo',caster_type='token',caster_id='gob1',targets=[{'type':'character','id':'vezemir'}],roll_mode='physical',d20=[20])
        self.assertEqual(result['mechanic']['damage'],'5d6')

    def test_unknown_caster_level_cannot_silently_cast_level_one_damage(self):
        with closing(sqlite3.connect(self.db)) as connection,connection:
            sheet=json.loads(connection.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0])
            sheet.pop('spellcaster_level',None)
            connection.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",(json.dumps(sheet),))
        with self.assertRaisesRegex(ValueError,'nível de conjurador'):
            cast_spell(self.db,spell_id='arcana-bola-de-fogo',caster_type='token',caster_id='gob1',targets=[{'type':'character','id':'vezemir'}])
        self.assertEqual(self.hp(),30)

    def test_fireball_shares_one_damage_roll_as_declared_by_its_source(self):
        from unittest.mock import patch
        with patch('app.spell_engine.roll_formula',return_value={'total':8}) as roll:
            result=cast_spell(self.db,spell_id='arcana-bola-de-fogo',caster_type='token',caster_id='gob1',
                targets=[{'type':'character','id':'vezemir'},{'type':'token','id':'gob1'}],roll_mode='physical',d20=[1,1])
        self.assertEqual(roll.call_count,1)
        self.assertEqual([r['damage_rolled'] for r in result['results']],[8,8])

    def test_fireball_digital_cast_applies_full_or_half(self) -> None:
        result = cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                            targets=[{"type": "character", "id": "vezemir"}], roll_mode="digital")
        outcome = result["results"][0]
        if outcome["save"]["success"]:
            self.assertEqual(outcome["damage_dealt"], outcome["damage_rolled"] // 2)
        else:
            self.assertEqual(outcome["damage_dealt"], outcome["damage_rolled"])
        self.assertEqual(self.hp(), 30 - outcome["damage_dealt"])
        self.assertIsNone(result["manual_note"])

    def test_physical_d20_decides_save(self) -> None:
        result = cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                            targets=[{"type": "character", "id": "vezemir"}], roll_mode="physical", d20=[20])
        self.assertTrue(result["results"][0]["save"]["success"])
        result = cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                            targets=[{"type": "character", "id": "vezemir"}], roll_mode="physical", d20=[1])
        self.assertFalse(result["results"][0]["save"]["success"])

    def test_monster_usable_action_executes_with_save_and_damage(self) -> None:
        result = execute_token_action(self.db, token_id="gob1", ability_name="Baforada de teste",
                                      targets=[{"type": "character", "id": "vezemir"}], roll_mode="physical", d20=[1])
        outcome = result["results"][0]
        self.assertFalse(outcome["save"]["success"])
        self.assertGreater(outcome["damage_dealt"], 0)
        self.assertEqual(self.hp(), 30 - outcome["damage_dealt"])

    def test_passive_ability_refuses_execution(self) -> None:
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",
                               (json.dumps({"saving_throw": 10, "abilities": ["Casca-grossa: imune a veneno"]}),))
        with self.assertRaises(ValueError):
            execute_token_action(self.db, token_id="gob1", ability_name="Casca-grossa",
                                 targets=[{"type": "character", "id": "vezemir"}])

    def test_catalog_damage_honors_native_temporary_hp_and_synchronizes_pin(self):
        from unittest.mock import patch
        from app.combat_effects import init_effects
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            state = json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state['temporary_hp'] = 3
            connection.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))
            connection.execute("INSERT INTO session_workspace_tokens(id,token_type,name,character_id,current_hp,maximum_hp,created_at,updated_at) VALUES('vez-pin','character','Vezemir','vezemir',30,30,'now','now')")
        with patch('app.spell_engine.roll_formula', return_value={'total': 5}):
            result = execute_token_action(self.db, token_id='gob1', ability_name='Baforada de teste',
                targets=[{'type':'token','id':'vez-pin'}], roll_mode='physical', d20=[1])
        self.assertEqual(self.hp(), 28)
        self.assertEqual(self.token_hp('vez-pin'), 28)
        self.assertEqual(result['results'][0]['hp']['temporary_hp_absorbed'], 3)

    def test_non_damage_ability_never_rolls_duration_as_damage(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",
                (json.dumps({'saving_throw':10,'abilities':['Sopro de sono: JPS nega; dorme 2d6 rodadas.']}),))
        result = execute_token_action(self.db, token_id='gob1', ability_name='Sopro de sono',
            targets=[{'type':'character','id':'vezemir'}], roll_mode='physical',d20=[1])
        self.assertEqual(result['results'][0]['damage_dealt'], 0)
        self.assertEqual(self.hp(), 30)
        self.assertTrue(result['manual_note'])

    def test_character_and_its_pin_are_one_target_and_fail_atomically(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO session_workspace_tokens(id,token_type,name,character_id,current_hp,maximum_hp,created_at,updated_at) VALUES('vez-pin','character','Vezemir','vezemir',30,30,'now','now')")
        with self.assertRaisesRegex(ValueError, 'mesmo alvo'):
            execute_token_action(self.db, token_id='gob1', ability_name='Baforada de teste',
                targets=[{'type':'character','id':'vezemir'},{'type':'token','id':'vez-pin'}],
                roll_mode='physical',d20=[1,1])
        self.assertEqual(self.hp(), 30)
        self.assertEqual(self.token_hp('vez-pin'), 30)

    def test_invalid_last_target_does_not_damage_first(self):
        with self.assertRaises(ValueError):
            execute_token_action(self.db, token_id='gob1', ability_name='Baforada de teste',
                targets=[{'type':'character','id':'vezemir'},{'type':'token','id':'missing'}],
                roll_mode='physical',d20=[1,1])
        self.assertEqual(self.hp(), 30)

    def test_unknown_spell_and_bad_damage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cast_spell(self.db, spell_id="inexistente", caster_type="token", caster_id="gob1",
                       targets=[{"type": "character", "id": "vezemir"}])
        with self.assertRaises(ValueError):
            cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                       targets=[{"type": "character", "id": "vezemir"}], damage_override="2d6+1d4")

    def test_battle_turn_consumed_and_second_cast_blocked(self) -> None:
        from app.combat_effects import init_effects
        init_effects(self.db)
        encounter = {"active": True, "battle_mode": True, "map_id": "default",
                     "participants": [{"target_type": "token", "target_id": "gob1"},
                                      {"target_type": "character", "target_id": "vezemir"}],
                     "turn_index": 0, "attack_limit": 1, "attacks_used": 0}
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (json.dumps(encounter),))
        cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                   targets=[{"type": "character", "id": "vezemir"}], roll_mode="digital")
        with closing(sqlite3.connect(self.db)) as connection:
            used = int(json.loads(connection.execute(
                "SELECT encounter_json FROM combat_effect_clock WHERE id=1").fetchone()[0])["attacks_used"])
        self.assertEqual(used, 1)
        with self.assertRaises(ValueError):
            cast_spell(self.db, spell_id="arcana-bola-de-fogo", caster_type="token", caster_id="gob1",
                       targets=[{"type": "character", "id": "vezemir"}], roll_mode="digital")


if __name__ == "__main__":
    unittest.main()
