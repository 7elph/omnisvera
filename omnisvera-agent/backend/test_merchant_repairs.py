"""Magic rust repair, using the native item condition and commerce transaction."""
import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_map_commerce
from app import map_commerce as shop
from app.access import AccessContext
from app.inventory_conditions import init_schema, read_condition, save_condition, project_condition
from app.merchant import purse_copper
from app.player_inventory import upsert_inventory


class MerchantRepairTests(unittest.TestCase):
    setUp_base = test_map_commerce.MapCommerceTests.setUp
    purse = test_map_commerce.MapCommerceTests.purse

    def setUp(self):
        self.setUp_base()
        self.path = 'Items/Repair fixture.md'
        self.rules = [
            {'id':'repair-enchantment','trigger':'while_equipped','kind':'attack_bonus','value':3,'label':'Encantamento +3'},
            {'id':'repair-strength','trigger':'while_equipped','kind':'damage_bonus','value':2,'label':'FOR +2'}]
        with closing(sqlite3.connect(self.db)) as db, db:
            init_schema(db)
            db.execute('CREATE TABLE IF NOT EXISTS notes(path TEXT PRIMARY KEY,title TEXT,aliases TEXT,type TEXT,tags TEXT,frontmatter TEXT,content TEXT,updated_at TEXT)')
            db.execute('INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                (self.path,'Espada de ensaio','[]','item','[]',json.dumps({'item_type':'weapon','effect_rules':self.rules}),'','now'))
        self.item = upsert_inventory(self.db,profile_id='vezemir',item_path=self.path,item_title='Espada de ensaio',quantity=1,equipped=True,notes=None)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE player_inventory SET charges_current=1,charges_max=3 WHERE id=?',(self.item['id'],))
            from app.monster_rust import preview, contact
            selection={'material':'metal','magical':True,'enchantment_bonus':3,'enhancement_rule_ids':['repair-enchantment']}
            current=preview(db,'character','vezemir',self.item['id'],selection)
            with patch('app.monster_rust.roll_formula',return_value={'total':100}):
                contact(db,'character','vezemir',self.item['id'],selection,expected_fingerprint=current['fingerprint'],now='rust')

    def condition(self):
        with closing(sqlite3.connect(self.db)) as db:
            return read_condition(db,self.item['id'])

    def service(self,price=125):
        return shop.add_service(self.db,self.mid,self.gm,name='Restaurar encantamento',kind='repair',price_copper=price)

    def quote(self, service, key='repair-quote-01', access=None, **changes):
        return shop.quote(self.db,self.mid,access or self.owner,character_id='vezemir',kind='service',
            target_id=service['id'],quantity=1,negotiate=False,request_id=key,inventory_id=changes.pop('inventory_id',self.item['id']),**changes)

    def test_restores_only_original_enchantment_charges_and_attributes_unchanged_retry_reload(self):
        before=purse_copper(self.purse());service=self.service();q=self.quote(service)
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='repair-confirm-01')
        self.assertEqual(receipt,shop.confirm(self.db,q['id'],self.owner,request_id='repair-confirm-01'))
        self.assertEqual(receipt,shop.confirm(self.db,q['id'],self.owner,request_id='repair-confirm-reload'))
        self.assertEqual(purse_copper(self.purse()),before-125)
        condition=self.condition();self.assertEqual(condition['bonus_remaining'],3)
        self.assertEqual([r['value'] for r in project_condition({'_instance_condition':condition,'effect_rules':self.rules})['effect_rules']],[3,2])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT charges_current,charges_max FROM player_inventory WHERE id=?',(self.item['id'],)).fetchone(),(1,3))
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='commerce' AND source_id=?",(q['id'],)).fetchone()[0],1)
        self.assertEqual(receipt['service_effect']['bonus_before'],2)
        self.assertEqual(receipt['service_effect']['bonus_after'],3)

    def test_two_confirmations_for_same_damaged_item_charge_once(self):
        before=purse_copper(self.purse());service=self.service()
        quotes=[self.quote(service,'repair-race-quote-'+str(i)) for i in range(2)]
        def confirm(i):
            try:return shop.confirm(self.db,quotes[i]['id'],self.owner,request_id='repair-race-confirm-'+str(i))
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(confirm,range(2)))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(purse_copper(self.purse()),before-125)

    def test_changed_condition_or_source_rejects_stale_quote_without_charging(self):
        service=self.service();q=self.quote(service);before=purse_copper(self.purse())
        with closing(sqlite3.connect(self.db)) as db, db:
            state=read_condition(db,self.item['id']);state['bonus_remaining']=1
            save_condition(db,self.item['id'],state,'another-contact')
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='repair-stale-confirm')
        self.assertEqual(purse_copper(self.purse()),before)
        q=self.quote(service,'repair-source-quote')
        with closing(sqlite3.connect(self.db)) as db, db:db.execute('UPDATE notes SET frontmatter=? WHERE path=?',(json.dumps({'effect_rules':[]}),self.path))
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='repair-source-confirm')
        self.assertEqual(purse_copper(self.purse()),before)

    def test_destroyed_stacked_unverified_and_other_owner_rejected(self):
        service=self.service();before=purse_copper(self.purse())
        with self.assertRaises(PermissionError):self.quote(service,access=AccessContext(mode='player',profile_id='raziel'))
        original=self.condition()
        for change in ({'destroyed':True},{'original_bonus':9},{'selection':None}):
            with closing(sqlite3.connect(self.db)) as db, db:save_condition(db,self.item['id'],{**original,**change},'invalid')
            with self.assertRaises(ValueError):self.quote(service,'invalid-repair-'+str(len(str(change))))
        with closing(sqlite3.connect(self.db)) as db, db:
            save_condition(db,self.item['id'],original,'restore-fixture')
            db.execute('UPDATE player_inventory SET quantity=2 WHERE id=?',(self.item['id'],))
        with self.assertRaises(ValueError):self.quote(service,'stacked-repair-quote')
        self.assertEqual(purse_copper(self.purse()),before)

    def test_payment_failure_rolls_back_repair_and_no_effect_without_confirmation(self):
        service=self.service();condition=self.condition();before=purse_copper(self.purse())
        q=self.quote(service);self.assertEqual(self.condition(),condition)
        with patch('app.map_commerce._save_purse',side_effect=RuntimeError('synthetic payment failure')):
            with self.assertRaises(RuntimeError):shop.confirm(self.db,q['id'],self.owner,request_id='repair-rollback-01')
        self.assertEqual(self.condition(),condition);self.assertEqual(purse_copper(self.purse()),before)

    def test_free_repair_invalidates_sheet_version_without_changing_money(self):
        service=self.service(0);before=self.purse()
        with closing(sqlite3.connect(self.db)) as db:
            version=db.execute("SELECT version FROM character_states WHERE profile_id='vezemir'").fetchone()[0]
        q=self.quote(service)
        shop.confirm(self.db,q['id'],self.owner,request_id='free-repair-confirm')
        self.assertEqual(self.purse(),before)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT version FROM character_states WHERE profile_id='vezemir'").fetchone()[0],version+1)
        self.assertEqual(self.condition()['bonus_remaining'],3)

    def test_native_http_route_contract_and_owner_boundary(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.commerce_routes import register
        app=FastAPI();register(app,lambda:self.db,lambda:self.owner)
        service=self.service()
        payload={'character_id':'vezemir','kind':'service','target_id':service['id'],'request_id':'http-repair-quote','inventory_id':self.item['id']}
        with TestClient(app) as client:
            self.assertEqual(client.post(f'/gm/merchants/{self.mid}/services',json={'name':'Forged','kind':'repair','price_copper':0}).status_code,403)
            for invalid in (True,0,-1,'1'):
                response=client.post(f'/commerce/{self.mid}/quotes',json={**payload,'inventory_id':invalid})
                self.assertEqual(response.status_code,422)
            self.assertEqual(client.post(f'/commerce/{self.mid}/quotes',json={**payload,'character_id':'raziel'}).status_code,403)
            response=client.post(f'/commerce/{self.mid}/quotes',json=payload)
            self.assertEqual(response.status_code,200,response.text)
            confirmed=client.post('/commerce/quotes/'+response.json()['id']+'/confirm',json={'request_id':'http-repair-confirm'})
            self.assertEqual(confirmed.status_code,200,confirmed.text)
            self.assertEqual(confirmed.json()['service_effect']['bonus_after'],3)

    def test_combat_and_insufficient_funds_never_change_the_item(self):
        from app.combat_effects import init_effects
        init_effects(self.db);service=self.service();before=self.condition()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1",(json.dumps({'active':True}),))
        with self.assertRaisesRegex(ValueError,'combate'):self.quote(service)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE combat_effect_clock SET encounter_json='{}' WHERE id=1")
            state=self.purse();state.update(coins=0,silver_coins=0,copper_coins=0,platinum_coins=0)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        q=self.quote(service)
        with self.assertRaisesRegex(ValueError,'Saldo'):shop.confirm(self.db,q['id'],self.owner,request_id='no-money-repair')
        self.assertEqual(self.condition(),before)
