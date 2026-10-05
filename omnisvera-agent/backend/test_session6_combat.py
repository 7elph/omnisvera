import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat import confirm_attack_resolution, resolve_attack, bone_dagger_definition
from app.combat_effects import readeffects
from app.session_workspace import save_workspace_token, get_workspace_snapshot
from app.summons import create_summon
from test_battle_mode import BattleModeTests
import test_combat as fixture


class Session6CombatTests(unittest.TestCase):
    def setUp(self):
        self.base = BattleModeTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.db = self.base.db
        self.spec = {'name': 'Esqueleto', 'hp': 5, 'ac': 13, 'marker': 'S', 'attack_name': 'Arma',
            'attack_bonus': 2, 'damage': '1d6', 'resource_key': 'levantar_um_esqueleto', 'duration': 'week', 'note': 'Mesa'}
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES('morthak',?,1,'now')", (json.dumps({'current_hp': 8, 'maximum_hp': 8, 'resources': [
                {'key': 'levantar_um_esqueleto', 'current': 1, 'maximum': 1}, {'key': 'animar_mortos', 'current': 1, 'maximum': 1}]}),))

    def summon(self, **kwargs):
        options = dict(caster='morthak', technique='levantar-esqueleto', spec=self.spec, request_id='summon-session6-001', actor_id='morthak', actor_role='player')
        options.update(kwargs)
        return create_summon(self.db, **options)

    def start_morthak(self):
        self.base.command('start', map_id='arena', battle_mode=True, participants=[
            {'target_type': 'character', 'target_id': 'morthak', 'name': 'Morthak', 'initiative': 20},
            {'target_type': 'token', 'target_id': self.base.enemy['id'], 'name': 'Aranha', 'initiative': 10}])

    def test_two_attacks_different_targets_exactly_once_and_turn_limit(self):
        self.base.start()
        definition = self.base.base.definition
        definition['attacks'][0]['attack_count'] = 2
        second = save_workspace_token(self.db, token_type='monster', name='Outro', latitude=40, longitude=50, current_hp=18, maximum_hp=18, sheet={'armor_class': 10}, map_id='arena')
        members = readeffects(self.db)['encounter']['participants']
        self.base.command('initiative', participants=members + [{'target_type':'token','target_id':second['id'],'name':'Outro','initiative':0}])
        def hit(target, request):
            return resolve_attack(self.db, request_id=request, actor_character_id='vezemir', actor_name='Vezemir', requested_by_id='vezemir', requested_by_role='player', definition=definition, inventory=self.base.base.inventory, attack_id='melee', target={'type':'token','id':target['id'],'name':target['name'],'armor_class':10,'current_hp':18}, roll_mode='physical', physical_d20=15, rng=fixture.SequenceRng(3))[0]
        first = hit(self.base.enemy, 'first-session6')
        for _ in range(2):
            confirm_attack_resolution(self.db, resolution_id=first['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        self.assertEqual(1, readeffects(self.db)['encounter']['attacks_used'])
        self.assertFalse(readeffects(self.db)['encounter']['action_committed'])
        other = hit(second, 'second-session6')
        confirm_attack_resolution(self.db, resolution_id=other['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        with self.assertRaises(ValueError): hit(second, 'third-session6')

    def test_summon_visible_current_map_replay_independent_hp_and_persists(self):
        self.start_morthak()
        first = self.summon()
        self.assertEqual(first, self.summon())
        token = next(t for t in get_workspace_snapshot(self.db, is_gm=False)['tokens'] if t['id'] == first['token']['id'])
        self.assertEqual('arena', token['map_id'])
        self.assertIsNone(token['character_id'])
        self.assertEqual('morthak', token['sheet']['summon']['caster'])
        self.assertEqual(first['token']['id'], readeffects(self.db)['encounter']['participants'][1]['target_id'])
        self.base.command('next_turn')
        with patch.object(main, 'settings', replace(main.settings, database_path=self.db)):
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='vezemir')
            try:
                with TestClient(main.app) as client:
                    reply = client.post(f"/gm/combat/tokens/{token['id']}/attacks/resolve", json={'request_id':'unauthorized-summon','attack_id':'0','target_type':'token','target_id':self.base.enemy['id'],'roll_mode':'digital'})
                    self.assertEqual(403, reply.status_code)
            finally: main.app.dependency_overrides.clear()
        self.base.command('end')
        restored = next(t for t in get_workspace_snapshot(self.db, is_gm=False)['tokens'] if t['id'] == token['id'])
        self.assertEqual(5, restored['current_hp'])

    def test_invalid_corpse_does_not_spend_and_valid_corpse_only_once(self):
        spec = {**self.spec, 'resource_key': 'animar_mortos'}
        corpse = save_workspace_token(self.db, token_type='monster', name='Lobo', latitude=30, longitude=40, current_hp=0, maximum_hp=8, sheet={'armor_class': 13, 'reanimation_allowed': True})
        with self.assertRaises(ValueError): self.summon(technique='animar-mortos', spec=spec, corpse_id=self.base.enemy['id'])
        first = self.summon(technique='animar-mortos', spec=spec, corpse_id=corpse['id'])
        self.assertEqual('Lobo reanimado', first['token']['name'])
        with self.assertRaises(ValueError): self.summon(technique='animar-mortos', spec=spec, corpse_id=corpse['id'], request_id='another-summon')

    def test_character_pin_bound_to_arena_not_other_map(self):
        save_workspace_token(self.db, token_type='character', character_id='vezemir', name='Velho', latitude=1, longitude=1)
        canonical = save_workspace_token(self.db, token_type='character', character_id='vezemir', name='Atual', latitude=20, longitude=20, map_id='arena')
        self.base.start()
        self.assertEqual(canonical['id'], readeffects(self.db)['encounter']['participants'][0]['token_id'])

    def test_catalog_skeleton_id_calls_real_summon(self):
        with patch.object(main, 'settings', replace(main.settings, database_path=self.db)):
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
            try:
                with TestClient(main.app) as client:
                    reply = client.post('/characters/morthak/techniques/levantar-um-esqueleto', json={'request_id':'catalog-summon-001'})
                    self.assertEqual(200, reply.status_code, reply.text)
                    self.assertEqual('default', reply.json()['token']['map_id'])
            finally: main.app.dependency_overrides.clear()

    def test_bone_dagger_has_campaign_damage_without_equipped_weapon(self):
        definition = {'id': 'morthak', 'name': 'Morthak', 'level': 2,
            'session_abilities': [{'id': 'adaga-de-osso'}],
            'attacks': [{'id': 'ranged', 'attack_bonus': 3, 'damage': None, 'weapon_item_path': None}]}
        attack = bone_dagger_definition(definition)
        result, _ = resolve_attack(self.db, request_id='bone-dagger', actor_character_id='morthak', actor_name='Morthak',
            requested_by_id='morthak', requested_by_role='player', definition=attack, inventory=[], attack_id='adaga-de-osso',
            target={'type': 'token', 'id': self.base.enemy['id'], 'name': 'Aranha', 'armor_class': 10, 'current_hp': 18},
            roll_mode='physical', physical_d20=15, rng=fixture.SequenceRng(4))
        self.assertEqual((3, '1d4', 4), (result['attack_bonus'], result['damage_formula'], result['damage_total']))
        confirmed, applied = confirm_attack_resolution(self.db, resolution_id=result['resolution_id'], requested_by_id='morthak', requested_by_role='player')
        self.assertTrue(applied)
        self.assertEqual(14, confirmed['hp_after'])
        with self.assertRaises(ValueError): bone_dagger_definition({**definition, 'id': 'vezemir'})

    def test_summon_owner_can_attack_and_pass_its_turn(self):
        self.start_morthak()
        token = self.summon()['token']
        self.base.command('next_turn')
        with patch.object(main, 'settings', replace(main.settings, database_path=self.db)):
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
            try:
                with TestClient(main.app) as client:
                    reply = client.post(f"/gm/combat/tokens/{token['id']}/attacks/resolve", json={'request_id': 'owned-summon-attack', 'attack_id': '0', 'target_type': 'token', 'target_id': self.base.enemy['id'], 'roll_mode': 'digital'})
                    self.assertEqual(200, reply.status_code, reply.text)
                    resolution = reply.json()
                    confirm_attack_resolution(self.db, resolution_id=resolution['resolution_id'], requested_by_id='morthak', requested_by_role='player')
                    body = {'request_id': 'owned-summon-next', 'expected_version': readeffects(self.db)['version'], 'action': 'next_turn'}
                    reply = client.post('/combat/next-turn', json=body)
                    self.assertEqual(200, reply.status_code, reply.text)
                    self.assertEqual(reply.json(), client.post('/combat/next-turn', json=body).json())
                    self.assertEqual(self.base.enemy['id'], readeffects(self.db)['encounter']['participants'][readeffects(self.db)['encounter']['turn_index']]['target_id'])
            finally: main.app.dependency_overrides.clear()
