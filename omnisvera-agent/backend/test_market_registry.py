import json,sqlite3,unittest
from contextlib import closing
from app import map_commerce as shop
from app.item_registry import registry,resolve_item,set_trade_profile,audit_items,enqueue_gaps
import test_map_commerce

class MarketRegistryTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp
    purse=test_map_commerce.MapCommerceTests.purse
    quote=test_map_commerce.MapCommerceTests.quote

    def owned(self,path='Items/Ração de viagem.md',name='Ração de viagem',qty=3):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES(?,?,?,?,0,?)',('vezemir',path,name,qty,'now'))
        return path

    def test_vault_item_is_sellable_and_quote_credits_exactly_once(self):
        path=self.owned()
        set_trade_profile(self.db,self.gm,item_path=path,price_copper=100,trade_group='supplies',request_id='ration-value-v1')
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],policy={'buy':['supplies'],'sell':['equipment']})
        offers=shop.for_pin(self.db,self.pin['id'],self.owner,'vezemir')[0]
        self.assertEqual(offers['sellable'][0]['price_copper'],50)
        before=self.purse()['coins']*100+self.purse()['silver_coins']*10+self.purse()['copper_coins']
        q=self.quote(key='sell-vault-item',kind='sell',target_id=path,quantity=2)
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='sell-vault-confirm')
        self.assertEqual(receipt,shop.confirm(self.db,q['id'],self.owner,request_id='sell-vault-confirm'))
        self.assertEqual(receipt['balance_after_copper']-receipt['balance_before_copper'],100)
        self.assertEqual(receipt['balance_before_copper'],before)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity FROM player_inventory WHERE item_path=?',(path,)).fetchone()[0],1)

    def test_unknown_valuation_has_a_visible_reason_and_is_not_free(self):
        path=self.owned('session-item:900','Relíquia desconhecida')
        rows=shop.for_pin(self.db,self.pin['id'],self.owner,'vezemir')[0]
        self.assertTrue(any(r['id']==path and r['reason']=='price_missing' for r in rows['blocked_sales']))
        with self.assertRaises(ValueError):self.quote(key='unknown-sale',kind='sell',target_id=path)

    def test_shop_policy_is_enforced_at_quote_and_confirmation(self):
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],policy={'sell':['arcane'],'buy':['arcane']})
        with self.assertRaisesRegex(ValueError,'tipo de item'):self.quote(key='forbidden-equipment')

    def test_audit_covers_every_source_and_every_gap_has_a_native_job_plan(self):
        self.owned()
        report=audit_items(self.db,vault_root=self.db.parent)
        self.assertEqual(report['total'],len(report['items']))
        self.assertEqual(report['gap_count'],len(report['generation_plan']))
        self.assertTrue(any(r['item_path']=='Items/Ração de viagem.md' for r in report['items']))
        workshop=self.db.parent/'workshop.sqlite3'
        first=enqueue_gaps(self.db,workshop,self.gm,request_id='catalog-plan-once',vault_root=self.db.parent)
        second=enqueue_gaps(self.db,workshop,self.gm,request_id='catalog-plan-once',vault_root=self.db.parent)
        self.assertEqual(first,second)
        self.assertEqual(first['planned'],report['gap_count'])
        self.assertFalse(first['published'])
