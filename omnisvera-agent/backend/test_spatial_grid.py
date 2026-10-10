import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor

import test_session_coherence as fixture
from app.spatial_grid import configure_grid, move_entity, distance_between, enrich_snapshot, seed_session7_grids
from app.session_workspace import set_workspace_map, save_workspace_token, get_workspace_snapshot, update_workspace_token_position
from app.combat_effects import readeffects, effect_command


class SpatialGridTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.SessionCoherenceTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.database
        self.fixture._character()
        self.map = set_workspace_map(self.db, title='Grid fixture', image_path='fixture.svg', visible_to_players=True)['id']
        self.token = save_workspace_token(self.db, token_type='character', character_id='vezemir', name='Vezemir',
            latitude=12, longitude=12, map_id=self.map)
        self.configure()

    def configure(self, **changes):
        return configure_grid(self.db, actor_id='master', role='gm', request_id='configure-grid-001', map_id=self.map,
            config=dict(cols=10, rows=10, cell_size_m=1.5, **changes))

    def position(self):
        return get_workspace_snapshot(self.db, map_id=self.map, is_gm=True)['tokens'][0]['grid_position']

    def command(self, mode='GM_REPOSITION', cells=None, **changes):
        pos = self.position()
        state = readeffects(self.db)
        args = dict(actor_id='master', role='gm', request_id=f'move-grid-{pos["version"]:04}', map_id=self.map,
            token_id=self.token['id'], mode=mode, cells=cells or [[pos['cell_x'],pos['cell_y']],[2,1]],
            expected_position_version=pos['version'], expected_grid_version=1, expected_combat_version=state['version'],
            load_movement=lambda _: '9 m')
        args.update(changes)
        return move_entity(self.db, **args)

    def start(self):
        state = readeffects(self.db)
        return effect_command(self.db, actor_id='master', actor_role='gm', request_id='grid-combat-start',
            expected_version=state['version'], action='start', payload={'map_id': self.map,
            'participants':[{'target_type':'character','target_id':'vezemir','initiative':10}]})

    def test_configuration_persists_and_legacy_projection_snaps(self):
        snapshot = get_workspace_snapshot(self.db, map_id=self.map, is_gm=True)
        self.assertEqual(1.5, snapshot['map']['grid']['cell_size_m'])
        self.assertEqual((1,1), (self.position()['cell_x'],self.position()['cell_y']))
        self.assertEqual(15, snapshot['tokens'][0]['longitude'])
        self.assertEqual('fixture.svg', snapshot['map']['image_path'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(12, db.execute('SELECT longitude FROM session_workspace_tokens WHERE id=?',(self.token['id'],)).fetchone()[0])

    def test_gm_reposition_persist_reload_and_no_budget(self):
        result = self.command(cells=[[1,1],[9,9]])
        self.assertEqual(9,self.position()['cell_x'])
        self.assertIsNone(result['movement'])
        self.assertFalse(readeffects(self.db).get('encounter',{}).get('movement'))

    def test_bounds_and_source_rejected_atomically(self):
        for cells in ([[1,1],[10,1]], [[0,1],[1,1]], [[1,1],[1.5,2]]):
            with self.subTest(cells=cells), self.assertRaises(ValueError): self.command(cells=cells)
        self.assertEqual(1, self.position()['version'])

    def test_combat_valid_movement_budget_and_no_teleport(self):
        self.start()
        with self.assertRaisesRegex(ValueError,'adjacentes'): self.command('COMBAT_MOVE', [[1,1],[3,1]])
        result = self.command('COMBAT_MOVE', [[1,1],[2,1],[3,1]])
        self.assertEqual(3,result['movement']['spent_m'])
        self.assertEqual(9,result['movement']['budget_m'])
        with self.assertRaisesRegex(ValueError,'limite'):
            self.command('COMBAT_MOVE', [[3,1],[4,1],[5,1],[6,1],[7,1],[8,1]], request_id='over-budget-command')
        self.assertEqual(3,self.position()['cell_x'])
        with self.assertRaises(ValueError): self.command('GM_REPOSITION')

    def test_budget_resets_next_turn_and_survives_initiative(self):
        self.start()
        self.command('COMBAT_MOVE')
        for action in ['initiative','next_turn']:
            state=readeffects(self.db)
            effect_command(self.db, actor_id='master',actor_role='gm',request_id='grid-'+action,
                expected_version=state['version'],action=action,payload={'participants':state['encounter']['participants']})
            if action=='initiative': self.assertEqual(1.5,readeffects(self.db)['encounter']['movement']['spent_m'])
        self.assertEqual(1.5,self.command('COMBAT_MOVE',[[2,1],[3,1]])['movement']['spent_m'])

    def test_idempotent_concurrent_retry_one_ledger_event(self):
        args=dict(actor_id='master',role='gm',request_id='stable-retry-001',map_id=self.map,token_id=self.token['id'],
            mode='GM_REPOSITION',cells=[[1,1],[2,1]],expected_position_version=1,expected_grid_version=1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:move_entity(self.db,**args),range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(2,self.position()['version'])
        with closing(sqlite3.connect(self.db)) as db:
            rows=db.execute("SELECT detail_json FROM session_ledger WHERE source_type='spatial_move'").fetchall()
        self.assertEqual(1,len(rows))
        self.assertEqual([[1,1],[2,1]],json.loads(rows[0][0])['path'])
        with self.assertRaisesRegex(ValueError,'outro comando'): move_entity(self.db,**{**args,'cells':[[1,1],[3,1]]})

    def test_distance_and_each_maps_scale(self):
        other=save_workspace_token(self.db,token_type='monster',name='NPC',latitude=42,longitude=32,map_id=self.map,sheet={'movement':6})
        self.assertEqual({'cells':3,'meters':4.5,'rule':'chebyshev','provisional':True},distance_between(self.db,self.map,self.token['id'],other['id']))
        configure_grid(self.db,actor_id='master',role='gm',request_id='reconfigure-001',map_id=self.map,expected_version=1,
            config=dict(cols=10,rows=10,cell_size_m=2,distance_rule='manhattan'))
        self.assertEqual(10,distance_between(self.db,self.map,self.token['id'],other['id'])['meters'])

    def test_hidden_map_never_emits_public_path(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_maps SET visible_to_players=0 WHERE id=?',(self.map,))
        self.command()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual('gm',db.execute("SELECT visibility FROM session_ledger WHERE source_type='spatial_move'").fetchone()[0])
        with self.assertRaises(PermissionError): self.command(role='player',actor_id='vezemir')

    def test_player_cannot_reposition_or_move_other_character(self):
        with self.assertRaises(PermissionError): self.command(role='player',actor_id='vezemir')
        self.start()
        with self.assertRaises(PermissionError): self.command('COMBAT_MOVE',role='player',actor_id='raziel')
        self.assertEqual(1.5,self.command('COMBAT_MOVE',role='player',actor_id='vezemir')['movement']['spent_m'])

    def test_legacy_pixel_api_cannot_bypass_logical_position(self):
        with self.assertRaises(ValueError): update_workspace_token_position(self.db,token_id=self.token['id'],latitude=99,longitude=99)

    def test_six_session7_maps_only_are_migrated_idempotently(self):
        from app.session7_content import MAPS
        maps=[set_workspace_map(self.db,title=value[0],image_path='original.svg')['id'] for value in MAPS.values()]
        self.assertEqual(set(maps),set(seed_session7_grids(self.db)))
        self.assertEqual([],seed_session7_grids(self.db))
        for map_id in maps:
            snapshot=get_workspace_snapshot(self.db,map_id=map_id,is_gm=True)
            self.assertEqual(1.5,snapshot['map']['grid']['cell_size_m'])
            self.assertEqual('original.svg',snapshot['map']['image_path'])

    def test_http_auth_command_conflict_and_legacy_bypass(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.spatial_routes import register_spatial_routes
        from app.access import AccessContext
        app=FastAPI()
        access=AccessContext(mode='player',profile_id='vezemir')
        register_spatial_routes(app,lambda:self.db,lambda:access,lambda _:9)
        client=TestClient(app)
        endpoint=f'/workspace/maps/{self.map}'
        self.assertEqual(403,client.post(endpoint+'/grid',json=dict(request_id='http-config-001',cols=5,rows=5,cell_size_m=1)).status_code)
        self.start()
        command=dict(request_id='http-move-001',token_id=self.token['id'],mode='COMBAT_MOVE',path=[[1,1],[2,1]],
            expected_position_version=1,expected_grid_version=1,expected_combat_version=readeffects(self.db)['version'])
        first=client.post(endpoint+'/move',json=command)
        self.assertEqual(200,first.status_code,first.text)
        self.assertEqual(first.json(),client.post(endpoint+'/move',json=command).json())
        self.assertEqual(409,client.post(endpoint+'/move',json={**command,'request_id':'http-new-command'}).status_code)
        self.assertEqual(422,client.post(endpoint+'/move',json={**command,'path':[[1.3,1]]}).status_code)

    def test_new_summon_and_map_transfer_seed_positions_without_erasing_old_cells(self):
        other=set_workspace_map(self.db,title='Second grid',image_path='two.svg')['id']
        configure_grid(self.db,actor_id='master',role='gm',request_id='other-grid-config',map_id=other,config=dict(cols=10,rows=10,cell_size_m=2))
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET map_id=? WHERE id=?',(other,self.token['id']))
            db.execute('UPDATE session_workspace_tokens SET map_id=? WHERE id=?',(self.map,self.token['id']))
        self.assertEqual(1,self.position()['cell_x'])
        summon=save_workspace_token(self.db,token_type='monster',name='Invocação',latitude=20,longitude=40,map_id=self.map,sheet={'movement':6,'summon':{'caster':'vezemir'}})
        snapshot=get_workspace_snapshot(self.db,map_id=self.map,is_gm=True)
        self.assertEqual(4,next(t for t in snapshot['tokens'] if t['id']==summon['id'])['grid_position']['cell_x'])

    def test_hidden_intermediate_path_keeps_ledger_private(self):
        from app.session_workspace import update_workspace_fog
        update_workspace_fog(self.db,map_id=self.map,layer='exploration',enabled=True,revealed_cells=[],mist_density={'8:3':1})
        self.command(cells=[[1,1],[2,1],[3,1]])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual('gm',db.execute("SELECT visibility FROM session_ledger WHERE source_type='spatial_move'").fetchone()[0])

    def test_unknown_speed_is_not_invented_and_npc_uses_its_sheet(self):
        npc=save_workspace_token(self.db,token_type='monster',name='NPC',latitude=12,longitude=12,map_id=self.map,current_hp=10,sheet={'movement':'6 m'})
        state=readeffects(self.db)
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='grid-npc-start',expected_version=state['version'],action='start',payload={'map_id':self.map,'participants':[{'target_type':'token','target_id':npc['id'],'initiative':10}]})
        args=dict(actor_id='master',role='gm',request_id='grid-npc-move',map_id=self.map,token_id=npc['id'],mode='COMBAT_MOVE',cells=[[1,1],[2,1]],expected_position_version=1,expected_grid_version=1,expected_combat_version=readeffects(self.db)['version'])
        self.assertEqual(6,move_entity(self.db,**args)['movement']['budget_m'])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps({'summon':{'caster':'vezemir'}}),npc['id']))
        with self.assertRaisesRegex(ValueError,'não configurado'):
            move_entity(self.db,**{**args,'request_id':'grid-no-speed','expected_position_version':2,'cells':[[2,1],[3,1]],'expected_combat_version':readeffects(self.db)['version']})

    def test_authorized_move_after_main_action_and_stale_turn_rejected(self):
        self.start()
        with closing(sqlite3.connect(self.db)) as db,db:
            state=readeffects(self.db)['encounter'];state['action_committed']=True
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(state),))
        self.assertEqual(1.5,self.command('COMBAT_MOVE')['movement']['spent_m'])
        with self.assertRaisesRegex(ValueError,'turno ou os efeitos'):
            self.command('COMBAT_MOVE',[[2,1],[3,1]],expected_combat_version=-1)


if __name__ == '__main__': unittest.main()
