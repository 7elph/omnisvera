import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class ItemCoverageRegressionTests(unittest.TestCase):
    def test_audit_distinguishes_native_executor_from_missing_adapter(self):
        from app.item_registry import audit_items
        from app.item_catalog import get_catalog_item
        entries={}
        for identity in ['arma-corpo-espada-longa','item-magico-manto-da-confusao','item-magico-espelho-de-oposicao']:
            item=get_catalog_item(identity)
            entries[identity]={'id':identity,'name':item['name'],'catalog_entry_kind':'item','trade_group':'equipment',
                'price_copper':100,'image_path':'fixture.png','description':item['description'],'effect_rules':item.get('effect_rules') or [],
                'mechanics':item['mechanics'],'revision':'fixture','source_kind':'book','source_snapshot':{}}
        with TemporaryDirectory() as folder:
            path=Path(folder)/'isolated.sqlite3';sqlite3.connect(path).close()
            with patch('app.item_registry.registry',return_value={'entries':entries}):report=audit_items(path)
        by_id={item['id']:item for item in report['items']}
        self.assertNotIn('mechanics_review',by_id['arma-corpo-espada-longa']['gaps'])
        self.assertNotIn('mechanics_review',by_id['item-magico-manto-da-confusao']['gaps'])
        self.assertIn('mechanics_review',by_id['item-magico-espelho-de-oposicao']['gaps'])
        self.assertEqual('native',by_id['arma-corpo-espada-longa']['mechanical_coverage']['status'])
        self.assertEqual('not_certified',by_id['arma-corpo-espada-longa']['automation_status'])
