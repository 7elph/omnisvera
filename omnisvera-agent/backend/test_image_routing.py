import unittest
import tempfile
import json
from pathlib import Path
from io import BytesIO
from unittest.mock import patch
import httpx
from PIL import Image
from app.cloudflare_provider import ImageProviderError
from app.image_routing import RoutedImageProvider
from app.zerogpu_provider import ZeroGPUProvider, BASE_URL


class RoutingTests(unittest.TestCase):
    def test_official_quota_preserves_prompt_and_references_in_one_fallback(self):
        with patch('app.image_routing.FluxKleinProvider') as cf, patch('app.image_routing.ZeroGPUProvider') as hf:
            cf.return_value.generate.side_effect = ImageProviderError('quota', reason='daily_quota')
            hf.return_value.generate.return_value = Path('output.png')
            provider = RoutedImageProvider()
            provider.generate('precise edit', Path('output.png'), [Path('reference.png')])
            cf.assert_called_once_with(model='flux-2-klein-9b')
            hf.return_value.generate.assert_called_once_with('precise edit', Path('output.png'), [Path('reference.png')])
            self.assertEqual(provider.last_run['used_provider'], 'huggingface_zerogpu')

    def test_test_mode_and_unknown_auth_timeout_do_not_fallback(self):
        for mode, reason in [('test', 'daily_quota'), ('official', 'unknown'), ('official', 'timeout')]:
            with self.subTest(mode=mode, reason=reason), patch('app.image_routing.FluxKleinProvider') as cf, patch('app.image_routing.ZeroGPUProvider') as hf:
                cf.return_value.generate.side_effect = ImageProviderError('safe error', reason=reason)
                with self.assertRaises(ImageProviderError):
                    RoutedImageProvider(mode).generate('prompt', Path('output.png'))
                hf.assert_not_called()
                cf.assert_called_once_with(model='flux-2-klein-4b' if mode == 'test' else 'flux-2-klein-9b')

    def test_capacity_and_upstream_fallback_but_no_recursive_retries(self):
        for reason in ['capacity', 'upstream']:
            with patch('app.image_routing.FluxKleinProvider') as cf, patch('app.image_routing.ZeroGPUProvider') as hf:
                cf.return_value.generate.side_effect = ImageProviderError('primary', reason=reason)
                hf.return_value.generate.side_effect = ImageProviderError('fallback quota')
                with self.assertRaisesRegex(ImageProviderError, 'Fallback: fallback quota'):
                    RoutedImageProvider().generate('prompt', Path('output.png'))
                hf.return_value.generate.assert_called_once()


class ZeroGPUTests(unittest.TestCase):
    def run_provider(self, *, external=False, queue_error=False, reject_upload=False):
        self.calls = []
        self.data = None
        buffer = BytesIO()
        Image.new('RGB', (32, 32), 'blue').save(buffer, format='PNG')
        def handler(request):
            self.calls.append(str(request.url))
            path = request.url.path
            if path.endswith('/upload'):
                self.assertIn(b'reference_0.png', request.content)
                return httpx.Response(200, json=[] if reject_upload else ['/tmp/gradio/ref.png'])
            if path.endswith('/config'):
                return httpx.Response(200, json={'dependencies': [{'id': 6, 'api_name': 'generate'}]})
            if path.endswith('/queue/join'):
                self.data = json.loads(request.content)['data']
                return httpx.Response(200, json={'event_id': 'fixture-event'})
            if path.endswith('/queue/data'):
                if queue_error:
                    error = 'You have exceeded your ZeroGPU quota (85s requested vs. 73s left). Try again in 22:17:09. secret-token'
                    return httpx.Response(200, text='data: ' + json.dumps({'msg':'process_completed', 'success':False,'output':{'error':error}}) + '\n\n')
                url = 'https://evil.example/image.png' if external else BASE_URL + '/gradio_api/file=/tmp/gradio/output.png'
                return httpx.Response(200, text='data: ' + json.dumps({'msg':'process_completed','success':True,'output':{'data':[{'url':url},42]}}) + '\n\n')
            return httpx.Response(200, content=buffer.getvalue())
        real_client = httpx.Client
        with tempfile.TemporaryDirectory() as folder:
            ref, output = Path(folder) / 'private-name.png', Path(folder) / 'out.png'
            Image.new('RGB', (32, 48), 'red').save(ref)
            original = ref.read_bytes()
            with patch('app.zerogpu_provider.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)):
                if external or queue_error or reject_upload:
                    with self.assertRaises(ImageProviderError) as caught:
                        ZeroGPUProvider().generate('edit fixture', output, [ref])
                    self.assertNotIn('secret-token', str(caught.exception))
                    if queue_error:
                        self.assertIn('85s', str(caught.exception))
                        self.assertIn('73s', str(caught.exception))
                        self.assertIn('22:17:09', str(caught.exception))
                    self.assertFalse(output.exists())
                else:
                    ZeroGPUProvider().generate('edit fixture', output, [ref])
                    with Image.open(output) as image:
                        self.assertEqual(image.size, (32, 32))
                    self.assertEqual(self.data[0], 'edit fixture')
                    self.assertEqual(len(self.data[1]), 1)
                    self.assertEqual(self.data[2], 'Distilled (4 steps)')
                    self.assertFalse(self.data[-1], 'No paid VLM prompt upsampling')
                self.assertEqual(ref.read_bytes(), original)
                self.assertTrue(all(url.startswith(BASE_URL) for url in self.calls))
    def test_reference_upload_call_sse_and_image_download(self):
        self.run_provider()
    def test_external_download_is_blocked(self):
        self.run_provider(external=True)
    def test_space_quota_is_sanitized_and_original_preserved(self):
        self.run_provider(queue_error=True)
    def test_rejected_reference_never_falls_back_to_text_only(self):
        self.run_provider(reject_upload=True)
