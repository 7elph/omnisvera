"""Read-only projection of native image reviews, never a second approval path."""
from contextlib import closing
import hashlib
from pathlib import Path
import re
import sqlite3


def _same_approved_draft(campaign_path, asset, output):
    original = str(output.get('image_path') or '')
    approved = re.fullmatch(r'zz_media/ui/icons/approved/asset_' + str(asset['id']) + r'_([a-f0-9]{24})\.png',
                            str(asset['image_path'] or ''))
    if not approved:
        return False
    if original == asset['image_path']:
        return True
    if not original.startswith('draft:'):
        return False
    # Approval changes the path; match the original bytes against its native digest.
    # A regenerated image under the same asset ID is not the previous result.
    try:
        root = (Path(campaign_path).parent / 'asset_drafts').resolve()
        source = (root / original[6:]).resolve()
        if not source.is_relative_to(root) or not source.is_file() or source.stat().st_size > 25_000_000:
            return False
        digest = hashlib.sha256()
        size = 0
        with source.open('rb') as stream:
            for chunk in iter(lambda: stream.read(262144), b''):
                size += len(chunk)
                if size > 25_000_000:
                    return False
                digest.update(chunk)
        return digest.hexdigest()[:24] == approved.group(1)
    except (OSError, ValueError, RuntimeError):
        return False


def project_image_reviews(jobs, campaign_path):
    """Return detached DTOs; neither the workshop nor campaign is written.

    Only completed image outputs can acquire a native review projection. Match
    entity and source hash as well as the numeric ID; stale/reused references
    require review instead of attributing a different generation's approval.
    """
    projected = {job['id']: dict(job) for job in jobs}
    candidates = []
    for job in jobs:
        if job.get('queue') != 'image' or job.get('status') not in {'awaiting_approval', 'needs_review', 'external_pending'}:
            continue
        output = job.get('output_json') or {}
        identity = output.get('asset_job_id') if isinstance(output, dict) else None
        reference = re.fullmatch(r'asset_generation_jobs:([1-9][0-9]*)', str(job.get('external_ref') or ''))
        if not reference or (identity is not None and (type(identity) is not int or identity != int(reference.group(1)))):
            projected[job['id']].update(status='needs_review', asset_review_status='unavailable')
            continue
        candidates.append((job, int(reference.group(1))))
    if not candidates:
        return projected
    assets = {}
    try:
        with closing(sqlite3.connect(Path(campaign_path).resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
            db.row_factory = sqlite3.Row
            for job, identity in candidates:
                row = db.execute('SELECT id,entity_type,entity_id,status,image_path,source_hash '
                                 'FROM asset_generation_jobs WHERE id=?', (identity,)).fetchone()
                if row:
                    assets[identity] = dict(row)
    except (OSError, sqlite3.DatabaseError):
        pass
    for job, identity in candidates:
        result = projected[job['id']]
        output, payload = job.get('output_json') or {}, job.get('payload_json') or {}
        asset = assets.get(identity)
        if (not isinstance(output, dict) or not isinstance(payload, dict) or not asset
                or asset['entity_type'] != (payload.get('entity_type') or job['entity_type'])
                or str(asset['entity_id']) != str(payload.get('entity_id') or job['entity_id'])
                or not payload.get('source_hash') or asset['source_hash'] != payload['source_hash']):
            result.update(status='needs_review', asset_review_status='unavailable')
        elif asset['status'] == 'ignored':
            result.update(status='cancelled', asset_review_status='ignored')
        elif asset['status'] == 'approved' and _same_approved_draft(campaign_path, asset, output):
            result.update(status='completed', asset_review_status='approved')
        elif (asset['status'] in {'awaiting_approval', 'ready'}
              and output.get('image_path') == asset['image_path']):
            result['asset_review_status'] = asset['status']
        elif (asset['status'] in {'queued', 'generating'} and job['status'] == 'external_pending'
              and not output.get('image_path')):
            result['asset_review_status'] = asset['status']
        else:
            result.update(status='needs_review', asset_review_status='superseded')
    return projected


def project_counts(counts, original, projected):
    result = {queue: dict(values) for queue, values in counts.items()}
    for job in original:
        status = projected[job['id']]['status']
        if status != job['status']:
            bucket = result.setdefault(job['queue'], {})
            if bucket.get(job['status'], 0) > 0:
                bucket[job['status']] -= 1
                bucket[status] = bucket.get(status, 0) + 1
    return result
