import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app.session_workspace import set_workspace_map, edit_workspace_map, list_workspace_maps, set_active_workspace_map, get_workspace_snapshot


class MapLibraryTests(unittest.TestCase):
    def test_rename_active_and_delete_recoverably(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.sqlite'
            active = set_workspace_map(path, title='Active', image_path='a.png')
            other = set_workspace_map(path, title='Copy', image_path='b.png')
            edit_workspace_map(path, active['id'], title='Renamed')
            with self.assertRaises(ValueError):
                edit_workspace_map(path, active['id'], delete=True)
            edit_workspace_map(path, other['id'], delete=True)
            self.assertIsNone(set_active_workspace_map(path, other['id']))
            self.assertNotEqual((get_workspace_snapshot(path, is_gm=False, map_id=other['id']).get('map') or {}).get('id'), other['id'])
            self.assertEqual([m['title'] for m in list_workspace_maps(path)], ['Renamed'])
            with closing(sqlite3.connect(path)) as db:
                backup = json.loads(db.execute('SELECT record_json FROM deleted_workspace_maps').fetchone()[0])
                self.assertEqual(backup['image_path'], 'b.png')
                self.assertEqual(db.execute('SELECT map_title FROM session_workspace_state').fetchone()[0], 'Renamed')

    def test_reject_blank_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.sqlite'
            record = set_workspace_map(path, title='Original', image_path='a.png')
            with self.assertRaises(ValueError):
                edit_workspace_map(path, record['id'], title='  ')
            self.assertIsNone(edit_workspace_map(path, 'missing', delete=True))
