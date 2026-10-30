import unittest
from app.action_cards import active_effect_icons


class ActiveEffectIconTests(unittest.TestCase):
    def setUp(self):
        self.card = dict(id='velocidade', name='Velocidade', image_path='speed.jpg', description='Público', private='secret')
        self.effect = dict(id='effect1', target_type='character', target_id='vezemir',
                           label='Velocidade', source='Velocidade (Vezemir)', duration='rounds', rounds=3)

    def icons(self, effects):
        return active_effect_icons(effects, lambda _: [self.card], ['vezemir'])

    def test_current_catalog_icon_without_ledger_and_no_private_fields(self):
        value = self.icons([self.effect])[0]
        self.assertEqual(value['card']['image_path'], 'speed.jpg')
        self.assertEqual(value['rounds'], 3)
        self.assertNotIn('private', value['card'])
        self.assertNotIn('source', value)

    def test_expiration_removal_and_fictional_time(self):
        self.assertEqual(self.icons([]), [])
        self.assertEqual(self.icons([{**self.effect, 'rounds': 0}]), [])
        self.assertEqual(self.icons([{**self.effect, 'duration': 'fictional_time', 'remaining_seconds': 0}]), [])
        self.assertEqual(len(self.icons([{**self.effect, 'duration': 'next_attack', 'rounds': None}])), 1)

    def test_hidden_and_unknown_cards_not_exposed(self):
        self.card['hidden'] = True
        self.assertEqual(self.icons([self.effect]), [])
        self.card['hidden'] = False
        self.assertEqual(self.icons([{**self.effect, 'label': 'Segredo', 'source': 'Mestre'}]), [])

    def test_longest_name_and_target_identity(self):
        icons = active_effect_icons([{**self.effect, 'target_type': 'token', 'target_id': 'enemy'}],
            lambda _: [self.card, dict(id='short', name='Velo', image_path='wrong.jpg')], ['vezemir'])
        self.assertEqual(icons[0]['target_id'], 'enemy')
        self.assertEqual(icons[0]['card']['id'], 'velocidade')

    def test_active_night_form_uses_selected_animal_image(self):
        effect = {**self.effect, 'label': 'Forma da Noite', 'duration': 'manual', 'rounds': None, 'animal': 'morcego'}
        icons = active_effect_icons([effect], lambda _: [dict(id='forma-da-noite', name='Forma da Noite')], ['raziel'])
        self.assertTrue(icons[0]['card']['image_path'].endswith('raziel_morcego_82a3c8733e.jpg'))
