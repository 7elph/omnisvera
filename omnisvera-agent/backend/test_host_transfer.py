"""Portable host packaging over generated SQLite, credentials and artwork only."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import closing
from scripts.transfer_bundle import export_bundle, restore_bundle

spec = importlib.util.spec_from_file_location('portable_host', Path(__file__).resolve().parents[1] / 'serve_companion.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class HostTransferTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='omni-host-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        (self.vault / 'character.md').write_text('# Synthetic character', encoding='utf-8')
        (self.vault / '.env').write_text('DO_NOT_EXPORT=secret', encoding='utf-8')
        (self.vault / 'node_modules').mkdir()
        (self.vault / 'node_modules/not-a-vault-note.md').write_text('ignore')
        self.db = self.root / 'source.sqlite3'
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('CREATE TABLE wallet(value INTEGER)')
            db.execute('INSERT INTO wallet VALUES(1234)')
        self.tokens = self.root / 'access.json'
        self.access = {'master_token': 'synthetic-master', 'player_token': 'synthetic-player',
                       'player_profiles': {'hero': {'token': 'synthetic-hero'}, 'dorn7': {'token': 'synthetic-dorn', 'gm_controlled': True}}}
        self.tokens.write_text(json.dumps(self.access), encoding='utf-8')
        self.bundle = self.root / 'private.zip'

    def export(self):
        return export_bundle(self.vault, self.db, self.tokens, self.bundle, code_ref='synthetic-ref')

    def test_round_trip_preserves_state_tokens_and_excludes_tools(self):
        self.export()
        destination = self.root / 'restored'
        restore_bundle(self.bundle, destination)
        self.assertEqual(json.loads((destination / 'state/access_tokens.json').read_text()), self.access)
        with closing(sqlite3.connect(destination / 'state/companion.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT value FROM wallet').fetchone()[0], 1234)
        self.assertTrue((destination / 'vault/character.md').exists())
        self.assertFalse((destination / 'vault/.env').exists())
        self.assertFalse((destination / 'vault/node_modules').exists())
        with self.assertRaises(ValueError):
            restore_bundle(self.bundle, destination)

    def test_export_never_overwrites_or_goes_inside_vault(self):
        self.export()
        with self.assertRaises(ValueError): self.export()
        with self.assertRaises(ValueError):
            export_bundle(self.vault, self.db, self.tokens, self.vault / 'leak.zip', code_ref='test')

    def test_snapshot_includes_committed_wal_without_modifying_source(self):
        with closing(sqlite3.connect(self.db)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('UPDATE wallet SET value=4321')
            writer.commit()
            self.export()
            writer.execute('UPDATE wallet SET value=9876')
            writer.commit()
            destination = self.root / 'wal-restored'
            restore_bundle(self.bundle, destination)
            with closing(sqlite3.connect(destination / 'state/companion.sqlite3')) as snapshot:
                self.assertEqual(snapshot.execute('SELECT value FROM wallet').fetchone()[0], 4321)
            self.assertEqual(writer.execute('SELECT value FROM wallet').fetchone()[0], 9876)

    def test_tampering_and_path_traversal_leave_no_destination(self):
        self.export()
        for name in ('vault/character.md', '../escape'):
            edited = self.root / ('edited-' + str(len(name)) + '.zip')
            with zipfile.ZipFile(self.bundle) as original, zipfile.ZipFile(edited, 'w') as target:
                for entry in original.infolist():
                    if entry.filename != 'vault/character.md': target.writestr(entry, original.read(entry))
                target.writestr(name, 'altered')
            destination = self.root / 'must-not-exist'
            with self.assertRaises(ValueError): restore_bundle(edited, destination)
            self.assertFalse(destination.exists())

    def test_host_preserves_credentials_and_filters_gm_controlled_profiles(self):
        self.export()
        site = self.root / 'site'
        site.mkdir()
        restore_bundle(self.bundle, site / 'host-data')
        (site / 'frontend/dist/assets').mkdir(parents=True)
        (site / 'frontend/dist/index.html').write_text('synthetic')
        env = {}
        self.assertTrue(host.configure(root=site, environ=env)['access_ready'])
        self.assertEqual(env['OMNISVERA_MASTER_TOKEN'], self.access['master_token'])
        self.assertEqual(set(json.loads(env['OMNISVERA_PLAYER_PROFILES_JSON'])), {'hero'})
        self.assertEqual(json.loads((site / 'host-data/state/access_tokens.json').read_text()), self.access)

    def test_host_does_not_silently_regenerate_access(self):
        site = self.root / 'site'
        (site / 'host-data/vault').mkdir(parents=True)
        with self.assertRaises(ValueError): host.configure(root=site, environ={})
        self.assertFalse((site / 'host-data/state/access_tokens.json').exists())

    def test_optional_workshop_and_private_drafts_survive_transfer(self):
        drafts = self.db.parent / 'asset_drafts'
        drafts.mkdir()
        (drafts / 'synthetic.png').write_bytes(b'synthetic artwork')
        export_bundle(self.vault, self.db, self.tokens, self.bundle, code_ref='test', workshop=self.db)
        destination = self.root / 'with-workshop'
        restore_bundle(self.bundle, destination)
        with closing(sqlite3.connect(destination / 'state/ai-workshop.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT value FROM wallet').fetchone()[0], 1234)
        self.assertEqual((destination / 'state/asset_drafts/synthetic.png').read_bytes(), b'synthetic artwork')
