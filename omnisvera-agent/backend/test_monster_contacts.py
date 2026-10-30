import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_monster_runtime as fixture

class ContactTests(unittest.TestCase):
    setUp=fixture.MonsterRuntimeTests.setUp
    hp=fixture.MonsterRuntimeTests.hp

    def sphere(self):
        from app.monster_catalog import get_catalog_monster
        with closing(sqlite3.connect(self.db)) as db,db:
            m=get_catalog_monster('esfera-da-aniquilacao')
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",(json.dumps({**m,'source':{'monster_id':m['id']}}),))
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=5 WHERE token_id='vez-pin'")
            db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps({}),))

    def command(self,key='sphere-contact-once',payload=None):
        from app.monster_contacts import preview
        from app.combat_effects import readeffects,effect_snapshot,effect_command
        if payload is None:
            with closing(sqlite3.connect(self.db)) as db:
                p=preview(db,effect_snapshot(db),'gob1','vez-pin')
            payload={'token_id':'gob1','target_pin_id':'vez-pin','fingerprint':p['fingerprint']}
        return effect_command(self.db,actor_id='master',actor_role='gm',request_id=key,expected_version=readeffects(self.db)['version'],action='monster_contact',payload=payload)

    def test_sphere_is_contact_not_a_damage_or_save_roll_and_no_corpse(self):
        self.sphere()
        with patch('app.dorn_spells.save') as saving,patch('app.monster_contacts.roll_formula') as dice:
            result=self.command()
        saving.assert_not_called();dice.assert_not_called()
        self.assertLessEqual(self.hp(),0)
        with closing(sqlite3.connect(self.db)) as db:
            sheet=json.loads(db.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id='vez-pin'").fetchone()[0])
            self.assertTrue(sheet['disintegrated']);self.assertFalse(sheet['reanimation_allowed'])
        self.assertEqual(result['protocol_result']['kind'],'disintegration')

    def test_retry_recovers_receipt_after_target_is_gone(self):
        from app.monster_contacts import preview
        from app.combat_effects import effect_snapshot
        self.sphere()
        with closing(sqlite3.connect(self.db)) as db:p=preview(db,effect_snapshot(db),'gob1','vez-pin')
        payload={'token_id':'gob1','target_pin_id':'vez-pin','fingerprint':p['fingerprint']}
        first=self.command(payload=payload)
        self.assertEqual(self.command(payload=payload),first)

    def test_stale_position_rejects_without_damage(self):
        from app.monster_contacts import preview
        from app.combat_effects import effect_snapshot
        self.sphere()
        with closing(sqlite3.connect(self.db)) as db,db:
            p=preview(db,effect_snapshot(db),'gob1','vez-pin')
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=15 WHERE token_id='vez-pin'")
        with self.assertRaises(ValueError):self.command(payload={'token_id':'gob1','target_pin_id':'vez-pin','fingerprint':p['fingerprint']})
        self.assertEqual(self.hp(),30)

    def test_unknown_actor_and_player_cannot_use_native_contacts(self):
        from app.combat_effects import effect_command,readeffects
        self.sphere()
        with self.assertRaises(PermissionError):
            effect_command(self.db,actor_id='raziel',actor_role='player',allow_player=True,request_id='bad-contact-player',expected_version=readeffects(self.db)['version'],action='monster_contact',payload={})
        with self.assertRaises(ValueError):self.command(payload={'token_id':'other','target_pin_id':'vez-pin','fingerprint':'x'})

    def test_statless_sphere_cannot_join_normal_initiative(self):
        from app.combat_effects import effect_command,readeffects
        self.sphere()
        with self.assertRaisesRegex(ValueError,'cenário'):
            effect_command(self.db,actor_id='master',actor_role='gm',request_id='sphere-not-participant',expected_version=readeffects(self.db)['version'],action='start',payload={'participants':[{'target_type':'token','target_id':'gob1','name':'Sphere','initiative':20}]})

    def rust(self):
        from app.monster_catalog import get_catalog_monster
        from app.player_inventory import upsert_inventory
        self.sphere()
        with closing(sqlite3.connect(self.db)) as db,db:
            monster=get_catalog_monster('monstro-ferrugem')
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",(json.dumps({**monster,'source':{'monster_id':monster['id']}}),))
            db.execute("INSERT INTO session_custom_items(id,name,item_type,created_at,updated_at) VALUES(772,'Escudo teste','escudo','now','now')")
        return upsert_inventory(self.db,profile_id='vezemir',item_path='session-item:772',item_title='Escudo teste',quantity=1,equipped=True,notes=None)

    def rust_command(self,item,ac=20):
        from app.monster_contacts import preview
        from app.combat_effects import effect_snapshot
        with closing(sqlite3.connect(self.db)) as db:
            contract=preview(db,effect_snapshot(db),'gob1','vez-pin',target_ac=ac)
        payload={'token_id':'gob1','target_pin_id':'vez-pin','fingerprint':contract['fingerprint'],
                 '_server_target_ac':ac,'inventory_id':item['id'],
                 'selection':{'material':'metal','magical':False,'enchantment_bonus':0,'enhancement_rule_ids':[]}}
        return self.command(key='rust-native-interaction',payload=payload)['protocol_result']

    def test_reflections_intercept_rust_contact_without_corroding_real_equipment(self):
        from app.player_inventory import list_inventory
        item=self.rust()
        effect={'id':'mirror-test','target_type':'character','target_id':'vezemir','label':'Reflexos',
                'source':'Teste','duration':'manual','rounds':None,'modifiers':{},'spell':'reflexos','images_remaining':2}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character','vezemir',json.dumps(effect)))
        with patch('app.monster_contacts.roll_formula',return_value={'total':15,'individual_results':[15]}), \
             patch('app.dorn_spell_pack.roll_formula',return_value={'total':1,'individual_results':[1]}):
            result=self.rust_command(item)
        self.assertTrue(result['hit'])
        self.assertEqual(list_inventory(self.db,'vezemir')[0]['quantity'],1)
        self.assertTrue(result['reflection_result']['rolls'][0]['intercepted'])
        self.assertNotIn('corrosion',result)
        with closing(sqlite3.connect(self.db)) as db:
            remaining=json.loads(db.execute("SELECT data_json FROM combat_effects WHERE id='mirror-test'").fetchone()[0])['images_remaining']
        self.assertEqual(remaining,1)

    def test_rust_contact_receives_existing_five_bonus_against_blind_target(self):
        item=self.rust()
        effect={'id':'blind-test','target_type':'character','target_id':'vezemir','label':'Cegueira',
                'source':'Teste','duration':'manual','rounds':None,'modifiers':{},'monster_condition':'blinded'}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character','vezemir',json.dumps(effect)))
        with patch('app.monster_contacts.roll_formula',return_value={'total':15,'individual_results':[15]}):
            result=self.rust_command(item,ac=25)
        self.assertTrue(result['hit']);self.assertEqual(result['attack_bonus'],10)
        self.assertTrue(result['corrosion']['destroyed'])

    def test_guarded_ally_requires_retargeting_dorn_without_roll_or_corrosion(self):
        from app.player_inventory import list_inventory
        item=self.rust()
        guard={'id':'guard-test','target_type':'character','target_id':'dorn7','label':'Guarda',
               'source':'Teste','duration':'manual','rounds':None,'modifiers':{},'protocol':'guard','ally_id':'vezemir'}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO character_states(profile_id,state_json,updated_at) VALUES('dorn7',?, 'now')",(json.dumps({'current_hp':20,'maximum_hp':20}),))
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(guard['id'],'character','dorn7',json.dumps(guard)))
        with patch('app.monster_contacts.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'Selecione Dorn'):self.rust_command(item)
            dice.assert_not_called()
        self.assertEqual(list_inventory(self.db,'vezemir')[0]['quantity'],1)
