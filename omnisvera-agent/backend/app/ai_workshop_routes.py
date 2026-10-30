"""GM-only projection and explicit private draft review of the existing private preparation queue.

No generation, publication or provider requests. Confirmed review imports hidden GM elements.
Inputs/transcripts, credentials and raw provider records never reach the client.
"""
from pathlib import Path
import os
import sqlite3
from typing import Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel,Field

from . import ai_workshop as workshop


class WorkshopReview(BaseModel):
    decision:Literal['import','reject']
    scene_id:int|None=Field(default=None,gt=0)
    expected_revision:str=Field(min_length=1,max_length=256)
    expected_output_hash:str=Field(pattern=r'^[a-fA-F0-9]{64}$')
    request_id:str=Field(pattern=r'^[A-Za-z0-9._:-]{8,120}$')


def workshop_database_path() -> Path:
    default = Path(__file__).resolve().parents[2] / '.autonomy/runtime/ai-workshop.sqlite3'
    return Path(os.getenv('OMNISVERA_AI_WORKSHOP_DB', str(default))).resolve()


def _card(job: dict) -> dict:
    card = {key: job.get(key) for key in (
        'id', 'queue', 'entity_type', 'entity_id', 'purpose', 'revision',
        'status', 'attempts', 'updated_at')}
    if 'asset_review_status' in job:
        card['asset_review_status'] = job['asset_review_status']
    return card


def _preview(job: dict) -> dict:
    output = job.get('output_json')
    if not isinstance(output, dict):
        return {}
    result = {}
    for key in ('draft', 'provider', 'model','image_path'):
        if isinstance(output.get(key), str):
            result[key] = workshop.scrub_secrets(output[key])[:50000]
    for key in ('facts', 'suggestions', 'questions','quality_notes'):
        values = output.get(key)
        if isinstance(values, list):
            result[key] = [workshop.scrub_secrets(v)[:2000] for v in values[:20] if isinstance(v, str)]
    if type(output.get('asset_job_id')) is int:result['asset_job_id']=output['asset_job_id']
    native_status = job.get('asset_review_status')
    if native_status == 'ignored':
        result['draft'] = 'Imagem ignorada na biblioteca. O resultado original foi preservado para auditoria.'
    elif native_status == 'approved':
        result['draft'] = 'Imagem já aprovada na biblioteca pelo fluxo nativo. Nenhuma nova publicação foi realizada.'
    elif native_status in {'unavailable', 'superseded'}:
        result.pop('asset_job_id', None)
        result.pop('image_path', None)
        result['draft'] = 'O resultado de imagem mudou ou não pôde ser verificado. Confira a biblioteca antes de revisar.'
    return result


def build_workshop_router(workshop_path: Callable, campaign_path: Callable,
                          require_master: Callable) -> APIRouter:
    router = APIRouter(tags=['GM AI workshop'])

    @router.get('/gm/ai-workshop')
    def overview(access: Any = Depends(require_master)):
        path = Path(workshop_path())
        status = workshop.status(path)
        from .workshop_asset_reviews import project_image_reviews, project_counts
        image_jobs = workshop.list_jobs(path, queue='image', limit=1000)
        image_reviews = project_image_reviews(image_jobs, Path(campaign_path()))
        available = workshop.available_memory_mb()
        minimum = workshop.configured_min_free_ram_mb()
        # Prefer actual deliverables over pending windows from long transcripts.
        ready = workshop.list_jobs(path, status='awaiting_approval', limit=24)
        ready = [image_reviews.get(job['id'], job) for job in ready]
        ready = [job for job in ready if job['status'] == 'awaiting_approval'][:12]
        recent = workshop.list_jobs(path, limit=12)
        jobs = {job['id']: image_reviews.get(job['id'], job) for job in [*ready, *recent]}
        from .workshop_execution import configuration
        config=configuration()
        minimum=max(minimum,config['min_free_ram_mb'])
        return {
            'initialized': status['initialized'], 'worker': status['worker'],
            'counts': project_counts(status['counts'], image_jobs, image_reviews), 'stats': status['stats'],
            'table_state': workshop.read_table_state(Path(campaign_path())),
            'admission': {'free_ram_mb': available, 'min_free_ram_mb': minimum,
                          'ram_ok': available is not None and available >= minimum},
            'jobs': [_card(job) for job in jobs.values()],
            'image_generation': bool(config['enabled'] and config['image']), 'code_requires_sandbox': True,
            'automation':{'enabled':config['enabled'],'text':config['text'],'image':config['image'],
                          'code':config['code'],'code_provider':config['code_provider'],
                          'daily_limits':config['daily_limits']},
            'providers':status['providers'],
        }

    @router.get('/gm/ai-workshop/jobs/{job_id}')
    def detail(job_id: int, access: Any = Depends(require_master)):
        if job_id <= 0:
            raise HTTPException(404, 'Bloco não encontrado')
        try:
            job = workshop.get_job(Path(workshop_path()), job_id)
        except (FileNotFoundError, sqlite3.DatabaseError, workshop.WorkshopError):
            raise HTTPException(404, 'Bloco não encontrado') from None
        from .workshop_review import output_hash,review_for_job
        from .workshop_asset_reviews import project_image_reviews
        job = project_image_reviews([job], Path(campaign_path()))[job['id']]
        digest=output_hash(job) if isinstance(job.get('output_json'),dict) else None
        return {**_card(job), 'preview': _preview(job),'output_hash':digest,
                'review':review_for_job(Path(workshop_path()),job_id,output_hash=digest) if digest else None}

    @router.post('/gm/ai-workshop/jobs/{job_id}/review')
    def review(job_id:int,request:WorkshopReview,access:Any=Depends(require_master)):
        from .workshop_review import review_job,ReviewError
        try:
            return review_job(Path(workshop_path()),Path(campaign_path()),job_id,
                **request.model_dump())
        except ReviewError as error:
            code=getattr(error,'code','review_conflict')
            status=404 if code in {'job_not_found','scene_not_found'} else 503 if code=='campaign_unavailable' else 409
            raise HTTPException(status,code) from None
        except (ValueError,workshop.WorkshopError):
            raise HTTPException(409,'Não foi possível revisar este bloco. Atualize a prévia.') from None

    return router
