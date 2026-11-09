import hashlib
import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from functools import partial
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('serve_preview', PROJECT / 'tools/serve_preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class AssetsTests(unittest.TestCase):
    def test_morthak_original_and_five_complete_rows(self):
        root = PROJECT / 'assets/sprites'
        metadata = json.loads((root / 'morthak.json').read_text())
        self.assertEqual(metadata['character_id'], 'morthak')
        sheet = root / 'morthak-motion.jpg'
        self.assertEqual(hashlib.sha256(sheet.read_bytes()).hexdigest(), metadata['source_sha256'])
        self.assertEqual(len(metadata['animations']), 5)
        self.assertTrue(all(y+h < 500 for x,y,w,h in metadata['animations']['walk_up']['frames']))
        with Image.open(sheet) as image:
            for row, animation in enumerate(metadata['animations'].values()):
                self.assertEqual(len(animation['frames']), 8)
                for column, (x,y,w,h) in enumerate(animation['frames']):
                    self.assertGreaterEqual(x, round(column * image.width / 8))
                    self.assertLessEqual(x+w, round((column+1) * image.width / 8))
                    self.assertGreaterEqual(y, metadata['row_boundaries'][row])
                    self.assertLessEqual(y+h, metadata['row_boundaries'][row+1])

    def test_left_row_does_not_include_next_direction_and_right_keeps_head(self):
        metadata = json.loads((PROJECT / 'assets/sprites/dorn.json').read_text(encoding='utf-8'))
        left = metadata['animations']['walk_left']['frames']
        right = metadata['animations']['walk_right']['frames']
        self.assertTrue(all(y + height < 940 for x, y, width, height in left))
        self.assertTrue(all(y < 970 for x, y, width, height in right))

    def test_original_hashes_alpha_and_all_frame_regions(self):
        root = PROJECT / 'assets/sprites'
        metadata = json.loads((root / 'dorn.json').read_text(encoding='utf-8'))
        self.assertEqual(len(metadata['animations']), 7)
        for name, source in metadata['sources'].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), source['sha256'])
        for animation in metadata['animations'].values():
            with Image.open(root / animation['sheet']) as image:
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.getchannel('A').getextrema(), (0, 255))
                self.assertEqual(len(animation['frames']), 8)
                for x, y, width, height in animation['frames']:
                    self.assertGreater(width, 40)
                    self.assertGreater(height, 80)
                    self.assertLessEqual(x + width, image.width)
                    self.assertLessEqual(y + height, image.height)

    def test_web_shell_consumes_fragment_without_hardcoded_credentials(self):
        shell = (PROJECT / 'index.html').read_text(encoding='utf-8-sig')
        self.assertIn('history.replaceState', shell)
        self.assertIn('location.origin', shell)
        self.assertNotIn('cf01-local', shell)
        self.assertNotIn('localhost:8000', shell)
        preset = (PROJECT / 'export_presets.cfg').read_text(encoding='utf-8-sig')
        self.assertIn('variant/thread_support=false', preset)
        self.assertIn('html/custom_html_shell="res://index.html"', preset)


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        requests = self.requests
        class Backend(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_GET(self):
                requests.append((self.path, self.headers.get('X-Omnisvera-Token')))
                self.send_response(200 if self.headers.get('X-Omnisvera-Token') == 'test-only' else 401)
                self.end_headers()
                self.wfile.write(b'{"status":"fixture"}')
            do_POST = do_GET
        self.backend = ThreadingHTTPServer(('127.0.0.1', 0), Backend)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0),
            partial(preview.Preview, directory=str(PROJECT / 'build/web')))
        self.server.backend = f'http://127.0.0.1:{self.backend.server_port}'
        self.threads = []
        for server in (self.backend, self.server):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)
        self.addCleanup(self.close)

    def close(self):
        for server in (self.server, self.backend):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=2)

    def call(self, path, token='test-only', body=None):
        request = Request(f'http://127.0.0.1:{self.server.server_port}' + path,
            headers={'X-Omnisvera-Token': token}, data=body)
        return urlopen(request, timeout=3)

    def test_reads_use_existing_header_and_force_non_mutating_projection(self):
        with self.call('/characters/dorn7?read_only=false') as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(self.requests, [('/characters/dorn7?read_only=true', 'test-only')])

    def test_credentials_in_query_and_rule_commands_are_rejected(self):
        for path, body, status in [('/health?token=secret', None, 400),
                                   ('/gm/combat/effects', b'{}', 405),
                                   ('/characters/dorn7/actions/unknown', b'{}', 405)]:
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.call(path, body=body)
            self.assertEqual(error.exception.code, status)
            error.exception.close()
        self.assertFalse(self.requests)

    def test_character_actions_preserve_backend_authentication(self):
        path = '/characters/dorn7/actions'
        with self.call(path, body=b'{}') as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as error:
            self.call(path, token='invalid-test', body=b'{}')
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        self.assertEqual(self.requests, [(path + '?read_only=true', 'test-only'),
                                         (path + '?read_only=true', 'invalid-test')])

    def test_invalid_access_stays_invalid(self):
        with self.assertRaises(HTTPError) as error:
            self.call('/characters', token='invalid-test')
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

    def test_map_and_session_reads_keep_native_authorization(self):
        for route in ['/workspace/maps', '/sessions', '/sessions/1', '/scenes', '/scenes/1', '/media/zz_media/test.png?preview_size=128']:
            with self.call(route) as response:
                self.assertEqual(response.status, 200)
        self.assertEqual([path for path, token in self.requests],
            ['/workspace/maps', '/sessions', '/sessions/1', '/scenes', '/scenes/1', '/media/zz_media/test.png?preview_size=128'])
        self.assertTrue(all(token == 'test-only' for path, token in self.requests))

    def test_media_does_not_forward_traversal_or_token_urls(self):
        for route in ['/media/zz_media/%2e%2e/private.png?preview_size=128',
                      '/media/zz_media/image.png?token=secret&preview_size=128',
                      '/media/zz_media/image.png?preview_size=4096']:
            with self.subTest(route=route), self.assertRaises(HTTPError) as error:
                self.call(route)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
        self.assertFalse(self.requests)
