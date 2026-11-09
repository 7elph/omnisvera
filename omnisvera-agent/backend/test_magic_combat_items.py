"""Approved combat magic items, on synthetic databases only."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

RAPINA='compendium:item-magico-armadura-leve-da-rapina'
NOW='2026-11-02T12:00:00+00:00'
DRUMS='compendium:item-magico-tambores-do-panico'


class RapinaActivationTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)

    def seed(self,equipped=True,slot='Armadura'):
        from app.player_inventory import upsert_inventory
        return upsert_inventory(self.db,profile_id='vezemir',item_path=RAPINA,
            item_title='Armadura Leve da Rapina',quantity=1,equipped=equipped,
            equipment_slot=slot if equipped else None,notes=None)

    def use(self,key='rapina-use-test'):
        return self.client.post('/characters/vezemir/actions',json={'action':'use_item',
            'payload':{'item_path':RAPINA},'request_id':key})

    def stored(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE item_path=?',(RAPINA,)).fetchone())

    def effects(self):
        from app.combat_effects import readeffects
        return [e for e in readeffects(self.db)['effects'] if e.get('magic_item')==RAPINA.removeprefix('compendium:')]

    def test_contract_is_body_armor_with_seven_defense_and_three_daily_uses(self):
        from app.map_commerce import catalog_inventory
        item=catalog_inventory(RAPINA)
        self.assertEqual(item['item_type'],'armor')
        self.assertEqual(item['mechanics']['equipment_slots'],['Armadura'])
        self.assertEqual(item['mechanics']['charges_max'],3)
        self.assertEqual(sum(r['value'] for r in item['effect_rules'] if r['trigger']=='while_equipped' and r['kind']=='armor_class_bonus'),7)
        self.assertTrue(item['usable'])

    def test_active_item_icons_do_not_depend_on_having_generated_art(self):
        from app.action_cards import active_effect_icons
        common={'duration':'manual','rounds':None,'modifiers':{},'target_type':'character','target_id':'vezemir'}
        effects=[{**common,'id':'rapina-status','label':'Rapina','magic_item':RAPINA.removeprefix('compendium:'),
            'duration':'fictional_time','remaining_seconds':30,'source_duration_unit':'rounds'},
            {**common,'id':'music-status','label':'Tambores · tocando','magic_item':DRUMS.removeprefix('compendium:'),'drum_performance':True},
            {**common,'id':'fear-status','label':'Pânico · Tambores','magic_item':DRUMS.removeprefix('compendium:'),'drum_fear':True}]
        icons=active_effect_icons(effects,lambda _:[],['vezemir'])
        self.assertEqual(len(icons),3)
        self.assertEqual(icons[0]['turns_remaining'],3)
        self.assertEqual(icons[2]['card']['name'],'Pânico · Tambores')

    def test_activation_rolls_once_adds_three_ac_and_retry_does_not_spend_twice(self):
        self.seed()
        with patch('app.magic_item_uses.roll_formula',return_value={'total':3,'individual_results':[3]}) as rng:
            first=self.use();self.assertEqual(first.status_code,200,first.text)
            retry=self.use();self.assertEqual(retry.status_code,200,retry.text)
            rng.assert_called_once_with('1d4')
        effect=self.effects()[0]
        self.assertEqual((effect['duration'],effect['remaining_seconds'],effect['modifiers']),('fictional_time',30,{'armor_class_bonus':3}))
        self.assertEqual(self.stored()['charges_current'],2)
        self.assertEqual(first.json(),retry.json())
        self.assertEqual(self.use('rapina-no-stacking').status_code,400)
        self.assertEqual(self.stored()['charges_current'],2)

    def test_stowed_wrong_slot_and_other_player_cannot_activate(self):
        from app import main
        from app.access import AccessContext
        self.seed(equipped=False)
        self.assertEqual(self.use('rapina-stowed').status_code,400)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET equipped=1,equipment_slot=? WHERE item_path=?',('Acessório',RAPINA))
        self.assertEqual(self.use('rapina-wrong-slot').status_code,400)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        self.assertEqual(self.use('rapina-wrong-owner').status_code,403)
        self.assertIsNone(self.stored()['charges_current'])

    def test_three_activations_exhaust_then_master_rest_clears_and_recharges(self):
        self.seed()
        for i in range(3):
            with closing(sqlite3.connect(self.db)) as db,db:
                db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.magic_item')=?",(RAPINA.removeprefix('compendium:'),))
            r=self.use('rapina-daily-'+str(i));self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.stored()['charges_current'],0)
        self.assertEqual(self.use('rapina-daily-four').status_code,400)
        r=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','payload':{},'request_id':'rapina-master-rest'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.stored()['charges_current'],3)
        self.assertFalse(self.effects())

    def test_unequipping_prunes_boost_and_never_changes_base_sheet(self):
        self.seed()
        with closing(sqlite3.connect(self.db)) as db:
            before=db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]
        self.assertEqual(self.use().status_code,200)
        r=self.client.post('/characters/vezemir/actions',json={'action':'unequip_item','payload':{'item_path':RAPINA},'request_id':'rapina-stow'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertFalse(self.effects())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(before,db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])

    def test_activation_ledger_failure_rolls_back_charge_and_effect(self):
        self.seed()
        with patch('app.combat_consumables.append_session_ledger_event',side_effect=RuntimeError('synthetic failure')):
            with self.assertRaises(RuntimeError):self.use()
        self.assertIsNone(self.stored()['charges_current'])
        self.assertFalse(self.effects())

    def test_duration_uses_native_clock_and_expiration_allows_a_new_activation(self):
        self.seed()
        with patch('app.magic_item_uses.roll_formula',return_value={'total':2,'individual_results':[2]}):
            self.assertEqual(self.use().status_code,200)
        from app.combat_effects import effect_snapshot
        from app.dorn_spells import elapse
        with closing(sqlite3.connect(self.db)) as db,db:
            elapse(db,effect_snapshot(db),10,[],NOW)
        self.assertEqual(self.effects()[0]['remaining_seconds'],10)
        with closing(sqlite3.connect(self.db)) as db,db:
            elapse(db,effect_snapshot(db),10,[],NOW)
        self.assertFalse(self.effects())
        self.assertEqual(self.use('rapina-after-expiration').status_code,200)
        self.assertEqual(self.stored()['charges_current'],1)


class RapinaReflectionTests(unittest.TestCase):
    def _insert_character(self,*args):
        from test_combat import CombatAttackResolutionTests
        return CombatAttackResolutionTests._insert_character(self,*args)

    def setUp(self):
        from test_combat import CombatAttackResolutionTests
        CombatAttackResolutionTests.setUp(self)
        self.addCleanup(CombatAttackResolutionTests.tearDown,self)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.database,profile_id='raziel',item_path=RAPINA,
            item_title='Armadura Leve da Rapina',quantity=1,equipped=True,equipment_slot='Armadura',notes=None)

    def hp(self,owner):
        with closing(sqlite3.connect(self.database)) as db:
            return json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(owner,)).fetchone()[0])['current_hp']

    def resolve(self,key='rapina-native-hit',d20=20):
        from test_combat import CombatAttackResolutionTests,SequenceRng
        return CombatAttackResolutionTests._resolve(self,target={'type':'character','id':'raziel','name':'Raziel','armor_class':18,'current_hp':14},request_id=key,d20=d20,rng=SequenceRng(3,3,3,3))

    def confirm(self,resolution):
        from app.combat import confirm_attack_resolution
        return confirm_attack_resolution(self.database,resolution_id=resolution['resolution_id'],requested_by_id='vezemir',requested_by_role='player')

    def test_confirm_takes_full_damage_reflects_floor_and_retry_is_exactly_once(self):
        resolution=self.resolve();damage=resolution['damage_total'];before=self.hp('vezemir')
        confirmed,changed=self.confirm(resolution)
        self.assertTrue(changed)
        self.assertEqual(self.hp('raziel'),max(0,14-damage))
        self.assertEqual(self.hp('vezemir'),before-damage//2)
        self.assertEqual(confirmed['breakdown']['rapina_reflection']['damage'],damage//2)
        again,changed=self.confirm(resolution)
        self.assertFalse(changed);self.assertEqual(again,confirmed)
        self.assertEqual(self.hp('vezemir'),before-damage//2)

    def test_stowed_armor_never_reflects(self):
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('UPDATE player_inventory SET equipped=0 WHERE item_path=?',(RAPINA,))
        before=self.hp('vezemir');self.confirm(self.resolve())
        self.assertEqual(self.hp('vezemir'),before)

    def test_reflection_can_retire_the_attacker_and_uses_the_same_confirmation_receipt(self):
        with closing(sqlite3.connect(self.database)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state['current_hp']=1
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        r=self.resolve();confirmed,changed=self.confirm(r)
        self.assertTrue(changed);self.assertEqual(self.hp('vezemir'),0)
        self.assertEqual(confirmed['breakdown']['rapina_reflection']['hp']['hp_after'],0)
        with closing(sqlite3.connect(self.database)) as db:
            title=db.execute('SELECT title FROM session_ledger WHERE source_id=?',(r['resolution_id'],)).fetchone()[0]
        self.assertIn('Rapina devolveu',title)

    def test_miss_does_not_reflect(self):
        before=self.hp('vezemir');r=self.resolve('rapina-missed',d20=2)
        self.assertEqual(r['result'],'miss')
        result,_=self.confirm(r)
        self.assertNotIn('rapina_reflection',result['breakdown'])
        self.assertEqual(self.hp('vezemir'),before)

    def test_overkill_uses_incoming_damage_not_clamped_hp_loss(self):
        with closing(sqlite3.connect(self.database)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['current_hp']=1
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        r=self.resolve();before=self.hp('vezemir');self.confirm(r)
        self.assertEqual(self.hp('raziel'),0)
        self.assertEqual(self.hp('vezemir'),before-r['damage_total']//2)

    def test_temporary_hp_still_receives_damage_and_does_not_erase_reflection(self):
        with closing(sqlite3.connect(self.database)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['temporary_hp']=100
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        r=self.resolve();before=self.hp('vezemir');result,_=self.confirm(r)
        self.assertEqual(self.hp('raziel'),14);self.assertEqual(self.hp('vezemir'),before-r['damage_total']//2)
        self.assertEqual(result['breakdown']['rapina_reflection']['damage'],r['damage_total']//2)

    def test_both_wearers_do_not_bounce_reflection_and_ledger_failure_is_atomic(self):
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.database,profile_id='vezemir',item_path=RAPINA,item_title='Rapina',quantity=1,equipped=True,equipment_slot='Armadura',notes=None)
        resolution=self.resolve();before=(self.hp('vezemir'),self.hp('raziel'))
        with patch('app.combat.append_session_ledger_event',side_effect=RuntimeError('synthetic ledger failure')):
            with self.assertRaises(RuntimeError):self.confirm(resolution)
        self.assertEqual((self.hp('vezemir'),self.hp('raziel')),before)
        r,_=self.confirm(resolution)
        self.assertEqual(self.hp('vezemir'),before[0]-r['damage_total']//2)
        self.assertEqual(self.hp('raziel'),max(0,before[1]-r['damage_total']))


class DrumTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path=DRUMS,item_title='Tambores do pânico',quantity=1,equipped=False,notes=None)
        from app.session_workspace import save_workspace_token
        from app.spatial_grid import configure_grid
        self.performer=save_workspace_token(self.db,token_type='character',character_id='vezemir',name='Músico',latitude=25,longitude=25,current_hp=20,maximum_hp=20)['id']
        self.listeners=[]
        for name,x in [('Aliado',6),('Inimigo',8),('Distante',19)]:
            token=save_workspace_token(self.db,token_type='monster',name=name,latitude=25,longitude=x*5,
                current_hp=20,maximum_hp=20,sheet={'saving_throw':14,'movement':'9 m','attributes':{'wisdom':10},'attacks':[{'name':'Espada','bonus':2,'damage':'1d6'}]})
            self.listeners.append(token['id'])
        configure_grid(self.db,actor_id='master',role='gm',request_id='drum-test-grid',map_id='default',config={'cols':20,'rows':20,'cell_size_m':1.5})

    def use(self,key='drums-start-test'):
        return self.client.post('/characters/vezemir/actions',json={'action':'use_item','payload':{'item_path':DRUMS},'request_id':key})

    def effects(self):
        from app.combat_effects import readeffects
        return [e for e in readeffects(self.db)['effects'] if e.get('magic_item')==DRUMS.removeprefix('compendium:')]

    def start(self):
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}):
            r=self.use();self.assertEqual(r.status_code,200,r.text)

    def test_all_nearby_creatures_save_once_and_retry_never_rolls_again(self):
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as dice:
            a=self.use();self.assertEqual(a.status_code,200,a.text)
            b=self.use();self.assertEqual(b.status_code,200,b.text)
            self.assertEqual(dice.call_count,2)
        fear=[e for e in self.effects() if e.get('drum_fear')]
        self.assertEqual({e['target_id'] for e in fear},set(self.listeners[:2]))
        self.assertNotIn('vezemir',{e['target_id'] for e in fear})
        from app.magic_item_drums import sync
        with patch('app.dorn_spells.roll_formula',side_effect=AssertionError('already checked')):
            with closing(sqlite3.connect(self.db)) as db,db:sync(db,NOW)

    def test_playing_and_fear_block_attacks_but_stop_is_free_and_releases_everyone(self):
        self.start()
        from app.monster_conditions import assert_can_act
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaisesRegex(ValueError,'Tambores'):assert_can_act(db,'vezemir')
            with self.assertRaisesRegex(ValueError,'Pânico'):assert_can_act(db,self.listeners[0])
        r=self.use('drums-stop-test');self.assertEqual(r.status_code,200,r.text)
        self.assertFalse(self.effects())
        with closing(sqlite3.connect(self.db)) as db:assert_can_act(db,self.listeners[0])

    def test_each_step_must_increase_distance_and_musician_may_still_move(self):
        self.start()
        from app.magic_item_drums import validate_path
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaisesRegex(ValueError,'afastar'):validate_path(db,'default',self.listeners[0],[[6,5],[5,5]])
            with self.assertRaisesRegex(ValueError,'afastar'):validate_path(db,'default',self.listeners[0],[[6,5],[6,6]])
            validate_path(db,'default',self.listeners[0],[[6,5],[7,5],[8,5]])
            validate_path(db,'default',self.performer,[[5,5],[4,5]])

    def test_native_movement_rejects_approach_and_accounts_allowed_retreat(self):
        self.start()
        from app.spatial_grid import move_entity
        from app.combat_effects import readeffects
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter={'active':True,'map_id':'default','participants':[{'target_type':'token','target_id':self.listeners[1],'initiative':10}],
                'turn_index':0,'turn_sequence':1,'started_at':NOW}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1',(json.dumps(encounter),))
            position=db.execute('SELECT version FROM session_workspace_entity_positions WHERE token_id=?',(self.listeners[1],)).fetchone()[0]
        args={'actor_id':'master','role':'gm','map_id':'default','token_id':self.listeners[1],'mode':'COMBAT_MOVE',
            'expected_position_version':position,'expected_grid_version':1,'expected_combat_version':readeffects(self.db)['version']}
        with self.assertRaisesRegex(ValueError,'afastar'):
            move_entity(self.db,request_id='drums-invalid-approach',cells=[[8,5],[7,5]],**args)
        result=move_entity(self.db,request_id='drums-valid-retreat',cells=[[8,5],[9,5]],**args)
        self.assertEqual(result['movement']['spent_m'],1.5)
        self.assertEqual(move_entity(self.db,request_id='drums-valid-retreat',cells=[[8,5],[9,5]],**args),result)

    def test_stopping_does_not_require_another_consumable_slot(self):
        self.start()
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter={'active':True,'battle_mode':True,'map_id':'default','participants':[{'target_type':'character','target_id':'vezemir'}],
                'turn_index':0,'turn_sequence':1,'started_at':NOW,'consumable_used':True}
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        result=self.use('drums-stop-spent-turn');self.assertEqual(result.status_code,200,result.text)
        self.assertFalse(self.effects())

    def test_dead_musician_stops_and_missing_grid_does_not_consume_or_roll(self):
        self.start()
        from app.combat_effects import change_hp
        with closing(sqlite3.connect(self.db)) as db,db:change_hp(db,'character','vezemir',-100,NOW)
        self.assertFalse(self.effects())
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("DELETE FROM session_workspace_map_grids WHERE map_id='default'")
        with patch('app.dorn_spells.roll_formula',side_effect=AssertionError('no invented distance')):
            r=self.use('drums-no-grid');self.assertEqual(r.status_code,400,r.text)

    def test_dead_musician_cannot_claim_a_new_activation(self):
        from app.combat_effects import change_hp
        with closing(sqlite3.connect(self.db)) as db,db:change_hp(db,'character','vezemir',-100,NOW)
        with patch('app.dorn_spells.roll_formula',side_effect=AssertionError('dead musician cannot roll JP')):
            r=self.use();self.assertEqual(r.status_code,400,r.text)
        self.assertFalse(self.effects())

    def test_resistance_hidden_victim_and_failure_rollback(self):
        from app.session_workspace import update_workspace_token
        update_workspace_token(self.db,token_id=self.listeners[1],visible_to_players=False)
        with patch('app.combat_consumables.append_session_ledger_event',side_effect=RuntimeError('synthetic ledger failure')):
            with self.assertRaises(RuntimeError):self.start()
        self.assertFalse(self.effects())
        self.start()
        with closing(sqlite3.connect(self.db)) as db:
            rows=db.execute("SELECT visibility,detail_json FROM session_ledger WHERE source_type='magic_item_fear'").fetchall()
        hidden=[v for v,raw in rows if self.listeners[1] in raw]
        self.assertEqual(hidden,['gm'])

    def test_successful_save_and_explicit_deafness_prevent_fear(self):
        from app.session_workspace import update_workspace_token
        update_workspace_token(self.db,token_id=self.listeners[0],conditions=['surdo'])
        with patch('app.dorn_spells.roll_formula',return_value={'total':20,'individual_results':[20]}) as dice:
            r=self.use();self.assertEqual(r.status_code,200,r.text);self.assertEqual(dice.call_count,1)
        self.assertFalse([e for e in self.effects() if e.get('drum_fear')])

    def test_new_creature_entering_aura_checks_once_and_cannot_attack(self):
        self.start()
        from app.session_workspace import save_workspace_token,update_workspace_token
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as dice:
            newcomer=save_workspace_token(self.db,token_type='monster',name='Entrante',latitude=25,longitude=30,
                current_hp=10,maximum_hp=10,sheet={'saving_throw':14,'movement':'9 m','attributes':{'wisdom':10},'attacks':[{'name':'Mordida','bonus':2,'damage':'1d6'}]})
            update_workspace_token(self.db,token_id=newcomer['id'],maximum_hp=10)
            self.assertEqual(dice.call_count,1)
        r=self.client.post('/gm/combat/tokens/'+newcomer['id']+'/attacks/resolve',json={
            'request_id':'drums-attack-denied','attack_id':'0','target_type':'character','target_id':'vezemir','roll_mode':'physical','d20':20})
        self.assertEqual(r.status_code,400,r.text);self.assertIn('Pânico',r.text)

    def test_mental_ward_is_consumed_once_before_jp(self):
        from app.player_inventory import upsert_inventory
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) SELECT 'raziel',state_json,1,updated_at FROM character_states WHERE profile_id='vezemir'")
            db.execute("INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) SELECT 'raziel',character_path,'Raziel','approved',data_json,updated_at FROM character_sheets WHERE profile_id='vezemir'")
            db.execute('UPDATE session_workspace_tokens SET character_id=? WHERE id=?',('raziel',self.listeners[0]))
        upsert_inventory(self.db,profile_id='raziel',item_path='compendium:item-magico-anel-da-conviccao',item_title='Anel da convicção',quantity=1,equipped=True,equipment_slot='Acessório',notes=None)
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as dice:
            self.assertEqual(self.use().status_code,200);self.assertEqual(self.use().status_code,200)
            self.assertEqual(dice.call_count,1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE profile_id='raziel'").fetchone()[0],5)
        self.assertNotIn('raziel',{e['target_id'] for e in self.effects() if e.get('drum_fear')})

    def test_owner_cannot_leak_hidden_listener_through_effects_or_ledger(self):
        from app.session_workspace import update_workspace_token
        from app import main
        from app.access import AccessContext
        update_workspace_token(self.db,token_id=self.listeners[1],visible_to_players=False)
        self.start()
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')
        r=self.client.get('/combat/effects');self.assertEqual(r.status_code,200,r.text)
        self.assertNotIn(self.listeners[1],r.text)
        r=self.client.get('/workspace/ledger');self.assertEqual(r.status_code,200,r.text)
        self.assertNotIn(self.listeners[1],r.text)

    def test_owner_sees_restrictions_for_their_visible_summon(self):
        from app import main
        from app.access import AccessContext
        with closing(sqlite3.connect(self.db)) as db,db:
            row=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.listeners[0],)).fetchone()
            sheet=json.loads(row[0]);sheet['summon']={'caster':'vezemir'}
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),self.listeners[0]))
        self.start()
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')
        r=self.client.get('/combat/effects');self.assertEqual(r.status_code,200,r.text)
        self.assertTrue(any(e.get('drum_fear') and e['target_id']==self.listeners[0] for e in r.json()['effects']))
