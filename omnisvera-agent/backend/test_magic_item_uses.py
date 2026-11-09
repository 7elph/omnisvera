"""Charged magic items on synthetic sheets and the existing fictional clock."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

CUP='compendium:item-magico-caneco-do-beberrao'
BOOTS='compendium:item-magico-botas-da-velocidade'


class MagicUseTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)

    def seed(self,path,*,equipped=False,quantity=1):
        from app.player_inventory import upsert_inventory
        from app.item_catalog import get_catalog_item
        return upsert_inventory(self.db,profile_id='vezemir',item_path=path,
            item_title=get_catalog_item(path.removeprefix('compendium:'))['name'],quantity=quantity,
            equipped=equipped,equipment_slot='Pés' if equipped else None,notes=None)

    def use(self,path,key='magic-use-1'):
        return self.client.post('/characters/vezemir/actions',json={'action':'use_item',
            'payload':{'item_path':path},'request_id':key})

    def view(self):return self.client.get('/characters/vezemir?read_only=true').json()

    def stored(self,path):
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',path)).fetchone())

    def elapse(self,seconds):
        from app.combat_effects import effect_snapshot
        from app.dorn_spells import elapse
        with closing(sqlite3.connect(self.db)) as db,db:
            elapse(db,effect_snapshot(db),seconds,[],'2026-11-01T12:00:00+00:00')

    def test_catalog_has_explicit_charge_and_time_contracts(self):
        from app.map_commerce import catalog_inventory
        for path in [CUP,BOOTS]:
            item=catalog_inventory(path)
            self.assertTrue(item['usable'])
            self.assertEqual(item['mechanics']['magic_activation_schema'],1)

    def test_get_shows_catalog_budget_without_seeding_inventory(self):
        self.seed(BOOTS,equipped=True);before=self.stored(BOOTS)
        item=next(i for i in self.view()['inventory'] if i['item_path']==BOOTS)
        self.assertEqual(item['charges_current'],18000)
        self.assertEqual(self.stored(BOOTS),before)

    def test_cup_roll_table_all_boundaries_and_native_retry(self):
        self.seed(CUP)
        for die,label in [(1,'anã'),(10,'anã'),(11,'respeitável'),(45,'respeitável'),(46,'baixa'),(98,'baixa'),(99,'orc'),(100,'orc')]:
            with self.subTest(die=die):
                with closing(sqlite3.connect(self.db)) as db,db:
                    db.execute('UPDATE player_inventory SET charges_current=3,charges_max=3 WHERE item_path=?',(CUP,))
                with patch('app.magic_item_uses.roll_formula',return_value={'total':die,'individual_results':[die]} ) as roll:
                    result=self.use(CUP,'cup-boundary-'+str(die))
                    self.assertEqual(result.status_code,200,result.text)
                    self.assertEqual(self.use(CUP,'cup-boundary-'+str(die)).status_code,200)
                    roll.assert_called_once()
                self.assertEqual(self.stored(CUP)['charges_current'],2)
                with closing(sqlite3.connect(self.db)) as read:
                    detail=json.loads(read.execute('SELECT detail_json FROM session_ledger WHERE source_type=? AND source_id=?',('item_use','cup-boundary-'+str(die))).fetchone()[0])
                self.assertIn(label,detail['rules'][0]['label'])

    def test_fourth_cup_use_rejected_without_destroying_item(self):
        self.seed(CUP)
        for n in range(3):self.assertEqual(self.use(CUP,'cup-use-'+str(n)).status_code,200)
        self.assertEqual(self.use(CUP,'cup-exhausted').status_code,400)
        item=self.stored(CUP);self.assertEqual((item['quantity'],item['charges_current'],item['recharge']),(1,0,'inn_rest'))

    def test_boots_require_equipment(self):
        self.seed(BOOTS)
        self.assertEqual(self.use(BOOTS).status_code,400)
        self.assertIsNone(self.stored(BOOTS)['charges_current'])

    def test_boots_apply_x4_without_rewriting_base_movement(self):
        self.seed(BOOTS,equipped=True)
        before=self.view()['definition']['movement']
        r=self.use(BOOTS);self.assertEqual(r.status_code,200,r.text)
        self.assertIn('36',r.json()['definition']['movement'])
        self.assertIn('×4',r.json()['definition']['movement'])
        self.assertEqual(self.stored(BOOTS)['charges_current'],18000)
        self.assertEqual(self.use(BOOTS).status_code,200)
        self.assertIn('×4',self.view()['definition']['movement'])
        self.assertEqual(self.use(BOOTS,'boots-stop').status_code,200)
        self.assertEqual(self.view()['definition']['movement'],before)

    def test_boots_spend_only_active_fictional_time_across_reactivation(self):
        self.seed(BOOTS,equipped=True);self.assertEqual(self.use(BOOTS).status_code,200)
        self.elapse(600);self.assertEqual(self.stored(BOOTS)['charges_current'],17400)
        self.assertEqual(self.use(BOOTS,'boots-stop').status_code,200)
        self.elapse(3600);self.assertEqual(self.stored(BOOTS)['charges_current'],17400)
        self.assertEqual(self.use(BOOTS,'boots-resume').status_code,200)
        self.elapse(17400);self.assertEqual(self.stored(BOOTS)['charges_current'],0)
        self.assertNotIn('×4',self.view()['definition']['movement'])
        self.assertEqual(self.use(BOOTS,'boots-empty').status_code,400)

    def test_unequip_ends_speed_without_refilling_budget(self):
        self.seed(BOOTS,equipped=True);self.use(BOOTS);self.elapse(10)
        r=self.client.post('/characters/vezemir/actions',json={'action':'unequip_item','payload':{'item_path':BOOTS},'request_id':'boots-stow'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertNotIn('×4',r.json()['definition']['movement'])
        self.assertEqual(self.stored(BOOTS)['charges_current'],17990)

    def test_master_rest_restores_daily_uses_and_ends_effect(self):
        self.seed(CUP);self.seed(BOOTS,equipped=True);self.use(CUP);self.use(BOOTS,'boots-start');self.elapse(20)
        r=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','payload':{},'request_id':'magic-full-rest'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.stored(CUP)['charges_current'],3)
        self.assertEqual(self.stored(BOOTS)['charges_current'],18000)
        self.assertNotIn('×4',r.json()['definition']['movement'])

    def test_failed_ledger_rolls_back_charges_and_timed_effect(self):
        self.seed(BOOTS,equipped=True)
        from app.combat_consumables import use_inventory_item
        from app.map_commerce import catalog_inventory
        item={**catalog_inventory(BOOTS),'item_path':BOOTS,'name':'Botas da velocidade'}
        with patch('app.combat_consumables.append_session_ledger_event',side_effect=RuntimeError('fixture ledger failure')):
            with self.assertRaises(RuntimeError):use_inventory_item(self.db,character_id='vezemir',actor_id='master',actor_role='gm',request_id='boots-rollback',item=item)
        self.assertIsNone(self.stored(BOOTS)['charges_current'])
        self.assertNotIn('×4',self.view()['definition']['movement'])

    def test_multiple_unseparated_charged_copies_are_not_silently_pooled(self):
        self.seed(CUP,quantity=2)
        self.assertEqual(self.use(CUP).status_code,400)
        self.assertIsNone(self.stored(CUP)['charges_current'])

    def test_player_cannot_use_another_sheet_or_recharge_daily_items(self):
        from app import main
        from app.access import AccessContext
        self.seed(CUP)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        self.assertEqual(self.use(CUP).status_code,403)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')
        self.assertEqual(self.use(CUP,'cup-owner').status_code,200)
        rest=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','payload':{},'request_id':'cup-own-rest'})
        self.assertEqual(rest.status_code,403)
        self.assertEqual(self.stored(CUP)['charges_current'],2)

    def test_same_request_cannot_switch_items(self):
        self.seed(CUP);self.seed(BOOTS,equipped=True)
        self.assertEqual(self.use(CUP,'magic-collision').status_code,200)
        self.assertEqual(self.use(BOOTS,'magic-collision').status_code,400)
        self.assertIsNone(self.stored(BOOTS)['charges_current'])

    def test_explicit_master_recharge_syncs_running_budget(self):
        from app.player_inventory import recharge_inventory
        self.seed(BOOTS,equipped=True);self.use(BOOTS);self.elapse(600)
        recharge_inventory(self.db,'inn_rest','vezemir');self.elapse(10)
        self.assertEqual(self.stored(BOOTS)['charges_current'],17990)

    def test_manual_budget_correction_updates_active_expiration(self):
        self.seed(BOOTS,equipped=True);self.use(BOOTS);self.elapse(10)
        corrected=self.client.post('/characters/vezemir/actions',json={'action':'change_charges',
            'payload':{'item_path':BOOTS,'charges':60},'request_id':'boots-correct-budget'})
        self.assertEqual(corrected.status_code,200,corrected.text)
        self.elapse(60)
        self.assertEqual(self.stored(BOOTS)['charges_current'],0)
        self.assertNotIn('×4',self.view()['definition']['movement'])

    def test_unreviewed_magic_opcode_cannot_execute_or_consume(self):
        from app.combat_consumables import use_inventory_item
        self.seed(CUP)
        fake={'item_path':CUP.replace('caneco-do-beberrao','unknown'),'usable':True,
              'name':'Unknown','effect_rules':[{'trigger':'on_use','kind':'magic_activation'}],
              'mechanics':{'magic_activation_schema':1}}
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=fake['item_path'],item_title='Unknown',quantity=1,equipped=False,notes=None)
        with self.assertRaises(ValueError):use_inventory_item(self.db,character_id='vezemir',actor_id='master',actor_role='gm',request_id='unknown-magic',item=fake)

    def test_book_limits_are_not_increased_by_legacy_charge_columns(self):
        self.seed(CUP)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=999,charges_max=999 WHERE item_path=?',(CUP,))
        self.assertEqual(self.use(CUP).status_code,200)
        self.assertEqual((self.stored(CUP)['charges_current'],self.stored(CUP)['charges_max']),(2,3))

    def test_combat_activation_keeps_attack_and_stop_remains_available(self):
        from app.combat_effects import init_effects,effect_snapshot
        self.seed(BOOTS,equipped=True);self.seed(CUP);init_effects(self.db)
        encounter={'active':True,'battle_mode':True,'started_at':'fixture','turn_index':0,'turn_sequence':1,
                   'participants':[{'target_type':'character','target_id':'vezemir'}],
                   'action_committed':False,'attacks_used':0,'attack_limit':1}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        self.assertEqual(self.use(BOOTS).status_code,200)
        self.assertEqual(self.use(CUP,'cup-same-turn').status_code,400)
        self.assertEqual(self.use(BOOTS,'boots-stop-same-turn').status_code,200)
        with closing(sqlite3.connect(self.db)) as db:state=effect_snapshot(db)['encounter']
        self.assertTrue(state['consumable_used']);self.assertFalse(state['action_committed'])
        self.assertEqual(state['attacks_used'],0)

    def test_concurrent_retry_consumes_one_charge_and_one_roll(self):
        from concurrent.futures import ThreadPoolExecutor
        from app.combat_consumables import use_inventory_item
        from app.map_commerce import catalog_inventory
        self.seed(CUP)
        item={**catalog_inventory(CUP),'item_path':CUP,'name':'Caneco do Beberrão'}
        def use(_):return use_inventory_item(self.db,character_id='vezemir',actor_id='master',actor_role='gm',request_id='cup-concurrent',item=item)
        with patch('app.magic_item_uses.roll_formula',return_value={'total':50,'individual_results':[50]}) as roll,ThreadPoolExecutor(max_workers=2) as workers:
            a,b=list(workers.map(use,range(2)))
        self.assertEqual(a,b);roll.assert_called_once()
        self.assertEqual(self.stored(CUP)['charges_current'],2)

    def test_native_delivery_rejects_merging_daily_items_before_mutation(self):
        from app.item_transfer import grant_item
        from app.item_registry import registry
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row;item=registry(db,vault_root=self.db.parent)['entries'][CUP.removeprefix('compendium:')]
            grant_item(db,item,'vezemir',1,'fixture',origin='fixture')
            with self.assertRaises(ValueError):grant_item(db,item,'vezemir',1,'fixture',origin='fixture')
        self.assertEqual(self.stored(CUP)['quantity'],1)


class MagicChargeMarketTests(unittest.TestCase):
    def setUp(self):
        from test_map_commerce import MapCommerceTests
        MapCommerceTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);data['coins']=5000
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(data),))

    def test_failed_multiple_copies_purchase_never_takes_money_or_stock(self):
        from app import map_commerce as shop
        from app.merchant import add_stock,purse_copper
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id=CUP.removeprefix('compendium:'),quantity=3)
        def state():
            with closing(sqlite3.connect(self.db)) as db:
                return (purse_copper(json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])),
                        db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(line['id'],)).fetchone()[0])
        def quote(key,qty):return shop.quote(self.db,self.mid,self.owner,request_id=key,character_id='vezemir',kind='buy',target_id=line['id'],quantity=qty)
        before=state();q=quote('magic-two-copies',2)
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='magic-two-confirm')
        self.assertEqual(state(),before)
        q=quote('magic-one-copy',1);shop.confirm(self.db,q['id'],self.owner,request_id='magic-one-confirm')
        after=state();self.assertEqual(after,(before[0]-q['total_copper'],2))
        q=quote('magic-second-copy',1)
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='magic-second-confirm')
        self.assertEqual(state(),after)
