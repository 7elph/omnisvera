import unittest
from unittest.mock import patch
import test_monster_conditions_runtime as fixtures


class EffectOnlyAttackTests(unittest.TestCase):
    setUp = fixtures.MonsterConditionRuntimeTests.setUp
    hp = fixtures.MonsterConditionRuntimeTests.hp
    token_hp = fixtures.MonsterConditionRuntimeTests.token_hp
    setup_monster = fixtures.MonsterConditionRuntimeTests.setup_monster
    effects = fixtures.MonsterConditionRuntimeTests.effects

    def exercise(self, identity, index, effect, seconds):
        from app.combat import monster_attack_definition, resolve_attack, confirm_attack_resolution
        actor = self.setup_monster(identity)
        definition = monster_attack_definition(actor, str(index))
        resolution, _ = resolve_attack(self.db, request_id='effect-only-native', actor_character_id='gob1',
            actor_name=actor['name'], requested_by_id='master', requested_by_role='gm', definition=definition,
            inventory=[], attack_id=str(index), target={'type':'character', 'id':'vezemir', 'name':'Vezemir', 'armor_class':1, 'current_hp':30},
            roll_mode='physical', physical_d20=15, rng=lambda a,b: 1)
        self.assertEqual(resolution['damage_total'], 0)
        self.assertEqual(resolution['damage_rolls'], [])
        with patch('app.dorn_spells.roll_formula', return_value={'total':1, 'individual_results':[1]}) as save, \
             patch('app.monster_conditions.roll_formula', return_value={'total':2, 'individual_results':[2]}) as duration:
            first, _ = confirm_attack_resolution(self.db, resolution_id=resolution['resolution_id'], requested_by_id='master', requested_by_role='gm')
            repeat, created = confirm_attack_resolution(self.db, resolution_id=resolution['resolution_id'], requested_by_id='master', requested_by_role='gm')
        self.assertFalse(created)
        self.assertEqual(first, repeat)
        self.assertEqual(self.hp(), 30)
        self.assertEqual(len(self.effects()), 1)
        self.assertEqual(self.effects()[0]['monster_condition'], effect)
        self.assertEqual(self.effects()[0]['remaining_seconds'], seconds)
        save.assert_called_once()
        duration.assert_called_once()

    def test_blinding_spit_does_not_roll_fictitious_damage(self):
        self.exercise('cobra-cuspidora', 0, 'blinded', 20)

    def test_carrion_tentacle_paralyzes_without_replacing_it_with_damage(self):
        self.exercise('verme-da-carcaca', 1, 'paralyzed', 1200)

    def test_unsupported_special_does_not_become_a_zero_damage_attack(self):
        from app.combat import monster_attack_definition
        with self.assertRaisesRegex(ValueError, 'contato especial'):
            monster_attack_definition(self.setup_monster('esfera-da-aniquilacao'), '0')

    def test_projectile_distribution_rejection_does_not_mutate_hp(self):
        from app.spell_engine import cast_spell
        with self.assertRaisesRegex(ValueError, 'um alvo'):
            cast_spell(self.db, spell_id='arcana-dardos-misticos', caster_type='token', caster_id='gob1',
                       targets=[{'type':'character','id':'vezemir'}, {'type':'token','id':'gob1'}])
        self.assertEqual(self.hp(), 30)
        self.assertEqual(self.token_hp(), 12)
