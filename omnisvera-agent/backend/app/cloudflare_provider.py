from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Protocol

class CloudflareProvider:
    def generate(self, prompt: str, output_path: Path, references: list[Path] | None = None) -> Path:
        raise NotImplementedError

class ImageProviderError(RuntimeError):
    """Only fixed, safe diagnostics may cross into persisted asset jobs."""
    def __init__(self, message, *, reason='unknown'):
        super().__init__(message)
        self.reason = reason

def _http_error(response):
    codes = []
    daily_quota = False
    try:
        payload = response.json()
        for error in payload.get('errors', []) if isinstance(payload, dict) else []:
            code = error.get('code') if isinstance(error, dict) else None
            if type(code) is int and 0 <= code <= 999999:
                codes.append(str(code))
                message = error.get('message', '')
                # 4006 was observed with this explicit upstream explanation.
                # Do not classify every 429/4006 as quota or persist raw text.
                if code == 3036 or (code == 4006 and isinstance(message, str)
                        and 'you have used up your daily free allocation of 10,000 neurons' in message.lower()):
                    daily_quota = True
    except (ValueError, TypeError):
        pass
    suffix = (' · código ' + ', '.join(codes[:3])) if codes else ''
    if response.status_code == 429 and daily_quota:
        return ImageProviderError(f'Cloudflare Workers AI: HTTP 429{suffix}. '
                                  'Franquia gratuita diária de 10.000 neurônios esgotada, confirmada pelo provider. '
                                  'Renova às 21h de Brasília (00:00 UTC). Nenhuma troca de modelo libera a cota compartilhada.', reason='daily_quota')
    return ImageProviderError(f'Cloudflare Workers AI: HTTP {response.status_code}{suffix}. '
                              'O provider recusou a geração; a causa não foi confirmada como limite diário.',
                              reason='upstream' if response.status_code >= 500 else 'capacity' if '3040' in codes else 'unknown')

class MockProvider(CloudflareProvider):
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls: list[str] = []
    def generate(self, prompt: str, output_path: Path, references: list[Path] | None = None) -> Path:
        self.calls.append(prompt)
        if self.fail:
            raise RuntimeError("mock failure")
        # Create a minimal PNG placeholder (1x1)
        # Use base64 for a valid PNG
        png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
        data = base64.b64decode(png_b64)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        return output_path

def _load_cloudflare_creds() -> tuple[str | None, str | None]:
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token = os.getenv("CLOUDFLARE_WORKERS_AI_TOKEN")
    if account_id and token:
        return account_id, token
    # Fallback to backend/data/cloudflare.json (gitignored, same pattern as access_tokens.json)
    try:
        # backend/app/cloudflare_provider.py -> backend -> data/cloudflare.json
        data_path = Path(__file__).resolve().parents[1] / "data" / "cloudflare.json"
        if data_path.exists():
            import json as _json
            data = _json.loads(data_path.read_text(encoding="utf-8"))
            return data.get("account_id") or data.get("CLOUDFLARE_ACCOUNT_ID"), data.get("token") or data.get("CLOUDFLARE_WORKERS_AI_TOKEN")
    except Exception:
        pass
    return account_id, token

class FluxKleinProvider(CloudflareProvider):
    """Klein provider; explicit per-instance selection preserves the default."""
    def __init__(self, model: str = 'flux-2-klein-9b', timeout_seconds: float = 180):
        if model not in ('flux-2-klein-4b', 'flux-2-klein-9b'):
            raise ValueError('Modelo Klein não suportado; nenhum fallback automático')
        if not 1 <= timeout_seconds <= 300:
            raise ValueError('Timeout deve estar entre 1 e 300 segundos')
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, output_path: Path, references: list[Path] | None = None) -> Path:
        account_id, token = _load_cloudflare_creds()
        if not account_id or not token:
            raise ImageProviderError('Workers AI não configurado: credenciais ausentes.')
        import httpx
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/{self.model}"
        headers = {"Authorization": f"Bearer {token}"}
        from PIL import Image
        if len(references or []) > 4:
            raise ValueError('O modelo aceita até quatro referências')
        usable_refs: list[Path] = []
        for path in references or []:
            try:
                with Image.open(path) as probe:
                    probe.verify()
                usable_refs.append(path)
            except Exception as exc:
                raise ValueError('Referência inválida; geração cancelada para preservar a identidade visual') from exc
        files = {"prompt": (None, prompt)}
        for index, path in enumerate(usable_refs):
            with Image.open(path) as original:
                picture = original.convert('RGB')
                picture.thumbnail((511, 511))
                buffer = BytesIO()
                picture.save(buffer, format='PNG')
            files[f'input_image_{index}'] = (f'reference_{index}.png', buffer.getvalue(), 'image/png')
        with httpx.Client(timeout=self.timeout_seconds) as client:
            started = time.monotonic()
            try:
                resp = client.post(url, headers=headers, files=files)
                # A received 5xx can be transient (identical real request later
                # succeeded). Retry once, with the same reference and model.
                # Do not retry ambiguous timeouts, quota or authorization errors.
                if 500 <= resp.status_code <= 599:
                    remaining = self.timeout_seconds - (time.monotonic() - started)
                    if remaining > 1:
                        resp = client.post(url, headers=headers, files=files, timeout=remaining)
            except httpx.TimeoutException as exc:
                raise ImageProviderError('Workers AI não respondeu dentro do tempo limite.') from exc
            except httpx.TransportError as exc:
                raise ImageProviderError('Não foi possível conectar ao Workers AI.') from exc
            # Never silently drop identity references and retry text-only.
            if resp.is_error:
                raise _http_error(resp)
            # Response may be binary image or JSON with image
            content_type = resp.headers.get("content-type", "")
            if "image" in content_type:
                image = resp.content
            else:
                # Try JSON with base64
                try:
                    data = resp.json()
                    # Cloudflare returns result as binary or base64?
                    # Fallback: if result is base64 string
                    if isinstance(data.get("result"), str):
                        image = base64.b64decode(data["result"], validate=True)
                    elif isinstance(data.get("result"), dict) and "image" in data["result"]:
                        image = base64.b64decode(data["result"]["image"], validate=True)
                    else:
                        raise ValueError("Resposta sem imagem")
                except (ValueError, TypeError, KeyError) as exc:
                    raise ImageProviderError("Cloudflare retornou uma resposta sem imagem válida; nenhum asset foi salvo.") from exc
            if not (image.startswith(b"\x89PNG\r\n\x1a\n") or image.startswith(b"\xff\xd8\xff") or (image.startswith(b"RIFF") and image[8:12] == b"WEBP")):
                raise ImageProviderError("Cloudflare retornou conteúdo que não é uma imagem; nenhum asset foi salvo.")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image)
        return output_path

def get_provider(mock: bool = False, mode: str = 'official') -> CloudflareProvider:
    if mock or os.getenv("OMNISVERA_ASSET_MOCK") == "1":
        return MockProvider()
    from .image_routing import RoutedImageProvider
    return RoutedImageProvider(mode)
