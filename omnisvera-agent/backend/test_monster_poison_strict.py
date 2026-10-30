"""Independent integration review of the delegated parser on the real catalog."""
import copy
import unittest
from app.monster_catalog import get_catalog_monster
from app.monster_poison_specs import poison_specs


class MonsterPoisonStrictTests(unittest.TestCase):
    def test_all_eight_real_sources_and_renamed_copies_keep_the_same_mechanics(self):
        for identity in ['centopeia-gigante','vespa-gigante','cerbero','drider','naga-negra','homunculo','sibilante','roper']:
            with self.subTest(identity=identity):
                original=get_catalog_monster(identity);custom=copy.deepcopy(original);custom['id']='custom-copy'
                first=poison_specs(original)['on_hit'];second=poison_specs(custom)['on_hit']
                self.assertEqual(len(first),1);self.assertEqual(len(second),1)
                clean=lambda rows:[{k:v for k,v in r.items() if k not in {'id','monster_id'}} for r in rows]
                self.assertEqual(clean(first),clean(second))

    def test_infection_is_not_silently_converted_to_poison(self):
        self.assertEqual(poison_specs(get_catalog_monster('otyugh'))['on_hit'],[])

    def test_negated_drain_and_immunity_descriptions_never_activate(self):
        for name,text in [('Veneno','Não causa perda de 1d6 pontos de Destreza por turno até o valor chegar a 3. Uma JPC evita.'),
                          ('Imunidade','Imune a veneno que causa perda de 1d6 pontos de Destreza por turno até o valor chegar a 3. JPC evita.')]:
            monster={'id':'cerbero','attacks':[{'name':'Mordida','damage':'1d4 + Veneno'}],'abilities':[{'name':name,'description':text}]}
            self.assertEqual(poison_specs(monster)['on_hit'],[])

    def test_zero_attribute_limit_does_not_invent_death_and_other_limits_are_parsed(self):
        for ending,floor in [('até que o valor chegue a 5',5),('até o valor chegar a 0',0)]:
            monster={'id':'custom','attacks':[{'name':'Mordida','damage':'1d4 + Veneno'}],
                'abilities':[{'name':'Veneno','description':f'A mordida causa perda de 1d6 pontos de Destreza por turno {ending}. Uma JPC evita.'}]}
            spec=poison_specs(monster)['on_hit'][0]
            self.assertEqual(spec['floor'],floor);self.assertFalse(spec['lethal_at_floor'])
