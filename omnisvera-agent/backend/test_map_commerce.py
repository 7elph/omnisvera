"""Player commerce: native inventory/ledger, isolated SQLite and deterministic dice."""
import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_merchant
from app.access import AccessContext
from app import map_commerce as shop
from app.merchant import add_stock, purse_copper
from app.session_workspace import save_workspace_token


class MapCommerceTests(unittest.TestCase):
    purse = test_merchant.MerchantTests.purse
    def setUp(self):
        test_merchant.MerchantTests.setUp(self)
        shop.initialize(self.db)
        self.gm = AccessContext(mode='gm')
        self.owner = AccessContext(mode='player', profile_id='vezemir')
        self.pin = save_workspace_token(self.db, token_type='location', name='Balcão',
            latitude=40, longitude=40, visible_to_players=True)
        self.mid = self.merchant['id']
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT OR REPLACE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','Nimalis','map.png','now')")
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Nimalis','map.png',1,'now','now')")
        shop.configure(self.db, self.mid, self.gm, token_id=self.pin['id'], npc_id=None,
            location_id=None, enabled=True, buy_pct=50)
        self.line = add_stock(self.db, merchant_id=self.mid,
            compendium_item_id='arma-corpo-espada-longa', quantity=2)

    def quote(self, key='quote-0001', **changes):
        return shop.quote(self.db, self.mid, self.owner, request_id=key,
            character_id='vezemir', kind=changes.pop('kind','buy'),
            target_id=changes.pop('target_id',self.line['id']), quantity=changes.pop('quantity',1), **changes)

    def test_purchase_retry_persists_one_receipt(self):
        before = purse_copper(self.purse())
        with closing(sqlite3.connect(self.db)) as db:
            version=db.execute("SELECT version FROM character_states WHERE profile_id='vezemir'").fetchone()[0]
        quote = self.quote()
        result = shop.confirm(self.db, quote['id'], self.owner, request_id='buy-0001')
        again = shop.confirm(self.db, quote['id'], self.owner, request_id='buy-0001')
        third = shop.confirm(self.db, quote['id'], self.owner, request_id='buy-0002')
        self.assertEqual(result['receipt_id'], again['receipt_id'])
        self.assertEqual(result['receipt_id'], third['receipt_id'])
        self.assertEqual(purse_copper(self.purse()), before - quote['total_copper'])
        with closing(sqlite3.connect(self.db)) as db, db:
            self.assertEqual(db.execute("SELECT version FROM character_states WHERE profile_id='vezemir'").fetchone()[0],version+1)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='commerce' AND source_id=?",(result['receipt_id'],)).fetchone()[0], 1)
            path = db.execute('SELECT item_path FROM player_inventory').fetchone()[0]
        self.assertEqual(shop.catalog_inventory(path)['damage_formula'], '1d8')

    def test_small_purchase_preserves_gold_and_only_spends_silver(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            state = self.purse()
            state.update(coins=105, silver_coins=25, copper_coins=0, platinum_coins=0)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))
            db.execute('UPDATE merchant_stock SET price_override_po=0.5 WHERE id=?', (self.line['id'],))
        q = self.quote()
        result = shop.confirm(self.db, q['id'], self.owner, request_id='small-buy-001')
        expected = dict(coins=105, silver_coins=20, copper_coins=0, platinum_coins=0)
        self.assertEqual(result['purse_after'], expected)
        self.assertEqual(shop.confirm(self.db, q['id'], self.owner, request_id='small-retry-001'), result)
        self.assertEqual({k:self.purse()[k] for k in expected}, expected)

    def test_owner_hidden_pin_and_reused_key_are_checked(self):
        q = self.quote()
        with self.assertRaises(PermissionError):
            shop.confirm(self.db, q['id'], AccessContext(mode='player',profile_id='raziel'), request_id='steal-001')
        with self.assertRaises(ValueError):
            self.quote(quantity=2)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id=?',(self.pin['id'],))
        self.assertEqual(shop.for_pin(self.db,self.pin['id'],self.owner),[])
        with self.assertRaises(PermissionError):
            shop.confirm(self.db,q['id'],self.owner,request_id='hidden-001')

    def test_bargain_is_bound_and_cannot_reroll_with_new_quote(self):
        with patch('app.map_commerce.roll_formula', return_value={'total':20}) as dice:
            q = self.quote(negotiate=True)
            retry = self.quote('quote-0002',negotiate=True,quantity=2)
        self.assertEqual(dice.call_count,1)
        self.assertEqual(q['bargain']['d20'],retry['bargain']['d20'])
        self.assertEqual(q['unit_copper'],int(q['base_unit_copper']*.8))

    def test_changed_price_and_insufficient_balance_roll_back(self):
        q = self.quote()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE merchant_stock SET price_override_po=99 WHERE id=?',(self.line['id'],))
        with self.assertRaises(ValueError): shop.confirm(self.db,q['id'],self.owner,request_id='changed-001')
        q = self.quote('quote-0002')
        before = self.purse()
        with self.assertRaises(ValueError): shop.confirm(self.db,q['id'],self.owner,request_id='poor-001')
        self.assertEqual(before,self.purse())

    def test_two_buyers_last_item(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE merchant_stock SET quantity=1 WHERE id=?',(self.line['id'],))
            db.execute("INSERT INTO character_states(profile_id,state_json,updated_at) SELECT 'raziel',state_json,updated_at FROM character_states WHERE profile_id='vezemir'")
        other=AccessContext(mode='player',profile_id='raziel')
        quotes=[(self.quote('quote-race-1'),self.owner),
            (shop.quote(self.db,self.mid,other,request_id='quote-race-2',character_id='raziel',kind='buy',target_id=self.line['id']),other)]
        def attempt(pair):
            q,owner=pair
            try: return shop.confirm(self.db,q['id'],owner,request_id='race-'+q['id'])
            except ValueError: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,quotes))
        self.assertEqual(sum(result is not None for result in results),1)

    def test_sell_uses_catalog_price_and_updates_stock(self):
        q=self.quote(); shop.confirm(self.db,q['id'],self.owner,request_id='buy-sell-1')
        with closing(sqlite3.connect(self.db)) as db, db:
            path=db.execute('SELECT item_path FROM player_inventory').fetchone()[0]
        q=self.quote('quote-sell',kind='sell',target_id=path)
        result=shop.confirm(self.db,q['id'],self.owner,request_id='sell-0001')
        self.assertEqual(result['total_copper'],q['total_copper'])
        with closing(sqlite3.connect(self.db)) as db, db:
            self.assertEqual(db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(self.line['id'],)).fetchone()[0],2)

    def test_service_delivery_and_lodging_wait_for_master_rest(self):
        delivery=shop.add_service(self.db,self.mid,self.gm,name='Entrega de adaga',kind='delivery',
            price_copper=1,compendium_item_id='arma-corpo-espada-longa',amount=1)
        q=self.quote('quote-service',kind='service',target_id=delivery['id'])
        shop.confirm(self.db,q['id'],self.owner,request_id='service-001')
        lodging=shop.add_service(self.db,self.mid,self.gm,name='Hospedagem',kind='lodging',price_copper=1)
        before=self.purse()['current_hp']
        q=self.quote('quote-room',kind='service',target_id=lodging['id'])
        result=shop.confirm(self.db,q['id'],self.owner,request_id='room-001')
        self.assertEqual(self.purse()['current_hp'],before)
        self.assertEqual(result['service_status'],'reserved')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.row_factory=sqlite3.Row
            shop.complete_lodging(db,'vezemir')
            self.assertEqual(db.execute('SELECT status FROM merchant_service_orders').fetchone()[0],'completed')

    def test_player_payload_forbids_price_and_other_character(self):
        from app.commerce_routes import QuoteRequest
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            QuoteRequest(request_id='quote-1234',character_id='vezemir',kind='buy',target_id='x',final_price_po=0)
        with self.assertRaises(PermissionError):
            shop.quote(self.db,self.mid,self.owner,request_id='bad-owner',character_id='raziel',kind='buy',target_id=self.line['id'])

    def test_failed_bargain_invalidates_old_quote_and_cannot_be_bypassed(self):
        original=self.quote()
        with patch('app.map_commerce.roll_formula',return_value={'total':1}):
            negotiated=self.quote('quote-failed',negotiate=True)
        self.assertGreater(negotiated['unit_copper'],original['unit_copper'])
        with self.assertRaises(ValueError): shop.confirm(self.db,original['id'],self.owner,request_id='old-price-01')
        plain=self.quote('quote-plain')
        self.assertEqual(plain['unit_copper'],negotiated['unit_copper'])

    def test_expired_quote_disabled_shop_and_equipped_sale_reject(self):
        q=self.quote()
        with patch('app.map_commerce.time.time',return_value=q['expires_at']+1):
            with self.assertRaises(ValueError): shop.confirm(self.db,q['id'],self.owner,request_id='expired-001')
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],enabled=False)
        self.assertEqual(shop.for_pin(self.db,self.pin['id'],self.owner),[])
        with self.assertRaises(PermissionError): self.quote('disabled-quote')
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'])
        shop.confirm(self.db,q['id'],self.owner,request_id='equipped-buy')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET equipped=1')
            path=db.execute('SELECT item_path FROM player_inventory').fetchone()[0]
        self.assertEqual(shop.for_pin(self.db,self.pin['id'],self.owner,'vezemir')[0]['sellable'],[])
        with self.assertRaises(ValueError): self.quote('equipped-sale',kind='sell',target_id=path)

    def test_npc_history_private_data_not_exposed_and_master_rest_completes_lodging(self):
        from app.npc_memory import init_npc_memory,create_npc
        from app.character_play import apply_character_action
        init_npc_memory(self.db)
        npc,_=create_npc(self.db,request_id='npc-commerce-001',campaign_id='omnisvera',actor_id='master',
            fields={'name':'Mercador','visible_to_players':True,'private_description':'SEGREDO-NPC'})
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],npc_id=npc['id'])
        safe=shop.for_pin(self.db,self.pin['id'],self.owner,'vezemir')
        self.assertNotIn('SEGREDO-NPC',json.dumps(safe))
        lodging=shop.add_service(self.db,self.mid,self.gm,name='Quarto',kind='lodging',price_copper=1)
        q=self.quote('lodging-npc-001',kind='service',target_id=lodging['id'])
        shop.confirm(self.db,q['id'],self.owner,request_id='room-npc-001')
        expired_by_rest=self.quote('before-rest-quote')
        with closing(sqlite3.connect(self.db)) as db,db:
            self.assertEqual(db.execute("SELECT count(*) FROM npc_events WHERE event_type='commerce'").fetchone()[0],1)
        apply_character_action(self.db,character_id='vezemir',action='rest_at_inn',payload={},reason='Descanso do Mestre',
            actor_id='master',actor_role='gm',request_id='rest-commerce-001')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT status FROM merchant_service_orders').fetchone()[0],'completed')
        self.assertEqual(self.purse()['commerce_rest_epoch'],1)
        with self.assertRaises(ValueError):
            shop.confirm(self.db,expired_by_rest['id'],self.owner,request_id='after-rest-confirm')

    def test_bargain_renews_on_master_rest_and_catalog_placeholder_is_not_damage(self):
        from app.character_play import apply_character_action
        with patch('app.map_commerce.roll_formula',return_value={'total':20}) as dice:
            self.quote('bargain-before',negotiate=True)
            apply_character_action(self.db,character_id='vezemir',action='rest_at_inn',payload={},actor_id='master',actor_role='gm',request_id='rest-bargain-001')
            self.quote('bargain-after',negotiate=True)
            self.assertEqual(dice.call_count,2)
        self.assertIsNone(shop.catalog_inventory('compendium:arma-distancia-arco-curto')['damage_formula'])

    def test_merchant_creation_and_configuration_are_private(self):
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT visibility FROM session_ledger WHERE source_type='merchant'").fetchone()[0],'gm')

    def test_player_cannot_bind_or_add_service_and_deleted_service_rejects_quote(self):
        with self.assertRaises(PermissionError):
            shop.configure(self.db,self.mid,self.owner,token_id=self.pin['id'])
        with self.assertRaises(PermissionError):
            shop.add_service(self.db,self.mid,self.owner,name='x',kind='lodging',price_copper=0)
        service=shop.add_service(self.db,self.mid,self.gm,name='Quarto',kind='lodging',price_copper=1)
        q=self.quote('delete-service',kind='service',target_id=service['id'])
        shop.remove_service(self.db,self.mid,service['id'],self.gm)
        with self.assertRaises(ValueError): shop.confirm(self.db,q['id'],self.owner,request_id='deleted-001')
