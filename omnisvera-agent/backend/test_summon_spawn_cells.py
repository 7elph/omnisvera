"""Summons must not hide a living target under their newly created pin."""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase


class SummonSpawnCellTests(TestCase):
    def setUp(self):
        from test_hemomante_techniques import NecromanteSummonTests
        from app.spatial_grid import init_spatial
        from app.session_workspace import save_workspace_token
        self.fixture=NecromanteSummonTests()
        self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.path=self.fixture.db
        init_spatial(self.path)
        self.caster=save_workspace_token(self.path,token_type='character',character_id='morthak',
            name='Morthak',map_id='default',latitude=50,longitude=50,current_hp=4,maximum_hp=4)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("INSERT INTO session_workspace_map_grids VALUES('default','square',3,3,1.5,0,0,'chebyshev',1,1)")
            for identity,x,y in [(self.caster['id'],1,1),(self.fixture.healthy['id'],2,1)]:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,?,1,1,1)",(identity,x,y))

    def test_occupied_right_cell_uses_a_free_adjacent_cell_and_retry_keeps_it(self):
        request={'request_id':'spawn-cell-once'}
        response=self.fixture.use('morthak','levantar-esqueleto',request)
        self.assertEqual(200,response.status_code,response.text)
        identity=response.json()['token']['id']
        with closing(sqlite3.connect(self.path)) as db:
            cell=db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE token_id=?',(identity,)).fetchone()
        self.assertNotIn(cell,[(1,1),(2,1)])
        self.assertLessEqual(max(abs(cell[0]-1),abs(cell[1]-1)),1)
        self.assertEqual(response.json(),self.fixture.use('morthak','levantar-esqueleto',request).json())
        self.assertEqual(0,self.fixture._resource('levantar_um_esqueleto'))

    def test_no_adjacent_cell_rejects_atomically_without_spending_or_spawning(self):
        from app.session_workspace import save_workspace_token
        for x in range(3):
            for y in range(3):
                if (x,y) in {(1,1),(2,1)}:continue
                pin=save_workspace_token(self.path,token_type='monster',name=f'Occupied {x},{y}',
                    map_id='default',latitude=50,longitude=50,current_hp=3,maximum_hp=3)
                with closing(sqlite3.connect(self.path)) as db,db:
                    db.execute("UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=? WHERE token_id=?",(x,y,pin['id']))
        with closing(sqlite3.connect(self.path)) as db:
            before=db.execute('SELECT count(*) FROM session_workspace_tokens').fetchone()[0]
        response=self.fixture.use('morthak','levantar-esqueleto',{'request_id':'blocked-spawn-cell'})
        self.assertEqual(400,response.status_code,response.text)
        self.assertIn('adjacente',response.text)
        self.assertEqual(1,self.fixture._resource('levantar_um_esqueleto'))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(before,db.execute('SELECT count(*) FROM session_workspace_tokens').fetchone()[0])
