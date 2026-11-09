"""Native container commands use only a synthetic inventory/SQLite fixture."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch


class MagicContainerTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        from app.player_inventory import upsert_inventory
        self.bag='compendium:item-magico-sacola-magica-ordeira'
        upsert_inventory(self.db,profile_id='vezemir',item_path=self.bag,item_title='Sacola mágica ordeira',quantity=1,equipped=False,notes=None)
        self.path='session-item:'+str(self.custom('Gema de ensaio',0.1,2))
        upsert_inventory(self.db,profile_id='vezemir',item_path=self.path,item_title='Gema de ensaio',quantity=2,equipped=False,notes=None)

    def custom(self,title,weight,entry_cm):
        with closing(sqlite3.connect(self.db)) as db,db:
            cursor=db.execute("INSERT INTO session_custom_items(name,item_type,description,effects_json,usable,image_path,created_at,updated_at,effect_rules_json,mechanics_json) VALUES(?,?,?,'[]',0,NULL,'fixture','fixture','[]',?)",
                (title,'item','Objeto sintético com medidas explícitas.',json.dumps({'weight_kg':weight,'container_entry_cm':entry_cm})))
            return cursor.lastrowid

    def view(self):
        from app.magic_containers import inspect
        return inspect(self.db,owner='vezemir',actor='master',role='gm',item_path=self.bag)

    def command(self,operation,key,**extra):
        from app.magic_containers import command
        return command(self.db,owner='vezemir',actor='master',role='gm',request_id=key,
            payload={'item_path':self.bag,'operation':operation,'expected_version':self.view()['version'],**extra})

    def row(self,path=None):
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',path or self.path)).fetchone())

    def test_catalog_has_two_concrete_variants_and_no_arbitrary_container_on_similar_names(self):
        from app.item_catalog import get_catalog_item
        for suffix in ['ordeira','caotica']:
            entry=get_catalog_item('item-magico-sacola-magica-'+suffix)
            self.assertIsNotNone(entry)
            self.assertEqual(entry['mechanics']['magic_container_schema'],1)
        from app.magic_containers import compile_item
        self.assertIsNone(compile_item({'id':'invented-bag','name':'Sacola mágica'}))

    def test_catalog_potion_estimates_enable_storage_reload_retry_and_take(self):
        from app.player_inventory import upsert_inventory
        from app.hp_potions import ITEM_PATH
        upsert_inventory(self.db,profile_id='vezemir',item_path=ITEM_PATH,item_title='Poção de HP',quantity=2,equipped=False,notes=None)
        self.command('open','estimated-open')
        result=self.command('store','estimated-store',source_path=ITEM_PATH,quantity=1)
        self.assertEqual(self.row(ITEM_PATH)['quantity'],1)
        from app.magic_containers import command
        command(self.db,owner='vezemir',actor='master',role='gm',request_id='estimated-store',payload=result['intent'])
        state=self.view()
        self.assertEqual(state['contents'][0]['quantity'],1)
        self.command('take','estimated-take',entry_id=state['contents'][0]['id'],quantity=1)
        self.assertEqual(self.row(ITEM_PATH)['quantity'],2)

    def test_living_stock_is_rejected_even_with_explicit_fitting_dimensions(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_custom_items SET name='Cavalo de montaria' WHERE id=?",(int(self.path.split(':')[1]),))
        self.command('open','livestock-open')
        with self.assertRaisesRegex(ValueError,'criaturas'):
            self.command('store','livestock-store',source_path=self.path,quantity=1)
        self.assertEqual(self.row()['quantity'],2)
        self.assertEqual(self.view()['contents'],[])

    def test_estimated_shield_does_not_fit_bag_but_fits_portable_hole(self):
        from app.player_inventory import upsert_inventory
        shield='compendium:protecao-escudo-de-vibranium'
        upsert_inventory(self.db,profile_id='vezemir',item_path=shield,item_title='Escudo',quantity=1,equipped=False,notes=None)
        self.command('open','shield-bag-open')
        with self.assertRaisesRegex(ValueError,'abertura'):
            self.command('store','shield-too-wide',source_path=shield,quantity=1)
        self.bag='compendium:item-magico-buraco-portatil'
        upsert_inventory(self.db,profile_id='vezemir',item_path=self.bag,item_title='Buraco portátil',quantity=1,equipped=False,notes=None)
        self.command('open','shield-hole-open')
        self.command('store','shield-hole-store',source_path=shield,quantity=1)
        state=self.view()
        self.assertEqual(state['weight_kg'],2)
        self.assertGreater(state['volume_m3'],0)
        self.command('take','shield-hole-take',entry_id=state['contents'][0]['id'],quantity=1)
        self.assertEqual(self.row(shield)['quantity'],1)

    def test_adamas_storage_uses_actual_form_weight_and_keeps_estimate_provenance(self):
        from app.player_inventory import upsert_inventory
        from app.inventory_conditions import save_condition,read_condition
        sword='compendium:item-magico-espada-adamas'
        upsert_inventory(self.db,profile_id='vezemir',item_path=sword,item_title='Adamas',quantity=1,equipped=False,notes=None)
        with closing(sqlite3.connect(self.db)) as db,db:
            save_condition(db,self.row(sword)['id'],{'magic_form':'arma-corpo-espada-larga'},'fixture')
        self.command('open','adamas-bag-open')
        self.command('store','adamas-bag-store',source_path=sword,quantity=1)
        self.assertEqual(self.view()['weight_kg'],7)
        with closing(sqlite3.connect(self.db)) as db:
            contents=read_condition(db,self.row(self.bag)['id'])['magic_container']['contents']
        self.assertEqual(contents[0]['unit_packed_length_cm'],160)
        self.assertEqual(contents[0]['physical_metadata']['status'],'provisional_campaign')
        self.command('take','adamas-bag-take',entry_id=contents[0]['id'],quantity=1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(read_condition(db,self.row(sword)['id'])['magic_form'],'arma-corpo-espada-larga')

    def test_store_and_take_move_native_quantity_with_one_receipt_and_persisted_contents(self):
        self.command('open','bag-open')
        result=self.command('store','bag-store',source_path=self.path,quantity=1)
        self.assertEqual(self.row()['quantity'],1)
        self.assertEqual(self.view()['contents'][0]['quantity'],1)
        from app.magic_containers import command
        command(self.db,owner='vezemir',actor='master',role='gm',request_id='bag-store',payload=result['intent'])
        self.assertEqual(self.row()['quantity'],1)
        entry=self.view()['contents'][0]
        self.command('take','bag-take',entry_id=entry['id'],quantity=1)
        self.assertEqual(self.row()['quantity'],2)
        self.assertEqual(self.view()['contents'],[])

    def test_closed_container_equipped_item_and_oversized_object_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'Abra'):self.command('store','closed',source_path=self.path,quantity=1)
        self.command('open','bag-open')
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET equipped=1 WHERE item_path=?',(self.path,))
        with self.assertRaisesRegex(ValueError,'equipado'):self.command('store','equipped',source_path=self.path,quantity=1)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(self.path,))
            db.execute('UPDATE session_custom_items SET mechanics_json=? WHERE id=?',(json.dumps({'weight_kg':1,'container_entry_cm':31}),int(self.path.split(':')[1])))
        with self.assertRaisesRegex(ValueError,'abertura'):self.command('store','oversize',source_path=self.path,quantity=1)

    def test_item_with_zero_carried_quantity_cannot_be_equipped_from_storage(self):
        self.command('open','bag-open')
        self.command('store','all-stored',source_path=self.path,quantity=2)
        response=self.client.post('/characters/vezemir/actions',json={'action':'equip_item','request_id':'stored-equip',
            'payload':{'item_path':self.path,'equipment_slot':'Acessório'}})
        self.assertEqual(response.status_code,400,response.text)
        self.assertFalse(self.row()['equipped'])

    def test_capacity_unknown_dimensions_and_nested_containers_never_silently_pass(self):
        self.command('open','bag-open')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_custom_items SET mechanics_json=? WHERE id=?',(json.dumps({'weight_kg':1001,'container_entry_cm':2}),int(self.path.split(':')[1])))
        with self.assertRaisesRegex(ValueError,'capacidade'):self.command('store','too-heavy',source_path=self.path,quantity=1)
        with self.assertRaisesRegex(ValueError,'recipiente'):self.command('store','nested',source_path=self.bag,quantity=1)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_custom_items SET mechanics_json=? WHERE id=?',(json.dumps({'weight_kg':1}),int(self.path.split(':')[1])))
        with self.assertRaisesRegex(ValueError,'Dimensões'):self.command('store','unknown-size',source_path=self.path,quantity=1)

    def test_chaotic_loss_rolls_once_and_never_returns_the_lost_unit(self):
        from app.player_inventory import upsert_inventory
        self.bag='compendium:item-magico-sacola-magica-caotica'
        upsert_inventory(self.db,profile_id='vezemir',item_path=self.bag,item_title='Sacola caótica',quantity=1,equipped=False,notes=None)
        self.command('open','chaos-open')
        with patch('app.magic_containers.roll_formula',return_value={'total':1}) as rng:
            result=self.command('store','chaos-store',source_path=self.path,quantity=1)
            from app.magic_containers import command
            command(self.db,owner='vezemir',actor='master',role='gm',request_id='chaos-store',payload=result['intent'])
            rng.assert_called_once_with('1d100')
        self.assertEqual(self.row()['quantity'],1)
        self.assertEqual(self.view()['contents'],[])
        self.assertEqual(result['lost'],1)

    def test_unauthorized_owner_and_stale_version_are_rejected(self):
        from app.magic_containers import inspect,command
        with self.assertRaises(PermissionError):inspect(self.db,owner='vezemir',actor='raziel',role='player',item_path=self.bag)
        self.command('open','version-open')
        with self.assertRaisesRegex(ValueError,'mudou'):command(self.db,owner='vezemir',actor='master',role='gm',request_id='stale',payload={'item_path':self.bag,'operation':'close','expected_version':0})

    def test_ledger_failure_rolls_back_both_inventory_and_container(self):
        self.command('open','bag-open')
        with patch('app.magic_containers.append_session_ledger_event',side_effect=RuntimeError('fixture failure')):
            with self.assertRaises(RuntimeError):self.command('store','rollback',source_path=self.path,quantity=1)
        self.assertEqual(self.row()['quantity'],2)
        self.assertEqual(self.view()['contents'],[])

    def test_paralysis_cannot_be_bypassed_by_container_commands(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',('container-paralysis','character','vezemir',json.dumps({'id':'container-paralysis','target_type':'character','target_id':'vezemir','label':'Paralisado','duration':'manual','rounds':None,'modifiers':{},'monster_condition':'paralyzed','blocks_actions':True})))
        with self.assertRaisesRegex(ValueError,'Paralisado'):self.command('open','paralyzed-open')
        self.assertFalse(self.view()['open'])

    def test_portable_hole_requires_packed_dimensions_and_enforces_physical_volume(self):
        from app.player_inventory import upsert_inventory
        self.bag='compendium:item-magico-buraco-portatil'
        upsert_inventory(self.db,profile_id='vezemir',item_path=self.bag,item_title='Buraco Portátil',quantity=1,equipped=False,notes=None)
        self.command('open','hole-open')
        with self.assertRaisesRegex(ValueError,'Volume'):self.command('store','missing-volume',source_path=self.path,quantity=1)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_custom_items SET mechanics_json=? WHERE id=?',(json.dumps({'weight_kg':1,'container_entry_cm':2,'storage_volume_m3':6,'container_packed_length_cm':10}),int(self.path.split(':')[1])))
        with self.assertRaisesRegex(ValueError,'volume'):self.command('store','huge-volume',source_path=self.path,quantity=1)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_custom_items SET mechanics_json=? WHERE id=?',(json.dumps({'weight_kg':1,'container_entry_cm':2,'storage_volume_m3':0.01,'container_packed_length_cm':10}),int(self.path.split(':')[1])))
        self.command('store','valid-volume',source_path=self.path,quantity=1)
        self.assertEqual(self.row()['quantity'],1)
        self.assertTrue(self.view()['creature_occupants_supported'])

    def test_api_uses_native_actions_and_other_players_cannot_read_or_change_contents(self):
        read=self.client.get('/characters/vezemir/container',params={'item_path':self.bag})
        self.assertEqual(read.status_code,200,read.text)
        self.assertEqual(read.headers['cache-control'],'private, no-store')
        response=self.client.post('/characters/vezemir/actions',json={'action':'container','request_id':'container-api-open',
            'payload':{'item_path':self.bag,'operation':'open','expected_version':0}})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(self.view()['open'])
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        self.assertEqual(self.client.get('/characters/vezemir/container',params={'item_path':self.bag}).status_code,403)
        self.assertEqual(self.client.post('/characters/vezemir/actions',json={'action':'container','payload':{'item_path':self.bag,'operation':'close','expected_version':1}}).status_code,403)

    def test_storage_preserves_charge_condition_and_rest_recharges_eligible_contents(self):
        from app.inventory_conditions import init_schema,save_condition
        from app.magic_containers import recharge_contents
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET quantity=1,charges_current=2,charges_max=5,recharge=? WHERE item_path=?',('inn_rest',self.path))
            init_schema(db);save_condition(db,self.row()['id'],{'fixture_condition':'preserved'},'fixture')
        self.command('open','bag-open');self.command('store','charged-store',source_path=self.path,quantity=1)
        self.assertEqual(self.row()['quantity'],0)
        self.assertEqual(self.view()['contents'][0]['charges_current'],2)
        with closing(sqlite3.connect(self.db)) as db,db:recharge_contents(db,'vezemir','rest')
        self.assertEqual(self.view()['contents'][0]['charges_current'],5)
        self.command('take','charged-return',entry_id=self.view()['contents'][0]['id'],quantity=1)
        self.assertEqual(self.row()['charges_current'],5)
        from app.inventory_conditions import read_condition
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(read_condition(db,self.row()['id'])['fixture_condition'],'preserved')

    def test_stored_lifetime_items_do_not_regain_gems_or_absorption_on_rest(self):
        from app.inventory_conditions import save_condition,read_condition
        from app.magic_containers import recharge_contents
        from app.magic_absorption import ID as BROOCH
        from app.magic_passives import RING
        contents=[{'id':key,'item_path':'compendium:'+key,'name':key,'quantity':1,'unit_weight_kg':1,
            'charges_current':1,'charges_max':6,'recharge':'inn_rest'} for key in [RING,BROOCH]]
        with closing(sqlite3.connect(self.db)) as db,db:
            save_condition(db,self.row(self.bag)['id'],{'magic_container':{'open':False,'contents':contents}},'fixture')
            recharge_contents(db,'vezemir','rest')
            state=read_condition(db,self.row(self.bag)['id'])['magic_container']
            self.assertEqual([e['charges_current'] for e in state['contents']],[1,1])

    def test_ambiguous_charged_stack_is_not_trapped_in_a_container(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=2,charges_max=5 WHERE item_path=?',(self.path,))
        self.command('open','bag-open')
        with self.assertRaisesRegex(ValueError,'Individualize'):
            self.command('store','ambiguous-stack',source_path=self.path,quantity=2)
        self.assertEqual(self.row()['quantity'],2)
        self.assertEqual(self.view()['contents'],[])
