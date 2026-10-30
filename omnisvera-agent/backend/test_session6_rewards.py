import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

import test_battle_mode as fixture
from app.combat_effects import effect_command, readeffects
from app.session6_rewards import missile_maximum, synchronize_resource
from app.session_workspace import save_session_item, get_workspace_snapshot, save_workspace_token
from app.player_inventory import upsert_inventory


class RewardTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.BattleModeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        upsert_inventory(self.db, profile_id='vezemir', item_path='session-item:99', item_title='Pulseira de Vinhas', quantity=1, equipped=True, notes=None, equipment_slot='Acessório')
        self.fixture.start()

    def cast(self, actor='vezemir', request='vine-test-001'):
        return effect_command(self.db, actor_id=actor, actor_role='player', allow_player=True, request_id=request,
            expected_version=readeffects(self.db)['version'], action='vine_cast', payload={
                'target_type': 'token', 'target_id': self.fixture.enemy['id'], '_saving_throw': 15,
                '_saving_throw_bonus': 1, '_target_name': 'Aranha'})

    def test_three_failed_target_turns_skip_and_expire_without_consuming_item(self):
        result = self.cast()
        self.assertEqual(result, self.cast())
        with patch('app.session6_rewards.random.randint', return_value=1) as roll:
            for index in range(3):
                state = self.fixture.command('next_turn')
                self.assertEqual(state['encounter']['participants'][state['encounter']['turn_index']]['target_id'], 'vezemir')
                self.assertEqual(len(state['effects']), 1 if index < 2 else 0)
            self.assertEqual(roll.call_count, 3)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT quantity FROM player_inventory WHERE item_title='Pulseira de Vinhas'").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='vines_save' AND visibility='public'").fetchone()[0], 3)

    def test_success_on_normal_jp_allows_target_turn(self):
        self.cast()
        with patch('app.session6_rewards.random.randint', return_value=14):
            state = self.fixture.command('next_turn')
        self.assertFalse(state['effects'])
        self.assertEqual(state['encounter']['turn_index'], 1)
        self.assertFalse(state['encounter']['action_committed'])

    def test_vines_use_consumable_not_attack_budget(self):
        result=self.cast()
        self.assertTrue(result['encounter']['consumable_used'])
        self.assertFalse(result['encounter'].get('action_committed'))
        self.assertEqual(0,result['encounter'].get('attacks_used',0))
        with self.assertRaisesRegex(ValueError,'consumível'):
            self.cast(request='another-vine-this-turn')

    def test_vines_can_follow_an_attack_without_reopening_attack(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0])
            encounter.update(action_committed=True,attacks_used=1,attack_limit=1)
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        result=self.cast()
        self.assertTrue(result['encounter']['consumable_used'])
        self.assertTrue(result['encounter']['action_committed'])
        self.assertEqual(1,result['encounter']['attacks_used'])

    def test_charges_consumed_once_and_exhaustion_blocks(self):
        first = self.cast()
        self.assertEqual(first, self.cast())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE item_title='Pulseira de Vinhas'").fetchone()[0], 1)
        self.fixture.command('remove', id=first['effects'][0]['id'])
        self.fixture.command('next_turn'); self.fixture.command('next_turn')
        second = self.cast(request='vines-second-use')
        self.fixture.command('remove', id=second['effects'][0]['id'])
        self.fixture.command('next_turn'); self.fixture.command('next_turn')
        with self.assertRaisesRegex(ValueError, 'Sem usos'):
            self.cast(request='vines-third-use')

    def test_other_owner_cannot_use_and_item_must_be_equipped(self):
        with self.assertRaises(PermissionError): self.cast('raziel')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE player_inventory SET equipped=0 WHERE profile_id='vezemir'")
        with self.assertRaises(ValueError): self.cast()

    def test_end_clears_vines(self):
        self.cast()
        self.assertFalse(self.fixture.command('end')['effects'])

    def test_approved_nine_meter_vines_reject_without_spending(self):
        from app.spatial_grid import configure_grid
        from app.session_workspace import save_workspace_token
        enemy = self.fixture.enemy
        with closing(sqlite3.connect(self.db)) as db:
            map_id=db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0]
        pc = save_workspace_token(self.db, token_type='character', name='Vezemir', character_id='vezemir',
            map_id=map_id, latitude=0, longitude=0)
        self.fixture.command('end')
        configure_grid(self.db, actor_id='master', role='gm', request_id='vine-grid', map_id=map_id,
            config=dict(cols=20, rows=20, cell_size_m=1.5))
        self.fixture.start()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=0,cell_y=0 WHERE token_id IN (SELECT id FROM session_workspace_tokens WHERE character_id='vezemir')")
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=7,cell_y=0 WHERE token_id=?',(enemy['id'],))
            before=db.execute("SELECT charges_current FROM player_inventory WHERE item_title='Pulseira de Vinhas'").fetchone()[0]
        version=readeffects(self.db)['version']
        with self.assertRaisesRegex(ValueError,'máximo 9'):
            self.cast(request='vine-outside-range')
        self.assertEqual(version,readeffects(self.db)['version'])
        with closing(sqlite3.connect(self.db)) as db, db:
            self.assertEqual(before,db.execute("SELECT charges_current FROM player_inventory WHERE item_title='Pulseira de Vinhas'").fetchone()[0])
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=6 WHERE token_id=?',(enemy['id'],))
        self.assertTrue(self.cast(request='vine-nine-meters')['effects'])

    def test_authenticated_route_uses_server_jp_and_rejects_other_player(self):
        from dataclasses import replace
        from fastapi.testclient import TestClient
        from app import main
        from app.access import AccessContext
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?', (json.dumps({'armor_class': 10, 'saving_throw': 15}), self.fixture.enemy['id']))
        with patch.object(main, 'settings', replace(main.settings, database_path=self.db)):
            try:
                main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='raziel')
                with TestClient(main.app) as client:
                    body = {'request_id': 'vines-api-001', 'target_type': 'token', 'target_id': self.fixture.enemy['id']}
                    self.assertEqual(client.post('/characters/vezemir/vines', json=body).status_code, 403)
                    main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='vezemir')
                    response = client.post('/characters/vezemir/vines', json=body)
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()['effects'][0]['saving_throw'], 15)
                    self.assertEqual(response.json(), client.post('/characters/vezemir/vines', json=body).json())
            finally:
                main.app.dependency_overrides.pop(main.require_any, None)

    def test_page_equipped_maximum_and_toggle_never_refills_spent_use(self):
        item = {'item_title': 'Página de Grimório', 'quantity': 1, 'equipped': True}
        self.assertEqual(missile_maximum([item]), 4)
        item['equipped'] = False
        self.assertEqual(missile_maximum([item]), 3)
        for current in range(5):
            resource = {'maximum': 4, 'current': current}
            synchronize_resource(resource, 3)
            synchronize_resource(resource, 4)
            self.assertEqual(resource['current'], current)

    def test_definition_and_state_follow_equipment(self):
        from app.character_play import build_character_definition, get_or_create_state
        item = {'item_title': 'Página de Grimório', 'quantity': 1, 'equipped': True}
        sheet = {'character_class': {'level': 2, 'hit_points': 10}}
        options = dict(profile_id='morthak', note={'title': 'Morthak'}, sheet=sheet, inventory=[item])
        first = build_character_definition(**options)
        state = get_or_create_state(self.db, profile_id='morthak', sheet=sheet, definition=first)
        missile = next(r for r in state['resources'] if r['key']=='misseis_magicos')
        self.assertEqual(missile['maximum'], 4)
        with closing(sqlite3.connect(self.db)) as db, db:
            stored = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            next(r for r in stored['resources'] if r['key']=='misseis_magicos')['current'] = 1
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'", (json.dumps(stored),))
        item['equipped'] = False
        state = get_or_create_state(self.db, profile_id='morthak', sheet=sheet, definition=build_character_definition(**options))
        missile = next(r for r in state['resources'] if r['key']=='misseis_magicos')
        self.assertEqual((missile['maximum'], missile['current']), (3, 0))
        item['equipped'] = True
        state = get_or_create_state(self.db, profile_id='morthak', sheet=sheet, definition=build_character_definition(**options))
        self.assertEqual(next(r for r in state['resources'] if r['key']=='misseis_magicos')['current'], 1)

    def test_skeleton_exposes_only_public_reward_card(self):
        item = save_session_item(self.db, name='Essência de Mana', item_type='Acessório', description='Recompensa pública', effects=[], usable=False, image_path='essence.jpg')
        upsert_inventory(self.db, profile_id='morthak', item_path=item['item_path'], item_title=item['name'], quantity=1, equipped=False, notes='PRIVATE')
        token = save_workspace_token(self.db, token_type='monster', map_id='arena', name='Esqueleto', latitude=50, longitude=50, sheet={'summon': {'caster': 'morthak', 'technique': 'levantar-esqueleto'}}, visible_to_players=True)
        rows = get_workspace_snapshot(self.db, is_gm=True)['tokens']
        card = next(t for t in rows if t['id'] == token['id'])['sheet']['reward_items'][0]
        self.assertEqual(card['image_path'], 'essence.jpg')
        self.assertNotIn('PRIVATE', json.dumps(card))
