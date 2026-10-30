"""Plan or explicitly enqueue transcript windows into the native PRIVATE queue."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai_workshop_sources import source_tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--allow-root', action='append', type=Path, required=True)
    parser.add_argument('--db', type=Path)
    parser.add_argument('--enqueue', action='store_true', help='Explicit private queue writes only')
    args = parser.parse_args()
    if args.enqueue:
        if args.db is None:
            parser.error('--enqueue requires a private --db')
        target = args.db.resolve()
        runtime = (ROOT / '.autonomy/runtime').resolve()
        if (not runtime.is_relative_to(ROOT) or not target.is_relative_to(runtime)
                or target.suffix != '.sqlite3'
                or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                       for p in (args.db.absolute(), *args.db.absolute().parents))):
            parser.error('Queue DB must remain in private .autonomy/runtime')
        from app.ai_workshop import enqueue_job
    index = json.loads(args.index.read_text(encoding='utf-8'))
    counts = {}
    queued = 0
    for task in source_tasks(index, args.allow_root):
        number = task['payload']['facts'][0]['session_number']
        counts[number] = counts.get(number, 0) + 1
        if args.enqueue:
            fingerprint = json.dumps(['sources-v1', task['entity_id'], task['revision'], task['purpose']])
            request_id = 'sources:' + hashlib.sha256(fingerprint.encode()).hexdigest()
            enqueue_job(args.db, request_id=request_id, **task)
            queued += 1
    print(json.dumps({'windows': sum(counts.values()), 'by_session': counts,
                      'native_enqueue_receipts': queued, 'generations_dispatched': 0,
                      'campaign_mutated': False, 'note': 'planning/queueing is not generation'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
