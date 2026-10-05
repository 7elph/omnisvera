import sqlite3
import unittest
from contextlib import closing
from app.combat_effects import effect_command, readeffects
from app.combat import resolve_attack, confirm_attack_resolution
from app.session_workspace import save_workspace_token, get_workspace_snapshot
import test_combat as fixture


class BattleModeTests(unittest.TestCase):
    def setUp(self):
        self.base = fixture.CombatAttackResolutionTests()
        self.base.setUp()
        self.addCleanup(self.base.tearDown)
        self.db = self.base.database
        self.enemy = save_workspace_token(self.db, token_type='monster', name='Aranha', latitude=35, longitude=60, current_hp=18, maximum_hp=18, sheet={'armor_class': 10})
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('arena','Arena','fixture.png',1,'now','now')")
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('default','Exploração','fixture.png',1,'now','now')")
            db.execute("INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES (1,'default','Exploração','fixture.png','now')")
        self.initial = get_workspace_snapshot(self.db, is_gm=True)

    def command(self, action, **payload):
        state = readeffects(self.db)
        return effect_command(self.db, actor_id='master', actor_role='gm', request_id=f'battle-{state["version"]}', expected_version=state['version'], action=action, payload=payload)

    def start(self):
        return self.command('start', map_id='arena', battle_mode=True, participants=[
            {'target_type': 'character', 'target_id': 'vezemir', 'name': 'Vezemir', 'initiative': 20},
            {'target_type': 'token', 'target_id': self.enemy['id'], 'name': 'Aranha', 'initiative': 10}])

    def attack(self, request_id='battle-attack'):
        return resolve_attack(self.db, request_id=request_id, actor_character_id='vezemir', actor_name='Vezemir', requested_by_id='vezemir', requested_by_role='player', definition=self.base.definition, inventory=self.base.inventory, attack_id='melee', target={'type': 'token', 'id': self.enemy['id'], 'name': 'Aranha', 'armor_class': 10, 'current_hp': 18}, roll_mode='physical', physical_d20=15, rng=fixture.SequenceRng(3))[0]

    def test_transition_turn_replay_and_restore_without_healing(self):
        self.start()
        during = get_workspace_snapshot(self.db, is_gm=True)
        self.assertEqual(during['map']['id'], 'arena')
        self.assertEqual(len(during['tokens']), 2)
        resolution = self.attack()
        for _ in range(2):
            confirm_attack_resolution(self.db, resolution_id=resolution['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        with self.assertRaises(ValueError):
            self.attack('second-action')
        self.command('next_turn')
        with self.assertRaises(ValueError):
            self.attack('wrong-turn')
        self.command('end')
        restored = get_workspace_snapshot(self.db, is_gm=True)
        self.assertEqual(restored['map']['id'], self.initial['map']['id'])
        enemy = next(t for t in restored['tokens'] if t['id'] == self.enemy['id'])
        self.assertEqual((enemy['latitude'], enemy['longitude']), (35, 60))
        self.assertLess(enemy['current_hp'], 18)
        self.assertFalse(any(t['id'].startswith('battle:') for t in restored['tokens']))

    def test_private_arena_rejected_without_moving_tokens(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_maps SET visible_to_players=0 WHERE id='arena'")
        with self.assertRaises(ValueError):
            self.start()
        self.assertFalse(readeffects(self.db)['encounter'].get('active'))
        self.assertEqual(get_workspace_snapshot(self.db, is_gm=True)['tokens'], self.initial['tokens'])
