import copy
import unittest
from app.monster_catalog import load_monster_catalog, get_catalog_monster
from app.monster_encounters import encounter_defaults
from app.monster_actions import build_action_map, parse_spellcasting


class MonsterEncounterTests(unittest.TestCase):
    def test_all_approved_weapon_choices_are_usable_and_preserve_source(self):
        count = 0
        for monster in load_monster_catalog()['monsters']:
            original = copy.deepcopy(monster)
            preset = encounter_defaults(monster)
            if preset and preset['equipment']:
                count += 1
                result = build_action_map(monster['name'], preset['attacks'], preset['abilities'])
                self.assertEqual(result['summary']['attacks_incomplete'], 0, monster['id'])
                self.assertEqual(preset['kind'], 'campaign_encounter_choices')
                self.assertEqual(preset['equipment'][0]['edition'], 'OD1')
            self.assertEqual(monster, original)
        self.assertEqual(count, 29)

    def test_monster_flat_damage_bonus_is_added_once(self):
        preset = encounter_defaults(get_catalog_monster('gigante-da-colina'))
        self.assertEqual(preset['attacks'][0]['damage'], '2d6+6')
        self.assertEqual(preset['attacks'][0]['bonus'], 11)

    def test_all_sixteen_repertoires_link_to_existing_spells_and_real_levels(self):
        total = 0
        for monster in load_monster_catalog()['monsters']:
            preset = encounter_defaults(monster)
            if not preset or not preset['spells']:
                continue
            total += 1
            casting = build_action_map(monster['name'], preset['attacks'], preset['abilities'])['spellcasting']
            self.assertTrue(casting, monster['id'])
            self.assertTrue(casting[0]['spellcasting']['caster_level'], monster['id'])
            linked = {s['id'] for a in casting for n in a['spellcasting']['named_spells'] for s in n['links']}
            self.assertTrue({s['id'] for s in preset['spells']} <= linked, monster['id'])
        self.assertEqual(total, 16)

    def test_accent_and_specialized_cleric_are_not_missing_caster_levels(self):
        for text in ('como um Clérigo de 3º nível.', 'como se fosse um Clérigo Xamã de 3º nível.'):
            casting = parse_spellcasting(text)
            self.assertEqual((casting['caster_level'], casting['tradition']), (3, 'divina'))

    def test_other_monsters_do_not_receive_arbitrary_equipment(self):
        self.assertIsNone(encounter_defaults(get_catalog_monster('troll')))

    def test_projectiles_are_aggregated_only_for_a_single_selected_target(self):
        from app.spell_catalog import get_catalog_spell
        from app.spell_engine import scaled_spell_mechanic
        for identity, level, damage, count in [
            ('arcana-dardos-misticos', 7, '4d4+4', 4),
            ('arcana-dardos-misticos', 15, '5d4+5', 5),
            ('divina-dardo-de-brasa', 3, '1d4+3', 1),
            ('divina-dardo-de-brasa', 6, '2d4+10', 2),
        ]:
            result = scaled_spell_mechanic(get_catalog_spell(identity), level)
            self.assertEqual((result['damage'], result['projectiles']), (damage, count))

    def test_touch_uses_the_flat_level_bonus_not_the_example_level(self):
        from app.spell_catalog import get_catalog_spell
        from app.spell_engine import scaled_spell_mechanic
        self.assertEqual(scaled_spell_mechanic(get_catalog_spell('arcana-toque-chocante'), 7)['damage'], '1d8+7')

    def test_snake_variant_is_explicit_and_original_is_untouched(self):
        monster = get_catalog_monster('serpente')
        preset = encounter_defaults(monster)
        self.assertIn('ou', monster['attacks'][0]['damage'])
        self.assertEqual(preset['attacks'][0]['damage'], '1d3')
        self.assertIn('não venenosa', preset['label'])
        self.assertTrue(any(a['name'] == 'Veneno' for a in monster['abilities']))
        self.assertFalse(any(a['name'] == 'Veneno' for a in preset['abilities']))

    def test_source_and_encounter_readiness_counts_remain_distinct(self):
        from app.catalog_readiness import build_catalog_readiness
        count = build_catalog_readiness()['counts']['monsters']
        self.assertEqual(count['attacks_incomplete'], 30)
        self.assertEqual(count['attacks_incomplete_after_encounter_choices'], 0)
        self.assertEqual(count['spellcasting_without_repertoire'], 16)
        self.assertEqual(count['spellcasting_without_repertoire_after_encounter_choices'], 0)
