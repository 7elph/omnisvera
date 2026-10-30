import unittest
from app.monster_catalog import get_catalog_monster,load_monster_catalog
from app.monster_riders import rider_specs


class MonsterRidersTests(unittest.TestCase):
    def test_incomplete_lethal_poison_is_not_downgraded_to_damage_only(self):
        monster={'id':'custom','attacks':[{'name':'Mordida','damage':'1d4 + Veneno'}],
            'abilities':[{'name':'Veneno','description':'A mordida causa 1d4 de dano extra. Uma JPC evita a morte.'}]}
        result=rider_specs(monster)
        self.assertEqual(result['on_hit'],[])
        self.assertTrue(result['pending'])

    def test_paralysis_keeps_real_attack_indices_and_exploration_units(self):
        for identity in ['ghoul','thoul','cubo-gelatinoso']:
            with self.subTest(identity=identity):
                monster=get_catalog_monster(identity);rows=rider_specs(monster)['on_hit'];self.assertTrue(rows)
                spec=next(r for r in rows if r['effect']=='paralyzed')
                self.assertEqual(spec['save'],'JPC');self.assertEqual(spec['duration_unit'],'turns')
                self.assertTrue(spec['duration_formula'])
                self.assertTrue(all(type(i) is int and 0<=i<len(monster['attacks']) for i in spec['attack_indices']))

    def test_elf_immunity_is_explicit_and_never_half_elf(self):
        for identity in ['ghoul','thoul']:
            spec=next(r for r in rider_specs(get_catalog_monster(identity))['on_hit'] if r['effect']=='paralyzed')
            self.assertEqual(spec['immunity_races'],['elfo'])
        self.assertEqual(rider_specs(get_catalog_monster('cubo-gelatinoso'))['on_hit'][0]['immunity_races'],[])

    def test_lich_permanent_and_cockatrice_only_petrifies_with_bite(self):
        lich=next(r for r in rider_specs(get_catalog_monster('lich'))['on_hit'] if r['effect']=='paralyzed')
        self.assertEqual(lich['duration_unit'],'permanent')
        rows=rider_specs(get_catalog_monster('cocatriz'))['on_hit']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['effect'],'petrified');self.assertEqual(rows[0]['attack_indices'],[0])

    def test_poison_extra_damage_is_not_duration(self):
        for identity in ['derro','diabrete']:
            spec=next(r for r in rider_specs(get_catalog_monster(identity))['on_hit'] if r['effect']=='poison_damage')
            self.assertEqual((spec['damage_formula'],spec['duration_unit'],spec['save_effect']),('1d6','instant','halves'))

    def test_poison_death_keeps_expression_and_unit(self):
        for identity,formula in [('aranha-cacadora-gigante','1d3'),('aranha-camufladora-gigante','1d3+1'),('cobra-venenosa','1d10'),('escorpiao-gigante','1d3+1')]:
            with self.subTest(identity=identity):
                spec=next(r for r in rider_specs(get_catalog_monster(identity))['on_hit'] if r['effect']=='poison_death')
                self.assertEqual((spec['duration_formula'],spec['duration_unit']),(formula,'turns'));self.assertIsNone(spec['damage_formula'])

    def test_gaze_attribute_drain_delayed_sleep_remain_pending(self):
        for identity in ['basilisco','medusa','gorgon','drider','centopeia-gigante','homunculo']:
            with self.subTest(identity=identity):self.assertEqual(rider_specs(get_catalog_monster(identity))['on_hit'],[])

    def test_all_sources_lossless_and_deterministic(self):
        for monster in load_monster_catalog()['monsters']:
            spec=rider_specs(monster);self.assertEqual(spec,rider_specs(monster))
            self.assertEqual([s['text'] for s in spec['sources']],[a['description'] for a in monster['abilities']])
            self.assertFalse(spec['coverage']['fully_automated'])
