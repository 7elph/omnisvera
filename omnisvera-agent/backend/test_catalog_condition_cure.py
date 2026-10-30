"""Reviewed condition cures reuse the native effect/turn/receipt transaction."""
from contextlib import closing
import json
import sqlite3
from unittest import TestCase
from unittest.mock import patch

import test_spell_engine as baseline
from app.spell_catalog import get_catalog_spell, list_spell_catalog
from app.spell_engine import cast_spell, derive_spell_mechanic, scaled_spell_mechanic

SPELL = 'divina-remover-paralisia'


class CatalogConditionCureTests(TestCase):
    setUp = baseline.SpellEngineTests.setUp
    hp = baseline.SpellEngineTests.hp

    def effect(self, identity='paralysis', *, target_type='character', target_id='vezemir', **extra):
        from app.combat_effects import init_effects
        init_effects(self.db)
        value = dict(id=identity, target_type=target_type, target_id=target_id,
            label='Paralisia', duration='manual', rounds=None, modifiers={},
            monster_condition='paralyzed', blocks_actions=True, immobilized=True)
        value.update(extra)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',
                (identity, target_type, target_id, json.dumps(value)))
        return value

    def active(self):
        with closing(sqlite3.connect(self.db)) as db:
            return [row[0] for row in db.execute('SELECT id FROM combat_effects WHERE active=1 ORDER BY id')]

    def cast(self, **extra):
        return cast_spell(self.db, spell_id=SPELL, caster_type='token', caster_id='gob1',
            targets=[{'type':'character','id':'vezemir'}], request_id=extra.pop('request_id','catalog-condition-cure'), **extra)

    def test_cure_removes_only_individual_paralysis_without_dice_or_hp_change(self):
        self.effect()
        self.effect('petrified', monster_condition='petrified')
        self.effect('web', monster_condition=None, environmental=True)
        self.effect('latent', monster_condition='poison_pending', poison_runtime=True)
        with closing(sqlite3.connect(self.db)) as db, db:
            raw = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            raw['conditions'] = ['Paralisia', 'Petrificação', 'Imobilizado']
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(raw),))
        with patch('app.spell_engine.roll_formula', side_effect=AssertionError('cure needs no dice')):
            result = self.cast(roll_mode='physical')
        self.assertEqual(['latent','petrified','web'], self.active())
        outcome = result['results'][0]
        self.assertEqual('paralyzed', outcome['condition_cure'])
        self.assertEqual(['paralysis'], [entry['id'] for entry in outcome['removed_effects']])
        self.assertEqual(['Paralisia'], outcome['removed_conditions'])
        self.assertEqual(0, outcome['damage_dealt'])
        self.assertEqual(30, self.hp())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(['Petrificação','Imobilizado'], json.loads(db.execute(
                "SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])['conditions'])
        self.assertTrue(outcome['manual'])  # Barriers and non-paralysis related effects remain assisted.

    def test_replay_does_not_remove_a_new_condition_after_the_first_cure(self):
        self.effect()
        first = self.cast()
        self.effect('new-paralysis')
        self.assertEqual(first, self.cast())
        self.assertEqual(['new-paralysis'], self.active())

    def test_source_change_and_overrides_are_rejected(self):
        self.effect()
        spell = get_catalog_spell(SPELL)
        with patch('app.spell_engine.get_catalog_spell', return_value={**spell, 'description':spell['description']+' changed'}):
            with self.assertRaisesRegex(ValueError, 'fonte|revis'): self.cast()
        for extra in ({'damage_override':'1d20'}, {'save_override':'JPD'}, {'range_m':1000}, {'range_cells':1}):
            with self.subTest(extra=extra), self.assertRaises(ValueError): self.cast(**extra)
        self.assertEqual(['paralysis'], self.active())

    def test_single_target_mode_cannot_silently_apply_the_different_group_rule(self):
        self.effect()
        with self.assertRaisesRegex(ValueError, 'um alvo|alvo único'):
            cast_spell(self.db, spell_id=SPELL, caster_type='token', caster_id='gob1',
                targets=[{'type':'character','id':'vezemir'}, {'type':'token','id':'gob1'}])

    def test_receipt_failure_rolls_back_effect_and_manual_condition_removal(self):
        self.effect()
        with patch('app.spell_engine.save_receipt', side_effect=sqlite3.OperationalError('receipt unavailable')):
            with self.assertRaises(sqlite3.OperationalError): self.cast()
        self.assertEqual(['paralysis'], self.active())

    def grid(self, target_x=20):
        from app.spatial_grid import init_spatial
        init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,character_id,map_id,current_hp,maximum_hp,sheet_json,created_at,updated_at) VALUES('pc','character','Vezemir','vezemir','default',30,30,'{}','now','now')")
            db.execute("UPDATE session_workspace_tokens SET map_id='default',sheet_json=? WHERE id='gob1'", (json.dumps({'spellcaster_level':5}),))
            db.execute("INSERT INTO session_workspace_map_grids(map_id,grid_type,cols,rows,cell_size_m,origin_x,origin_y,distance_rule,version) VALUES('default','square',100,20,1.5,0,0,'chebyshev',1)")
            db.execute("INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h,version) VALUES('default','gob1',1,5,1,1,1)")
            db.execute("INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h,version) VALUES('default','pc',?,5,1,1,1)", (target_x,))

    def test_range_uses_caster_level_not_a_global_fixed_ten_meters(self):
        self.effect(); self.grid()
        result = self.cast()
        self.assertTrue(result['results'][0]['range']['checked'])
        self.assertEqual(50, result['mechanic']['range_m'])
        self.assertEqual([], self.active())

    def test_out_of_range_missing_positions_or_level_cannot_bypass_validation(self):
        self.effect(); self.grid(target_x=50)
        with self.assertRaises(ValueError): self.cast()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("DELETE FROM session_workspace_entity_positions WHERE token_id='pc'")
        with self.assertRaisesRegex(ValueError, 'grid'): self.cast()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json='{}' WHERE id='gob1'")
        with self.assertRaisesRegex(ValueError, 'nível'): self.cast()
        self.assertEqual(['paralysis'], self.active())

    def test_catalogue_exposes_supported_mode_and_explicit_limits(self):
        entry = next(s for s in list_spell_catalog()['spells'] if s['id']==SPELL)
        self.assertEqual('condition_cure', entry['automation']['family'])
        self.assertEqual('single_target', entry['automation']['mode'])
        self.assertIn('barreira', entry['automation']['note'])
        self.assertIsNone(derive_spell_mechanic(get_catalog_spell(SPELL))['range_m'])
        self.assertEqual(50, scaled_spell_mechanic(get_catalog_spell(SPELL),5)['range_m'])
        with self.assertRaisesRegex(ValueError, 'nível'):
            scaled_spell_mechanic(get_catalog_spell(SPELL),None)

    def test_cure_consumes_existing_turn_once_and_preserves_rollback_budget(self):
        import test_generic_spell_retry as retry
        self.effect(); retry.GenericSpellRetryTests.battle(self)
        with patch('app.spell_engine.save_receipt', side_effect=sqlite3.OperationalError('rollback')):
            with self.assertRaises(sqlite3.OperationalError): self.cast()
        self.assertEqual(['paralysis'], self.active())
        self.assertEqual(0, retry.GenericSpellRetryTests.attacks_used(self))
        self.cast(); self.cast()
        self.assertEqual(1, retry.GenericSpellRetryTests.attacks_used(self))
        with self.assertRaises(ValueError): self.cast(request_id='different-cure')

    def test_hidden_target_results_are_private_in_the_native_ledger(self):
        self.effect()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id='gob1'")
        self.cast()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual('gm', db.execute("SELECT visibility FROM session_ledger ORDER BY id DESC LIMIT 1").fetchone()[0])
