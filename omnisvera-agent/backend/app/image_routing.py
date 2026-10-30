"""Official 9B -> independent ZeroGPU; explicit 4B test never silently upgrades."""
from contextlib import closing
import json
from .cloudflare_provider import FluxKleinProvider, ImageProviderError
from .zerogpu_provider import ZeroGPUProvider, SPACE


class RoutedImageProvider:
    def __init__(self, mode='official'):
        if mode not in ('official', 'test'):
            raise ValueError('Modo de imagem inválido')
        self.mode = mode
        self.model = 'flux-2-klein-4b' if mode == 'test' else 'flux-2-klein-9b'
        self.timeout_seconds = 180
        self.last_run = {'mode': mode, 'requested_model': self.model, 'used_provider': None, 'fallback_used': False}

    def generate(self, prompt, output_path, references=None):
        try:
            result = FluxKleinProvider(model=self.model).generate(prompt, output_path, references)
            self.last_run['used_provider'] = 'cloudflare'
            return result
        except ImageProviderError as exc:
            if self.mode == 'test' or exc.reason not in ('daily_quota', 'capacity', 'upstream'):
                raise
            self.last_run.update(fallback_used=True, fallback_reason=exc.reason, fallback_space=SPACE)
            try:
                result = ZeroGPUProvider().generate(prompt, output_path, references)
                self.last_run['used_provider'] = 'huggingface_zerogpu'
                return result
            except ImageProviderError as fallback_error:
                self.last_run['fallback_error_reason'] = fallback_error.reason
                raise ImageProviderError(f'{exc} Fallback: {fallback_error}', reason=fallback_error.reason) from fallback_error


def record_image_route(database_path, job_id, provider):
    route = getattr(provider, 'last_run', None)
    if not isinstance(route, dict):
        return
    from .asset_generation import _connect
    with closing(_connect(database_path)) as conn, conn:
        row = conn.execute('SELECT context_json FROM asset_generation_jobs WHERE id=?', (job_id,)).fetchone()
        context = json.loads(row[0] or '{}')
        context['generation'] = route
        conn.execute('UPDATE asset_generation_jobs SET context_json=? WHERE id=?', (json.dumps(context, ensure_ascii=False), job_id))
