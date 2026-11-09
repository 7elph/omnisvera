import sqlite3
import unittest
from contextlib import closing


class OpticalSuppressionTests(unittest.TestCase):
    def setUp(self):
        from test_magic_targeted_items import TargetedMagicTests
        TargetedMagicTests.setUp(self)
        from test_magic_equipment import MagicEquipmentApiTests
        self.mantle=MagicEquipmentApiTests.equip(self,'manto-da-confusao','Acessório')
        MagicEquipmentApiTests.equip(self,'cinto-da-forca-do-ogro','Cinto')
        self.powder=TargetedMagicTests.seed(self,'po-do-aparecimento',quantity=2)

    def sheet(self):return self.client.get('/characters/vezemir?read_only=true').json()

    def use(self):
        return self.client.post('/characters/vezemir/actions',json={'action':'use_item','request_id':'optics-powder',
            'payload':{'item_path':self.powder}})

    def test_powder_suppresses_only_optical_bonus_without_destroying_equipment(self):
        before=self.sheet()
        response=self.use();self.assertEqual(response.status_code,200,response.text)
        after=self.sheet()
        self.assertEqual(after['definition']['defenses']['armor_class'],before['definition']['defenses']['armor_class']-2)
        self.assertEqual(after['definition']['attributes']['strength'],before['definition']['attributes']['strength'])
        item=next(i for i in after['inventory'] if i['item_path']==self.mantle)
        self.assertTrue(item['equipped']);self.assertEqual(item['quantity'],1)

    def test_reequip_does_not_bypass_suppression_and_rest_restores_the_source_bonus(self):
        before=self.sheet()['definition']['defenses']['armor_class']
        self.assertEqual(self.use().status_code,200)
        for action in ['unequip_item','equip_item']:
            r=self.client.post('/characters/vezemir/actions',json={'action':action,'request_id':'optics-'+action,
                'payload':{'item_path':self.mantle,'equipment_slot':'Acessório'}})
            self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.sheet()['definition']['defenses']['armor_class'],before-2)
        r=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','request_id':'optics-rest','payload':{}})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.sheet()['definition']['defenses']['armor_class'],before)

    def test_true_sight_does_not_subtract_the_already_suppressed_armor_again(self):
        self.assertEqual(self.use().status_code,200)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='raziel',item_path='compendium:item-magico-elmo-da-visao-da-verdade',
            item_title='Elmo',quantity=1,equipped=True,equipment_slot='Cabeça',notes=None)
        from app.magic_passives import illusion_ac_ignored
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(illusion_ac_ignored(db,'raziel','character','vezemir'),0)
