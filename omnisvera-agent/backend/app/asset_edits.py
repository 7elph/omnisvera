"""Non-destructive, request-idempotent image edits using existing asset jobs."""
import hashlib
import json
from contextlib import closing

from .asset_generation import _connect, _now, get_job, init_asset_generation, update_job_status
from .asset_approval import image_file, validate_image
from .cloudflare_provider import ImageProviderError
from .image_routing import record_image_route


def adjust_image(settings, *, image_path, instruction, request_id, provider, parent_job_id=None, category='map', generation_mode='official'):
    init_asset_generation(settings.database_path)
    identity = [image_path, instruction, parent_job_id, category]
    if generation_mode != 'official':
        identity.append(generation_mode)
    fingerprint = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
    with closing(_connect(settings.database_path)) as conn:
        previous = conn.execute("SELECT * FROM asset_generation_jobs WHERE entity_type='asset_revision' AND entity_id=?", (request_id,)).fetchone()
        if previous:
            if previous['source_hash'] != fingerprint:
                raise ValueError('Requisição já usada para outro ajuste')
            return dict(previous)
    parent = get_job(parent_job_id, settings.database_path) if parent_job_id else None
    if parent_job_id and (not parent or parent['image_path'] != image_path or parent['status'] == 'generating'):
        raise ValueError('A imagem mudou. Atualize a visualização antes de ajustar.')
    source = image_file(settings, {'image_path': image_path})
    validate_image(source)
    # Capture the reference before another process can replace its contents.
    source_bytes = source.read_bytes()
    context = {'base_image_path': image_path, 'parent_job_id': parent_job_id,
               'instruction': instruction, 'reference_suffix': source.suffix,
               'base_sha256': hashlib.sha256(source_bytes).hexdigest()}
    prompt = ('Use case: precise-object-edit. Image 0 is the image to edit, not just inspiration. '
              'Modify only what the user requests; preserve every unmentioned element, identity, '
              'style, materials and composition. Do not add text, watermark, equipment or lore. '
              'Requested adjustment: ' + instruction)
    now = _now()
    with closing(_connect(settings.database_path)) as conn, conn:
        cursor = conn.execute("""INSERT INTO asset_generation_jobs
            (entity_type,entity_id,asset_type,style_version,status,prompt,source_hash,context_json,created_at,updated_at)
            VALUES ('asset_revision',?,?,?,?,?,?,?,?,?)""",
            (request_id, parent['asset_type'] if parent else ('item_art' if category == 'items' else 'image_edit'),
             parent['style_version'] if parent else 'omnisvera.edit.v1', 'generating', prompt, fingerprint,
             json.dumps(context, ensure_ascii=False), now, now))
        job_id = cursor.lastrowid
    folder = settings.database_path.parent / 'asset_drafts'
    folder.mkdir(parents=True, exist_ok=True)
    reference = folder / f'edit_reference_{job_id}{source.suffix}'
    reference.write_bytes(source_bytes)
    output = folder / f'edit_{job_id}.png'
    try:
        provider.generate(prompt, output, references=[reference])
        validate_image(output)
        update_job_status(job_id, 'awaiting_approval', image_path=f'draft:{output.name}', database_path=settings.database_path)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, ImageProviderError) else 'Erro interno ao gerar ou validar a nova imagem.'
        update_job_status(job_id, 'failed', error=f'Ajuste não concluído. A imagem anterior foi preservada. {reason}', database_path=settings.database_path)
    finally:
        record_image_route(settings.database_path, job_id, provider)
    return get_job(job_id, settings.database_path)
