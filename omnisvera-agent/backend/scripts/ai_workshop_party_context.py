"""Plan ONE context-bound transcript revision; --enqueue writes only private queue.

Uses the authenticated loopback Companion roster; never calls a model or prints
tokens, source contents, private fields or generated prose. No campaign writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai_preparation_context import contextual_task
from app import ai_workshop as workshop


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--source-job', type=int, required=True)
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--enqueue', action='store_true')
    args = parser.parse_args()
    runtime = (ROOT / '.autonomy/runtime').resolve()
    target = args.db.resolve()
    if (not runtime.is_relative_to(ROOT) or not target.is_relative_to(runtime)
            or target.suffix != '.sqlite3' or not target.is_file()
            or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                   for p in (args.db.absolute(), *args.db.absolute().parents))):
        parser.error('Existing private .autonomy/runtime queue required')
    if not 1 <= args.port <= 65535:
        parser.error('invalid port')
    credentials = json.loads((ROOT/'backend/data/access_tokens.json').read_text(encoding='utf-8-sig'))
    request = urllib.request.Request(f'http://127.0.0.1:{args.port}/characters',
                                    headers={'X-Omnisvera-Token': credentials['master_token']})
    # No environment proxy or redirects: credentials never leave loopback.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=10) as response:
        roster = json.loads(response.read(256_001))
    task = contextual_task(workshop.get_job(target, args.source_job), roster)
    receipt = workshop.enqueue_job(target, **task) if args.enqueue else None
    print(json.dumps({'source_job': args.source_job, 'revision': task['revision'],
                      'party_members': len(task['payload']['facts'][-1]['members']),
                      'enqueued_job': receipt['job']['id'] if receipt else None,
                      'created': receipt['created'] if receipt else False,
                      'generations_dispatched': 0, 'campaign_mutated': False}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, workshop.WorkshopError):
        raise SystemExit('Context preparation failed; no provider dispatched. Check local roster and private queue.') from None
