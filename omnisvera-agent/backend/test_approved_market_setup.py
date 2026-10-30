import json,sqlite3,unittest
from contextlib import closing
from app import approved_market_setup as setup
from app.access import AccessContext
from app.merchant import create_merchant,add_stock,purse_copper
import test_map_commerce


class ApprovedMarketSetupTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp
    purse=test_map_commerce.MapCommerceTests.purse

    def receipts(self):
        from app.session_ledger import append_session_ledger_event
        with closing(sqlite3.connect(self.db)) as db,db:
            for identity in ['hp-purchase-a','hp-purchase-b']:
                append_session_ledger_event(db,source_type='commerce',source_id=identity,event_kind='state',actor_id='vezemir',actor_name='Vezemir',actor_role='player',character_id='vezemir',title='Comprou poção',detail={'kind':'buy','name':'Poção (serviço)','quantity':1,'total_copper':1350,'bargain':{'multiplier':.9}},created_at='now')
        return ['hp-purchase-a','hp-purchase-b']

    def test_approved_18_gold_refund_once_keeps_every_other_denomination(self):
        sources=self.receipts();before=self.purse()
        receipt=setup.refund_hp_overcharge(self.db,self.gm,character_id='vezemir',source_receipts=sources)
        again=setup.refund_hp_overcharge(self.db,self.gm,character_id='vezemir',source_receipts=list(reversed(sources)))
        self.assertEqual(receipt,again);self.assertEqual(self.purse()['coins'],before['coins']+18)
        for field in ['silver_coins','copper_coins','platinum_coins']:self.assertEqual(self.purse()[field],before[field])
        self.assertEqual(receipt['balance_after_copper']-receipt['balance_before_copper'],1800)
        with self.assertRaises(ValueError):setup.refund_hp_overcharge(self.db,self.gm,character_id='vezemir',source_receipts=sources,expected_refund_copper=2000)

    def test_refund_requires_matching_evidence_and_gm(self):
        sources=self.receipts();before=self.purse()
        with self.assertRaises(PermissionError):setup.refund_hp_overcharge(self.db,self.owner,character_id='vezemir',source_receipts=sources)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute("UPDATE session_ledger SET detail_json='{}' WHERE source_id=?",(sources[0],))
        with self.assertRaises(ValueError):setup.refund_hp_overcharge(self.db,self.gm,character_id='vezemir',source_receipts=sources)
        self.assertEqual(self.purse(),before)

    def test_shop_setup_moves_existing_stock_prices_hp_and_is_idempotent(self):
        other=create_merchant(self.db,name='Conclave',location='Nimalis')
        add_stock(self.db,merchant_id=self.mid,compendium_item_id='campanha-pocao-hp',quantity=15,price_override_po=15)
        powder=add_stock(self.db,merchant_id=self.mid,compendium_item_id='item-magico-po-do-desaparecimento',quantity=3,price_override_po=10)
        first=setup.setup_shops(self.db,self.gm,thoradin_id=self.mid,conclave_id=other['id'])
        self.assertEqual(first,setup.setup_shops(self.db,self.gm,thoradin_id=self.mid,conclave_id=other['id']))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT merchant_id,quantity FROM merchant_stock WHERE id=?',(powder['id'],)).fetchone(),(other['id'],3))
            self.assertEqual(db.execute("SELECT price_override_po FROM merchant_stock WHERE compendium_item_id='campanha-pocao-hp'").fetchone()[0],5)
            self.assertEqual(db.execute("SELECT count(*) FROM merchant_services WHERE active=1").fetchone()[0],3)

    def test_explicit_restock_is_finite_audited_and_never_repeated(self):
        other=create_merchant(self.db,name='Conclave',location='Nimalis')
        powder=add_stock(self.db,merchant_id=self.mid,compendium_item_id='item-magico-po-do-desaparecimento',quantity=1,price_override_po=10)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE merchant_stock SET quantity=0 WHERE id=?',(powder['id'],))
        args=dict(thoradin_id=self.mid,conclave_id=other['id'],replenish_empty_arcane=5)
        result=setup.setup_shops(self.db,self.gm,**args)
        self.assertEqual(result,setup.setup_shops(self.db,self.gm,**args))
        self.assertEqual(result['replenished'][0]['after'],5)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(powder['id'],)).fetchone()[0],5)

    def test_khlauss_identity_and_public_trade_visibility_keep_private_notes(self):
        from app.npc_memory import init_npc_memory,create_npc
        from app import map_commerce
        init_npc_memory(self.db)
        npc,_=create_npc(self.db,request_id='guild-master-market',campaign_id='omnisvera',actor_id='master',fields={'name':'Mestre do Conclave','portrait_path':'guild.png','private_description':'SEGREDO-INTERNO','visible_to_players':False})
        from app.session_workspace import save_workspace_token
        child=save_workspace_token(self.db,token_type='monster',name='Mestre do Conclave',image_path='guild.png',latitude=40,longitude=40,visible_to_players=True)
        other=create_merchant(self.db,name='Conclave',location='Nimalis')
        map_commerce.configure(self.db,other['id'],self.gm,token_id=self.pin['id'],npc_id=npc['id'])
        setup.setup_shops(self.db,self.gm,thoradin_id=self.mid,conclave_id=other['id'])
        with closing(sqlite3.connect(self.db)) as db:
            name,visible,private=db.execute('SELECT name,visible_to_players,private_description FROM npc_definitions WHERE id=?',(npc['id'],)).fetchone()
            self.assertEqual((name,visible,private),('Klhauss',1,'SEGREDO-INTERNO'))
            self.assertEqual(db.execute("SELECT count(*) FROM npc_events WHERE npc_id=? AND event_type='npc_updated'",(npc['id'],)).fetchone()[0],1)
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(child['id'],)).fetchone()[0])
            self.assertEqual(sheet['embedded_in_location'],self.pin['id'])
        offers=map_commerce.for_pin(self.db,self.pin['id'],self.owner,'vezemir')
        self.assertNotIn('SEGREDO-INTERNO',json.dumps(offers))
