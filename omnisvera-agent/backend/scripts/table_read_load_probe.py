"""Read-only 4-role load rehearsal on the existing CF-01 localhost:8871 fixture."""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from cf01_probe import TOKENS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger-limit', type=int, choices=(150, 500), default=500)
    args = parser.parse_args()
    elapsed = []
    failures = []
    with httpx.Client(base_url='http://127.0.0.1:8871', trust_env=False, timeout=10) as client:
        for role in ('gm', 'vezemir', 'raziel', 'morthak'):
            response = client.get('/health', headers={'X-Omnisvera-Token': TOKENS[role]})
            response.raise_for_status()
            assert response.json()['access_mode'] == ('gm' if role == 'gm' else 'player')

        def read(task):
            role, route = task
            start = time.perf_counter()
            try:
                response = client.get(route, headers={'X-Omnisvera-Token': TOKENS[role]})
                response.raise_for_status()
                response.json()
                return time.perf_counter() - start, None
            except Exception as error:
                return time.perf_counter() - start, {'role': role, 'route': route, 'error': type(error).__name__}

        tasks = [(role, route) for role in ('gm', 'vezemir', 'raziel', 'morthak')
                 for route in ('/combat/effects', '/workspace', f'/workspace/ledger?limit={args.ledger_limit}', '/characters')]
        with ThreadPoolExecutor(max_workers=16) as pool:
            for _ in range(5):
                for seconds, error in pool.map(read, tasks):
                    elapsed.append(seconds)
                    if error:
                        failures.append(error)
    print(json.dumps({'status': 'FAIL' if failures else 'PASS', 'transport': 'loopback HTTP',
                      'roles': ['master', 'vezemir', 'raziel', 'morthak'], 'concurrency': 16,
                      'reads': len(elapsed), 'ledger_limit': args.ledger_limit, 'failures': failures,
                      'max_seconds': round(max(elapsed), 3),
                      'p95_seconds': round(sorted(elapsed)[int(len(elapsed) * .95) - 1], 3)}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
