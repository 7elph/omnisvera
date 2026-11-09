"""Broche-escudo: native HP/ledger transactions on synthetic inventories."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

PATH='compendium:item-magico-broche-escudo'
NOW='2026-11-01T20:00:00+00:00'
MISSILE={'kind':'spell','spell_id':'misseis-magicos','magical':True}


class MagicAbsorptionTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(current_hp=250,maximum_hp=250)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))

    def seed(self,*,equipped=True,quantity=1,path=PATH):
        from app.player_inventory import upsert_inventory
        return upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title='Broche-escudo',
            quantity=quantity,equipped=equipped,equipment_slot='Acessório' if equipped else None,notes=None)

    def stored(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE item_path=?',(PATH,)).fetchone())

    def damage(self,amount,context=MISSILE):
        from app.combat_effects import change_hp
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            return change_hp(db,'character','vezemir',-amount,NOW,damage_context=context)

    def test_magic_missile_consumes_capacity_instead_of_hp(self):
        self.seed();result=self.damage(10)
        self.assertEqual(result['hp_after'],250)
        self.assertEqual(result['magic_item_absorption']['absorbed'],10)
        self.assertEqual(self.stored()['charges_current'],91)

    def test_overflow_breaks_item_and_only_remaining_damage_reaches_hp(self):
        self.seed();result=self.damage(106)
        self.assertEqual(result['hp_after'],245)
        self.assertEqual(result['magic_item_absorption']['remaining'],0)
        item=self.stored()
        self.assertEqual((item['quantity'],item['charges_current'],item['equipped']),(0,0,0))
        self.assertEqual(self.damage(6)['hp_after'],239)

    def test_equipment_and_canonical_identity_required(self):
        self.seed(equipped=False)
        self.assertEqual(self.damage(10)['hp_after'],240)
        self.assertIsNone(self.stored()['charges_current'])
        self.seed(path='Items/Broche-escudo.md')
        self.assertEqual(self.damage(10)['hp_after'],230)

    def test_other_spells_physical_damage_and_healing_do_not_spend_capacity(self):
        self.seed()
        for context in [None,{'kind':'weapon','spell_id':'misseis-magicos'},
                        {'kind':'spell','spell_id':'relampago'}, {'kind':'spell','magical':True}]:
            self.assertEqual(self.damage(4,context)['damage_taken'],4)
        self.damage(-8)
        self.assertIsNone(self.stored()['charges_current'])

    def test_temporary_hp_remains_untouched_while_brooch_absorbs(self):
        self.seed()
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state['temporary_hp']=12
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        result=self.damage(10)
        self.assertEqual(result['temporary_hp_absorbed'],0)
        self.assertEqual(result['damage_taken'],0)

    def test_unavoidable_critical_damage_is_not_absorbed(self):
        self.seed();result=self.damage(12,{**MISSILE,'unavoidable_damage':5})
        self.assertEqual(result['damage_taken'],5)
        self.assertEqual(self.stored()['charges_current'],94)

    def test_daily_rest_does_not_recharge_lifetime_capacity(self):
        self.seed();self.damage(15)
        from app.player_inventory import recharge_inventory
        recharge_inventory(self.db,'inn_rest','vezemir')
        self.assertEqual(self.stored()['charges_current'],86)

    def test_stacked_legacy_copies_do_not_duplicate_capacity_or_freeze_damage(self):
        self.seed(quantity=2)
        self.assertEqual(self.damage(5)['damage_taken'],5)
        self.assertIsNone(self.stored()['charges_current'])

    def test_read_only_inventory_projects_capacity_without_writing(self):
        self.seed();before=self.stored()
        response=self.client.get('/characters/vezemir?read_only=true');self.assertEqual(response.status_code,200)
        item=next(i for i in response.json()['inventory'] if i['item_path']==PATH)
        self.assertEqual((item['charges_current'],item['charges_max']),(101,101))
        self.assertEqual(item['recharge'],'none');self.assertFalse(item['usable'])
        self.assertEqual(before,self.stored())

    def test_catalog_extracts_brooch_without_fabricating_price_or_rules_for_elf_boots(self):
        from app.item_catalog import get_catalog_item
        item=get_catalog_item('item-magico-broche-escudo')
        self.assertIsNotNone(item)
        self.assertEqual(item['mechanics']['magic_absorption_schema'],1)
        self.assertIsNone(item['preco_po'])
        boots=get_catalog_item('item-magico-botas-elficas')
        self.assertNotIn('Broche-escudo',boots['description'])
        self.assertNotIn('magic_absorption_schema',boots['mechanics'])

    def test_manifest_passive_has_no_action_endpoint_and_requires_equipment(self):
        from app.native_action_manifest import sheet_action_manifest
        self.seed();before=self.stored()
        character=self.client.get('/characters/vezemir?read_only=true').json()
        def manifest():return sheet_action_manifest('vezemir',character['definition'],character['state'],character['inventory'])
        entry=next(e for e in manifest() if e['ref']=='item:vezemir:'+PATH)
        self.assertEqual(entry['binding'],'equipped_magic_absorption')
        self.assertIsNone(entry['execution']);self.assertEqual(entry['availability']['state'],'passive')
        next(i for i in character['inventory'] if i['item_path']==PATH)['equipped']=False
        entry=next(e for e in manifest() if e['ref']=='item:vezemir:'+PATH)
        self.assertEqual(entry['availability']['state'],'unavailable')
        forged=next(i for i in character['inventory'] if i['item_path']==PATH)
        forged.update(item_path='session-item:unreviewed-brooch',catalog_id='item-magico-broche-escudo')
        self.assertFalse(any(e['binding']=='equipped_magic_absorption' for e in manifest()))
        self.assertEqual(self.stored(),before)

    def test_passive_cannot_be_used_as_a_consumable(self):
        self.seed();before=self.stored()
        response=self.client.post('/characters/vezemir/actions',json={'action':'use_item',
            'payload':{'item_path':PATH},'request_id':'brooch-cannot-consume'})
        self.assertEqual(response.status_code,400,response.text);self.assertEqual(self.stored(),before)

    def test_brooch_does_not_change_weapon_damage_attack_bonus_or_armor_class(self):
        before=self.client.get('/characters/vezemir?read_only=true').json()['definition']
        self.seed()
        after=self.client.get('/characters/vezemir?read_only=true').json()['definition']
        self.assertEqual(after['defenses']['armor_class'],before['defenses']['armor_class'])
        self.assertEqual(after['attacks'],before['attacks'])

    def test_canonical_budget_clamps_corrupt_oversized_inventory_without_free_charge(self):
        self.seed()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=1000,charges_max=1000 WHERE item_path=?',(PATH,))
        result=self.damage(20)
        self.assertEqual(result['magic_item_absorption']['remaining'],81)
        self.assertEqual(self.stored()['charges_max'],101)


class BroochMarketTests(unittest.TestCase):
    def setUp(self):
        from test_map_commerce import MapCommerceTests
        MapCommerceTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(current_hp=20,maximum_hp=20)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))

    def test_native_market_requires_master_price_and_preserves_partial_capacity_on_sale(self):
        from app import map_commerce as shop
        from app.merchant import add_stock,purse_copper
        from app.combat_effects import change_hp
        with self.assertRaisesRegex(ValueError,'preço'):add_stock(self.db,merchant_id=self.mid,compendium_item_id='item-magico-broche-escudo')
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id='item-magico-broche-escudo',quantity=3,price_override_po=1)
        def balance():
            with closing(sqlite3.connect(self.db)) as db:
                return purse_copper(json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]))
        before=balance()
        def quote(key,quantity=1):return shop.quote(self.db,self.mid,self.owner,request_id=key,
            character_id='vezemir',kind='buy',target_id=line['id'],quantity=quantity)
        invalid=quote('brooch-multiple',2)
        with self.assertRaises(ValueError):shop.confirm(self.db,invalid['id'],self.owner,request_id='brooch-multiple-confirm')
        self.assertEqual(balance(),before)
        buy=quote('brooch-single');receipt=shop.confirm(self.db,buy['id'],self.owner,request_id='brooch-single-confirm')
        self.assertEqual(shop.confirm(self.db,buy['id'],self.owner,request_id='brooch-single-confirm'),receipt)
        self.assertEqual(balance(),before-buy['total_copper'])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            db.execute('UPDATE player_inventory SET equipped=1,equipment_slot=? WHERE item_path=?',('Acessório',PATH))
            change_hp(db,'character','vezemir',-8,NOW,damage_context=MISSILE)
            db.execute('UPDATE player_inventory SET equipped=0,equipment_slot=NULL WHERE item_path=?',(PATH,))
        # Explicit synthetic appraisal, not a campaign/catalog price.
        shop.appraise_item(self.db,self.mid,self.gm,character_id='vezemir',item_path=PATH,unit_copper=25,request_id='brooch-appraisal')
        sale=shop.quote(self.db,self.mid,self.owner,request_id='brooch-sale',character_id='vezemir',kind='sell',target_id=PATH,quantity=1)
        sold=shop.confirm(self.db,sale['id'],self.owner,request_id='brooch-sale-confirm')
        self.assertEqual(shop.confirm(self.db,sale['id'],self.owner,request_id='brooch-sale-confirm'),sold)
        self.assertEqual(balance(),before-buy['total_copper']+sale['total_copper'])
        with closing(sqlite3.connect(self.db)) as db:
            row=db.execute('SELECT instance_json FROM merchant_stock WHERE merchant_id=? AND instance_json IS NOT NULL',(self.mid,)).fetchone()
            instance=json.loads(row[0])
            self.assertEqual((instance['charges_current'],instance['charges_max'],instance['recharge']),(93,101,'none'))


class NativeMissileAbsorptionTests(unittest.TestCase):
    def _insert_character(self,*args):
        from test_combat import CombatAttackResolutionTests
        return CombatAttackResolutionTests._insert_character(self,*args)

    def _character_hp(self,*args):
        from test_combat import CombatAttackResolutionTests
        return CombatAttackResolutionTests._character_hp(self,*args)

    def setUp(self):
        from test_combat import CombatAttackResolutionTests
        CombatAttackResolutionTests.setUp(self)
        self.addCleanup(CombatAttackResolutionTests.tearDown,self)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.database,profile_id='raziel',item_path=PATH,item_title='Broche-escudo',
            quantity=1,equipped=True,equipment_slot='Acessório',notes=None)
        self._insert_character('morthak',10,10)
        from app.character_play import load_session_abilities
        self.mage={'id':'morthak','name':'Morthak','level':2,'session_abilities':load_session_abilities('morthak')}
        with closing(sqlite3.connect(self.database)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            state['resources']=[{'key':'misseis_magicos','current':3,'maximum':3}]
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps(state),))

    def mage_state(self):
        from test_action_recovery import ActionRecoveryTests
        return ActionRecoveryTests.mage_state(self)

    def missiles(self,key='brooch-native-missile'):
        from test_action_recovery import ActionRecoveryTests
        return ActionRecoveryTests.missiles(self,key)

    def stored(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE item_path=?',(PATH,)).fetchone())

    def confirm(self,resolution,role='player',actor='morthak'):
        from app.combat import confirm_attack_resolution
        return confirm_attack_resolution(self.database,resolution_id=resolution['resolution_id'],
            requested_by_id=actor,requested_by_role=role)

    def test_preview_does_not_spend_then_native_confirm_retry_spends_once(self):
        r=self.missiles()
        self.assertIsNone(self.stored()['charges_current'])
        self.assertEqual(r['breakdown']['damage_profile']['spell_id'],'misseis-magicos')
        first,applied=self.confirm(r);self.assertTrue(applied)
        second,applied=self.confirm(r);self.assertFalse(applied)
        self.assertEqual(first,second)
        self.assertEqual(first['damage_total'],0)
        self.assertEqual(self._character_hp('raziel'),14)
        self.assertEqual(self.stored()['charges_current'],96)
        self.assertEqual(self.mage_state()['resources'][0]['current'],2)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='magic_item_absorption'").fetchone()[0],1)

    def test_native_overflow_breakage_and_reload_receipt(self):
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=2,charges_max=101 WHERE item_path=?',(PATH,))
        r=self.missiles();result,_=self.confirm(r)
        self.assertEqual(result['damage_total'],3)
        self.assertEqual(self._character_hp('raziel'),11)
        self.assertEqual((self.stored()['quantity'],self.stored()['equipped']),(0,0))
        replay,applied=self.confirm(r)
        self.assertFalse(applied);self.assertEqual(replay['damage_total'],3)

    def test_concurrent_confirmations_do_not_double_absorb_or_spend_spell_use(self):
        from concurrent.futures import ThreadPoolExecutor
        r=self.missiles()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.confirm(r),range(2)))
        self.assertEqual(sorted(x[1] for x in results),[False,True])
        self.assertEqual(self.stored()['charges_current'],96)
        self.assertEqual(self.mage_state()['resources'][0]['current'],2)

    def test_failed_parent_ledger_rolls_back_absorption_item_resource_and_hp(self):
        r=self.missiles()
        with patch('app.combat.append_session_ledger_event',side_effect=RuntimeError('isolated ledger failure')):
            with self.assertRaisesRegex(RuntimeError,'isolated ledger failure'):self.confirm(r)
        self.assertIsNone(self.stored()['charges_current'])
        self.assertEqual(self.mage_state()['resources'][0]['current'],3)
        self.assertEqual(self._character_hp('raziel'),14)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='magic_item_absorption'").fetchone()[0],0)
        self.assertTrue(self.confirm(r)[1])

    def test_other_owner_cannot_confirm_or_debit_brooch(self):
        r=self.missiles()
        with self.assertRaises(PermissionError):self.confirm(r,actor='raziel')
        self.assertIsNone(self.stored()['charges_current'])


if __name__=='__main__':unittest.main()
