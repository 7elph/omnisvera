"""Catalogue/offer guard: isolated shops and pure reports, no campaign mutations."""
from contextlib import closing
import sqlite3
from unittest import TestCase
from unittest.mock import patch

from app import item_catalog as catalog, map_commerce as shop, merchant
from app.catalog_readiness import _item_entry
import test_map_commerce as baseline


class ItemOfferReadinessTests(TestCase):
    def test_references_stay_blocked_even_with_a_zero_price_override(self):
        ref = next(i for i in catalog.load_item_catalog()['items'] if catalog.is_catalog_reference(i))
        report = catalog.item_offer_readiness(ref, price_override_po=0)
        self.assertFalse(report['commerce_ready'])
        self.assertIn('entrada_de_tabela_nao_concreta', report['blocking_gaps'])

    def test_missing_invalid_and_legitimate_zero_prices_are_distinct(self):
        item = {'id':'ordinary','name':'Corda','category':'kit-basico','description':'Corda comum','source':'fixture'}
        self.assertIn('preco_ausente', catalog.item_offer_readiness(item)['blocking_gaps'])
        for value in [float('nan'), float('inf'), -1, True, 'NaN']:
            with self.subTest(value=value):
                self.assertIn('preco_invalido', catalog.item_offer_readiness(item, price_override_po=value)['blocking_gaps'])
        self.assertTrue(catalog.item_offer_readiness(item, price_override_po=0)['commerce_ready'])

    def test_special_description_does_not_claim_an_automated_effect(self):
        item = catalog.get_catalog_item('item-magico-tapete-voador')
        report = catalog.item_offer_readiness(item)
        self.assertTrue(report['commerce_ready'])
        self.assertEqual('assisted', report['effect_status'])
        self.assertIn('efeito_especial_assistido', report['warnings'])
        report = catalog.item_offer_readiness(item, require_automated_effect=True)
        self.assertFalse(report['commerce_ready'])
        self.assertIn('efeito_automatizado_nao_comprovado', report['blocking_gaps'])

    def test_prices_or_weights_inside_a_concrete_title_do_not_make_a_table_fragment(self):
        item = catalog.get_catalog_item('propriedades-carroca-capacidade-de-carga-100-kg-8-po')
        report = _item_entry(item, 'OD1')
        self.assertTrue(report['concrete'])
        self.assertTrue(report['offer_readiness']['commerce_ready'])
        self.assertNotIn('entrada_de_tabela_nao_concreta', report['gaps'])


class ExistingShopReadinessTests(TestCase):
    setUp = baseline.MapCommerceTests.setUp
    purse = baseline.MapCommerceTests.purse
    quote = baseline.MapCommerceTests.quote

    def legacy_reference(self):
        ref = next(i for i in catalog.load_item_catalog()['items'] if catalog.is_catalog_reference(i))
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE merchant_stock SET compendium_item_id=?,name=?,price_override_po=0 WHERE id=?',
                (ref['id'],ref['name'],self.line['id']))
        return ref

    def test_legacy_reference_stock_cannot_quote_or_mutate_money(self):
        self.legacy_reference(); before = self.purse()
        with self.assertRaisesRegex(ValueError, 'referência|tabela'): self.quote()
        self.assertEqual(before, self.purse())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(2, db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(self.line['id'],)).fetchone()[0])

    def test_confirm_revalidates_catalogue_after_quote_without_spending(self):
        quoted = self.quote(); before = self.purse(); self.legacy_reference()
        with self.assertRaises(ValueError): shop.confirm(self.db,quoted['id'],self.owner,request_id='confirm-bad-catalog')
        self.assertEqual(before,self.purse())

    def test_legacy_gm_purchase_cannot_bypass_the_reference_guard(self):
        self.legacy_reference(); before = self.purse()
        with self.assertRaisesRegex(ValueError,'referência|tabela'):
            merchant.buy(self.db,request_id='readiness-buy-001',merchant_id=self.mid,stock_id=self.line['id'],character_id='vezemir',final_price_po=0)
        self.assertEqual(before,self.purse())

    def test_native_stock_rejects_nonfinite_prices_but_keeps_explicit_free_offers(self):
        for price in [float('nan'),float('inf')]:
            with self.subTest(price=price), self.assertRaises(ValueError):
                merchant.add_stock(self.db,merchant_id=self.mid,compendium_item_id='arma-corpo-espada-longa',price_override_po=price)
        free = merchant.add_stock(self.db,merchant_id=self.mid,compendium_item_id='arma-corpo-espada-longa',price_override_po=0)
        self.assertEqual(0, self.quote('quote-free-0001',target_id=free['id'])['total_copper'])

    def test_delivery_service_cannot_give_a_reference_and_legacy_service_is_blocked(self):
        ref = self.legacy_reference()
        with self.assertRaisesRegex(ValueError,'referência|tabela'):
            shop.add_service(self.db,self.mid,self.gm,name='Entrega inválida',kind='delivery',price_copper=0,compendium_item_id=ref['id'])
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('INSERT INTO merchant_services(id,merchant_id,name,kind,price_copper,compendium_item_id,amount,active) VALUES(?,?,?,?,?,?,?,1)',
                ('bad-service',self.mid,'Entrega legada','delivery',0,ref['id'],1))
        with self.assertRaises(ValueError): self.quote(kind='service',target_id='bad-service')

    def test_gm_report_is_read_only_and_hidden_gap_names_never_reach_players(self):
        self.legacy_reference()
        with closing(sqlite3.connect(self.db)) as db:
            before = db.execute('SELECT * FROM merchant_stock').fetchall()
        report = shop.offer_readiness_report(self.db,self.gm)
        self.assertEqual(1,report['counts']['blocked'])
        self.assertIn('entrada_de_tabela_nao_concreta',report['offers'][0]['readiness']['blocking_gaps'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(before,db.execute('SELECT * FROM merchant_stock').fetchall())
        gm = shop.for_pin(self.db,self.pin['id'],self.gm)[0]
        player = shop.for_pin(self.db,self.pin['id'],self.owner)[0]
        self.assertEqual([],player['offers'])
        self.assertNotIn('blocked_offers',player)
        self.assertEqual(1,len(gm['blocked_offers']))
        with self.assertRaises(PermissionError): shop.offer_readiness_report(self.db,self.owner)
