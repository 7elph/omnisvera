from __future__ import annotations

import unittest

from app.monster_catalog import get_catalog_monster
from app.monster_poison_specs import poison_specs


class MonsterPoisonSpecsTests(unittest.TestCase):
    def _copy_with_custom_id(self, monster):
        m2 = dict(monster)
        m2['id'] = 'custom-id'
        return m2

    def test_catalog_cerbero_real(self):
        m = get_catalog_monster('cerbero')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'poison_attribute_periodic')
        self.assertEqual(hit['attribute'], 'dexterity')
        self.assertEqual(hit['amount_formula'], '1d6')
        self.assertEqual(hit['interval_seconds'], 600)
        self.assertEqual(hit['floor'], 0)
        self.assertTrue(hit['lethal_at_floor'])

    def test_catalog_cerbero_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('cerbero'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['monster_id'], 'custom-id')
        self.assertEqual(hit['effect'], 'poison_attribute_periodic')
        self.assertEqual(hit['attribute'], 'dexterity')

    def test_catalog_drider_real(self):
        m = get_catalog_monster('drider')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'poison_attribute_periodic')
        self.assertEqual(hit['attribute'], 'dexterity')
        self.assertEqual(hit['amount_formula'], '1d6')
        self.assertEqual(hit['interval_seconds'], 600)
        self.assertEqual(hit['floor'], 3)
        self.assertFalse(hit['lethal_at_floor'])

    def test_catalog_drider_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('drider'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['monster_id'], 'custom-id')
        self.assertEqual(hit['floor'], 3)
        self.assertFalse(hit['lethal_at_floor'])

    def test_catalog_naga_negra_real_not_sleep(self):
        m = get_catalog_monster('naga-negra')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'poison_attribute_periodic')
        self.assertEqual(hit['attribute'], 'intelligence')
        self.assertEqual(hit['amount_formula'], '1d6')
        self.assertEqual(hit['floor'], 0)
        self.assertTrue(hit['lethal_at_floor'])
        self.assertNotIn('asleep', str(hit))
        self.assertNotIn('sleep', str(hit))

    def test_catalog_naga_negra_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('naga-negra'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['monster_id'], 'custom-id')
        self.assertEqual(hit['attribute'], 'intelligence')
        self.assertNotIn('asleep', str(hit))

    def test_catalog_centipeia_gigante_real(self):
        m = get_catalog_monster('centopeia-gigante')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'poison_attribute')
        self.assertEqual(hit['attribute'], 'constitution')
        self.assertEqual(hit['amount_formula'], '1d4+2')
        self.assertIsNone(hit['interval_seconds'])
        self.assertIsNone(hit['duration'])
        self.assertIsNone(hit['restoration'])

    def test_catalog_centipeia_gigante_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('centopeia-gigante'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        self.assertEqual(res['on_hit'][0]['monster_id'], 'custom-id')
        self.assertEqual(res['on_hit'][0]['amount_formula'], '1d4+2')

    def test_catalog_vespa_gigante_real(self):
        m = get_catalog_monster('vespa-gigante')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'poison_attribute')
        self.assertEqual(hit['attribute'], 'constitution')
        self.assertEqual(hit['amount_formula'], '1d4+2')

    def test_catalog_vespa_gigante_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('vespa-gigante'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        self.assertEqual(res['on_hit'][0]['monster_id'], 'custom-id')

    def test_catalog_homunculo_real(self):
        m = get_catalog_monster('homunculo')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'delayed_condition')
        self.assertEqual(hit['condition'], 'asleep')
        self.assertEqual(hit['delay_formula'], '1d6+5')
        self.assertEqual(hit['delay_unit'], 'rounds')
        self.assertEqual(hit['duration_formula'], '1d3')
        self.assertEqual(hit['duration_unit'], 'turns')
        self.assertEqual(hit['delay_seconds_per_unit'], 10)
        self.assertEqual(hit['duration_seconds_per_unit'], 600)

    def test_catalog_homunculo_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('homunculo'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        self.assertEqual(res['on_hit'][0]['monster_id'], 'custom-id')
        self.assertEqual(res['on_hit'][0]['condition'], 'asleep')

    def test_catalog_sibilante_real(self):
        m = get_catalog_monster('sibilante')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'delayed_condition')
        self.assertEqual(hit['condition'], 'paralyzed')
        self.assertEqual(hit['delay_formula'], '1d6+2')
        self.assertEqual(hit['delay_unit'], 'rounds')
        self.assertEqual(hit['duration_formula'], '1d3')
        self.assertEqual(hit['duration_unit'], 'turns')

    def test_catalog_sibilante_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('sibilante'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        self.assertEqual(res['on_hit'][0]['monster_id'], 'custom-id')
        self.assertEqual(res['on_hit'][0]['condition'], 'paralyzed')

    def test_catalog_roper_real(self):
        m = get_catalog_monster('roper')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['effect'], 'delayed_attribute')
        self.assertEqual(hit['attribute'], 'strength')
        self.assertEqual(hit['multiplier'], 0.5)
        self.assertEqual(hit['delay_formula'], '1d3')
        self.assertEqual(hit['delay_unit'], 'turns')
        self.assertEqual(hit['duration_formula'], '2d4+1')
        self.assertEqual(hit['duration_unit'], 'turns')
        self.assertIsNone(hit['rounding'])

    def test_catalog_roper_custom_id(self):
        m = self._copy_with_custom_id(get_catalog_monster('roper'))
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 1)
        self.assertEqual(res['on_hit'][0]['monster_id'], 'custom-id')
        self.assertEqual(res['on_hit'][0]['multiplier'], 0.5)
        self.assertIsNone(res['on_hit'][0]['rounding'])

    def test_otyugh_rejected_as_disease(self):
        m = get_catalog_monster('otyugh')
        res = poison_specs(m)
        self.assertEqual(len(res['on_hit']), 0)
        # Should be rejected as disease/infection or not poison-linked
        reasons = ' '.join(str(p.get('reason', '')) for p in res['pending'])
        self.assertTrue('doenca' in reasons or 'infecc' in reasons or 'fora' in reasons)

    def test_negacao(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'não causa perda de Constituição em caso de falha em uma JPC.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(any('negado' in str(p.get('reason','')) for p in res['pending']))

    def test_atributo_sem_dado(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'perde pontos por turno até zero e morrer em caso de falha em uma JPC.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(any('atributo' in str(p.get('reason','')) for p in res['pending']))

    def test_periodico_sem_limite_explicito(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa perda de 1d6 pontos de Destreza por turno em caso de falha em uma JPC.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(len(res['pending']) > 0)

    def test_sono_sem_atraso(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa efeitos soníferos por 1d3 turnos em caso de falha em uma JPC.'}], 'attacks': [{'name': 'Mordida', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(len(res['pending']) > 0)

    def test_ataque_marcado_com_outro_efeito(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa a perda de 1d4+2 pontos de Constituição em caso de falha em uma JPC.'}], 'attacks': [{'name': 'Picada', 'damage': '+Fogo', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(any('vinculo' in str(p.get('reason','')) for p in res['pending']))

    def test_medusa_sem_gatilho_serpente(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'qualquer criatura mordida pelas serpentes do cabelo da Medusa deve ser bem-sucedida em uma JPC para evitar os efeitos do veneno ou cairá morta em 1d3 turnos.'}], 'attacks': []}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(any('gatilho' in str(p.get('reason','')) or 'vinculo' in str(p.get('reason','')) for p in res['pending']))

    def test_wyvern_pendente_generico(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'seu ferrão inocula veneno mortal, capaz de matar em até 1d6+2 rodadas todos os que não passarem em um teste de JPC.'}], 'attacks': [{'name': 'Ferrão', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(len(res['pending']) > 0)

    def test_jp_ausente(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa a perda de 1d4+2 pontos de Constituição.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(any('jp' in str(p.get('reason','')) for p in res['pending']))

    def test_jp_ambigua(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa a perda de 1d4+2 pontos de Constituição em caso de falha em JPD ou JPC.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(len(res['pending']) > 0)

    def test_immunity_title_rejected(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Imunidade', 'description': 'Imune a veneno que causa perda de 1d6 pontos de Destreza por turno até o valor chegar a 3. JPC evita.'}], 'attacks': [{'name': 'Ferrão', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 0)
        self.assertTrue(len(res['pending']) > 0)

    def test_floor_zero_no_explicit_death_not_lethal(self):
        monster = {'id': 'x', 'abilities': [{'name': 'Veneno', 'description': 'causa perda de 1d6 pontos de Destreza por turno até o alvo perder todos os pontos de Destreza. JPC evita.'}], 'attacks': [{'name': 'Picada', 'damage': '+Veneno', 'raw': ''}]}
        res = poison_specs(monster)
        self.assertEqual(len(res['on_hit']), 1)
        hit = res['on_hit'][0]
        self.assertEqual(hit['floor'], 0)
        self.assertFalse(hit['lethal_at_floor'])


if __name__ == '__main__':
    unittest.main()
