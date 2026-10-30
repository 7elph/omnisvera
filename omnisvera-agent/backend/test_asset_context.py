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

    def test_monster_prompt_includes_catalog_attacks_and_traits_not_just_name(self):
        from app.prompt_builder import build_prompt
        context = resolve_asset_context(self.settings, {
            'entity_type': 'compendium_monster', 'entity_id': 'gorgon', 'asset_type': 'monster_art'})
        prompt = build_prompt('monster_art', 'omnisvera.monster.v1', context['source'])
        self.assertIn('touro', prompt.casefold())
        self.assertIn('carapa', prompt.casefold())
        self.assertIn('Chifre', prompt)
        self.assertIn('Baforada Petrificante', prompt)
        self.assertTrue(context['warnings'])
        self.assertEqual(context['references'], [])

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

    def test_reference_error_never_retries_without_reference(self):
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(400, json={'error': 'reference rejected'})
            with self.assertRaises(RuntimeError):
                FluxKleinProvider().generate('reference', self.root / 'out.png', references=[self.image])
            self.assertEqual(post.call_count, 1)
            self.assertIn('input_image_0', post.call_args.kwargs['files'])
            self.assertFalse((self.root / 'out.png').exists())

    def test_small_reference_is_not_silently_omitted(self):
        Image.new('RGB', (32, 32), 'red').save(self.image)
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = httpx.Response(200, content=self.image.read_bytes(), headers={'content-type': 'image/png'})
            FluxKleinProvider().generate('reference', self.root / 'out.png', references=[self.image])
            self.assertIn('input_image_0', client.return_value.__enter__.return_value.post.call_args.kwargs['files'])

    def test_http_failure_keeps_only_status_and_numeric_codes(self):
        from app.cloudflare_provider import ImageProviderError
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(429, json={'errors': [{'code': 1234, 'message': 'private prompt secret'}, {'code': 'secret'}]})
            with self.assertRaises(ImageProviderError) as caught:
                FluxKleinProvider().generate('private prompt', self.root / 'out.png', [self.image])
            self.assertIn('HTTP 429', str(caught.exception))
            self.assertIn('1234', str(caught.exception))
            self.assertNotIn('secret', str(caught.exception))
            self.assertIn('não foi confirmada', str(caught.exception))
            self.assertEqual(post.call_count, 1)
            self.assertFalse((self.root / 'out.png').exists())

    def test_transport_errors_do_not_leak_request_or_token(self):
        from app.cloudflare_provider import ImageProviderError
        for failure, expected in ((httpx.ReadTimeout('secret URL'), 'tempo limite'), (httpx.ConnectError('secret token'), 'conectar')):
            with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
                client.return_value.__enter__.return_value.post.side_effect = failure
                with self.assertRaises(ImageProviderError) as caught:
                    FluxKleinProvider().generate('private prompt', self.root / 'out.png', [self.image])
                self.assertIn(expected, str(caught.exception))
                self.assertNotIn('secret', str(caught.exception))

    def test_transient_500_retries_once_with_identical_reference_and_model(self):
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.side_effect = [httpx.Response(500, json={'errors':[{'code':3043}]}),
                                httpx.Response(200, content=self.image.read_bytes(), headers={'content-type':'image/png'})]
            FluxKleinProvider().generate('same prompt', self.root / 'out.png', [self.image])
            self.assertEqual(post.call_count, 2)
            first, second = post.call_args_list
            self.assertEqual(first.args, second.args)
            self.assertEqual(first.kwargs['files'], second.kwargs['files'])
            self.assertLessEqual(second.kwargs['timeout'], 180)
            self.assertTrue((self.root / 'out.png').exists())

    def test_persistent_500_stops_after_two_calls(self):
        from app.cloudflare_provider import ImageProviderError
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(500, json={'errors':[{'code':3043}]})
            with self.assertRaises(ImageProviderError):
                FluxKleinProvider().generate('same prompt', self.root / 'out.png', [self.image])
            self.assertEqual(post.call_count, 2)
            self.assertFalse((self.root / 'out.png').exists())

    def test_auth_and_quota_errors_never_retry(self):
        from app.cloudflare_provider import ImageProviderError
        for status in (401,403,429):
            with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
                post = client.return_value.__enter__.return_value.post
                post.return_value = httpx.Response(status, json={'errors':[]})
                with self.assertRaises(ImageProviderError):
                    FluxKleinProvider().generate('same prompt', self.root / 'out.png', [self.image])
                self.assertEqual(post.call_count, 1)

    def test_500_at_timeout_budget_never_starts_second_call(self):
        from app.cloudflare_provider import ImageProviderError
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client, patch('app.cloudflare_provider.time.monotonic', side_effect=[0,180]):
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(500, json={'errors':[]})
            with self.assertRaises(ImageProviderError):
                FluxKleinProvider().generate('same prompt', self.root / 'out.png', [self.image])
            self.assertEqual(post.call_count, 1)

    def test_invalid_reference_blocks_before_network(self):
        self.image.write_bytes(b'not an image')
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            with self.assertRaises(ValueError):
                FluxKleinProvider().generate('reference', self.root / 'out.png', references=[self.image])
            client.assert_not_called()

    def test_9b_is_explicit_and_keeps_reference_and_bounded_timeout(self):
        before = self.image.read_bytes()
        with patch('app.cloudflare_provider._load_cloudflare_creds', return_value=('account','secret')), patch('httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(200, content=before, headers={'content-type':'image/png'})
            FluxKleinProvider(model='flux-2-klein-9b', timeout_seconds=180).generate('same prompt', self.root / '9b.png', [self.image])
            self.assertTrue(post.call_args.args[0].endswith('/flux-2-klein-9b'))
            self.assertEqual(post.call_args.kwargs['files']['prompt'], (None, 'same prompt'))
            self.assertIn('input_image_0', post.call_args.kwargs['files'])
            client.assert_called_once_with(timeout=180)
            self.assertEqual(post.call_count, 1)
        self.assertEqual(self.image.read_bytes(), before)
        self.assertEqual(FluxKleinProvider().model, 'flux-2-klein-9b')

    def test_factory_defaults_to_9b_without_paid_fallback(self):
        from app.cloudflare_provider import get_provider
        with patch.dict('os.environ', {'OMNISVERA_ASSET_MOCK': '0'}):
            provider = get_provider()
        self.assertEqual(provider.model, 'flux-2-klein-9b')
        self.assertEqual(provider.timeout_seconds, 180)
        self.assertEqual(FluxKleinProvider(model='flux-2-klein-4b').model, 'flux-2-klein-4b')

    def test_model_selection_rejects_unknown_targets_and_unbounded_timeout(self):
        with patch('httpx.Client') as client:
            for model in ('flux-2-max', '../other-model', 'unknown'):
                with self.assertRaises(ValueError): FluxKleinProvider(model=model)
            for timeout in (0, 301, float('inf'), float('nan')):
                with self.assertRaises(ValueError): FluxKleinProvider(timeout_seconds=timeout)
            client.assert_not_called()
