from __future__ import annotations

import unittest

from app import monster_catalog
from app import monster_passives


class MonsterPassivesTests(unittest.TestCase):
    def test_explicit_electricity_and_plural_poison_immunities(self):
        for identity,kind in [('dragao-azul','lightning'),('dragao-verde','poison')]:
            with self.subTest(identity=identity):
                spec=monster_passives.passive_specs(monster_catalog.get_catalog_monster(identity))
                self.assertIn(kind,[entry['type'] for entry in spec['damage_immunities']])

    def test_thoul_cannot_regenerate_any_fire_or_acid_damage(self):
        spec=monster_passives.passive_specs(monster_catalog.get_catalog_monster('thoul'))
        self.assertEqual(set(spec['regeneration']['blocked_by']),{'fire','acid'})

    def test_unquantified_percent_and_negated_resistance_never_become_half(self):
        for text in ('Não tem resistência ao fogo e sofre metade do dano só com proteção.',
                     'Resistência a fogo de 90%.', 'Vulnerável ao frio quando molhado: dano em dobro.'):
            spec=monster_passives.passive_specs({'id':'test','abilities':[{'name':'Defesa','description':text}]})
            self.assertEqual(spec['damage_resistances'],[])
            self.assertEqual(spec['damage_vulnerabilities'],[])

    def test_conditional_or_negated_regeneration_is_not_unconditional(self):
        for text in ('Regenera 2 pontos de vida a cada rodada se estiver na água.',
                     'Não é capaz de regenerar 2 pontos de vida a cada rodada.'):
            spec=monster_passives.passive_specs({'id':'test','abilities':[{'name':'Regeneração','description':text}]})
            self.assertIsNone(spec['regeneration'])

    def test_mixed_negation_never_grants_immunity_to_the_negated_element(self):
        spec=monster_passives.passive_specs({'id':'test','abilities':[{'name':'Imunidade','description':'É imune a fogo, mas não a frio.'}]})
        self.assertNotIn('cold',[s['type'] for s in spec['damage_immunities']])
    def test_dragao_dourado_fire_immunity(self):
        m = monster_catalog.get_catalog_monster("dragao-dourado")
        s = monster_passives.passive_specs(m)
        self.assertEqual(s["schema_version"], 1)
        self.assertEqual([x["type"] for x in s["damage_immunities"]], ["fire"])
        self.assertIsNone(s["regeneration"])
        self.assertTrue(any("imunidade" in str(x).lower() for x in s["sources"]))

    def test_troll_regen_blocked_by_fire_acid(self):
        m = monster_catalog.get_catalog_monster("troll")
        s = monster_passives.passive_specs(m)
        self.assertIsNotNone(s["regeneration"])
        self.assertEqual(s["regeneration"]["amount"], 1)
        self.assertEqual(s["regeneration"]["interval"], "round")
        self.assertIn("fire", s["regeneration"]["blocked_by"])
        self.assertIn("acid", s["regeneration"]["blocked_by"])

    def test_negation_nao_e_imune_pendente(self):
        m = {"id": "x", "abilities": [
            {"name": "Fogo", "description": "Não é imune a fogo."},
            {"name": "Nunca", "description": "Nunca é imune ao frio."},
        ]}
        s = monster_passives.passive_specs(m)
        self.assertEqual(s["damage_immunities"], [])
        self.assertTrue(any(p["reason"] == "imunidade_negada_pendente" for p in s["pending"]))
        # both abilities preserved in sources and pending
        self.assertEqual(len(s["sources"]), 2)
        self.assertEqual(len(s["pending"]), 2)

    def test_multiplos_tipos_fogo_e_frio_mapeados(self):
        m = {"id": "x", "abilities": [
            {"name": "Resistente duplo", "description": "É imune a fogo e frio."},
        ]}
        s = monster_passives.passive_specs(m)
        types = sorted([x["type"] for x in s["damage_immunities"]])
        self.assertEqual(types, ["cold", "fire"])

    def test_nao_regenera_e_regenera_somente_condicional(self):
        m = {"id": "x", "abilities": [
            {"name": "Sem regen", "description": "Não regenera pontos de vida."},
            {"name": "Cond", "description": "Regenera somente quando em água, 2 pontos de vida a cada rodada."},
        ]}
        s = monster_passives.passive_specs(m)
        self.assertIsNone(s["regeneration"])
        reasons = [p["reason"] for p in s["pending"]]
        self.assertIn("regeneracao_negada_pendente", reasons)
        self.assertIn("regeneracao_condicional_pendente", reasons)
        self.assertEqual(len(s["sources"]), 2)

    def test_imunidade_armas_nao_magicas_nao_vira_dano(self):
        m = {"id": "x", "abilities": [
            {"name": "Armadura", "description": "Imune a armas não mágicas e também imune a fogo."},
        ]}
        s = monster_passives.passive_specs(m)
        # should not map fire as simple damage immunity due to precedence? must go pending
        self.assertEqual(s["damage_immunities"], [])
        self.assertTrue(any("nao_magicas" in p["reason"] for p in s["pending"]))
        self.assertEqual(len(s["sources"]), 1)
        self.assertEqual(len(s["pending"]), 1)

    def test_saves_nao_sao_resistencia_dano(self):
        m = {"id": "x", "abilities": [{"name": "Resistente", "description": "Tem vantagem em JPC contra veneno."}]}
        s = monster_passives.passive_specs(m)
        self.assertEqual(s["damage_resistances"], [])
        self.assertTrue(any("jp" in p["reason"] for p in s["pending"]))

    def test_sono_chance_nao_soma_pendente(self):
        m = {"id": "x", "abilities": [
            {"name": "Sono", "description": "1-2 em 1d6 de chance de adormecer por 1d4 rodadas."},
            {"name": "Falsa Morte", "description": "Finge estar morto com grande convicção."},
        ]}
        s = monster_passives.passive_specs(m)
        self.assertEqual(s["damage_immunities"], [])
        self.assertEqual(s["damage_resistances"], [])
        self.assertIsNone(s["regeneration"])
        self.assertEqual(len(s["sources"]), 2)
        self.assertEqual(len(s["pending"]), 2)
        reasons = [p["reason"] for p in s["pending"]]
        self.assertIn("passiva_nao_suportada_pendente", reasons)

    def test_todos255_sem_inventar_fontes_pendentes(self):
        allm = monster_catalog.load_monster_catalog()["monsters"]
        for m in allm:
            s = monster_passives.passive_specs(m)
            self.assertEqual(s["schema_version"], 1)
            self.assertIn("pending", s)
            self.assertIn("sources", s)
            # every ability must appear in sources
            self.assertEqual(len(s["sources"]), len(m.get("abilities") or []))
        t = monster_passives.passive_specs(monster_catalog.get_catalog_monster("troll"))
        self.assertTrue(len(t["sources"][0]["text"]) > 100)


if __name__ == "__main__":
    unittest.main()
