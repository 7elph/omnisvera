"""Approved estimates are metadata, never a source of combat/economy rules."""
import copy
import math
import unittest


class ItemDimensionsTests(unittest.TestCase):
    def test_source_weight_and_combat_rules_survive_catalog_and_inventory_projection(self):
        from app.item_catalog import get_catalog_item, normalize_catalog_item
        from app.map_commerce import catalog_inventory
        item = get_catalog_item('arma-corpo-espada-longa')
        mechanics = item['mechanics']
        self.assertEqual(mechanics['weight_kg'], 2)
        self.assertNotIn('weight_kg', mechanics['physical_metadata']['estimated_fields'])
        self.assertEqual(mechanics['physical_metadata']['status'], 'provisional_campaign')
        native = catalog_inventory('compendium:' + item['id'])
        for field in ('weight_kg', 'container_entry_cm', 'storage_volume_m3',
                      'container_packed_length_cm', 'physical_metadata'):
            self.assertEqual(native['mechanics'][field], mechanics[field])
        self.assertEqual(normalize_catalog_item(item), item)
        self.assertEqual(item['dano'], '1d8')

    def test_explicit_values_including_invalid_values_are_not_silently_replaced(self):
        from app.item_dimensions import enrich
        original = {'id': 'arma-corpo-espada-longa', 'name': 'Espada longa',
                    'category': 'arma-corpo', 'mechanics': {'weight_kg': 7,
                    'container_entry_cm': 44, 'container_packed_length_cm': 150,
                    'storage_volume_m3': 0.03}, 'preco_po': 10, 'effect_rules': []}
        before = copy.deepcopy(original)
        result = enrich(original)
        self.assertEqual(original, before)
        self.assertEqual(result, original)
        original['mechanics']['container_entry_cm'] = -1
        self.assertEqual(enrich(original)['mechanics']['container_entry_cm'], -1)

    def test_source_kit_weight_does_not_use_carrying_capacity(self):
        from app.item_catalog import load_item_catalog
        backpack = next(i for i in load_item_catalog()['items']
                        if i['id'].startswith('kit-basico-mochila-'))
        self.assertEqual(backpack['mechanics']['weight_kg'], 2)
        self.assertNotIn('weight_kg', backpack['mechanics']['physical_metadata']['estimated_fields'])

    def test_pack_metadata_is_for_one_inventory_pack_not_one_projectile(self):
        from app.item_catalog import get_catalog_item
        item = get_catalog_item('arma-distancia-flecha-x20-2')
        self.assertEqual(item['mechanics']['weight_kg'], 1.5)
        self.assertEqual(item['mechanics']['physical_metadata']['unit'], 'inventory_unit')
        self.assertGreater(item['mechanics']['container_packed_length_cm'], 60)

    def test_no_estimates_for_table_fragments_services_property_or_unknown_custom_items(self):
        from app.item_catalog import load_item_catalog
        from app.item_dimensions import enrich
        for item in load_item_catalog()['items']:
            if item['catalog_entry_kind'] == 'reference' or item['category'] in {'hospedagem', 'servico-magico', 'propriedades'}:
                self.assertNotIn('physical_metadata', item.get('mechanics', {}), item['id'])
        custom = {'id': 'unknown', 'category': 'item', 'name': 'Relíquia sem medidas'}
        self.assertEqual(enrich(custom), custom)

    def test_all_named_portable_catalog_families_have_finite_dimensions_without_changing_source(self):
        import json
        from app.item_catalog import CATALOG_PATH, load_item_catalog
        source = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
        names = {i['id']: i for i in source['items']}
        for item in load_item_catalog()['items']:
            if item['catalog_entry_kind'] != 'item' or item['category'] not in {
                'arma-corpo', 'arma-distancia', 'protecao', 'item-classe',
                'item-magico', 'kit-basico', 'kit-explorador'}:
                continue
            for field in ('weight_kg', 'container_entry_cm', 'storage_volume_m3', 'container_packed_length_cm'):
                value = item['mechanics'][field]
                self.assertTrue(math.isfinite(value) and (value >= 0 if field == 'weight_kg' else value > 0), (item['id'], field))
            if item['id'] in names:
                for field in ('preco_po', 'dano', 'bonus_defesa'):
                    self.assertEqual(item.get(field), names[item['id']].get(field), (item['id'], field))
                if names[item['id']].get('peso'):
                    self.assertEqual(item.get('peso'), names[item['id']]['peso'])
