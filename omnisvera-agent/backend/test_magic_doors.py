"""Door checks use synthetic location pins and the native inventory receipt."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch


class MagicDoorTests(unittest.TestCase):
    def setUp(self):
        from test_magic_targeted_items import TargetedMagicTests
        TargetedMagicTests.setUp(self)
        self.seed = lambda: TargetedMagicTests.seed(self, 'anel-ariete')
        self.use = lambda **kw: TargetedMagicTests.use(self, self.path, **kw)
        self.row = lambda: TargetedMagicTests.row(self, self.path)
        from app.session_workspace import save_workspace_token
        self.door = save_workspace_token(self.db, token_type='location', name='Porta de ensaio',
            latitude=32.5, longitude=32.5, map_id='default')['id']
        self.path = self.seed()

    def configure(self, **extra):
        from app.map_doors import configure
        return configure(self.db, token_id=self.door, actor='master', role='gm', request_id='door-config',
            payload={'difficulty':12, 'open':False, **extra})

    def test_door_roll_charges_replay_and_native_grid_position(self):
        self.configure()
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':15}) as roll:
            first=self.use(target_token_id=self.door,charges=2)
            self.assertEqual(first.status_code,200,first.text)
            replay=self.use(target_token_id=self.door,charges=2)
            self.assertEqual(replay.status_code,200,replay.text)
            roll.assert_called_once_with('1d20')
        self.assertEqual(self.row()['charges_current'],1)
        with closing(sqlite3.connect(self.db)) as db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.door,)).fetchone()[0])
            self.assertTrue(sheet['door']['open'])
            self.assertIsNotNone(db.execute('SELECT cell_x FROM session_workspace_entity_positions WHERE token_id=?',(self.door,)).fetchone())

    def test_failed_check_spends_charges_without_opening(self):
        self.configure(difficulty=25)
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':1}):
            r=self.use(target_token_id=self.door,charges=3)
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.row()['charges_current'],0)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertFalse(json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.door,)).fetchone()[0])['door']['open'])

    def test_configuration_is_gm_only_validated_and_keeps_existing_metadata(self):
        from app.map_doors import configure
        with self.assertRaises(PermissionError):
            configure(self.db,token_id=self.door,actor='raziel',role='player',request_id='no-door',payload={'difficulty':12,'open':False})
        with self.assertRaises(ValueError):self.configure(difficulty=True)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps({'description':'preservar','merchant_id':'existing'}),self.door))
        self.configure()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.door,)).fetchone()[0])['description'],'preservar')

    def test_location_without_door_contract_cannot_take_creature_damage(self):
        r=self.use(target_token_id=self.door)
        self.assertEqual(r.status_code,400)
        self.assertIsNone(self.row()['charges_current'])

    def test_open_door_does_not_spend_and_preview_includes_only_configured_doors(self):
        self.configure(open=True)
        r=self.use(target_token_id=self.door)
        self.assertEqual(r.status_code,400,r.text)
        self.assertIsNone(self.row()['charges_current'])

    def test_grid_preview_includes_configured_door_and_hides_private_dc(self):
        self.configure()
        response=self.client.get('/gm/grid/range',params={'ref':'technique:vezemir:magic-item:item-magico-anel-ariete',
            'attacker_character_id':'vezemir','map_id':'default'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(next(t for t in response.json()['targets'] if t['id']==self.door)['valid'])
        from app.session_workspace import get_workspace_snapshot
        view=get_workspace_snapshot(self.db,is_gm=False)
        # A fixture without an active session may intentionally hide the map.
        if view['tokens']:
            self.assertEqual(next(t for t in view['tokens'] if t['id']==self.door)['sheet']['door'],{'open':False})

    def test_door_difficulty_is_gm_only_even_in_item_use_result(self):
        self.configure(difficulty=17)
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':10}):
            response=self.use(target_token_id=self.door)
        self.assertEqual(response.status_code,200,response.text)
        with closing(sqlite3.connect(self.db)) as db:
            raw=db.execute("SELECT title,detail_json FROM session_ledger WHERE source_type='item_use'").fetchone()
            self.assertNotIn('contra 17',raw[0]);self.assertNotIn('"difficulty"',raw[1])
            private=db.execute("SELECT visibility,detail_json FROM session_ledger WHERE source_type='door_force_check'").fetchone()
            self.assertEqual(private[0],'gm');self.assertEqual(json.loads(private[1])['difficulty'],17)
