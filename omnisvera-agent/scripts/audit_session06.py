"""Read-only campaign readiness audit. Never prints credentials or changes state."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resource_conflicts(resources):
    seen = {}
    conflicts = []
    for item in resources:
        key = item.get('key')
        if key in seen:
            conflicts.append({'key': key, 'values': [seen[key], item.get('current')],
                              'reason': 'duplicate_resource_key'})
        seen[key] = item.get('current')
    return conflicts


def main():
    database = ROOT / 'backend/data/omnisvera_companion.sqlite3'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        result = {'database_access': 'READ_ONLY', 'characters': []}
        for profile, raw in db.execute('SELECT profile_id,state_json FROM character_states'):
            if profile not in {'vezemir', 'raziel', 'morthak', 'dorn7'}:
                continue
            state = json.loads(raw)
            result['characters'].append({'profile': profile,
                'hp': [state.get('current_hp'), state.get('maximum_hp')],
                'resources': state.get('resources', []),
                'conflicts': resource_conflicts(state.get('resources', []))})
        result['resource_integrity'] = ('FAIL' if any(c['conflicts'] for c in result['characters']) else 'PASS')
        # A resource integrity PASS is not a rules or multiplayer readiness claim.
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
