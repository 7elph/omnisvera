"""Percentile equipment checks use native rolls over synthetic inventories."""
import sqlite3,unittest
from contextlib import closing
from unittest.mock import patch

BOOTS='compendium:item-magico-botas-elficas'
CLOAK='compendium:item-magico-manto-da-aranha'

class EquipmentCheckTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')

    def equip(self,path,slot):
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title=path,quantity=1,equipped=True,equipment_slot=slot,notes=None)

    def roll(self,path,key='equipment-check-native',**extra):
        return self.client.post('/characters/vezemir/rolls',json={'request_id':key,'roll_type':'skill','source_id':'equipment:'+path,**extra})

    def test_boots_boundary_and_native_percentile_provenance(self):
        self.equip(BOOTS,'Pés')
        for result,outcome in [(1,'success'),(60,'success'),(61,'failure'),(100,'failure')]:
            with patch('app.dice_rolls.roll_formula',return_value={'formula':'1d100','dice':'1d100','modifier':0,'individual_results':[result],'subtotal':result,'total':result}):
                r=self.roll(BOOTS,'boots-boundary-'+str(result));self.assertEqual(r.status_code,200,r.text)
            self.assertEqual((r.json()['formula'],r.json()['target_value'],r.json()['target_comparison'],r.json()['outcome']),('1d100',60,'at_most',outcome))
            self.assertEqual(r.json()['source'],'equipment_check')

    def test_cloak_has_95_percent_per_three_meters_without_consuming_item(self):
        self.equip(CLOAK,'Acessório')
        r=self.roll(CLOAK);self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['target_value'],95);self.assertIn('3 m',r.json()['label'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity FROM player_inventory WHERE item_path=?',(CLOAK,)).fetchone()[0],1)

    def test_reviewed_check_equipment_does_not_invent_armor_attack_or_attribute_bonuses(self):
        before=self.client.get('/characters/vezemir?read_only=true').json()['definition']
        self.equip(BOOTS,'Pés');self.equip(CLOAK,'Acessório')
        after=self.client.get('/characters/vezemir?read_only=true').json()['definition']
        self.assertEqual(after['defenses'],before['defenses'])
        self.assertEqual(after['attributes'],before['attributes'])
        self.assertEqual(after['attacks'],before['attacks'])

    def test_unequipped_or_forged_item_does_not_roll(self):
        self.equip(BOOTS,'Pés')
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(BOOTS,))
        self.assertEqual(self.roll(BOOTS).status_code,400)
        self.assertEqual(self.roll('compendium:fake-boots','fake-check-id').status_code,400)

    def test_retry_survives_stowing_without_reroll_and_different_intent_is_rejected(self):
        self.equip(BOOTS,'Pés');self.equip(CLOAK,'Acessório')
        first=self.roll(BOOTS);self.assertEqual(first.status_code,200,first.text)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(BOOTS,))
        with patch('app.dice_rolls.roll_formula',side_effect=AssertionError('retry must not roll')):
            retry=self.roll(BOOTS);self.assertEqual(retry.status_code,200,retry.text);self.assertEqual(first.json(),retry.json())
            self.assertEqual(self.roll(CLOAK).status_code,400)

    def test_chance_cannot_be_overridden_and_other_character_is_protected(self):
        self.equip(BOOTS,'Pés');self.assertEqual(self.roll(BOOTS,target_value=100,visibility='private').status_code,400)
        r=self.client.post('/characters/raziel/rolls',json={'request_id':'wrong-character-check','roll_type':'skill','source_id':'equipment:'+BOOTS})
        self.assertEqual(r.status_code,403)

    def test_pending_request_preserves_comparison_and_default_jp_stays_gte(self):
        from app.dice_rolls import RollSpec,create_roll_request,complete_roll_request,create_roll
        self.equip(CLOAK,'Acessório')
        spec=RollSpec('skill','Escalada 3 m','1d100','equipment_check',CLOAK,95,'at_most')
        request,_=create_roll_request(self.db,request_id='pending-percentile',campaign_id='omnisvera',character_id='vezemir',requested_by='master',spec=spec,visibility='table')
        event,_=complete_roll_request(self.db,request_id=request['id'],completion_request_id='finish-percentile',actor_id='vezemir',actor_role='player',rng=lambda *_:95)
        self.assertEqual((event['target_comparison'],event['outcome']),('at_most','success'))
        jp,_=create_roll(self.db,request_id='normal-save-check',campaign_id='omnisvera',actor_id='vezemir',actor_role='player',character_id='vezemir',roll_type='saving_throw',label='JP',formula='1d20',visibility='table',target_value=14,rng=lambda *_:13)
        self.assertEqual((jp['target_comparison'],jp['outcome']),('at_least','failure'))

    def test_pending_check_revalidates_equipment_before_rng_and_can_resume(self):
        from app.dice_rolls import RollSpec,create_roll_request,complete_roll_request,list_rolls
        self.equip(BOOTS,'Pés')
        spec=RollSpec('skill','Silêncio','1d100','equipment_check',BOOTS,60,'at_most')
        request,_=create_roll_request(self.db,request_id='pending-gear-change',campaign_id='omnisvera',character_id='vezemir',requested_by='master',spec=spec,visibility='table')
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(BOOTS,))
        args=dict(request_id=request['id'],completion_request_id='resume-gear-check',actor_id='vezemir',actor_role='player',rng=lambda *_:30)
        with self.assertRaisesRegex(ValueError,'Equipe'):complete_roll_request(self.db,**args)
        self.assertEqual(list_rolls(self.db),[])
        self.equip(BOOTS,'Pés');event,_=complete_roll_request(self.db,**args)
        self.assertEqual(event['outcome'],'success')

    def test_readiness_and_source_recovery_do_not_pretend_all_items_execute(self):
        from app.item_catalog import get_catalog_item,normalize_catalog_item
        from app.magic_item_rulebook import rules_for
        boots=get_catalog_item(BOOTS.removeprefix('compendium:'))
        self.assertEqual(boots['mechanics']['magic_readiness']['status'],'native_on_check')
        armor=get_catalog_item('item-magico-armadura-leve-da-rapina')
        self.assertIn('CA +7',armor['description']);self.assertIn('ver descrição',armor['source_description'])
        self.assertEqual(armor['mechanics']['magic_readiness']['status'],'native_on_use')
        vessel=get_catalog_item('item-magico-vaso-da-agua-ungueal')['mechanics']['magic_readiness']
        self.assertEqual(vessel['status'],'native_field_interaction')
        self.assertEqual(vessel['blocking_gaps'],['easy_identification_difficulty'])
        self.assertEqual(normalize_catalog_item(armor)['source_description'],armor['source_description'])
        rules=rules_for('item-magico-manto-da-aranha');rules['parameters']['chance_percent']=1
        self.assertEqual(rules_for('item-magico-manto-da-aranha')['parameters']['chance_percent'],95)

    def test_legacy_rolls_survive_additive_comparison_migration(self):
        from app.dice_rolls import create_roll,init_dice_rolls,list_rolls
        event,_=create_roll(self.db,request_id='pre-migration-roll',campaign_id='omnisvera',actor_id='vezemir',actor_role='player',character_id='vezemir',roll_type='attribute',label='Anterior',formula='1d20',visibility='table',target_value=10,rng=lambda *_:15)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('ALTER TABLE dice_roll_events DROP COLUMN target_comparison')
            db.execute('ALTER TABLE dice_roll_requests DROP COLUMN target_comparison')
        init_dice_rolls(self.db);again=list_rolls(self.db)[0]
        self.assertEqual(again,event)

if __name__=='__main__':unittest.main()
