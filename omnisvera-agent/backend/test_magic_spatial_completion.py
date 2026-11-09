"""Synthetic inventory/map commands; never opens an operational database."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_magic_targeted_items as fixture


class MagicSpatialCompletionTests(unittest.TestCase):
    setUp=fixture.TargetedMagicTests.setUp
    seed=fixture.TargetedMagicTests.seed
    use=fixture.TargetedMagicTests.use
    row=fixture.TargetedMagicTests.row

    def cell_options(self,cell=None):
        with closing(sqlite3.connect(self.db)) as db:
            version=db.execute("SELECT version FROM session_workspace_map_grids WHERE map_id='default'").fetchone()[0]
        return {'map_id':'default','target_cell':cell or [5,6],'expected_grid_version':version}

    def test_illusion_places_empty_cell_once_and_survives_reload(self):
        path=self.seed('bomba-de-ilusao',quantity=2);options=self.cell_options()
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':2}) as rng:
            first=self.use(path,**options);self.assertEqual(200,first.status_code,first.text)
            self.assertEqual(200,self.use(path,**options).status_code);rng.assert_called_once_with('1d4')
        self.assertEqual(1,self.row(path)['quantity'])
        from app.combat_effects import readeffects,effect_snapshot
        from app.dorn_spells import elapse
        effect=next(e for e in readeffects(self.db)['effects'] if e.get('visual_area'))
        self.assertEqual([5,6],effect['visual_area']['cell'])
        self.assertEqual(1.5,effect['visual_area']['width_m'])
        self.assertEqual(9,effect['visual_area']['y_m'])
        self.assertFalse(effect['modifiers']);self.assertNotIn('web_area',effect)
        with closing(sqlite3.connect(self.db)) as db,db:elapse(db,effect_snapshot(db),20,[],'2026-11-03')
        self.assertFalse(any(e.get('visual_area') for e in readeffects(self.db)['effects']))

    def test_invalid_or_occupied_cells_never_consume_the_bomb(self):
        path=self.seed('bomba-de-ilusao',quantity=2)
        for i,cell in enumerate([[-1,5],[20,5],[10,10],[6,5],[5,5],[True,6],[5.5,6]]):
            with self.subTest(cell=cell):
                response=self.use(path,key=f'invalid-cell-{i}',**self.cell_options(cell))
                self.assertEqual(400,response.status_code,response.text)
                self.assertEqual(2,self.row(path)['quantity'])

    def test_appearance_powder_uses_logical_cell_after_grid_recalibration(self):
        path=self.seed('bomba-de-ilusao',quantity=2)
        self.assertEqual(200,self.use(path,key='illusion-before-scale',**self.cell_options()).status_code)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_map_grids SET cell_size_m=3,version=version+1')
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=5,cell_y=6,version=version+1 WHERE token_id=?',(self.performer,))
        powder=self.seed('po-do-aparecimento')
        response=self.use(powder,key='reveal-after-scale')
        self.assertEqual(200,response.status_code,response.text)
        from app.combat_effects import readeffects
        self.assertFalse(any(e.get('visual_area') for e in readeffects(self.db)['effects']))

    def test_stale_grid_wrong_map_and_mixed_targets_are_rejected(self):
        path=self.seed('bomba-de-ilusao',quantity=2);options=self.cell_options()
        for i,changes in enumerate([{'expected_grid_version':999},{'map_id':'other-map'},
                {'target_token_id':self.enemy},{'target_cell':[5,6,7]}]):
            self.assertEqual(400,self.use(path,key=f'cell-stale-{i}',**{**options,**changes}).status_code)
        self.assertEqual(2,self.row(path)['quantity'])

    def test_retry_does_not_accept_a_different_cell_and_rolls_back_on_audit_failure(self):
        path=self.seed('bomba-de-ilusao',quantity=2)
        with patch('app.combat_consumables.append_session_ledger_event',side_effect=RuntimeError('isolated audit failure')):
            with self.assertRaises(RuntimeError):self.use(path,key='bomb-audit-failure',**self.cell_options())
        self.assertEqual(2,self.row(path)['quantity'])
        self.assertEqual(200,self.use(path,key='bomb-stable-intent',**self.cell_options()).status_code)
        self.assertEqual(400,self.use(path,key='bomb-stable-intent',**self.cell_options([4,6])).status_code)
        self.assertEqual(1,self.row(path)['quantity'])

    def test_capability_patch_changes_only_its_field_and_requires_master(self):
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_master]=lambda:AccessContext(mode='gm',profile_id=None)
        url='/gm/workspace/tokens/'+self.enemy
        with closing(sqlite3.connect(self.db)) as db,db:
            raw=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0])
            raw['future_field']={'preserve':'new concurrent value'}
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(raw),self.enemy))
        response=self.client.patch(url,json={'magic_capability':False})
        self.assertEqual(200,response.status_code,response.text)
        self.assertEqual(raw['future_field'],response.json()['sheet']['future_field'])
        self.assertEqual(422,self.client.patch(url,json={'magic_capability':'yes'}).status_code)
        self.assertEqual(200,self.client.patch(url,json={'magic_capability':None}).status_code)
        main.app.dependency_overrides[main.require_master]=lambda:(_ for _ in ()).throw(__import__('fastapi').HTTPException(403,'Somente Mestre'))
        self.assertEqual(403,self.client.patch(url,json={'magic_capability':True}).status_code)

    def test_cell_ring_is_canonical_and_requires_the_inventory_item(self):
        path=self.seed('bomba-de-ilusao')
        response=self.client.get('/gm/grid/range',params={'ref':'technique:vezemir:magic-item:item-magico-bomba-de-ilusao',
            'map_id':'default','attacker_character_id':'vezemir','range_override_m':999})
        self.assertEqual(200,response.status_code,response.text)
        ring=response.json();self.assertEqual('cell',ring['selection_mode'])
        self.assertEqual(1,ring['range_cells']);self.assertTrue(ring['grid_version'])
        self.assertEqual([],ring['targets'])

    def test_player_cannot_place_illusion_under_fog(self):
        from app import main
        from app.access import AccessContext
        from app.session_workspace import update_workspace_fog,_token_fog_cell
        path=self.seed('bomba-de-ilusao',quantity=2)
        # Cell centre: x=27.5%, y=32.5% on the 20x20 fixture grid.
        update_workspace_fog(self.db,map_id='default',layer='exploration',enabled=True,revealed_cells=[],
            mist_density={_token_fog_cell(32.5,27.5):1})
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')
        response=self.use(path,**self.cell_options())
        self.assertEqual(403,response.status_code,response.text)
        self.assertEqual(2,self.row(path)['quantity'])

    def test_capability_registration_is_typed_private_and_survives_reload(self):
        from app.session_workspace import update_workspace_token,get_workspace_snapshot
        with closing(sqlite3.connect(self.db)) as db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0])
        for invalid in ['yes',1,{},[]]:
            with self.assertRaises(ValueError):update_workspace_token(self.db,token_id=self.enemy,sheet={**sheet,'magic_capability':invalid})
        update_workspace_token(self.db,token_id=self.enemy,sheet={**sheet,'magic_capability':False})
        gm=get_workspace_snapshot(self.db,is_gm=True);player=get_workspace_snapshot(self.db,is_gm=False)
        self.assertFalse(next(t for t in gm['tokens'] if t['id']==self.enemy)['sheet']['magic_capability'])
        self.assertNotIn('magic_capability',next(t for t in player['tokens'] if t['id']==self.enemy)['sheet'])
        path=self.seed('anel-inquisidor');response=self.use(path,target_token_id=self.enemy)
        self.assertEqual(200,response.status_code,response.text)
        with closing(sqlite3.connect(self.db)) as db:
            detail=json.loads(db.execute("SELECT detail_json FROM session_ledger WHERE source_type='item_use' ORDER BY id DESC LIMIT 1").fetchone()[0])
        self.assertIs(detail['rules'][0]['magic_capability'],False)
        self.assertEqual('registered',detail['rules'][0]['capability_source'])


class MagicCapabilityResolutionTests(unittest.TestCase):
    def test_structured_sources_and_uncertainty_are_not_guessed_from_names(self):
        from app.magic_capability import resolve
        self.assertEqual(True,resolve({'spellcaster_level':5})['value'])
        self.assertEqual(True,resolve({'character_class':{'class_name':'Mago'}})['value'])
        self.assertEqual(False,resolve({'magic_capability':False,'spellcaster_level':5})['value'])
        self.assertIsNone(resolve({'name':'Grande Arquimago lendário'})['value'])
        self.assertEqual(True,resolve({},monster={'id':'fixture','name':'Mago','attacks':[],
            'abilities':[{'name':'Magias','description':'Conjura como um mago de nível 5.'}]})['value'])
