"""Reviewed disease and explicitly configured snake-bite contracts, TEMP only."""
import copy
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from app.monster_catalog import get_catalog_monster
from app.monster_riders import combat_rider_specs
from app.combat_effects import init_effects, effect_snapshot
import test_spell_engine as fixture


class SourceContracts(unittest.TestCase):
    def test_rat_disease_uses_source_chance_save_con_and_days(self):
        for identity in ('rato', 'rato-gigante'):
            monster = copy.deepcopy(get_catalog_monster(identity))
            monster['id'] = 'custom-copy'
            spec = combat_rider_specs(monster)['on_hit'][0]
            self.assertEqual(spec['effect'], 'disease_attribute')
            self.assertEqual(spec['chance_formula'], '1d6')
            self.assertEqual(spec['chance_success_max'], 1)
            self.assertEqual(spec['save'], 'JPC')
            self.assertEqual((spec['attribute'], spec['attribute_max']), ('constitution', 1))
            self.assertEqual((spec['duration_formula'], spec['duration_unit']), ('1d6', 'days'))
            self.assertFalse(spec.get('poison', False))
            self.assertEqual(spec['attack_indices'], [0])

    def test_changed_or_cumulative_disease_remains_unmapped(self):
        monster = copy.deepcopy(get_catalog_monster('rato'))
        monster['abilities'][0]['description'] = monster['abilities'][0]['description'].replace('1 chance em 1d6', '2 chances em 1d6')
        self.assertEqual(combat_rider_specs(monster)['on_hit'], [])
        otyugh = combat_rider_specs(get_catalog_monster('otyugh'))
        self.assertEqual(otyugh['on_hit'], [])
        self.assertIn('doenca_chance_cumulativa_sem_escopo_revisado', [p['reason'] for p in otyugh['pending']])

    def test_medusa_default_does_not_gain_a_fictional_snake_attack(self):
        monster = get_catalog_monster('medusa')
        self.assertEqual(combat_rider_specs(monster)['on_hit'], [])
        self.assertEqual([a['name'] for a in monster['attacks']], ['Arco'])

    def test_medusa_poison_binds_only_to_explicit_hair_snake_attack(self):
        monster = copy.deepcopy(get_catalog_monster('medusa'))
        monster['attacks'].extend([
            {'name': 'Mordida', 'damage': '1d4', 'bonus': 2},
            {'name': 'Mordida das serpentes do cabelo', 'damage': '1d3 + Veneno', 'bonus': 3},
        ])
        specs = combat_rider_specs(monster)['on_hit']
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0]['attack_indices'], [2])
        self.assertEqual((specs[0]['effect'], specs[0]['save']), ('poison_death', 'JPC'))
        self.assertEqual((specs[0]['duration_formula'], specs[0]['duration_unit']), ('1d3', 'turns'))


class DiseaseRuntime(unittest.TestCase):
    setUp = fixture.SpellEngineTests.setUp
    hp = fixture.SpellEngineTests.hp

    def prepare(self):
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'", (json.dumps({'attributes': {'constitution': 12}}),))
        spec = combat_rider_specs(get_catalog_monster('rato'))['on_hit'][0]
        return spec

    def apply(self, spec, chance=1, resisted=False, days=2):
        from app.monster_conditions import apply_spec
        from app.dorn_spells import target
        with closing(sqlite3.connect(self.db)) as db, db, \
                patch('app.monster_conditions.roll_formula', return_value={'total': chance, 'individual_results': [chance]}) as roll, \
                patch('app.dorn_spells.save', return_value={'success': resisted, 'total': 1}) as saving, \
                patch('app.monster_poison_runtime.roll_formula', return_value={'total': days, 'individual_results': [days]}) as duration:
            result = apply_spec(db, target(db, 'character', 'vezemir'), spec, 'gob1', 'now')
            return result, roll.call_count, saving.call_count, duration.call_count

    def state(self):
        from app.monster_poison_runtime import current_attributes
        with closing(sqlite3.connect(self.db)) as db:
            return current_attributes(db, 'character', 'vezemir'), effect_snapshot(db)

    def test_failed_chance_does_not_roll_jp_duration_or_change_attributes(self):
        result, chance, saves, duration = self.apply(self.prepare(), chance=2)
        self.assertFalse(result['triggered'])
        self.assertEqual((chance, saves, duration), (1, 0, 0))
        self.assertEqual(self.state()[0]['constitution'], 12)
        self.assertEqual(self.state()[1]['effects'], [])

    def test_save_negates_disease_before_duration(self):
        result, _, saves, duration = self.apply(self.prepare(), resisted=True)
        self.assertTrue(result['resisted'])
        self.assertEqual((saves, duration), (1, 0))
        self.assertEqual(self.state()[1]['effects'], [])

    def test_con_becomes_one_for_exact_days_without_rewriting_sheet_or_hp(self):
        result, _, _, _ = self.apply(self.prepare(), days=2)
        attributes, snapshot = self.state()
        self.assertEqual(attributes['constitution'], 1)
        self.assertEqual(result['duration_seconds'], 172800)
        self.assertEqual(snapshot['effects'][0]['label'], 'Febre do Esgoto')
        self.assertEqual(self.hp(), 30)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])['attributes']['constitution'], 12)
        from app.dorn_spells import elapse
        with closing(sqlite3.connect(self.db)) as db, db:
            elapse(db, effect_snapshot(db), 172799, [], 'later')
        self.assertEqual(self.state()[0]['constitution'], 1)
        with closing(sqlite3.connect(self.db)) as db, db:
            elapse(db, effect_snapshot(db), 1, [], 'end')
        self.assertEqual(self.state()[0]['constitution'], 12)

    def test_construct_and_declared_vampire_immunity_precede_chance(self):
        spec = self.prepare()
        for traits in ({'construct_traits': True}, {'race': 'Vampiro'}):
            with closing(sqlite3.connect(self.db)) as db, db:
                db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'", (json.dumps(traits),))
            result, chance, saving, duration = self.apply(spec)
            self.assertTrue(result['immune'])
            self.assertEqual((chance, saving, duration), (0, 0, 0))

    def test_reinfection_is_assisted_and_never_silently_renews_duration(self):
        spec = self.prepare()
        self.apply(spec, days=2)
        result, chance, saving, duration = self.apply(spec, days=6)
        self.assertTrue(result['manual'])
        self.assertEqual((chance, saving, duration), (0, 0, 0))
        self.assertEqual(self.state()[1]['effects'][0]['remaining_seconds'], 172800)

    def test_misses_and_reflections_never_trigger_disease(self):
        from app.monster_conditions import apply_on_hit
        spec = self.prepare()
        for breakdown in ({'strikes': [{'result': 'miss'}]},
                          {'strikes': [{'result': 'hit'}], 'reflection_result': {'rolls': [{'strike': 0, 'intercepted': True}]}}):
            record = {'actor_character_id': 'gob1', 'target_type': 'character', 'target_id': 'vezemir',
                      'breakdown': {'monster_on_hit': {'riders': [spec]}, **breakdown}}
            with closing(sqlite3.connect(self.db)) as db, db, patch('app.monster_conditions.roll_formula', side_effect=AssertionError('no chance')):
                self.assertEqual(apply_on_hit(db, record, 'now'), [])

    def test_native_confirmation_retry_does_not_repeat_chance_save_or_duration(self):
        from app.combat import monster_attack_definition, resolve_attack, confirm_attack_resolution
        self.prepare()
        monster = get_catalog_monster('rato-gigante')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,name=? WHERE id='gob1'", (json.dumps({**monster, 'source': {'monster_id': 'rato-gigante'}}), monster['name']))
        actor = {'id': 'gob1', 'name': monster['name'], 'sheet': monster}
        resolved, _ = resolve_attack(self.db, request_id='rat-disease-native', actor_character_id='gob1', actor_name=actor['name'],
            requested_by_id='master', requested_by_role='gm', definition=monster_attack_definition(actor, '0'), inventory=[], attack_id='0',
            target={'type': 'character', 'id': 'vezemir', 'name': 'Vezemir', 'armor_class': 1, 'current_hp': 30},
            roll_mode='physical', physical_d20=15, rng=lambda a, b: 1)
        with patch('app.monster_conditions.roll_formula', return_value={'total': 1}) as chance, \
                patch('app.dorn_spells.save', return_value={'success': False, 'total': 1}) as saving, \
                patch('app.monster_poison_runtime.roll_formula', return_value={'total': 2}) as duration:
            first, _ = confirm_attack_resolution(self.db, resolution_id=resolved['resolution_id'], requested_by_id='master', requested_by_role='gm')
            repeat, created = confirm_attack_resolution(self.db, resolution_id=resolved['resolution_id'], requested_by_id='master', requested_by_role='gm')
        self.assertFalse(created)
        self.assertEqual(first, repeat)
        chance.assert_called_once()
        saving.assert_called_once()
        duration.assert_called_once()
        self.assertEqual(self.state()[0]['constitution'], 1)

    def test_rest_removes_disease_and_public_status_omits_blueprint(self):
        from app.combat_effects import expire_rest_effects
        from app.monster_conditions import public_effect
        self.apply(self.prepare())
        public = public_effect(self.state()[1]['effects'][0])
        self.assertEqual(public['monster_condition'], 'diseased')
        self.assertNotIn('poison_spec', public)
        self.assertNotIn('source_token_id', public)
        with closing(sqlite3.connect(self.db)) as db, db:
            expire_rest_effects(db, 'vezemir', complete=True)
        self.assertEqual(self.state()[0]['constitution'], 12)
        self.assertEqual(self.state()[1]['effects'], [])

    def test_missing_attribute_does_not_invent_a_base_value_or_roll_duration(self):
        spec = self.prepare()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_definition_overrides SET data_json='{}' WHERE profile_id='vezemir'")
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            data['attributes'].pop('constitution')
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(data),))
        self.assertNotIn('constitution',self.state()[0])
        result, _, _, duration = self.apply(spec)
        self.assertTrue(result['manual'])
        self.assertEqual(duration, 0)
        self.assertEqual(self.state()[1]['effects'], [])

    def test_missing_override_keeps_real_base_attribute_for_disease(self):
        spec=self.prepare()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE character_definition_overrides SET data_json='{}' WHERE profile_id='vezemir'")
        self.assertEqual(self.state()[0]['constitution'],12)
        result,_,_,duration=self.apply(spec,days=2)
        self.assertNotIn('manual',result)
        self.assertEqual(duration,1)
        self.assertEqual(self.state()[0]['constitution'],1)


if __name__ == '__main__':
    unittest.main()
