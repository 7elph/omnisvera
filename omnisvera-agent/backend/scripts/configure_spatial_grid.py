"""Explicit, backed-up configuration of existing S7 maps (not a QA runner)."""
import argparse
import json
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.spatial_grid import seed_session7_grids


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    args=parser.parse_args()
    database=args.database.resolve()
    if not database.is_file(): raise ValueError('Informe um banco existente; não cria banco operacional')
    backup=Path(tempfile.mkdtemp(prefix='omnisvera-before-grid-'))/'companion.sqlite3'
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(backup)) as target:
        source.backup(target)
        protected=('session_workspace_maps','session_workspace_tokens','session_workspace_map_fog','character_states','game_sessions','game_scenes')
        tables={row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        before={name:source.execute(f'SELECT * FROM {name} ORDER BY rowid').fetchall() for name in protected if name in tables}
    migrated=seed_session7_grids(database)
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as source:
        for name,rows in before.items():
            if rows!=source.execute(f'SELECT * FROM {name} ORDER BY rowid').fetchall():
                raise RuntimeError(f'Inspecione {name}; backup preservado em {backup}')
        count=source.execute('SELECT COUNT(*) FROM session_workspace_map_grids').fetchone()[0]
    print(json.dumps({'configured_map_ids':migrated,'grids_total':count,'existing_state_preserved':True,'backup':str(backup)},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
