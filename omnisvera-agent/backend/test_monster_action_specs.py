from __future__ import annotations

import unittest

from app import monster_action_specs
from app import monster_catalog


class MonsterActionSpecsTests(unittest.TestCase):
    def test_dragao_dourado_11d10_jpd_metade_cone(self):
        m = monster_catalog.get_catalog_monster("dragao-dourado")
        self.assertIsNotNone(m)
        specs = monster_action_specs.monster_action_specs(m)
        self.assertEqual(len(specs), 1)
        s = specs[0]
        self.assertEqual(s["family"], "breath")
        self.assertEqual(s["damage_formula"], "11d10")
        self.assertEqual(s["save"], "JPD")
        self.assertEqual(s["save_effect"], "halves")
        self.assertEqual(s["geometry"]["shape"], "cone")
        self.assertEqual(s["geometry"]["width_m"], 9)
        self.assertEqual(s["geometry"]["depth_m"], 27)
        self.assertEqual(s["uses"]["maximum"], 3)
        self.assertEqual(s["uses"]["recharge"], "day")
        self.assertEqual(s["automation_status"], "specification_complete")
        self.assertEqual(s["execution_status"], "not_bound")
        self.assertIn("dragao-dourado", s["source"]["monster_id"])
        self.assertIn("olddragon.com.br", s["source"]["url"] or "")
        self.assertTrue(s["description_full"])

    def test_real_catalog_breaths_preserve_even_chance_and_non_damage_actions(self):
        allm = monster_catalog.load_monster_catalog()["monsters"]
        total = 0
        specs_all = []
        for m in allm:
            sp = monster_action_specs.monster_action_specs(m)
            total += len(sp)
            specs_all.extend(sp)
        self.assertEqual(total, 15)  # 14 monsters; Drakold has two abilities.
        self.assertEqual(len({s['source']['monster_id'] for s in specs_all}), 14)
        # all have source monster_id/edition/url/license and id/name/family
        for s in specs_all:
            self.assertTrue(s["id"])
            self.assertTrue(s["name"])
            self.assertEqual(s["family"], "breath")
            self.assertIn("monster_id", s["source"])
            self.assertIn("edition", s["source"])
            self.assertIn("url", s["source"])
            self.assertIn("license", s["source"])

    def test_deterministic_no_db_no_network(self):
        m = monster_catalog.get_catalog_monster("grifo")
        sp = monster_action_specs.monster_action_specs(m)
        self.assertEqual(sp, [])  # grifo has no breath

    def test_damage_modifiers_and_non_damage_dice(self):
        for formula in ('2d6+2', '2d6-3'):
            specs = monster_action_specs.monster_action_specs({'id':'fixture', 'abilities':[
                {'name':'Sopro', 'description':f'Causa {formula} de dano. JPD reduz à metade.'}]})
            self.assertEqual(specs[0]['damage_formula'],formula)
        for text in ('JPS nega; dorme por 2d6 rodadas.', '1d6 imagens. JPD nega.', '1-3 chances em 1d6 de soprar.'):
            specs = monster_action_specs.monster_action_specs({'id':'fixture','image_license':'WRONG', 'abilities':[
                {'name':'Sopro', 'description':text}]})
            self.assertEqual(len(specs),1)
            self.assertIsNone(specs[0]['damage_formula'])
            self.assertEqual(specs[0]['source']['license'],'CC BY-SA 4.0')

    def test_full_descriptions_unknown_dv_and_conditional_damage(self):
        text = ' ' * 1300 + 'Dano igual ao número de seus dados de vida em d10.'
        specs = monster_action_specs.monster_action_specs({'id':'fixture','hit_dice':'11+???', 'abilities':[
            {'name':'Baforada','description':text}]})
        self.assertEqual(specs[0]['description_full'],text)
        self.assertIsNone(specs[0]['damage_formula'])
        shadow = monster_action_specs.monster_action_specs(monster_catalog.get_catalog_monster('dragao-das-sombras'))[0]
        self.assertIsNone(shadow['damage_formula'])
        chimera = monster_action_specs.monster_action_specs(monster_catalog.get_catalog_monster('quimera'))[0]
        self.assertEqual(chimera['damage_formula'],'3d6')
        self.assertEqual(chimera['automation_status'],'assisted')
        destroyer = monster_action_specs.monster_action_specs(monster_catalog.get_catalog_monster('destruidor'))[0]
        self.assertEqual(destroyer['damage_multiplier'],2)


if __name__ == "__main__":
    unittest.main()
