"""Native commerce regression. All mutations belong to a disposable fixture."""
import json,sqlite3,unittest
from contextlib import closing
from app import map_commerce as shop
from app.access import AccessContext
from app.merchant import add_stock,purse_copper
from app.item_registry import set_trade_profile
import test_map_commerce


class EconomyCompletionTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp
    purse=test_map_commerce.MapCommerceTests.purse
    quote=test_map_commerce.MapCommerceTests.quote

    def test_purchase_and_resale_have_full_replayable_audit(self):
        q=self.quote(key='economy-buy-001');receipt=shop.confirm(self.db,q['id'],self.owner,request_id='economy-confirm-001')
        self.assertEqual(len(receipt['inventory_changes']),1)
        self.assertEqual(receipt['inventory_changes'][0]['after']-receipt['inventory_changes'][0]['before'],1)
        self.assertEqual(receipt['stock_before']-receipt['stock_after'],1)
        path=receipt['inventory_changes'][0]['item_path']
        q=self.quote(key='economy-sale-001',kind='sell',target_id=path)
        sold=shop.confirm(self.db,q['id'],self.owner,request_id='economy-sale-confirm')
        self.assertEqual(sold['stock_after']-sold['stock_before'],1)
        self.assertEqual(sold,shop.confirm(self.db,q['id'],self.owner,request_id='economy-sale-confirm'))
        report=shop.history(self.db,self.owner,'vezemir')
        self.assertEqual(len(report),2)
        self.assertEqual(report[0]['audit_status'],'complete')
        with self.assertRaises(PermissionError):shop.history(self.db,AccessContext(mode='player',profile_id='raziel'),'vezemir')

    def test_delivery_cannot_bypass_shop_policy_or_overbook_linked_stock(self):
        service=shop.add_service(self.db,self.mid,self.gm,name='Entrega',kind='delivery',price_copper=1,
            compendium_item_id='arma-corpo-espada-longa',amount=2,stock_id=self.line['id'])
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],policy={'sell':['arcane']})
        with self.assertRaises(ValueError):self.quote(key='forbidden-service',kind='service',target_id=service['id'])
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],policy={'sell':['equipment']})
        q=self.quote(key='valid-service-001',kind='service',target_id=service['id'])
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='service-stock-confirm')
        self.assertEqual(receipt['stock_after'],0);self.assertEqual(receipt['inventory_changes'][0]['after'],2)
        with self.assertRaises(ValueError):self.quote(key='empty-service-001',kind='service',target_id=service['id'])

    def test_appraisal_is_a_real_service_without_inventing_unknown_prices(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES(?,?,?,?,0,?)',('vezemir','session-item:999','Relíquia',1,'now'))
        service=shop.add_service(self.db,self.mid,self.gm,name='Avaliação',kind='appraisal',price_copper=0)
        before=self.purse()
        q=self.quote(key='appraisal-quote-01',kind='service',target_id=service['id'])
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='appraisal-confirm-01')
        self.assertEqual(receipt['service_status'],'completed')
        self.assertTrue(any(i['reason']=='price_missing' for i in receipt['appraisal']))
        self.assertEqual(self.purse(),before)

    def test_native_custom_item_can_be_sold_and_bought_without_losing_identity(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO session_custom_items(name,item_type,description,image_path,effect_rules_json,mechanics_json,created_at,updated_at) VALUES('Ferramenta de teste','gear','Ferramenta','','[]','{}','now','now')")
            cid=db.execute('SELECT max(id) FROM session_custom_items').fetchone()[0]
            path='session-item:'+str(cid)
            db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES(?,?,?,?,0,?)',('vezemir',path,'Ferramenta de teste',1,'now'))
        set_trade_profile(self.db,self.gm,item_path=path,price_copper=100,trade_group='supplies',request_id='appraise-custom-01')
        q=self.quote(key='native-sale-001',kind='sell',target_id=path)
        shop.confirm(self.db,q['id'],self.owner,request_id='native-sale-confirm')
        offers=shop.for_pin(self.db,self.pin['id'],self.owner,'vezemir')[0]['offers']
        line=next(o for o in offers if o['name']=='Ferramenta de teste')
        q=self.quote(key='native-buy-001',target_id=line['id'])
        result=shop.confirm(self.db,q['id'],self.owner,request_id='native-buy-confirm')
        self.assertEqual(result['inventory_changes'][0]['item_path'],path)

    def test_hp_sale_coalesces_native_stacks_and_preserves_real_quantities(self):
        from app.hp_potions import ITEM_PATH
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES(?,?,?,?,0,?)',('vezemir',ITEM_PATH,'Poção de HP',2,'now'))
        q=self.quote(key='hp-sale-001',kind='sell',target_id=ITEM_PATH,quantity=2)
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='hp-sale-confirm')
        self.assertEqual(sum(r['before']-r['after'] for r in receipt['inventory_changes']),2)

    def test_sale_above_available_quantity_fails_before_confirmation(self):
        buy=self.quote();result=shop.confirm(self.db,buy['id'],self.owner,request_id='stock-purchase-01')
        path=result['inventory_changes'][0]['item_path']
        with self.assertRaises(ValueError):self.quote(key='too-many-sale-01',kind='sell',target_id=path,quantity=2)

    def test_depleted_or_rusted_item_is_not_resold_as_a_fresh_catalog_item(self):
        buy=self.quote();receipt=shop.confirm(self.db,buy['id'],self.owner,request_id='condition-purchase-01')
        path=receipt['inventory_changes'][0]['item_path']
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=1,charges_max=3 WHERE item_path=?',(path,))
        with self.assertRaises(ValueError):self.quote(key='used-charge-sale-01',kind='sell',target_id=path)
        from app.inventory_conditions import init_schema,save_condition
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=NULL,charges_max=NULL WHERE item_path=?',(path,))
            identity=db.execute('SELECT id FROM player_inventory WHERE item_path=?',(path,)).fetchone()[0]
            init_schema(db);save_condition(db,identity,{'kind':'rust','bonus_remaining':0},'now')
        with self.assertRaises(ValueError):self.quote(key='rusted-sale-01',kind='sell',target_id=path)

    def test_buyback_uses_lower_local_offer_not_higher_book_value(self):
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id='item-magico-po-do-desaparecimento',quantity=2,price_override_po=10)
        q=self.quote(key='cheap-powder-001',target_id=line['id'])
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='cheap-powder-confirm')
        path=receipt['inventory_changes'][0]['item_path']
        sale=self.quote(key='powder-resell-001',kind='sell',target_id=path)
        self.assertLessEqual(sale['total_copper'],receipt['total_copper'])
        self.assertEqual(sale['total_copper'],500)
