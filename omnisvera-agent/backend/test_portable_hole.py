"""Approved voluntary entry and fictional air deadline, temporary fixtures only."""
import json
import sqlite3
import unittest
from unittest.mock import patch
from contextlib import closing

HOLE='compendium:item-magico-buraco-portatil'
MEDAL='compendium:item-magico-medalhao-de-adaptacao'
NOW='2026-11-03T16:00:00+00:00'


class PortableHoleTests(unittest.TestCase):
    def setUp(self):
        from test_magic_combat_items import DrumTests
        DrumTests.setUp(self)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=HOLE,item_title='Buraco portátil',quantity=1,equipped=False,notes=None)
        self.owner='vezemir'

    def view(self):
        from app.magic_containers import inspect
        return inspect(self.db,owner=self.owner,actor='master',role='gm',item_path=HOLE)

    def container(self,operation,key):
        from app.magic_containers import command
        return command(self.db,owner=self.owner,actor='master',role='gm',request_id=key,
            payload={'item_path':HOLE,'operation':operation,'expected_version':self.view()['version']})

    def interact(self,operation='enter',key='hole-enter',actor='vezemir',role='player',token=None):
        from app.portable_hole import command,portal_view
        portal=self.view()['portal_id']
        view=portal_view(self.db,portal_id=portal,actor=actor,role=role,token_id=token or self.performer)
        return command(self.db,portal_id=portal,actor=actor,role=role,request_id=key,
            payload={'operation':operation,'token_id':token or self.performer,'expected_version':view['version'],
                'expected_combat_version':view['combat_version']},load_movement=lambda _:9)

    def elapse(self,seconds):
        from app.combat_effects import effect_snapshot
        from app.dorn_spells import elapse
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            elapse(db,effect_snapshot(db),seconds,[],NOW)

    def hp(self):
        with closing(sqlite3.connect(self.db)) as db:
            return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])['current_hp']

    def test_entry_exit_persist_retry_and_do_not_spend_an_attack(self):
        self.container('open','hole-open')
        result=self.interact()
        self.assertEqual(len(self.view()['occupants']),1)
        from app.portable_hole import command
        replay=command(self.db,portal_id=self.view()['portal_id'],actor='vezemir',role='player',request_id='hole-enter',payload=result['intent'],load_movement=lambda _:9)
        self.assertEqual(result,replay)
        self.interact('exit','hole-exit')
        self.assertEqual(self.view()['occupants'],[])

    def test_no_forced_capture_no_remote_entry_and_closed_hole_blocks_exit(self):
        self.container('open','hole-open')
        with self.assertRaises(PermissionError):self.interact(token=self.listeners[0])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=19,cell_y=19 WHERE token_id=?',(self.performer,))
        with self.assertRaisesRegex(ValueError,'adjacente'):self.interact()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=5,cell_y=5 WHERE token_id=?',(self.performer,))
        self.interact()
        self.container('close','hole-close')
        with self.assertRaisesRegex(ValueError,'fechado'):self.interact('exit','closed-exit')

    def test_close_kills_only_at_sixty_fictional_seconds_and_opening_cancels(self):
        self.container('open','hole-open');self.interact();before=self.hp()
        self.container('close','hole-close')
        self.elapse(59);self.assertEqual(self.hp(),before)
        self.container('open','hole-reopen');self.elapse(10);self.assertEqual(self.hp(),before)
        self.container('close','hole-close-again');self.elapse(60)
        self.assertLessEqual(self.hp(),0)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='environment_asphyxia'").fetchone()[0],1)
        self.elapse(60)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='environment_asphyxia'").fetchone()[0],1)

    def test_medallion_protects_only_equipped_and_does_not_create_air(self):
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=MEDAL,item_title='Medalhão',quantity=1,equipped=True,equipment_slot='Acessório',notes=None)
        self.container('open','hole-open');self.interact();before=self.hp()
        self.container('close','hole-close');self.elapse(60)
        self.assertEqual(self.hp(),before)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(MEDAL,))
        self.elapse(1);self.assertLessEqual(self.hp(),0)

    def test_repeated_close_does_not_replenish_air_and_rest_does_not_end_exposure(self):
        self.container('open','hole-open');self.interact();self.container('close','hole-close')
        self.elapse(59);self.container('close','still-closed')
        from app.combat_effects import expire_rest_effects
        with closing(sqlite3.connect(self.db)) as db,db:expire_rest_effects(db,'vezemir',complete=True)
        self.elapse(1);self.assertLessEqual(self.hp(),0)

    def test_asphyxia_reaches_native_death_limit_even_under_frenzy_at_zero_hp(self):
        self.container('open','hole-open');self.interact();self.container('close','hole-close')
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state['current_hp']=0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            effect={'id':'fixture-frenzy','skill':'frenesi','defy_death':True,'target_type':'character','target_id':'vezemir',
                'duration':'manual','label':'Frenesi','modifiers':{},'rounds':None}
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character','vezemir',json.dumps(effect)))
        self.elapse(60);self.assertLessEqual(self.hp(),-10)

    def test_native_no_breath_traits_are_protected_not_guessed_from_names(self):
        from app.environment_breathing import protection
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            self.assertIsNone(protection(db,'token',self.listeners[0]))
            self.assertIsNone(protection(db,'character','vezemir'))

    def test_combat_uses_same_movement_budget_and_preserves_attack_and_consumable(self):
        self.container('open','hole-open')
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter={'active':True,'battle_mode':True,'map_id':'default','started_at':'fixture','turn_sequence':1,
                'turn_index':0,'participants':[{'target_type':'character','target_id':'vezemir','active':True}],
                'attacks_used':0,'consumable_used':False}
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        self.interact()
        self.interact('exit','combat-exit')
        with closing(sqlite3.connect(self.db)) as db:
            enc=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0])
        self.assertEqual(enc['movement']['spent_m'],6)
        self.assertEqual(enc['attacks_used'],0);self.assertFalse(enc['consumable_used'])
        self.interact(key='enter-spend-nine')
        with self.assertRaisesRegex(ValueError,'Movimento'):self.interact('exit','exit-above-nine')
        self.assertEqual(len(self.view()['occupants']),1)

    def test_containment_blocks_external_actions_hides_pin_and_survives_rest(self):
        self.container('open','hole-open');self.interact()
        from app.monster_conditions import assert_can_act
        from app.combat_effects import expire_rest_effects
        from app.portable_hole import contained
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            with self.assertRaisesRegex(ValueError,'Buraco'):assert_can_act(db,'vezemir',movement=True)
            expire_rest_effects(db,'vezemir',complete=True)
            self.assertIsNotNone(contained(db,'character','vezemir'))
        from app.session_workspace import get_workspace_snapshot
        self.assertNotIn(self.performer,[t['id'] for t in get_workspace_snapshot(self.db,is_gm=True)['tokens']])

    def test_portal_api_has_no_holder_inventory_and_rejects_foreign_actor(self):
        self.container('open','hole-open')
        portal=self.view()['portal_id']
        r=self.client.get('/workspace/portals/'+portal,params={'character_id':'vezemir'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(set(r.json()),{'portal_id','token_id','version','combat_version','open','inside','movement_cost_m'})
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        r=self.client.get('/workspace/portals/'+portal,params={'character_id':'vezemir'})
        self.assertEqual(r.status_code,403,r.text)

    def test_occupied_container_cannot_be_transferred(self):
        self.container('open','hole-open');self.interact()
        from app.item_transfer import grant_item
        from app.inventory_conditions import read_condition
        from app.item_registry import registry,resolve_item
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT id FROM player_inventory WHERE item_path=?',(HOLE,)).fetchone()
            item=resolve_item(registry(db),HOLE)
            with self.assertRaisesRegex(ValueError,'ocupantes'):
                grant_item(db,item,'raziel',1,NOW,origin='fixture',instance={'inventory_condition':read_condition(db,row['id'])})

    def test_occupied_container_or_pin_cannot_be_removed_or_duplicated(self):
        self.container('open','hole-open');self.interact()
        from app.player_inventory import upsert_inventory
        from app.session_workspace import delete_workspace_token
        for quantity in (0,2):
            with self.assertRaisesRegex(ValueError,'ocupantes'):
                upsert_inventory(self.db,profile_id='vezemir',item_path=HOLE,item_title='Buraco',quantity=quantity,equipped=False,notes=None)
        with self.assertRaises(ValueError):delete_workspace_token(self.db,self.performer)
        with self.assertRaises(ValueError):delete_workspace_token(self.db,self.view()['portal_id'])

    def test_ledger_failure_rolls_back_entry_and_native_budget(self):
        self.container('open','hole-open')
        with patch('app.session_ledger.append_session_ledger_event',side_effect=RuntimeError('fixture fault')):
            with self.assertRaises(RuntimeError):self.interact()
        self.assertEqual(self.view()['occupants'],[])

    def test_gm_can_recover_dead_occupant_after_opening_outside_combat(self):
        self.container('open','hole-open');self.interact();self.container('close','hole-close');self.elapse(60)
        self.container('open','hole-reopen')
        self.interact('extract','gm-recover-body',actor='master',role='gm')
        self.assertEqual(self.view()['occupants'],[])
        self.assertLessEqual(self.hp(),0)

    def test_reopening_on_another_map_exits_without_losing_saved_positions(self):
        from app.session_workspace import set_workspace_map,save_workspace_token,set_active_workspace_map
        from app.spatial_grid import configure_grid
        self.container('open','hole-open')
        # The owner remains outside; a voluntary NPC enters under GM control.
        token=self.listeners[0]
        self.interact(token=token,actor='master',role='gm')
        self.container('close','hole-close')
        other=set_workspace_map(self.db,title='Outra fixture',image_path='fixture.png',visible_to_players=True)
        set_active_workspace_map(self.db,other['id'])
        configure_grid(self.db,actor_id='master',role='gm',request_id='other-hole-grid',map_id=other['id'],config={'cols':20,'rows':20,'cell_size_m':1})
        save_workspace_token(self.db,token_type='character',character_id='vezemir',map_id=other['id'],name='Vezemir',latitude=27.5,longitude=27.5)
        self.container('open','hole-on-other-map')
        self.interact('exit','npc-exit-other-map',actor='master',role='gm',token=token)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?',(token,)).fetchone()[0],other['id'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM session_workspace_entity_positions WHERE token_id=?',(token,)).fetchone()[0],2)

    def test_legacy_summon_uses_same_grid_profile_for_movement_and_respiration(self):
        token=self.listeners[0]
        self.container('open','hole-open')
        with closing(sqlite3.connect(self.db)) as db,db:
            sheet={'summon':{'caster':'morthak','technique':'levantar-um-esqueleto'}}
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),token))
            encounter={'active':True,'battle_mode':True,'map_id':'default','started_at':'fixture','turn_sequence':1,'turn_index':0,
                'participants':[{'target_type':'token','target_id':token,'active':True}],'attacks_used':0}
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        result=self.interact(actor='morthak',token=token)
        self.assertEqual(result['movement']['spent_m'],3)
        self.assertEqual(result['movement']['budget_m'],9)
        self.container('close','close-with-skeleton');self.elapse(60)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(token,)).fetchone()[0],20)

    def test_player_cannot_enter_through_saved_pins_on_an_inactive_map(self):
        from app.session_workspace import set_workspace_map,set_active_workspace_map
        self.container('open','hole-open')
        other=set_workspace_map(self.db,title='Cena diferente',image_path='fixture.png',visible_to_players=True)
        set_active_workspace_map(self.db,other['id'])
        with self.assertRaisesRegex(ValueError,'mapa atual'):self.interact()
