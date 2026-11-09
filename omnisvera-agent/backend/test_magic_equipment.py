"""Native magic equipment, using only synthetic actor inventories."""
import json
import sqlite3
import unittest
from contextlib import closing

ATTR_ITEMS={
    'coroa-do-dragao':('intelligence','Cabeça'),
    'cinto-da-forca-do-ogro':('strength','Cinto'),
    'cinturao-dos-anoes':('constitution','Cinto'),
    'colar-do-menestrel':('charisma','Acessório'),
    'luvas-do-acrobata':('dexterity','Mãos'),
    'manto-da-aguia':('wisdom','Acessório'),
}


class MagicContractTests(unittest.TestCase):
    def test_broken_source_boundaries_are_corrected_without_erasing_the_source(self):
        from app.item_catalog import get_catalog_item,normalize_catalog_item
        for identity,foreign_title in [('botas-elficas','Broche-escudo'),('anel-ariete','Armazenamento de magia:'),('anel-inquisidor','Invisibilidade:')]:
            item=get_catalog_item('item-magico-'+identity)
            self.assertNotIn(foreign_title,item['description'])
            self.assertIn(foreign_title,item['source_description'])
        self.assertIn('respirar',get_catalog_item('item-magico-medalhao-de-adaptacao')['description'])
        item=get_catalog_item('item-magico-cinto-da-forca-do-ogro')
        again=normalize_catalog_item(item)
        self.assertEqual(again['effect_rules'],item['effect_rules'])
        self.assertEqual(item['mechanics']['magic_readiness']['status'],'native_while_equipped')
        pending=get_catalog_item('item-magico-braceletes-de-armadura')
        self.assertEqual(pending['mechanics']['magic_readiness']['status'],'variants_available')
        self.assertFalse(pending.get('effect_rules'))

    def test_unknown_similar_name_does_not_gain_inferred_magic(self):
        from app.item_families import descriptor
        result=descriptor({'id':'unreviewed-item','category':'item-magico','name':'Cinto da força do ogro',
            'description':'+2 Força, +99 CA, lança qualquer magia'})
        self.assertEqual(result['effect_rules'],[])
        self.assertFalse(result['usable'])

    def test_fixed_magic_items_compile_native_equipped_rules_without_turning_into_weapons(self):
        from app.map_commerce import catalog_inventory
        for suffix,(attribute,slot) in ATTR_ITEMS.items():
            with self.subTest(item=suffix):
                item=catalog_inventory('compendium:item-magico-'+suffix)
                self.assertTrue(item['mechanics'].get('magical'))
                self.assertEqual(item['mechanics']['equipment_slots'],[slot])
                rules=[r for r in item['effect_rules'] if r['kind']=='attribute_bonus']
                self.assertEqual([(r['target'],r['value']) for r in rules],[(attribute,2)])
                self.assertEqual(rules[0]['trigger'],'while_equipped')
                self.assertIsNone(item['damage_formula'])
                self.assertFalse(item['usable'])
                from app.item_catalog import item_offer_readiness,get_catalog_item
                report=item_offer_readiness(get_catalog_item('item-magico-'+suffix))
                self.assertEqual(report['effect_status'],'native_while_equipped')
                self.assertNotIn('efeito_especial_assistido',report['warnings'])


class MagicEquipmentApiTests(unittest.TestCase):
    def setUp(self):
        from test_item_specials import ItemSpecialApiTests
        ItemSpecialApiTests.setUp(self)
        self.addCleanup(lambda:ItemSpecialApiTests.tearDown(self))
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            data['attributes']={'strength':13,'dexterity':14,'constitution':13,'intelligence':13,'wisdom':13,'charisma':13}
            data['character_class']['saving_throw']=14
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(data),))
        ItemSpecialApiTests.equip(self,'arma-corpo-espada-longa','Espada longa')

    def character(self):
        r=self.client.get('/characters/vezemir?read_only=true')
        self.assertEqual(r.status_code,200,r.text)
        return r.json()

    def equip(self,suffix,slot):
        from app.player_inventory import upsert_inventory
        path='compendium:item-magico-'+suffix
        upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title=suffix,quantity=1,equipped=False,notes=None)
        r=self.client.post('/characters/vezemir/actions',json={'action':'equip_item',
            'payload':{'item_path':path,'equipment_slot':slot},'request_id':'magic-equip-'+suffix})
        self.assertEqual(r.status_code,200,r.text)
        return path

    def test_strength_item_changes_score_attack_and_damage_then_stowing_reverts_without_base_edits(self):
        before=self.character();path=self.equip('cinto-da-forca-do-ogro','Cinto');after=self.character()
        self.assertEqual(after['definition']['attributes']['strength'],15)
        melee=lambda c:next(a for a in c['definition']['attacks'] if a['id']=='melee')
        self.assertEqual(melee(after)['attack_bonus'],melee(before)['attack_bonus']+1)
        from app.dice_rolls import parse_formula
        self.assertEqual(parse_formula(melee(after)['damage']).modifier,parse_formula(melee(before)['damage']).modifier+1)
        r=self.client.post('/characters/vezemir/actions',json={'action':'unequip_item','payload':{'item_path':path},'request_id':'magic-stow-ogre'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.character()['definition']['attributes'],before['definition']['attributes'])
        self.assertEqual(melee(self.character()),melee(before))

    def test_dexterity_item_changes_ranged_bonus_and_ac_without_replacing_armor(self):
        before=self.character();self.equip('luvas-do-acrobata','Mãos');after=self.character()
        self.assertEqual(after['definition']['attributes']['dexterity'],16)
        ranged=lambda c:next(a for a in c['definition']['attacks'] if a['id']=='ranged')['attack_bonus']
        self.assertEqual(ranged(after),ranged(before)+1)
        self.assertEqual(after['definition']['defenses']['armor_class'],before['definition']['defenses']['armor_class']+1)

    def test_magic_strength_reaches_confirmed_critical_damage_once(self):
        from test_item_specials import ItemSpecialApiTests
        self.equip('cinto-da-forca-do-ogro','Cinto')
        target=ItemSpecialApiTests.target(self)
        request=ItemSpecialApiTests.request(self,target,key='magic-native-critical')
        result=self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(result.status_code,200,result.text)
        resolution=result.json()
        self.assertEqual(resolution['damage_modifier'],1)
        self.assertEqual(resolution['damage_formula'],'1d8+1')
        strike=resolution['breakdown']['strikes'][0]
        self.assertEqual(strike['critical_multiplier'],2)
        self.assertEqual(len(strike['damage_rolls']),2)
        self.assertEqual(resolution['damage_total'],sum(strike['damage_rolls'])+1)
        endpoint='/combat/attacks/'+resolution['resolution_id']+'/confirm'
        confirmed=self.client.post(endpoint)
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.assertEqual(confirmed.json()['hp_after'],100-resolution['damage_total'])
        self.assertEqual(self.client.post(endpoint).json()['hp_after'],confirmed.json()['hp_after'])

    def test_constitution_item_reaches_native_save_attributes_without_healing_or_level_changes(self):
        from app.monster_poison_runtime import current_attributes
        self.equip('cinturao-dos-anoes','Cinto')
        with closing(sqlite3.connect(self.db)) as db:
            attrs=current_attributes(db,'character','vezemir')
            self.assertEqual(attrs['constitution'],15)
        c=self.character()
        self.assertEqual(c['state']['current_hp'],20)
        self.assertEqual(c['definition']['level'],2)

    def test_all_six_attributes_apply_once_and_stow_reverts_without_changing_stored_sheet(self):
        from app.dice_rolls import resolve_character_roll,parse_formula
        with closing(sqlite3.connect(self.db)) as db:
            stored=db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]
        for suffix,(attribute,slot) in ATTR_ITEMS.items():
            with self.subTest(item=suffix):
                before=self.character();path=self.equip(suffix,slot);after=self.character()
                self.assertEqual(after['definition']['attributes'][attribute],before['definition']['attributes'][attribute]+2)
                roll=resolve_character_roll(after['definition'],after['inventory'],'attribute',attribute)
                self.assertEqual(parse_formula(roll.formula).modifier,after['definition']['attribute_modifiers'][attribute])
                self.assertEqual(self.character()['definition'],after['definition'])
                response=self.client.post('/characters/vezemir/actions',json={'action':'unequip_item','payload':{'item_path':path},'request_id':'magic-stow-'+suffix})
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(self.character()['definition']['attributes'],before['definition']['attributes'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0],stored)

    def test_veteran_vezemir_does_not_receive_strength_bonus_twice(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            data['character_class'].update(level=5,base_attack=5)
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(data),))
        before=self.character();self.equip('cinto-da-forca-do-ogro','Cinto');after=self.character()
        melee=lambda c:next(a for a in c['definition']['attacks'] if a['id']=='melee')
        self.assertEqual(melee(after)['attack_bonus'],melee(before)['attack_bonus']+1)

    def test_dexterity_cap_of_armor_still_applies_to_magic_gloves(self):
        from test_item_specials import ItemSpecialApiTests
        ItemSpecialApiTests.equip(self,'protecao-armadura-de-carbono-media','Armadura de Carbono Média','Armadura')
        before=self.character();self.equip('luvas-do-acrobata','Mãos');after=self.character()
        self.assertEqual(after['definition']['attributes']['dexterity'],16)
        self.assertEqual(after['definition']['defenses']['armor_class'],before['definition']['defenses']['armor_class'])

    def test_native_jp_uses_equipped_constitution_score_once(self):
        from unittest.mock import patch
        from app.dorn_spells import target,save
        self.equip('cinturao-dos-anoes','Cinto')
        with closing(sqlite3.connect(self.db)) as db,patch('app.dorn_spells.roll_formula',return_value={'total':10,'individual_results':[10]}):
            result=save(db,target(db,'character','vezemir'),'constitution')
            self.assertEqual(result['attribute_bonus'],2)
            self.assertEqual(result['total'],12)

    def test_cloak_adds_two_ac_once_and_stow_restores_it(self):
        before=self.character();path=self.equip('manto-da-confusao','Acessório');after=self.character()
        self.assertEqual(after['definition']['defenses']['armor_class'],before['definition']['defenses']['armor_class']+2)
        self.assertEqual(after['state']['current_hp'],before['state']['current_hp'])
        self.client.post('/characters/vezemir/actions',json={'action':'unequip_item','payload':{'item_path':path},'request_id':'magic-stow-cloak'})
        self.assertEqual(self.character()['definition']['defenses']['armor_class'],before['definition']['defenses']['armor_class'])

    def test_missing_attribute_is_not_invented_to_equip_magic(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]);data['attributes'].pop('wisdom')
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(data),))
        from app.player_inventory import upsert_inventory
        path='compendium:item-magico-manto-da-aguia'
        upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title='Manto da águia',quantity=1,equipped=False,notes=None)
        r=self.client.post('/characters/vezemir/actions',json={'action':'equip_item','payload':{'item_path':path,'equipment_slot':'Acessório'},'request_id':'magic-missing-attribute'})
        self.assertEqual(r.status_code,400,r.text)
        self.assertIn('Sabedoria',r.text)

    def test_magic_accessory_does_not_make_an_ordinary_weapon_magical(self):
        from app.damage_profiles import attack_profile
        self.equip('cinto-da-forca-do-ogro','Cinto')
        character=self.character();attack=next(a for a in character['definition']['attacks'] if a['id']=='melee')
        self.assertFalse(attack_profile(attack,character['inventory'])['magical'])


from test_hemomancy_weapons import HemomancyGridFixture


class MagicHemomancyTests(HemomancyGridFixture):
    def test_blood_weapon_retains_magic_attribute_attack_and_flat_damage_bonus(self):
        from app.player_inventory import upsert_inventory
        self.durable_target()
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='raziel'").fetchone()[0])
            data['attributes']['strength']=13
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='raziel'",(json.dumps(data),))
        before=self.attack(weapon='foice',request='magic-raziel-before')
        self.assertEqual(before.status_code,200,before.text)
        upsert_inventory(self.db,profile_id='raziel',item_path='compendium:item-magico-cinto-da-forca-do-ogro',
            item_title='Cinto da força do ogro',quantity=1,equipped=True,equipment_slot='Cinto',notes=None)
        after=self.attack(weapon='foice',request='magic-raziel-after')
        self.assertEqual(after.status_code,200,after.text)
        self.assertEqual(after.json()['attack_bonus'],before.json()['attack_bonus']+1)
        self.assertEqual(after.json()['damage_modifier'],before.json()['damage_modifier']+1)


class MagicMarketTests(unittest.TestCase):
    def setUp(self):
        from test_map_commerce import MapCommerceTests
        MapCommerceTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);data['coins']=5000
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(data),))

    def test_buy_and_sell_magic_preserve_contract_and_native_wallet_value(self):
        from app import map_commerce as shop
        from app.merchant import add_stock,purse_copper
        from app.item_registry import registry
        identity='item-magico-cinto-da-forca-do-ogro';path='compendium:'+identity
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id=identity,quantity=2)
        def balance():
            with closing(sqlite3.connect(self.db)) as db:
                return purse_copper(json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]))
        before=balance()
        q=shop.quote(self.db,self.mid,self.owner,request_id='magic-buy-quote',character_id='vezemir',kind='buy',target_id=line['id'],quantity=1)
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id='magic-buy-once')
        self.assertEqual(shop.confirm(self.db,q['id'],self.owner,request_id='magic-buy-once'),receipt)
        self.assertEqual(balance(),before-q['total_copper'])
        self.assertEqual(shop.catalog_inventory(path)['effect_rules'][0]['value'],2)
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            index=registry(db,vault_root=self.db.parent)
            self.assertEqual(index['entries'][identity]['trade_group'],'arcane')
        sale=shop.quote(self.db,self.mid,self.owner,request_id='magic-sale-quote',character_id='vezemir',kind='sell',target_id=path,quantity=1)
        sold=shop.confirm(self.db,sale['id'],self.owner,request_id='magic-sale-once')
        self.assertEqual(shop.confirm(self.db,sale['id'],self.owner,request_id='magic-sale-once'),sold)
        self.assertEqual(balance(),before-q['total_copper']+sale['total_copper'])


if __name__=='__main__':unittest.main()
