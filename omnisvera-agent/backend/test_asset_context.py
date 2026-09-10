import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
import httpx
from app.config import get_settings
from app.asset_context import resolve_asset_context, media_reference, reference_instructions
from app.cloudflare_provider import FluxKleinProvider


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'test.db'
        self.settings = replace(get_settings(), database_path=self.db, vault_path=self.root)
        self.image = self.root / 'zz_media' / 'raven.png'
        self.image.parent.mkdir()
        Image.new('RGB', (800, 600), 'blue').save(self.image)
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.executescript('CREATE TABLE game_sessions(id INTEGER, title TEXT, public_summary TEXT, narrative_json TEXT); CREATE TABLE notes(path TEXT,title TEXT,aliases TEXT,frontmatter TEXT);')
            conn.execute('INSERT INTO game_sessions VALUES(1,?,?,?)', ('Scene', 'A raven adventurer', json.dumps({'participants': [{'name': 'Raven'}]})))
            conn.execute('INSERT INTO notes VALUES(?,?,?,?)', ('raven.md', 'Raven', '[]', json.dumps({'race': 'Avian anthropomorphic', 'thumbnail': 'zz_media/raven.png', 'gm_secret_text': 'DO NOT SEND'})))
        self.job = {'entity_type': 'game_session', 'entity_id': '1', 'asset_type': 'session_cover'}

    def tearDown(self): self.tmp.cleanup()

    def test_automatic_identity_and_reference_no_private_fields(self):
        context = resolve_asset_context(self.settings, self.job)
        self.assertEqual(len(context['references']), 1)
        self.assertEqual(context['entities'][0]['species'], 'Avian anthropomorphic')
        self.assertNotIn('DO NOT SEND', json.dumps(context))
        self.assertIn('Do not default to humans', reference_instructions(context))
        self.assertTrue(context['references'][0]['sha256'])

    def test_ambiguous_identity_blocks_instead_of_guessing(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("INSERT INTO notes VALUES('other.md','Raven','[]','{}')")
        self.assertTrue(resolve_asset_context(self.settings, self.job)['blocking'])

    def test_no_external_or_traversal_media(self):
        for path in ('../secret.png', 'https://example.org/a.png', '/secret.png'):
            with self.assertRaises(ValueError): media_reference(self.settings, path)

    def test_reference_limit_is_explicit(self):
        people = []
        with closing(sqlite3.connect(self.db)) as conn, conn:
            for index in range(5):
                name = f'Person {index}'
                file = self.image.parent / f'{index}.png'
                Image.new('RGB', (32, 32), 'red').save(file)
                conn.execute('INSERT INTO notes VALUES(?,?,?,?)', (f'{index}.md', name, '[]', json.dumps({'race': 'Nonhuman', 'thumbnail': f'zz_media/{index}.png'})))
                people.append({'name': name})
            conn.execute('UPDATE game_sessions SET narrative_json=?', (json.dumps({'participants': people}),))
        context = resolve_asset_context(self.settings, self.job)
        self.assertEqual(len(context['references']), 4)
        self.assertTrue(any('excede' in warning for warning in context['warnings']))

    def test_provider_sends_reference_bytes_without_modifying_original(self):
        before = self.image.read_bytes()
        response = httpx.Response(200, content=before, headers={'content-type': 'image/png'})
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = response
            FluxKleinProvider().generate('reference', self.root / 'out.png', references=[self.image])
            files = client.return_value.__enter__.return_value.post.call_args.kwargs['files']
            self.assertIn('input_image_0', files)
            from io import BytesIO
            with Image.open(BytesIO(files['input_image_0'][1])) as thumb:
                self.assertLess(max(thumb.size), 512)
        self.assertEqual(before, self.image.read_bytes())
