# -*- coding: utf-8 -*-
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch
import test_dorn_mage as fixture
from app.dorn_mage import apply_dorn_mage
from app.combat_effects import effect_command, readeffects, init_effects
from app.session_workspace import save_workspace_token
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger
from app import dorn_recharge


class DornCampaignOct24Tests(TestCase):
    def setUp(self):
        self.base = fixture.DornMageTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.db = self.base.db
        apply_dorn_mage(self.db)
        init_dice_rolls(self.db)
        init_session_ledger(self.db)
        init_effects(self.db)
        self.enemy = save_workspace_token(self.db, token_type='monster', name='Alvo fixture', latitude=50, longitude=50, current_hp=50, maximum_hp=50, sheet={'armor_class':12, 'saving_throw':20})
        self.count = 0

    def command(self, action='dorn_spell_cast', **payload):
        self.count += 1
        return effect_command(self.db, actor_id='master', actor_role='gm', request_id=f'oct24-{self.count:04d}', expected_version=readeffects(self.db)['version'], action=action, payload=payload)

    def args(self, spell):
        return dict(spell_id=spell, targets=[{'type':'token','id':self.enemy['id']}], position_confirmed=True, distance_meters=10, weight_kg=100, shape='line')


class DornReflexosTests(DornCampaignOct24Tests):
    def test_reflexos_area_ignored(self):
        self.command('start', participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20},{'target_type':'token','target_id':self.enemy['id'],'name':'Alvo','initiative':10}])
        self.command('dorn_spell_cast', spell_id='reflexos')
        from app import dorn_spell_pack
        strikes = [{'damage_total': 10, 'result': 'hit'}]
        amount, info = dorn_spell_pack.redirect_hits(self.base.db, 'character', 'dorn7', strikes, 'now', area=True)
        self.assertEqual(10, amount)
        self.assertEqual({}, info)

    def test_reflexos_player_natural20_unavoidable_ignores(self):
        self.command('start', participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20},{'target_type':'token','target_id':self.enemy['id'],'name':'Alvo','initiative':10}])
        self.command('dorn_spell_cast', spell_id='reflexos')
        from app import dorn_spell_pack
        strikes = [{'damage_total': 10, 'result': 'hit', 'unavoidable': True}]
        with closing(sqlite3.connect(self.base.db)) as db,db:
            amount, info = dorn_spell_pack.redirect_hits(db, 'character', 'dorn7', strikes, 'now')
        self.assertEqual(10, amount)


class DornLightningSplitTests(DornCampaignOct24Tests):
    def grid_lightning_setup(self):
        from app.spatial_grid import configure_grid
        with closing(sqlite3.connect(self.db)) as db:
            map_id = db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()[0]
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES(?, 'Fixture','fixture.svg',1,'now','now')", (map_id,))
        save_workspace_token(self.db, token_type='character', name='Dorn', character_id='dorn7', map_id=map_id, latitude=0, longitude=0)
        configure_grid(self.db, actor_id='master', role='gm', request_id='grid-lightning-001', map_id=map_id, config=dict(cols=100, rows=20, cell_size_m=1.5))
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=0,cell_y=0 WHERE token_id IN (SELECT id FROM session_workspace_tokens WHERE character_id='dorn7')")
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=4,cell_y=0 WHERE token_id=?', (self.enemy['id'],))
        return map_id

    def test_lightning_split_total_before_individual_jpd(self):
        map_id = self.grid_lightning_setup()
        targets = [self.enemy['id']] + [save_workspace_token(self.db, token_type='monster', map_id=map_id, name=f'Alvo {n}', latitude=0, longitude=6+n, current_hp=50, maximum_hp=50, sheet={'armor_class':12, 'saving_throw':20})['id'] for n in (1,2)]
        payload = {'spell_id': 'relampago', 'grid_selection': True, 'targets': [{'type':'token','id':i} for i in targets]}
        with patch('app.dorn_spells.roll_formula', side_effect=lambda formula: {'total':12 if formula=='3d6' else 1, 'individual_results':[4,4,4] if formula=='3d6' else [1]}):
            result = self.command(**payload)['protocol_result']
        self.assertEqual([4,4,4], [t['damage'] for t in result['results']])

    def test_lightning_split_remainder_to_firsts_floor_jpd(self):
        map_id = self.grid_lightning_setup()
        targets = [self.enemy['id']] + [save_workspace_token(self.db, token_type='monster', map_id=map_id, name=f'Alvo {n}', latitude=0, longitude=6+n, current_hp=50, maximum_hp=50, sheet={'armor_class':12, 'saving_throw':20})['id'] for n in (1,2)]
        payload = {'spell_id': 'relampago', 'grid_selection': True, 'targets': [{'type':'token','id':i} for i in targets]}
        with patch('app.dorn_spells.roll_formula', side_effect=lambda formula: {'total':10 if formula=='3d6' else 1, 'individual_results':[4,3,3] if formula=='3d6' else [1]}):
            result = self.command(**payload)['protocol_result']
        self.assertEqual([4,3,3], [t['damage'] for t in result['results']])  # all fail save; sum remains ten


class DornGuardTests(DornCampaignOct24Tests):
    def start_battle(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('arena','Arena fixture','fixture.png',1,'now','now')")
            db.execute("INSERT OR IGNORE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES (1,'arena','Arena','fixture.png','now')")
        state = json.loads(sqlite3.connect(self.db).execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states VALUES('ally',?,1,'now')", (json.dumps(state),))
        self.command('start', map_id='arena', participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20}, {'target_type':'character','target_id':'ally','name':'Aliado','initiative':10}])
        save_workspace_token(self.db, token_type='character', name='Aliado', character_id='ally', map_id='arena', latitude=5, longitude=5)

    def test_guard_expires_at_next_dorn_turn_start(self):
        self.start_battle()
        self.command('dorn_guard', ally_id='ally', position_confirmed=True)
        self.assertTrue(readeffects(self.db)['effects'])
        self.command('next_turn')
        self.assertTrue(readeffects(self.db)['effects'])
        self.command('next_turn')
        self.assertFalse(readeffects(self.db)['effects'])


class DornRechargeTests(DornCampaignOct24Tests):
    def test_recharge_on_dorn_turn_start_5or6(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('arena','Arena fixture','fixture.png',1,'now','now')")
            db.execute("INSERT OR IGNORE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES (1,'arena','Arena','fixture.png','now')")
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id=\"dorn7\"").fetchone()[0])
            db.execute("INSERT INTO character_states VALUES('ally',?,1,'now')", (json.dumps(state),))
        self.command('start', map_id='arena', participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20}, {'target_type':'character','target_id':'ally','name':'Aliado','initiative':10}])
        # spend lightning
        self.command('dorn_spell_cast', spell_id='relampago', targets=[{'type':'token','id':self.enemy['id']}], position_confirmed=True, distance_meters=10)
        with closing(sqlite3.connect(self.db)) as db, db:
            st = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            for r in st.get('resources', []):
                if r['key'] in ['dorn_relampago']:
                    r['current'] = 0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='dorn7'", (json.dumps(st),))
        self.command('next_turn')
        with patch('app.dorn_recharge.roll_formula', return_value={'total':5}):
            self.command('next_turn')
        st = json.loads(sqlite3.connect(self.db).execute("SELECT state_json FROM character_states WHERE profile_id=\"dorn7\"").fetchone()[0])
        rel = next((r for r in st['resources'] if r['key']=='dorn_relampago'), None)
        self.assertIsNotNone(rel)
        self.assertEqual(1, rel['current'])

    def test_both_start_available_by_combat(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES ('arena','Arena fixture','fixture.png',1,'now','now')")
        self.count += 1
        effect_command(self.base.db, actor_id='master', actor_role='gm', request_id=f'startx-{self.count:04d}', expected_version=readeffects(self.base.db)['version'], action='start', payload={'map_id':'arena','participants':[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20}]})
        st = json.loads(sqlite3.connect(self.db).execute("SELECT state_json FROM character_states WHERE profile_id=\"dorn7\"").fetchone()[0])
        rel = next((r for r in st.get('resources',[]) if r['key']=='dorn_relampago'), None)
        guard = next((r for r in st.get('resources',[]) if r['key']=='dorn_guard'), None)
        self.assertTrue(rel is not None and rel['current'] >= 1)
        self.assertTrue(guard is not None and guard['current'] >= 1)
