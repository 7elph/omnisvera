import sqlite3
import unittest
from contextlib import closing

BELT='compendium:item-magico-cinto-da-mudanca-de-sexo'


class AppearanceCurseTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=BELT,item_title='Cinto da mudança de sexo',quantity=1,equipped=False,notes=None)

    def action(self,action,key):
        return self.client.post('/characters/vezemir/actions',json={'action':action,'request_id':key,
            'payload':{'item_path':BELT,'equipment_slot':'Cinto'}})

    def sheet(self):return self.client.get('/characters/vezemir?read_only=true').json()

    def test_first_equip_second_equip_and_limit_persist_without_affecting_statistics(self):
        before=self.sheet()
        self.assertEqual(self.action('equip_item','curse-first').status_code,200)
        first=self.sheet();self.assertEqual(first['state']['appearance']['phase'],'changed')
        self.assertEqual(self.action('equip_item','curse-first').status_code,200)
        self.assertEqual(self.sheet()['state']['appearance']['phase'],'changed')
        self.action('unequip_item','curse-stow')
        self.action('equip_item','curse-second')
        self.assertEqual(self.sheet()['state']['appearance']['phase'],'mixed')
        self.action('unequip_item','curse-stow-again')
        self.action('equip_item','curse-third')
        self.assertEqual(self.sheet()['state']['appearance']['activation_count'],2)
        self.assertEqual(self.sheet()['definition']['attributes'],before['definition']['attributes'])

    def test_rest_and_stowing_do_not_undo_permanent_appearance(self):
        self.action('equip_item','curse-first')
        self.action('unequip_item','curse-stow')
        r=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','request_id':'curse-rest','payload':{}})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.sheet()['state']['appearance']['phase'],'changed')

    def test_stacked_belts_are_rejected_without_a_partial_activation(self):
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET quantity=2 WHERE item_path=?',(BELT,))
        r=self.action('equip_item','curse-stack')
        self.assertEqual(r.status_code,400,r.text)
        self.assertFalse(self.sheet()['state'].get('appearance'))
