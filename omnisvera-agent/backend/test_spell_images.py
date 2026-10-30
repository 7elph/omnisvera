import unittest
from app.character_play import attach_spell_images, load_session_abilities


class SpellImageTests(unittest.TestCase):
    def test_four_new_morthak_images_preserve_spell_rules_and_exist(self):
        from pathlib import Path
        from app.level_advancement import NECROMANCER_ABILITIES_5
        descriptions = {ability['id']: ability['description'] for ability in NECROMANCER_ABILITIES_5}
        originals = [
            {'id': ident, 'kind': 'spell', 'circle': 5, 'description': descriptions.get(ident, 'Regra preservada'),
             'uses': {'maximum': 1, 'resource_key': ident}, 'active': True}
            for ident in ('clonagem', 'magia-da-morte', 'toque-sombrio', 'aterrorizar')
        ]
        actual = attach_spell_images(originals)
        public = Path(__file__).resolve().parents[1] / 'frontend' / 'public'
        for before, after in zip(originals, actual):
            self.assertEqual(after.get('image_path'), f"companion-assets/morthak-{before['id']}.jpg")
            self.assertEqual({k: v for k, v in after.items() if k != 'image_path'}, before)
            self.assertTrue((public / after['image_path']).is_file())

    def test_four_dorn_spells_keep_their_mechanics(self):
        from app.dorn_mage import SPEC
        spells = [a for a in SPEC['abilities'] if a['kind'] == 'spell']
        enriched = attach_spell_images(spells)
        self.assertEqual(len(enriched), 4)
        for original, actual in zip(spells, enriched):
            self.assertTrue(actual['image_path'].endswith('.png'))
            self.assertEqual({k: v for k, v in actual.items() if k != 'image_path'}, original)

    def test_morthak_shares_missile_art_not_resources(self):
        missile = next(a for a in load_session_abilities('morthak') if a['id'] == 'misseis-magicos')
        dorn = attach_spell_images([{'id': 'misseis-magicos', 'kind': 'spell'}])[0]
        self.assertEqual(missile['image_path'], dorn['image_path'])
        self.assertNotEqual(missile['uses']['resource_key'], 'dorn_misseis_magicos')

    def test_unmapped_abilities_and_resources_unchanged(self):
        entries = [{'id': 'unknown', 'kind': 'spell'}, {'id': 'unknown-trait', 'kind': 'ability'}, {'id': 'unknown-resource', 'kind': 'resource'}]
        self.assertEqual(attach_spell_images(entries), entries)

    def test_five_morthak_images_preserve_passives_and_consumption(self):
        import json
        from app.character_play import SESSION_ABILITY_CATALOG_PATH
        originals = {a['id']: a for a in json.loads(SESSION_ABILITY_CATALOG_PATH.read_text(encoding='utf-8'))['characters']['morthak']}
        actual = {a['id']: a for a in load_session_abilities('morthak')}
        for ident in ('adaga-de-osso', 'levantar-um-esqueleto', 'nao-vida-consciente-esqueleto', 'animar-mortos', 'memoria-fraturada'):
            self.assertTrue(actual[ident]['image_path'].endswith('.jpg'))
            self.assertEqual(actual[ident]['description'], originals[ident]['description'])
            self.assertEqual(actual[ident]['active'], originals[ident].get('active', True))
            if 'uses' in originals[ident]:
                self.assertEqual(actual[ident]['uses']['maximum'], originals[ident]['uses']['maximum'])

    def test_vezemir_powers_receive_their_own_art(self):
        powers = load_session_abilities('vezemir')
        for ident in ('forca-arcana', 'velocidade'):
            ability = next(a for a in powers if a['id'] == ident)
            self.assertTrue(ability['image_path'].endswith('.jpg'))
            self.assertEqual(ability['uses']['maximum'], 1)

    def test_remaining_morthak_traits_receive_art_and_remain_passive(self):
        abilities = {a['id']: a for a in load_session_abilities('morthak')}
        for ident in ('chamado-necromantico', 'ossos-sem-carne', 'repouso-imovel', 'corpo-quebradico', 'cura-antinatural', 'afastar-mortos-vivos'):
            self.assertTrue(abilities[ident]['image_path'].endswith('.jpg'))
            self.assertFalse(abilities[ident]['active'])
            self.assertNotIn('uses', abilities[ident])

    def test_raziel_passive_traits_receive_distinct_art_without_rule_changes(self):
        from unittest.mock import patch
        ids = ('nao-vida-consciente-vampiro', 'visao-no-escuro-vampiro', 'imunidades-vampiricas', 'fotossensibilidade', 'cura-vampirica-invertida')
        with patch('app.character_play.attach_spell_images', side_effect=lambda entries: entries):
            originals = {a['id']: a for a in load_session_abilities('raziel')}
        actual = {a['id']: a for a in load_session_abilities('raziel')}
        for ident in ids:
            self.assertTrue(actual[ident]['image_path'].endswith('.jpg'))
            self.assertFalse(actual[ident]['active'])
            self.assertEqual({k: v for k, v in actual[ident].items() if k != 'image_path'}, originals[ident])
        self.assertEqual(len({actual[ident]['image_path'] for ident in ids}), 5)
        skeleton = next(a for a in load_session_abilities('morthak') if a['id'] == 'nao-vida-consciente-esqueleto')
        self.assertNotEqual(skeleton['image_path'], actual['nao-vida-consciente-vampiro']['image_path'])

    def test_remaining_raziel_art_preserves_rules_and_blocks(self):
        from unittest.mock import patch
        ids = ('regeneracao-vampirica', 'fome-de-sangue', 'medo-vampirico', 'sentido-do-sangue', 'corpo-predatorio')
        with patch('app.character_play.attach_spell_images', side_effect=lambda entries: entries):
            originals = {a['id']: a for a in load_session_abilities('raziel')}
        actual = {a['id']: a for a in load_session_abilities('raziel')}
        for ident in ids:
            self.assertTrue(actual[ident]['image_path'].endswith('.jpg'))
            self.assertEqual({k: v for k, v in actual[ident].items() if k != 'image_path'}, originals[ident])
        self.assertFalse(actual['fome-de-sangue']['active'])
        self.assertFalse(actual['sentido-do-sangue']['blocked'])
        self.assertTrue(actual['corpo-predatorio']['blocked'])

    def test_raziel_art_preserves_all_rules(self):
        ids = ('reserva-de-sangue', 'lamina-de-sangue', 'marca-rubra', 'caixao', 'mordida')
        actual = {a['id']: a for a in load_session_abilities('raziel')}
        for ident in ids:
            ability = actual[ident]
            self.assertTrue(ability['image_path'].endswith('.jpg'))
            original = {k: v for k, v in ability.items() if k != 'image_path'}
            self.assertEqual(attach_spell_images([original])[0], ability)
            self.assertEqual(original, {k: v for k, v in attach_spell_images([original])[0].items() if k != 'image_path'})
        self.assertEqual(actual['reserva-de-sangue']['uses']['maximum'], 10)
        self.assertEqual(actual['reserva-de-sangue']['uses']['resource_key'], 'reserva_de_sangue')

    def test_approved_dorn_definition_also_gets_images(self):
        from app.character_play import build_character_definition
        from app.dorn_mage import SPEC
        result = build_character_definition(profile_id='dorn7', note={'path':'fixture.md', 'title':'Dorn', 'frontmatter':{}, 'content':''},
            sheet=SPEC['sheet'], inventory=[], overrides={'approved_build':SPEC['version'], 'approved_session_abilities':SPEC['abilities']})
        spells = [a for a in result['session_abilities'] if a['kind'] == 'spell']
        self.assertEqual(len(spells), 4)
        self.assertTrue(all(a.get('image_path') for a in spells))
