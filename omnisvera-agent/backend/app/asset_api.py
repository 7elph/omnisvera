from __future__ import annotations

import os
import threading
import uuid
import json
from contextlib import closing

from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .access import AccessContext
from .asset_generation import list_jobs, queue_missing_assets, scan_eligible_gaps, update_job_status, get_job, _connect
from .asset_approval import approve_job, image_file, validate_image
from .config import get_settings
from .prompt_builder import build_prompt
from .cloudflare_provider import get_provider
from .asset_context import resolve_asset_context, reference_instructions, media_reference

_generation_lock = threading.Lock()


class AssetApproval(BaseModel):
    image_path: str


def init_asset_api(app, require_master):
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
    def regenerate_asset_job(job_id: int, _: AccessContext = Depends(require_master)):
        if not _generation_lock.acquire(blocking=False):
            raise HTTPException(409, "Já existe uma geração em andamento. Aguarde antes de tentar novamente.")
        try:
            job = get_job(job_id)
            if not job:
                raise HTTPException(404, "Job inexistente")
            settings = get_settings()
            context = resolve_asset_context(settings, job)
            if context['blocking']:
                raise HTTPException(409, 'Referências incompletas: ' + '; '.join(context['blocking']))
            prompt = build_prompt(job["asset_type"], job["style_version"], context['source']) + '\n' + reference_instructions(context)
            reference_files = [media_reference(settings, ref['path']) for ref in context['references']]
            with closing(_connect(settings.database_path)) as conn, conn:
                conn.execute('UPDATE asset_generation_jobs SET context_json=?,prompt=? WHERE id=?', (json.dumps(context, ensure_ascii=False), prompt, job_id))
            name = f"{job_id}_{uuid.uuid4().hex}.png"
            output = settings.database_path.parent / "asset_drafts" / name
            update_job_status(job_id, "generating")
            try:
                provider = get_provider(mock=os.getenv("OMNISVERA_ASSET_MOCK") == "1")
                if reference_files:
                    provider.generate(prompt, output, references=reference_files)
                else:
                    provider.generate(prompt, output)
                validate_image(output)
                update_job_status(job_id, "awaiting_approval", image_path=f"draft:{name}")
                return get_job(job_id)
            except Exception as exc:
                message = str(exc)[:500]
                update_job_status(job_id, "failed", error=message)
                raise HTTPException(502, message) from exc
        finally:
            _generation_lock.release()
