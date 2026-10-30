import tempfile
import unittest
from pathlib import Path
from PIL import Image
from types import SimpleNamespace
from unittest.mock import patch

from app.image_previews import preview_file, resolve_app_art


class ImagePreviewTests(unittest.TestCase):
    def test_preview_is_small_cached_and_original_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / 'item.png'
            with Image.new('RGBA', (1500, 1200), (130, 20, 50, 180)) as image:
                image.save(source)
            original = source.read_bytes()
            result = preview_file(source, 128, cache_root=root / 'cache')
            self.assertEqual(source.read_bytes(), original)
            with Image.open(result) as image:
                self.assertEqual(image.format, 'WEBP')
                self.assertEqual(image.size, (128, 102))
                self.assertIn('A', image.getbands())
            self.assertLess(result.stat().st_size, len(original) // 5)
            self.assertEqual(preview_file(source, 128, cache_root=root / 'cache'), result)

    def test_source_revision_changes_cache_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'item.png'
            with Image.new('RGB', (800, 600), 'red') as image:image.save(source)
            old=preview_file(source,128,cache_root=root/'cache')
            with Image.new('RGB', (900, 600), 'blue') as image:image.save(source)
            self.assertNotEqual(preview_file(source,128,cache_root=root/'cache'),old)

    def test_svg_and_unsupported_sizes_do_not_decode_or_replace_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'item.svg';source.write_text('<svg/>')
            self.assertEqual(preview_file(source,128,cache_root=root/'cache'),source)
            with self.assertRaises(ValueError):preview_file(source,999,cache_root=root/'cache')

    def test_app_asset_resolution_rejects_escape_and_vault_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'item.png').write_bytes(b'fixture')
            self.assertEqual(resolve_app_art('companion-assets/item.png',root),root/'item.png')
            for path in ['companion-assets/../outside.png','zz_media/item.png','companion-assets/C:/private.png']:
                self.assertIsNone(resolve_app_art(path,root))

    def test_authenticated_media_route_keeps_original_and_preview_separate(self):
        from app import main
        from fastapi.testclient import TestClient
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'zz_media').mkdir()
            with Image.new('RGB',(1200,900),'green') as image:image.save(root/'zz_media/item.png')
            client=TestClient(main.app)
            try:
                with patch.object(main,'settings',SimpleNamespace(vault_path=root,master_token='fixture-master',player_token='fixture-player')), patch.object(main,'_individual_player',return_value=None):
                    self.assertEqual(client.get('/media/zz_media/item.png?preview_size=128').status_code,401)
                    original=client.get('/media/zz_media/item.png?token=fixture-master')
                    preview=client.get('/media/zz_media/item.png?preview_size=128&token=fixture-player')
                    self.assertEqual((original.status_code,preview.status_code),(200,200))
                    self.assertEqual(original.headers['content-type'],'image/png')
                    self.assertEqual(preview.headers['content-type'],'image/webp')
                    self.assertTrue(preview.headers['cache-control'].startswith('private'))
                    self.assertLess(len(preview.content),len(original.content))
                    self.assertEqual(client.get('/media/zz_media/item.png?preview_size=999&token=fixture-master').status_code,400)
            finally:
                client.close()
