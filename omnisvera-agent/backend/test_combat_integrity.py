"""Session 7 regressions, exclusively against disposable combat fixtures."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch
from test_battle_mode import BattleModeTests
from test_combat import SequenceRng
from test_hemomante_techniques import NecromanteSummonTests
from app.combat import resolve_attack, confirm_attack_resolution
from app.combat_effects import readeffects
from app.battle_mode import require_battle_turn


class CombatIntegrityTests(BattleModeTests):
    def potion(self, request_id):
        from app.combat_consumables import use_inventory_item
        return use_inventory_item(self.db, character_id='vezemir', actor_id='vezemir', actor_role='player',
            request_id=request_id, item={'item_path': 'fixture-potion', 'name': 'Poção', 'usable': True,
                'effect_rules': [{'trigger': 'on_use', 'kind': 'heal_hp', 'value': 2}]})

    def prepare_potions(self):
        from app.player_inventory import init_player_inventory
        init_player_inventory(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('vezemir','fixture-potion','Poção',3,0,'fixture')")

    def test_one_consumable_and_attack_are_independent_and_retry_is_safe(self):
        self.prepare_potions(); self.start()
        first = self.potion('potion-one')
        self.assertEqual(first, self.potion('potion-one'))
        with self.assertRaisesRegex(ValueError, 'consumível'):
            self.potion('potion-two')
        record = self.digital('potion-and-attack', 1)
        confirm_attack_resolution(self.db, resolution_id=record['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        with self.assertRaisesRegex(ValueError, 'consumível'):
            self.potion('potion-after-attack')
        self.command('next_turn'); self.command('next_turn')
        self.potion('potion-next-turn')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1, db.execute("SELECT quantity FROM player_inventory WHERE item_path='fixture-potion'").fetchone()[0])

    def test_consumable_after_attack_and_off_turn_rejection(self):
        self.prepare_potions(); self.start()
        record = self.digital('attack-before-potion', 1)
        confirm_attack_resolution(self.db, resolution_id=record['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        self.potion('after-attack')
        self.command('next_turn')
        with self.assertRaisesRegex(ValueError, 'turno'):
            self.potion('off-turn')

    def test_consumable_concurrency_and_invalid_rule_are_atomic(self):
        self.prepare_potions(); self.start()
        from app.combat_consumables import use_inventory_item
        with self.assertRaises(ValueError):
            use_inventory_item(self.db, character_id='vezemir', actor_id='vezemir', actor_role='player', request_id='invalid-potion',
                item={'item_path': 'fixture-potion', 'name': 'Poção inválida', 'usable': True, 'effect_rules': [
                    {'trigger':'on_use','kind':'heal_hp','value':2}, {'trigger':'on_use','kind':'restore_resource','target':'missing','value':1}]})
        self.assertFalse(readeffects(self.db)['encounter'].get('consumable_used'))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.potion, ['same-potion-retry', 'same-potion-retry']))
        self.assertEqual(results[0], results[1])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(2, db.execute("SELECT quantity FROM player_inventory WHERE item_path='fixture-potion'").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT count(*) FROM session_ledger WHERE source_type='item_use'").fetchone()[0])

    def test_zero_hp_npc_and_confirmation_cannot_act(self):
        self.start(); record = self.digital('alive-then-down')
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state['current_hp'] = 0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?', (self.enemy['id'],))
        with self.assertRaisesRegex(ValueError, 'PV'):
            confirm_attack_resolution(self.db, resolution_id=record['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaisesRegex(ValueError, 'PV'):
                require_battle_turn(db, readeffects(self.db), self.enemy['id'])

    def digital(self, request_id, die=1):
        return resolve_attack(self.db, request_id=request_id, actor_character_id='vezemir',
            actor_name='Vezemir', requested_by_id='vezemir', requested_by_role='player',
            definition=self.base.definition, inventory=self.base.inventory, attack_id='melee',
            target=dict(type='token', id=self.enemy['id'], name='Aranha', armor_class=10, current_hp=18),
            roll_mode='digital', rng=SequenceRng(die, 3))[0]

    def test_new_request_id_cannot_fish_for_a_better_die(self):
        self.start()
        first = self.digital('integrity-preview-one', 1)
        with patch('app.combat.roll_formula', side_effect=AssertionError('must reuse stored roll')):
            second = self.digital('integrity-preview-two', 20)
        self.assertEqual(first, second)
        self.assertEqual(1, second['d20'])

    def test_concurrent_new_ids_share_one_turn_preview(self):
        self.start()
        with ThreadPoolExecutor(max_workers=2) as pool:
            records = list(pool.map(self.digital, ['integrity-concurrent-a', 'integrity-concurrent-b']))
        self.assertEqual(records[0]['resolution_id'], records[1]['resolution_id'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1, db.execute('SELECT count(*) FROM combat_attack_resolutions').fetchone()[0])

    def test_pending_attack_blocks_swapping_to_another_action(self):
        self.start(); self.digital('integrity-pending-a')
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaisesRegex(ValueError, 'pendente'):
                require_battle_turn(db, readeffects(self.db), 'vezemir')

    def test_old_preview_cannot_be_confirmed_on_a_later_turn(self):
        self.start(); record = self.digital('integrity-old-turn')
        self.command('next_turn'); self.command('next_turn')
        with self.assertRaises(ValueError):
            confirm_attack_resolution(self.db, resolution_id=record['resolution_id'], requested_by_id='vezemir', requested_by_role='player')

    def test_zero_hp_actor_cannot_attack(self):
        self.start()
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state['current_hp'] = 0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))
        with self.assertRaisesRegex(ValueError, 'PV'):
            self.digital('integrity-zero-hp')


class SkeletonIntegrityTests(NecromanteSummonTests):
    def test_second_live_skeleton_does_not_spend_or_spawn(self):
        first = self.use('morthak', 'levantar-esqueleto', {'request_id': 'integrity-skeleton-one'})
        self.assertEqual(200, first.status_code)
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            next(r for r in state['resources'] if r['key']=='levantar_um_esqueleto')['current'] = 1
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'", (json.dumps(state),))
        second = self.use('morthak', 'levantar-esqueleto', {'request_id': 'integrity-skeleton-two'})
        self.assertEqual(400, second.status_code)
        self.assertEqual(1, self._resource('levantar_um_esqueleto'))
        replay = self.use('morthak', 'levantar-esqueleto', {'request_id': 'integrity-skeleton-one'})
        self.assertEqual(first.json(), replay.json())
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?', (first.json()['token']['id'],))
        replacement = self.use('morthak', 'levantar-esqueleto', {'request_id': 'integrity-skeleton-three'})
        self.assertEqual(200, replacement.status_code)

    def test_zero_hp_caster_cannot_summon(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            state['current_hp'] = 0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'", (json.dumps(state),))
        self.assertEqual(400, self.use('morthak', 'levantar-esqueleto', {'request_id': 'integrity-dead-caster'}).status_code)
