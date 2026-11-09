import unittest
import sqlite3
from contextlib import closing


class AdamasTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        self.client.post('/characters/vezemir/actions',json={'action':'unequip_item',
            'request_id':'adamas-fixture-stow','payload':{'item_path':'compendium:arma-corpo-espada-longa'}})
        MagicEquipmentApiTests.equip(self,'espada-adamas','Corpo a corpo')
        self.path='compendium:item-magico-espada-adamas'

    def use(self,form,key='adamas-form-fixture'):
        return self.client.post('/characters/vezemir/actions',json={'action':'weapon_form',
            'request_id':key,'payload':{'item_path':self.path,'form_id':form}})

    def test_default_short_sword_has_four_damage_and_source_critical(self):
        from app.map_commerce import catalog_inventory
        item=catalog_inventory(self.path)
        self.assertEqual(item['damage_formula'],'1d6+4')
        self.assertEqual(item['mechanics']['critical_threshold'],18)
        self.assertEqual(item['mechanics']['critical_multiplier'],2)
        self.assertEqual(len(item['mechanics']['weapon_forms']),4)

    def test_shape_persists_in_existing_instance_condition_and_sheet_attack(self):
        first=self.use('arma-corpo-espada-larga');self.assertEqual(first.status_code,200,first.text)
        self.assertEqual(self.use('arma-corpo-espada-larga').status_code,200)
        item=next(i for i in self.client.get('/characters/vezemir?read_only=true').json()['inventory'] if i['item_path']==self.path)
        self.assertEqual(item['damage_formula'],'2d6+4')
        self.assertEqual(item['mechanics']['weapon_form_id'],'arma-corpo-espada-larga')
        self.assertEqual(self.use('arma-corpo-espada-curta').status_code,400)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='weapon_form'").fetchone()[0],1)

    def test_invalid_form_and_other_owner_are_rejected(self):
        self.assertEqual(self.use('fireball-999').status_code,400)
        for value in [[],{},True,None]:self.assertEqual(self.use(value).status_code,400)
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        self.assertEqual(self.use('arma-corpo-espada-longa').status_code,403)

    def test_corrosion_of_adamas_is_automatic_and_survives_form_change(self):
        from unittest.mock import patch
        from app.monster_rust import preview,contact
        from app.inventory_conditions import init_schema
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row;init_schema(db)
            iid=db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',self.path)).fetchone()[0]
            before=preview(db,'character','vezemir',iid)
            self.assertFalse(before['needs_metadata'])
            with patch('app.monster_rust.roll_formula',return_value={'total':100}):
                result=contact(db,'character','vezemir',iid,expected_fingerprint=before['fingerprint'],now='2026-11-03')
            self.assertEqual(3,result['bonus_after'])
        self.assertEqual(200,self.use('arma-corpo-espada-longa','corroded-adamas-form').status_code)
        item=next(i for i in self.client.get('/characters/vezemir?read_only=true').json()['inventory'] if i['item_path']==self.path)
        self.assertEqual('1d8+3',item['damage_formula'])
        self.assertEqual(18,item['mechanics']['critical_threshold'])
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            self.assertEqual(3,preview(db,'character','vezemir',iid)['bonus'])
