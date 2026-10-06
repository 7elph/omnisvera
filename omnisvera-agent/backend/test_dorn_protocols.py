import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat import resolve_attack, confirm_attack_resolution
from app.combat_effects import effect_command, readeffects, apply_definition_effects
from app.dorn_mage import apply_dorn_mage
from app.character_play import load_session_abilities
import test_dorn_mage as fixture
from app.session_ledger import init_session_ledger
from app.dice_rolls import init_dice_rolls


class DornProtocolTests(unittest.TestCase):
    def setUp(self):
        self.base = fixture.DornMageTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.db = self.base.db
        apply_dorn_mage(self.db)
        init_dice_rolls(self.db)
        init_session_ledger(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            db.execute("INSERT INTO character_states VALUES('ally',?,1,'now')", (json.dumps(state),))
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('arena','Arena fixture','fixture.png',1,'now','now')")
            db.execute("INSERT OR IGNORE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES (1,'default','Exploração','fixture.png','now')")
        self.counter = 0

    def command(self, action, **payload):
        self.counter += 1
        return effect_command(self.db, actor_id='master', actor_role='gm', request_id=f'dorn-protocol-{self.counter}', expected_version=readeffects(self.db)['version'], action=action, payload=payload)

    def start(self, battle_mode=False):
        return self.command('start', map_id='arena', participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20}, {'target_type':'character','target_id':'ally','name':'Aliado','initiative':10}], battle_mode=battle_mode)

    def guard(self):
        return self.command('dorn_guard', ally_id='ally', position_confirmed=True)

    def test_guard_action_idempotency_and_no_second_activation(self):
        self.start()
        version = readeffects(self.db)['version']
        options = dict(actor_id='master',actor_role='gm',request_id='guard-replay-001',expected_version=version,action='dorn_guard',payload={'ally_id':'ally','position_confirmed':True})
        result = effect_command(self.db, **options)
        self.assertEqual(result, effect_command(self.db, **options))
        self.assertTrue(result['encounter']['action_committed'])
        self.assertEqual(result['effects'][0]['modifiers'], {})
        with self.assertRaises(ValueError): self.guard()

    def test_guard_exhausts_real_battle_budget(self):
        self.start(battle_mode=True); self.guard()
        with self.assertRaisesRegex(ValueError, 'turno já foi confirmada'):
            resolve_attack(self.db,request_id='dorn-after-guard',actor_character_id='dorn7',actor_name='Dorn',requested_by_id='master',requested_by_role='gm',definition={'attacks':[{'id':'claw','name':'Teste','damage':'1d4','attack_bonus':2,'weapon_item_path':'natural:claw'}]},inventory=[],attack_id='claw',target={'type':'character','id':'ally','armor_class':11,'current_hp':13},roll_mode='physical',physical_d20=20)

    def test_guard_expires_on_dorn_turn_not_round(self):
        self.start(); self.guard()
        self.assertTrue(self.command('next_turn')['effects'])
        self.assertFalse(self.command('next_turn')['effects'])

    def test_guard_requires_live_other_ally_position_and_turn(self):
        self.start()
        for payload in ({'ally_id':'dorn7','position_confirmed':True}, {'ally_id':'ally'}, {'ally_id':'missing','position_confirmed':True}):
            with self.assertRaises(ValueError): self.command('dorn_guard', **payload)
        self.command('next_turn')
        with self.assertRaises(ValueError): self.guard()

    def attack(self, request='dorn-interpose-001', guard='dorn:guard', target='dorn7'):
        return resolve_attack(self.db, request_id=request, actor_character_id='ally',actor_name='Inimigo fixture',requested_by_id='master',requested_by_role='gm',definition={'name':'Inimigo','attacks':[{'id':'claw','name':'Ataque','attack_bonus':2,'damage':'1d4','weapon_item_path':'natural:claw'}]},inventory=[],attack_id='claw',target={'type':'character','id':target,'name':target,'armor_class':11,'current_hp':13},roll_mode='physical',physical_d20=20,guard_effect_id=guard,rng=lambda a,b:2)

    def test_interposition_consumed_with_preview_receives_damage_and_replays(self):
        self.start(); self.guard(); self.command('next_turn')
        record, created = self.attack()
        self.assertTrue(created)
        self.assertEqual(record['target_id'], 'dorn7')
        self.assertEqual(record['target_ac'], 11)
        self.assertFalse(readeffects(self.db)['effects'])
        self.assertEqual(self.attack()[0], record)
        result, _ = confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id='master',requested_by_role='gm')
        self.assertEqual(result['hp_after'], 11)
        with self.assertRaises(ValueError): self.attack('second-interposition')
        ordinary, _ = self.attack('ordinary-attack', guard=None, target='ally')
        self.assertEqual(ordinary['target_id'], 'ally')

    def test_failed_attack_validation_does_not_consume_guard(self):
        self.start(); self.guard(); self.command('next_turn')
        with self.assertRaises(ValueError): self.attack(target='ally')
        self.assertTrue(readeffects(self.db)['effects'])

    def test_http_redirect_uses_dorn_defenses_and_player_denied(self):
        self.start(); self.guard(); self.command('next_turn')
        request = main.AttackResolutionCreate(request_id='http-guard-001',attack_id='melee',target_type='character',target_id='ally',roll_mode='digital',guard_effect_id='dorn:guard')
        with patch.object(main,'settings',replace(main.settings,database_path=self.db)), patch.object(main,'_combat_target', side_effect=lambda kind,key: {'type':kind,'id':key,'name':key,'armor_class':11 if key=='dorn7' else 17,'current_hp':13}):
            self.assertEqual(main._guard_attack_target(request,AccessContext(mode='gm'))['armor_class'],11)
            with self.assertRaises(PermissionError): main._guard_attack_target(request,AccessContext(mode='player',profile_id='ally'))
        with patch.object(main,'settings',replace(main.settings,database_path=self.db,master_token='fixture-master',player_token='fixture-player')):
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player',profile_id='ally')
            try:
                client = TestClient(main.app)
                self.addCleanup(client.close)
                response = client.post('/gm/combat/effects',headers={'X-Omnisvera-Token':'fixture-player'},json={'request_id':'player-guard-001','expected_version':readeffects(self.db)['version'],'action':'dorn_guard','payload':{'ally_id':'ally','position_confirmed':True}})
                self.assertEqual(response.status_code,401)  # Existing require_master contract.
            finally: main.app.dependency_overrides.clear()

    def test_player_cannot_bypass_protocol_authorization(self):
        for action in ('dorn_guard','dorn_vanguard','dorn_diagnose'):
            with self.assertRaises(PermissionError): effect_command(self.db,actor_id='ally',actor_role='player',allow_player=True,request_id='denied-protocol',expected_version=0,action=action,payload={})

    def test_monster_http_interposition_confirmation_and_replay(self):
        enemy = fixture.save_workspace_token(self.db,token_type='monster',name='Inimigo fixture',latitude=30,longitude=30,current_hp=20,maximum_hp=20,sheet={'armor_class':12,'attacks':[{'name':'Garra','damage':'1d4','bonus':2}]})
        self.start(); self.guard(); self.command('next_turn')
        payload = {'request_id':'monster-interpose-http','attack_id':'0','target_type':'character','target_id':'ally','roll_mode':'physical','d20':20,'guard_effect_id':'dorn:guard'}
        with patch.object(main,'settings',replace(main.settings,database_path=self.db)), patch.object(main,'_combat_target',side_effect=lambda kind,key: {'type':kind,'id':key,'name':key,'armor_class':11 if key=='dorn7' else 17,'current_hp':13}):
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='gm')
            client = TestClient(main.app)
            try:
                url = f"/gm/combat/tokens/{enemy['id']}/attacks/resolve"
                response = client.post(url,json=payload)
                self.assertEqual(response.status_code,200,response.text)
                record = response.json()
                self.assertEqual(record['target_id'],'dorn7'); self.assertEqual(record['target_ac'],11)
                self.assertEqual(client.post(url,json=payload).json(),record)
                confirmed, _ = confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id=record['requested_by_id'],requested_by_role='gm')
                self.assertLess(confirmed['hp_after'],13)
                payload['request_id'] = 'second-http-interpose'
                self.assertEqual(client.post(url,json=payload).status_code,400)
            finally:
                client.close(); main.app.dependency_overrides.clear()

    def test_vanguard_toggle_persistence_scene_expiry_and_no_buffs(self):
        before = {'attributes':{'strength':14},'defenses':{'armor_class':11},'attacks':[{'id':'melee','damage':'1d6+2','attack_bonus':2}]}
        self.command('dorn_vanguard', enabled=True)
        state = readeffects(self.db)
        effect = state['effects'][0]
        self.assertEqual(effect['protocol'], 'vanguard')
        self.assertEqual(effect['modifiers'], {})
        after = apply_definition_effects(before,state['effects'])
        self.assertEqual(after['attributes'],before['attributes']); self.assertEqual(after['defenses'],before['defenses']); self.assertEqual(after['attacks'][0]['damage'],before['attacks'][0]['damage'])
        self.assertNotIn('traps', state)
        self.assertFalse(self.command('dorn_vanguard', enabled=False)['effects'])
        self.command('dorn_vanguard', enabled=True)
        self.assertFalse(self.command('scene')['effects'])

    def test_vanguard_is_exploration_only(self):
        self.start()
        with self.assertRaises(ValueError): self.command('dorn_vanguard',enabled=True)

    def test_diagnosis_uses_int_and_never_produces_lore(self):
        for rolled,outcome in ((18,'success'),(4,'inconclusive')):
            with patch('app.dorn_protocols.roll_formula',return_value={'total':rolled,'individual_results':[rolled-2]}) as dice:
                result = self.command('dorn_diagnose',subject='Núcleo',difficulty=12,_definition={'name':'Dorn','attributes':{'intelligence':16},'attribute_modifiers':{'intelligence':2}})['protocol_result']
            dice.assert_called_once_with('1d20+2')
            self.assertEqual(result['outcome'],outcome)
            self.assertIsNone(result['information'])

    def test_diagnosis_consumes_combat_action(self):
        self.start()
        args = dict(subject='Máquina',difficulty=12,_definition={'attributes':{'intelligence':16},'attribute_modifiers':{'intelligence':2}})
        self.assertTrue(self.command('dorn_diagnose',**args)['encounter']['action_committed'])
        with self.assertRaises(ValueError): self.command('dorn_diagnose',**args)

    def test_guard_end_cleanup_and_catalog_has_only_approved_protocols(self):
        self.start(); self.guard()
        self.assertFalse(self.command('end')['effects'])
        self.assertEqual([p['id'] for p in load_session_abilities('dorn7', approved_build=fixture.SPEC['version'])],['dorn_guard','dorn_vanguard','dorn_diagnose'])
