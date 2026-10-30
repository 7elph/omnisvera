import importlib.util
import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('art_inventory_audit', Path(__file__).resolve().parents[1] / 'scripts/audit_art_inventory.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ArtInventoryTests(unittest.TestCase):
    def test_inventory_preserves_database_and_does_not_export_raw_lore(self):
        with TemporaryDirectory() as directory:
            vault = Path(directory)
            (vault / 'Bestiary').mkdir()
            (vault / 'zz_media').mkdir()
            image = vault / 'zz_media/wolf.png'
            image.write_bytes(b'reference bytes')
            (vault / 'Bestiary/Lobo.md').write_text('---\ncover: zz_media/wolf.png\n---\nPRIVATE RAW LORE\n', encoding='utf-8')
            database = vault / 'fixture.db'
            with closing(sqlite3.connect(database)) as db, db:
                db.executescript('CREATE TABLE session_custom_items(id INTEGER,name TEXT,image_path TEXT); CREATE TABLE session_workspace_tokens(id TEXT,name TEXT,image_path TEXT,sheet_json TEXT,token_type TEXT);')
                db.execute('INSERT INTO session_custom_items VALUES (1,?,?)', ('Lobo', 'zz_media/wolf.png'))
            before = database.read_bytes()
            with patch.object(audit, 'load_monster_catalog', return_value={'monsters': [{'id': 'lobo', 'name': 'Lobo', 'image_path': 'zz_media/wolf.png'}]}):
                report = audit.inventory(database, vault)
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(image.read_bytes(), b'reference bytes')
            self.assertNotIn('PRIVATE RAW LORE', json.dumps(report))
            self.assertEqual(report['network_calls'], 0)
            self.assertEqual(report['counts']['monster_catalog'], 1)
            self.assertTrue(report['entries'][0]['original_reference']['sha256'])

    def test_media_reference_cannot_escape_library(self):
        with TemporaryDirectory() as directory:
            vault = Path(directory)
            (vault / 'private.txt').write_text('secret', encoding='utf-8')
            self.assertIsNone(audit.media(vault, 'private.txt'))
            self.assertIsNone(audit.media(vault, '../private.txt'))
