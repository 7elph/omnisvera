import base64
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import httpx
from app.cloudflare_provider import FluxKleinProvider


class AssetTransportTests(unittest.TestCase):
    def run_response(self, response, check=None):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "asset.png"
            with patch("app.cloudflare_provider._load_cloudflare_creds", return_value=("account", "secret")), patch("httpx.Client") as client:
                client.return_value.__enter__.return_value.post.return_value = response
                if check:
                    with self.assertRaises(RuntimeError):
                        FluxKleinProvider().generate("potion", output)
                    self.assertFalse(output.exists())
                else:
                    FluxKleinProvider().generate("potion", output)
                    self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))
                kwargs = client.return_value.__enter__.return_value.post.call_args.kwargs
                self.assertEqual(kwargs["files"], {"prompt": (None, "potion")})
                self.assertNotIn("json", kwargs)

    def test_multipart_and_base64(self):
        image = b"\x89PNG\r\n\x1a\n" + b"test"
        self.run_response(httpx.Response(200, json={"result": {"image": base64.b64encode(image).decode()}}))

    def test_error_does_not_save_response_or_leak_credentials(self):
        self.run_response(httpx.Response(400, json={"errors": [{"message": "secret"}]}), check=True)

    def test_json_without_image_is_not_saved_as_png(self):
        self.run_response(httpx.Response(200, json={"result": {}}), check=True)

    def test_invalid_image_is_rejected(self):
        self.run_response(httpx.Response(200, json={"result": {"image": base64.b64encode(b"not an image").decode()}}), check=True)
