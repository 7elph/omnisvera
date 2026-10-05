"""Default: rehearse in SQLite copy. --apply: approved live data migration + backup."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.dorn_mage import apply_dorn_mage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    live = ROOT / 'backend/data/omnisvera_companion.sqlite3'
    directory = ROOT / '.autonomy/runtime' / ('dorn-mage2-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    directory.mkdir(parents=True)
    backup = directory / 'before.sqlite3'
    with closing(sqlite3.connect(live.as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    test = directory / 'rehearsal.sqlite3'
    with closing(sqlite3.connect(backup)) as source, closing(sqlite3.connect(test)) as target:
        source.backup(target)
    result = apply_dorn_mage(test)
    assert apply_dorn_mage(test)['applied'] is False
    with closing(sqlite3.connect(backup)) as before, closing(sqlite3.connect(test)) as after:
        for table in ('character_states', 'character_sheets', 'character_definition_overrides', 'player_inventory'):
            sql = f"SELECT * FROM {table} WHERE profile_id!='dorn7' ORDER BY profile_id"
            assert before.execute(sql).fetchall() == after.execute(sql).fetchall(), table
        for table in ('combat_effect_clock', 'session_workspace_tokens', 'combat_effects'):
            assert before.execute(f'SELECT * FROM {table}').fetchall() == after.execute(f'SELECT * FROM {table}').fetchall(), table
    print(json.dumps({'rehearsal': result, 'other_characters_and_battle_unchanged': True, 'backup': str(backup), 'test_db': str(test)}, ensure_ascii=False))
    if args.apply:
        print(json.dumps({'live': apply_dorn_mage(live)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
