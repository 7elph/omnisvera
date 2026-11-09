"""Third image fallback: Pollinations (public, free, no account or key). Text-to-image only."""
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import httpx
from PIL import Image

from .cloudflare_provider import ImageProviderError

BASE_URL = 'https://image.pollinations.ai/prompt/'


class PollinationsProvider:
    def __init__(self, timeout_seconds=120):
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, output_path: Path, references=None) -> Path:
        # References (edit mode) are not supported here: it only draws from the text.
        url = BASE_URL + quote(prompt[:1500], safe='')
        params = {'width': 1024, 'height': 1024, 'nologo': 'true', 'model': 'flux', 'private': 'true'}
        try:
            response = httpx.get(url, params=params, timeout=self.timeout_seconds, follow_redirects=True)
        except httpx.HTTPError as error:
            raise ImageProviderError(f'Pollinations: sem resposta ({type(error).__name__}).', reason='upstream') from error
        if response.status_code == 429:
            raise ImageProviderError('Pollinations: muitas gerações seguidas; tente em alguns minutos.', reason='capacity')
        if response.is_error or not response.headers.get('content-type', '').startswith('image/'):
            raise ImageProviderError(f'Pollinations: HTTP {response.status_code}.', reason='upstream')
        try:
            with Image.open(BytesIO(response.content)) as picture:
                picture.convert('RGB').save(output_path, format='PNG')
        except Exception as error:  # noqa: BLE001
            raise ImageProviderError('Pollinations: imagem inválida.', reason='upstream') from error
        return Path(output_path)
