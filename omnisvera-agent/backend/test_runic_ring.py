"""Daily ring uses native catalogue, inventory, rest and idempotent transactions."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from app.character_play import init_character_play, apply_character_action
from app.combat_consumables import use_inventory_item
from app.combat_effects import init_effects
from app.dice_rolls import init_dice_rolls
from app.player_inventory import init_player_inventory, upsert_inventory
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_session_item, get_session_item
from scripts.runic_ring_contract import repair_payload


class RunicRingTests(TestCase):
    def setUp(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup);self.db=Path(folder.name)/'ring.sqlite3'
        for init in (init_character_play,init_player_inventory,init_effects,init_session_workspace,init_dice_rolls,init_session_ledger):init(self.db)
        state={'current_hp':5,'maximum_hp':20,'temporary_hp':0,'conditions':[],
               'resources':[{'key':'caixao','current':1,'maximum':1,'recharge':'inn_rest'}]}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO character_states VALUES(?,?,1,?)',('raziel',json.dumps(state),'fixture'))
        self.original=save_session_item(self.db,name='Anel Runico',item_type='Anel',description='1 vez por dia recupera 4 de vida',
            effects=[],effect_rules=[{'trigger':'on_use','kind':'heal_hp','value':4}],usable=True,image_path='ring.png',
            mechanics={'consume_mode':'none','charges_max':1,'recharge':'inn_rest','slot_limit':1})
        self.item=save_session_item(self.db,item_id=self.original['id'],**repair_payload(self.original))
        upsert_inventory(self.db,profile_id='raziel',item_path=self.item['item_path'],item_title=self.item['name'],
            quantity=1,equipped=True,notes=None,charges_current=1,charges_max=1,recharge='inn_rest')
    def use(self,request_id='ring-first'):
        return use_inventory_item(self.db,character_id='raziel',actor_id='raziel',actor_role='player',request_id=request_id,item=self.item)
    def saved(self):
        with closing(sqlite3.connect(self.db)) as db:
            return (json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])['current_hp'],
                tuple(db.execute("SELECT quantity,charges_current FROM player_inventory").fetchone()),
                db.execute("SELECT count(*) FROM session_ledger WHERE source_type='item_use'").fetchone()[0])
    def rest(self,action,role='gm',request_id='rest-ring'):
        return apply_character_action(self.db,character_id='raziel',actor_id='master' if role=='gm' else 'raziel',
            actor_role=role,action=action,payload={},request_id=request_id)
    def test_patch_changes_only_consume_mode_and_preserves_identity_art_and_heal(self):
        payload=repair_payload(self.original)
        self.assertEqual('charges',payload['mechanics']['consume_mode'])
        for key in ('name','item_type','description','effects','effect_rules','usable','image_path'):
            self.assertEqual(self.original[key],payload[key])
        self.assertEqual('none',self.original['mechanics']['consume_mode'])
        with self.assertRaises(ValueError):repair_payload({**self.original,'name':'Outro anel'})
    def test_heal_four_spend_one_retry_once_and_block_second_use(self):
        first=self.use();self.assertEqual((9,(1,0),1),self.saved())
        self.assertEqual(first,self.use());self.assertEqual((9,(1,0),1),self.saved())
        with self.assertRaisesRegex(ValueError,'cargas'):self.use('ring-second')
        self.assertEqual((9,(1,0),1),self.saved())
    def test_concurrent_clicks_and_reload_preserve_one_charge_one_heal(self):
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.use(),range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual((9,(1,0),1),self.saved())
        self.item=get_session_item(self.db,self.item['id']);self.use()
        self.assertEqual((9,(1,0),1),self.saved())
    def test_only_master_inn_rest_recharges_not_owner_coffin(self):
        self.use();self.rest('rest_in_coffin','player','coffin-after-ring')
        self.assertEqual((1,0),self.saved()[1])
        with self.assertRaisesRegex(ValueError,'cargas'):self.use('ring-after-coffin')
        with self.assertRaises(PermissionError):self.rest('rest_at_inn','player','owner-inn')
        self.rest('rest_at_inn');self.assertEqual((1,1),self.saved()[1]);self.use('ring-after-master')
        self.assertEqual((1,0),self.saved()[1])
    def test_hp_cap_and_unequip_do_not_recharge(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            row=json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0]);row['current_hp']=19
            db.execute('UPDATE character_states SET state_json=?',(json.dumps(row),))
        self.use();self.assertEqual(20,self.saved()[0])
        for action in ('unequip_item','equip_item'):
            apply_character_action(self.db,character_id='raziel',actor_id='raziel',actor_role='player',action=action,
                payload={'item_path':self.item['item_path'],'equipment_slot':'Acessório'},request_id='ring-'+action)
        self.assertEqual((1,0),self.saved()[1])
    def test_legacy_holder_missing_charge_metadata_inherits_recharge_on_first_use(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=NULL,charges_max=NULL,recharge=NULL')
        self.use();self.assertEqual((1,0),self.saved()[1])
        self.rest('rest_at_inn');self.assertEqual((1,1),self.saved()[1])
    def test_owner_cannot_refill_or_change_daily_recharge_through_manual_action(self):
        self.use()
        for payload in ({'charges':1},{'charges':0,'recharge':'scene'},{'charges':0,'charges_max':999}):
            with self.assertRaises(PermissionError):
                apply_character_action(self.db,character_id='raziel',actor_id='raziel',actor_role='player',
                    action='change_charges',payload={'item_path':self.item['item_path'],**payload})
            self.assertEqual((1,0),self.saved()[1])
    def test_owner_cannot_invent_maximum_for_uninitialized_legacy_charges(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=NULL,charges_max=NULL,recharge=NULL')
        with self.assertRaises(PermissionError):
            apply_character_action(self.db,character_id='raziel',actor_id='raziel',actor_role='player',
                action='change_charges',payload={'item_path':self.item['item_path'],'charges':999,'charges_max':999})
