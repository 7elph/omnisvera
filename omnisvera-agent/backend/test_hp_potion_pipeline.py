"""Approved S5 potion, bought/granted stocks and retry use isolated SQLite."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from app import map_commerce as shop
from app.access import AccessContext
from app.merchant import add_stock, purse_copper
from app.player_inventory import normalize_inventory_item_mechanics
from app.hp_potions import CATALOG_ID, ITEM_PATH, use_descriptor, coalesce_inventory
import test_map_commerce


class HpPotionPipelineTests(unittest.TestCase):
    setUp = test_map_commerce.MapCommerceTests.setUp
    purse = test_map_commerce.MapCommerceTests.purse
    quote = test_map_commerce.MapCommerceTests.quote

    def test_book_catalog_stays_intact_and_hp_potion_is_an_identified_campaign_addition(self):
        from app.item_catalog import load_item_catalog
        catalog=load_item_catalog()
        self.assertEqual(catalog['source_count'],326)
        self.assertEqual(catalog['count'],327)
        potion=next(item for item in catalog['items'] if item['id']==CATALOG_ID)
        self.assertEqual(potion['source_kind'],'campaign')
        self.assertEqual(potion['source_ref'],ITEM_PATH)
    def custom_potion(self, amount=4, formula='1d4'):
        with closing(sqlite3.connect(self.db)) as db, db:
            rules=[{'id':'fixture-heal','trigger':'on_use','kind':'heal_hp','formula':formula,'target':'','value':0}]
            row=db.execute("INSERT INTO session_custom_items(name,item_type,description,usable,effect_rules_json,mechanics_json,created_at,updated_at) VALUES('Poção de HP','Poção','Cura',1,?,?, 'now','now')",(json.dumps(rules),json.dumps({'consume_mode':'quantity'})))
            path=f'session-item:{row.lastrowid}'
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('vezemir',?,'Poção de HP',?,0,'now')",(path,amount))
            return {'item_path':path,'item_title':'Poção de HP','quantity':amount,'usable':True,'mechanics':{'consume_mode':'quantity'},'effect_rules':rules}

    def test_legacy_and_manual_potions_render_as_one_usable_stack_without_changing_stock(self):
        legacy=normalize_inventory_item_mechanics({'item_path':ITEM_PATH,'item_title':'Poção de HP','quantity':1,'item_type':'Poção'})
        custom=self.custom_potion()
        grouped=coalesce_inventory([legacy,custom])
        self.assertEqual(len(grouped),1);self.assertEqual(grouped[0]['quantity'],5)
        self.assertTrue(grouped[0]['usable']);self.assertEqual(grouped[0]['effect_rules'][0]['formula'],'1d4')
        self.assertFalse(grouped[0].get('damage_formula'))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity FROM player_inventory WHERE item_path=?',(custom['item_path'],)).fetchone()[0],4)

    def test_different_healing_variant_and_service_are_not_silently_merged(self):
        variant=self.custom_potion(formula='1d8')
        service={'item_path':'compendium:servico-magico-pocao-servico','item_title':'Poção (serviço)','quantity':1}
        legacy={'item_path':ITEM_PATH,'item_title':'Poção de HP','quantity':2}
        self.assertEqual(len(coalesce_inventory([legacy,variant,service])),3)

    def test_stock_sells_real_hp_potion_and_retry_does_not_duplicate_or_charge_twice(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('vezemir',?,'Poção de HP',1,0,'now')",(ITEM_PATH,))
        before=purse_copper(self.purse())
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id=CATALOG_ID,quantity=5)
        quote=self.quote(key='hp-potion-quote',target_id=line['id'],quantity=2)
        receipt=shop.confirm(self.db,quote['id'],self.owner,request_id='hp-potion-buy')
        self.assertEqual(receipt,shop.confirm(self.db,quote['id'],self.owner,request_id='hp-potion-buy'))
        self.assertEqual(purse_copper(self.purse()),before-1000)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT quantity FROM player_inventory WHERE profile_id='vezemir' AND item_path=?",(ITEM_PATH,)).fetchone()[0],3)
            self.assertEqual(db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(line['id'],)).fetchone()[0],3)

    def test_consumption_drains_manual_stack_when_legacy_is_empty_and_replay_heals_once(self):
        from app.combat_consumables import use_inventory_item
        custom=self.custom_potion()
        with closing(sqlite3.connect(self.db)) as db, db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(current_hp=10,maximum_hp=30,resources=[])
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        args=dict(character_id='vezemir',actor_id='vezemir',actor_role='player',request_id='hp-potion-use-once',item=use_descriptor())
        with patch('app.combat_consumables.roll_formula',return_value={'total':4,'individual_results':[4]}):
            first=use_inventory_item(self.db,**args)
            self.assertEqual(first,use_inventory_item(self.db,**args))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity FROM player_inventory WHERE item_path=?',(custom['item_path'],)).fetchone()[0],3)
        self.assertEqual(self.purse()['current_hp'],14)

    def test_magic_potion_service_cannot_be_purchased_as_a_healing_bottle(self):
        with self.assertRaisesRegex(ValueError,'[Ss]erviço'):
            add_stock(self.db,merchant_id=self.mid,compendium_item_id='servico-magico-pocao-servico',quantity=5,price_override_po=15)
