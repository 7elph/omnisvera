from __future__ import annotations

import base64
import os
from io import BytesIO
from pathlib import Path
from typing import Protocol

class CloudflareProvider:
    def generate(self, prompt: str, output_path: Path, references: list[Path] | None = None) -> Path:
        raise NotImplementedError

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
    """Real provider for @cf/black-forest-labs/flux-2-klein-4b"""
    def generate(self, prompt: str, output_path: Path, references: list[Path] | None = None) -> Path:
        account_id, token = _load_cloudflare_creds()
        if not account_id or not token:
            raise RuntimeError("CLOUDFLARE_ACCOUNT_ID/TOKEN not configured (env or backend/data/cloudflare.json)")
        import httpx
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-2-klein-4b"
        headers = {"Authorization": f"Bearer {token}"}
        from PIL import Image
        if len(references or []) > 4:
            raise ValueError('O modelo aceita até quatro referências')
        files = {"prompt": (None, prompt)}
        for index, path in enumerate(references or []):
            with Image.open(path) as original:
                picture = original.convert('RGB')
                picture.thumbnail((511, 511))
                buffer = BytesIO()
                picture.save(buffer, format='PNG')
            files[f'input_image_{index}'] = (f'reference_{index}.png', buffer.getvalue(), 'image/png')
        with httpx.Client(timeout=60) as client:
            resp = client.post(url, headers=headers, files=files)
            if resp.is_error:
                raise RuntimeError(f"Cloudflare Workers AI: HTTP {resp.status_code}. Verifique o formato da solicitação, as permissões e a disponibilidade do modelo.")
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
                    raise RuntimeError("Cloudflare retornou uma resposta sem imagem válida; nenhum asset foi salvo.") from exc
            if not (image.startswith(b"\x89PNG\r\n\x1a\n") or image.startswith(b"\xff\xd8\xff") or (image.startswith(b"RIFF") and image[8:12] == b"WEBP")):
                raise RuntimeError("Cloudflare retornou conteúdo que não é uma imagem; nenhum asset foi salvo.")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image)
        return output_path

def get_provider(mock: bool = False) -> CloudflareProvider:
    if mock or os.getenv("OMNISVERA_ASSET_MOCK") == "1":
        return MockProvider()
    return FluxKleinProvider()
