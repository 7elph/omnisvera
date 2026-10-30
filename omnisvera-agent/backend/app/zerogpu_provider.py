"""Fixed official BFL Space; Gradio upload/call/SSE, no paid API or prompt rewrite."""
import json
import os
import re
import time
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image
from .cloudflare_provider import ImageProviderError

SPACE = 'black-forest-labs/FLUX.2-klein-9B'
BASE_URL = 'https://black-forest-labs-flux-2-klein-9b.hf.space'


class ZeroGPUProvider:
    def __init__(self, timeout_seconds=180):
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, output_path: Path, references=None):
        if len(references or []) > 4:
            raise ValueError('O fallback aceita até quatro referências')
        # Validate all files before contacting the remote service.
        uploads = []
        width = height = 1024
        for index, path in enumerate(references or []):
            with Image.open(path) as image:
                image.load()
                if index == 0:
                    scale = 1024 / max(image.size)
                    width, height = [max(256, min(1024, round(n * scale / 8) * 8)) for n in image.size]
                picture = image.convert('RGB')
                picture.thumbnail((1024, 1024))
                buffer = BytesIO()
                picture.save(buffer, format='PNG')
                uploads.append(('files', (f'reference_{index}.png', buffer.getvalue(), 'image/png')))
        deadline = time.monotonic() + self.timeout_seconds
        token = os.getenv('OMNISVERA_HF_TOKEN', '')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        def remaining():
            left = deadline - time.monotonic()
            if left <= 0:
                raise ImageProviderError('ZeroGPU: tempo de fila/geração esgotado. Nenhuma repetição automática.', reason='timeout')
            return left
        def ensure_ok(response):
            if response.is_error:
                raise ImageProviderError(f'ZeroGPU: HTTP {response.status_code}. Verifique disponibilidade, autenticação ou cota do Space.')
        try:
            with httpx.Client(headers=headers, timeout=self.timeout_seconds, follow_redirects=False) as client:
                gallery = []
                if uploads:
                    upload = client.post(BASE_URL + '/gradio_api/upload', files=uploads, timeout=remaining())
                    ensure_ok(upload)
                    paths = upload.json()
                    if not isinstance(paths, list) or len(paths) != len(uploads) or not all(isinstance(p, str) and p.startswith('/tmp/gradio/') and '..' not in p for p in paths):
                        raise ImageProviderError('ZeroGPU: referências não foram aceitas. Ajuste cancelado, sem geração somente por texto.')
                    gallery = [{'image': {'path': p, 'meta': {'_type': 'gradio.FileData'}, 'orig_name': f'reference_{i}.png'}} for i, p in enumerate(paths)]
                config_response = client.get(BASE_URL + '/config', timeout=remaining())
                ensure_ok(config_response)
                functions = [item['id'] for item in config_response.json().get('dependencies', []) if item.get('api_name') == 'generate']
                if len(functions) != 1 or not isinstance(functions[0], int):
                    raise ImageProviderError('ZeroGPU: contrato de geração indisponível.')
                session = uuid.uuid4().hex
                call = client.post(BASE_URL + '/gradio_api/queue/join', timeout=remaining(), json={
                    'fn_index': functions[0], 'session_hash': session,
                    'data': [prompt, gallery, 'Distilled (4 steps)', 42, False, width, height, 4, 1.0, False]})
                ensure_ok(call)
                event_id = call.json().get('event_id', '')
                if not isinstance(event_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', event_id):
                    raise ImageProviderError('ZeroGPU: resposta de fila inválida.')
                result = None
                # The convenience /call API discards the actual error as data:null.
                # Native queue events retain quota/runtime errors for diagnosis.
                with client.stream('GET', BASE_URL + '/gradio_api/queue/data', params={'session_hash': session}, timeout=remaining()) as stream:
                    ensure_ok(stream)
                    for line in stream.iter_lines():
                        remaining()
                        if not line.startswith('data:'):
                            continue
                        update = json.loads(line[5:])
                        if update.get('msg') not in ('process_completed', 'unexpected_error'):
                            continue
                        output = update.get('output') or {}
                        if update.get('success') is not True:
                            detail = str(output.get('error') or update.get('message') or '')
                            if 'quota' in detail.lower() and ('exceeded' in detail.lower() or 'left' in detail.lower()):
                                reservation = re.search(r'(\d+)s requested vs\. (\d+)s left', detail)
                                renewal = re.search(r'Try again in (\d{1,3}:\d{2}:\d{2})', detail)
                                info = f' Reserva exigida: {reservation[1]}s; saldo: {reservation[2]}s.' if reservation else ''
                                info += f' Provider informa tentar novamente em {renewal[1]}.' if renewal else ''
                                raise ImageProviderError('ZeroGPU: cota própria insuficiente.' + info + ' Autentique com token Hugging Face ou aguarde; não há fallback pago.', reason='daily_quota')
                            error_class = detail if detail in ('RuntimeError', 'ValueError', 'TypeError') else 'erro interno não detalhado'
                            raise ImageProviderError(f'ZeroGPU: falha na execução remota ({error_class}). A imagem anterior foi preservada.', reason='remote_runtime')
                        result = output.get('data')
                        break
                if not isinstance(result, list) or not result or not isinstance(result[0], dict):
                    raise ImageProviderError('ZeroGPU: fila encerrou sem imagem válida.')
                url = result[0].get('url', '')
                parsed = urlparse(url)
                if parsed.scheme != 'https' or parsed.netloc != urlparse(BASE_URL).netloc or not parsed.path.startswith('/gradio_api/file='):
                    raise ImageProviderError('ZeroGPU: endereço da imagem inválido; download bloqueado.')
                content = bytearray()
                with client.stream('GET', url, timeout=remaining()) as download:
                    ensure_ok(download)
                    for chunk in download.iter_bytes():
                        remaining()
                        content.extend(chunk)
                        if len(content) > 20_000_000:
                            raise ImageProviderError('ZeroGPU: imagem excede o limite de download.')
                with Image.open(BytesIO(content)) as image:
                    image.load()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(output_path, format='PNG')
                return output_path
        except ImageProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise ImageProviderError('ZeroGPU: tempo de fila/geração esgotado; a tarefa remota pode continuar, não repita automaticamente.', reason='timeout') from exc
        except httpx.TransportError as exc:
            raise ImageProviderError('ZeroGPU: falha de conexão. Nenhuma repetição automática.') from exc
        except (ValueError, TypeError, KeyError, OSError) as exc:
            raise ImageProviderError('ZeroGPU: resposta ou imagem inválida. A imagem anterior foi preservada.') from exc
