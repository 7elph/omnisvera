"""Combat/ledger polling must not acquire schema/write locks on initialized DBs."""
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app.access import AccessContext
from app.combat_effects import init_effects, readeffects
from app.character_play import init_character_play
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger, list_session_ledger
from app.session_workspace import init_session_workspace


class TableReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'table.sqlite3'
        self.initialize_sources(self.path)
        init_effects(self.path)
        init_session_ledger(self.path)

    @staticmethod
    def initialize_sources(path):
        init_character_play(path)
        init_dice_rolls(path)
        init_session_workspace(path)

    def test_initialized_reads_do_not_reinitialize_schema(self):
        with patch('app.combat_effects.init_effects', side_effect=AssertionError('read attempted schema writes')):
            self.assertEqual(readeffects(self.path)['version'], 0)
        with patch('app.session_ledger.init_session_ledger', side_effect=AssertionError('read attempted schema writes')):
            self.assertEqual(list_session_ledger(self.path, AccessContext(mode='gm')), [])

    def test_reads_complete_while_another_connection_holds_write_reservation(self):
        writer = sqlite3.connect(self.path)
        try:
            writer.execute('BEGIN IMMEDIATE')
            with ThreadPoolExecutor(max_workers=2) as pool:
                effect_read = pool.submit(readeffects, self.path)
                ledger_read = pool.submit(list_session_ledger, self.path, AccessContext(mode='gm'))
                try:
                    self.assertEqual(effect_read.result(timeout=2)['version'], 0)
                    self.assertEqual(ledger_read.result(timeout=2), [])
                finally:
                    writer.rollback()
        finally:
            writer.close()

    def test_empty_database_still_initializes_on_first_read(self):
        empty = Path(self.folder.name) / 'empty.sqlite3'
        self.assertEqual(readeffects(empty)['version'], 0)
        self.initialize_sources(empty)
        self.assertEqual(list_session_ledger(empty, AccessContext(mode='gm')), [])

    def test_legacy_effect_clock_still_gets_its_required_column(self):
        legacy = Path(self.folder.name) / 'legacy.sqlite3'
        with closing(sqlite3.connect(legacy)) as db, db:
            db.execute('CREATE TABLE combat_effect_clock(id INTEGER PRIMARY KEY, round INTEGER, version INTEGER)')
            db.execute('INSERT INTO combat_effect_clock VALUES(1,2,9)')
        snapshot = readeffects(legacy)
        self.assertEqual((snapshot['round'], snapshot['version'], snapshot['encounter']), (2, 9, {}))

    def test_no_completed_state_cache_hides_the_next_version(self):
        self.assertEqual(readeffects(self.path)['version'], 0)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE combat_effect_clock SET version=version+1, round=2')
        self.assertEqual((readeffects(self.path)['version'], readeffects(self.path)['round']), (1, 2))


if __name__ == '__main__':
    unittest.main()
