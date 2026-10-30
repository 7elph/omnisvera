from __future__ import annotations

import os
import threading
import uuid
import json
from typing import Literal
from contextlib import closing

from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .access import AccessContext
from .asset_generation import list_jobs, queue_missing_assets, scan_eligible_gaps, update_job_status, get_job, _connect
from .asset_approval import approve_job, image_file, validate_image
from .config import get_settings
from .prompt_builder import build_prompt
from .cloudflare_provider import get_provider, ImageProviderError
from .image_routing import record_image_route
from .asset_context import resolve_asset_context, reference_instructions, media_reference

_generation_lock = threading.Lock()


class AssetApproval(BaseModel):
    image_path: str


class AssetGenerationOptions(BaseModel):
    generation_mode: Literal['official', 'test'] = 'official'


class AssetAdjustment(BaseModel):
    image_path: str = Field(min_length=1, max_length=500)
    instruction: str = Field(min_length=1, max_length=2000)
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')
    parent_job_id: int | None = Field(default=None, gt=0)
    category: Literal['map', 'items'] = 'map'
    generation_mode: Literal['official', 'test'] = 'official'


class AssetQueueProcess(BaseModel):
    mode: Literal['official', 'test'] = 'test'
    limit: int = Field(default=5, ge=1, le=25)
    entity_type: str | None = Field(default=None, max_length=40)


def _generate_job(settings, job_id: int, mode: str) -> dict:
    from .asset_generation import get_job as _get_job, update_job_status
    job = _get_job(job_id,database_path=settings.database_path)
    if not job:
        raise HTTPException(404, "Job inexistente")
    context = resolve_asset_context(settings, job)
    if context['blocking']:
        raise HTTPException(409, 'Referências incompletas: ' + '; '.join(context['blocking']))
    prompt = build_prompt(job["asset_type"], job["style_version"], context['source']) + '\n' + reference_instructions(context)
    reference_files = [media_reference(settings, ref['path']) for ref in context['references']]
    with closing(_connect(settings.database_path)) as conn, conn:
        conn.execute('UPDATE asset_generation_jobs SET context_json=?,prompt=? WHERE id=?', (json.dumps(context, ensure_ascii=False), prompt, job_id))
    name = f"{job_id}_{uuid.uuid4().hex}.png"
    output = settings.database_path.parent / "asset_drafts" / name
    with closing(_connect(settings.database_path)) as conn,conn:
        changed=conn.execute("UPDATE asset_generation_jobs SET status='generating',error=NULL WHERE id=? AND status IN ('queued','failed','missing','ready','awaiting_approval','approved')",(job_id,)).rowcount
        if not changed:raise HTTPException(409,'Geração já iniciada ou resultado aguardando revisão')
    provider = None
    try:
        provider = get_provider(mock=os.getenv("OMNISVERA_ASSET_MOCK") == "1", mode=mode)
        if reference_files:
            provider.generate(prompt, output, references=reference_files)
        else:
            provider.generate(prompt, output)
        validate_image(output)
        update_job_status(job_id, "awaiting_approval", image_path=f"draft:{name}",database_path=settings.database_path)
    except Exception as exc:
        message = str(exc)[:500] if isinstance(exc, ImageProviderError) else 'Erro interno ao gerar ou validar a imagem.'
        update_job_status(job_id, "failed", error=message,database_path=settings.database_path)
        raise HTTPException(502, message) from exc
    finally:
        record_image_route(settings.database_path, job_id, provider)
    return get_job(job_id,database_path=settings.database_path)


def _admitted_generation(settings,job_id,mode):
    from scripts.memory_guard import workload_slot
    with workload_slot() as acquired:
        if not acquired:raise HTTPException(409,'Aguarde o trabalho da oficina ou ensaio em andamento')
        return _generate_job(settings,job_id,mode)


def init_asset_api(app, require_master):
    @app.post('/gm/assets/adjust')
    def adjust(request: AssetAdjustment, _: AccessContext = Depends(require_master)):
        if not request.instruction.strip():
            raise HTTPException(422, 'Descreva o ajuste desejado')
        if not _generation_lock.acquire(blocking=False):
            raise HTTPException(409, 'Aguarde a geração em andamento')
        try:
            from .asset_edits import adjust_image
            from scripts.memory_guard import workload_slot
            with workload_slot() as acquired:
                if not acquired:
                    raise HTTPException(409, 'Aguarde o trabalho da oficina ou ensaio em andamento')
                return adjust_image(get_settings(), image_path=request.image_path,
                    instruction=request.instruction.strip(), request_id=request.request_id,
                    parent_job_id=request.parent_job_id, category=request.category,
                    generation_mode=request.generation_mode, provider=get_provider(mode=request.generation_mode))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        finally:
            _generation_lock.release()

    @app.get('/gm/assets/{job_id}/base-preview')
    def base_preview(job_id: int, _: AccessContext = Depends(require_master)):
        job = get_job(job_id)
        if not job or job['entity_type'] != 'asset_revision':
            raise HTTPException(404, 'Versão anterior indisponível')
        # Immutable captured reference, even after later edits to the original.
        context = json.loads(job.get('context_json') or '{}')
        suffix = context['reference_suffix']
        return FileResponse(image_file(get_settings(), {'image_path': f'draft:edit_reference_{job_id}{suffix}'}), headers={'Cache-Control': 'no-store'})

    @app.get("/gm/assets/jobs")
    def list_asset_jobs(_: AccessContext = Depends(require_master), status: str | None = None):
        return list_jobs(status=status)

    @app.post("/gm/assets/scan")
    def scan_assets(_: AccessContext = Depends(require_master)):
        gaps = scan_eligible_gaps()
        queued = queue_missing_assets()
        return {"gaps_found": len(gaps), "queued": len(queued), "gaps": gaps, "queued_jobs": queued}

    @app.get("/gm/assets/{job_id}")
    def get_asset_job(job_id: int, _: AccessContext = Depends(require_master)):
        job = get_job(job_id)
        if not job:
            raise HTTPException(404, "Job inexistente")
        return job

    @app.get("/gm/assets/{job_id}/preview")
    def preview(job_id: int, _: AccessContext = Depends(require_master)):
        job = get_job(job_id)
        if not job:
            raise HTTPException(404, "Job inexistente")
        try:
            return FileResponse(image_file(get_settings(), job), headers={"Cache-Control": "no-store"})
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get('/gm/assets/{job_id}/context')
    def context(job_id: int, _: AccessContext = Depends(require_master)):
        job = get_job(job_id)
        if not job:
            raise HTTPException(404, 'Job inexistente')
        if job['entity_type'] == 'asset_revision':
            return {'references': [{'name': 'Imagem anterior preservada', 'source': 'edit', 'index': 0}],
                    'entities': [], 'warnings': [], 'blocking': []}
        return resolve_asset_context(get_settings(), job)

    @app.post("/gm/assets/{job_id}/approve")
    def approve(job_id: int, request: AssetApproval, _: AccessContext = Depends(require_master)):
        try:
            return approve_job(get_settings(), job_id, request.image_path)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/gm/assets/{job_id}/ignore")
    def ignore_asset_job(job_id: int, _: AccessContext = Depends(require_master)):
        if not _generation_lock.acquire(blocking=False):
            raise HTTPException(409, "Aguarde a geração em andamento")
        try:
            if not get_job(job_id):
                raise HTTPException(404, "Job inexistente")
            update_job_status(job_id, "ignored")
            return get_job(job_id)
        finally:
            _generation_lock.release()

    @app.post("/gm/assets/{job_id}/regenerate")
    def regenerate_asset_job(job_id: int, request: AssetGenerationOptions | None = None, _: AccessContext = Depends(require_master)):
        if not _generation_lock.acquire(blocking=False):
            raise HTTPException(409, "Já existe uma geração em andamento. Aguarde antes de tentar novamente.")
        try:
            return _admitted_generation(get_settings(), job_id, request.generation_mode if request else 'official')
        finally:
            _generation_lock.release()

    @app.post("/gm/assets/process-queue")
    def process_asset_queue(request: AssetQueueProcess | None = None, _: AccessContext = Depends(require_master)):
        mode = request.mode if request else 'test'
        limit = request.limit if request else 5
        entity_type = request.entity_type if request else None
        from .asset_generation import list_jobs
        queued = [job for job in list_jobs(status="queued")
                  if entity_type is None or job["entity_type"] == entity_type][:limit]
        results = []
        for job in queued:
            if not _generation_lock.acquire(blocking=False):
                results.append({"job_id": job["id"], "status": "skipped", "detail": "geração em andamento"})
                continue
            try:
                generated = _admitted_generation(get_settings(), job["id"], mode)
                results.append({"job_id": job["id"], "status": generated["status"], "image_path": generated.get("image_path")})
            except HTTPException as exc:
                results.append({"job_id": job["id"], "status": "failed", "detail": exc.detail})
            finally:
                _generation_lock.release()
        return {"mode": mode, "processed": len(results), "results": results}
