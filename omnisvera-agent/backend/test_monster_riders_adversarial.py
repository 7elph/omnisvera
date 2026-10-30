from __future__ import annotations

import unittest

from app import monster_riders


class MonsterRidersAdversarialTests(unittest.TestCase):
    def test_attack_indices_must_be_list_of_integers(self):
        m = {"id": "x", "attacks": [{"name": "Garras", "raw": "", "damage": ""}], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras causa paralisia (JPC nega), duração 2d4 turnos."},
        ]}
        s = monster_riders.rider_specs(m)
        if s["on_hit"]:
            for oh in s["on_hit"]:
                self.assertIsInstance(oh.get("attack_indices"), list)
                for a in oh.get("attack_indices"):
                    self.assertIsInstance(a, int)

    def test_paralysis_without_jp_does_not_default_to_jpc(self):
        m = {"id": "x", "attacks": [{"name": "Garras", "raw": "", "damage": ""}], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras causa paralisia, duração 2d4 turnos."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])

    def test_empty_attacks_no_rider(self):
        m = {"id": "x", "attacks": [], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras causa paralisia (JPC nega), duração 2d4 turnos."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])

    def test_poison_does_not_grant_paralysis_from_other_ability(self):
        m = {"id": "x", "attacks": [{"name": "Mordida", "raw": "", "damage": "1d4 + Veneno"}], "abilities": [
            {"name": "Veneno", "description": "A mordida inocula veneno: 1d6 de dano adicional, JPC reduz à metade."},
            {"name": "Paralisia", "description": "Um efeito distinto não vinculado a este ataque."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertFalse(any(oh["effect"] == "paralyzed" for oh in s["on_hit"]))
        self.assertTrue(any(oh["effect"] == "poison_damage" for oh in s["on_hit"]))

    def test_periodic_poison_never_becomes_a_single_damage_roll(self):
        m={"id":"x","attacks":[{"name":"Mordida","damage":"1d4 + Veneno"}],"abilities":[
            {"name":"Veneno","description":"A mordida causa 1d6 de dano por rodada por 2d4 rodadas. JPC nega."}]}
        self.assertEqual(monster_riders.rider_specs(m)['on_hit'],[])

    def test_ghoul_id_without_source_no_free_rider(self):
        m = {"id": "ghoul", "attacks": [], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras causa paralisia (JPC nega), duração 2d4 turnos."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])

    def test_gaze_without_known_id_no_onhit(self):
        m = {"id": "unknown-gaze", "attacks": [{"name": "Olhar", "raw": "1x Olhar", "damage": ""}], "abilities": [
            {"name": "Olhar Petrificante", "description": "O olhar petrifica (JPC nega)."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])

    def test_immunity_to_petrification_does_not_apply_attack_rider(self):
        m = {"id": "x", "attacks": [{"name": "Bicada", "raw": "", "damage": ""}], "abilities": [
            {"name": "Imunidade", "description": "Imune a petrificação."},
            {"name": "Petrificação", "description": "Bicada causa petrificação (JPC nega)."},
        ]}
        s = monster_riders.rider_specs(m)
        # não deve criar rider on_hit por mera imunidade
        self.assertFalse(any(oh["effect"] == "petrified" for oh in s["on_hit"]))

    def test_does_not_paralyze_on_nega(self):
        m = {"id": "x", "attacks": [{"name": "Garras", "raw": "", "damage": ""}], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras não paralisa ou a habilidade nega paralisia (JPC nega)?"},
        ]}
        s = monster_riders.rider_specs(m)
        # se claramente nega, não criar
        self.assertEqual(s["on_hit"], [])

    def test_duration_formula_and_unit_preserved_1d3_plus_turns(self):
        m = {"id": "x", "attacks": [{"name": "Garras", "raw": "", "damage": ""}], "abilities": [
            {"name": "Paralisia", "description": "Ataque com garras causa paralisia (JPC nega), duração 1d3+1 turnos."},
        ]}
        s = monster_riders.rider_specs(m)
        if s["on_hit"]:
            p = s["on_hit"][0]
            self.assertEqual(p["duration_unit"], "turns")
            self.assertIsNotNone(p["duration_formula"])

    def test_dex_drain_poison_not_paralysis(self):
        m = {"id": "x", "attacks": [{"name": "Mordida", "raw": "", "damage": "1d4 + Veneno"}], "abilities": [
            {"name": "Veneno", "description": "Veneno drena Destreza permanentemente (JPC nega)."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])
        self.assertTrue(any(p["reason"].find("atributo") >= 0 or p["reason"].find("dreno") >= 0 for p in s["pending"]))

    def test_sleep_delayed_not_immediate(self):
        m = {"id": "x", "attacks": [{"name": "Garras", "raw": "", "damage": ""}], "abilities": [
            {"name": "Sono", "description": "Após 1d6+5 rodadas, causa sono (JPS nega)."},
        ]}
        s = monster_riders.rider_specs(m)
        self.assertEqual(s["on_hit"], [])
        self.assertTrue(any(p["reason"].find("atras") >= 0 or p["reason"].find("chance") >= 0 or p["reason"].find("sono") >= 0 for p in s["pending"]))


if __name__ == "__main__":
    unittest.main()
