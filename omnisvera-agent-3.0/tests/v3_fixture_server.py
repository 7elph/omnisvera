"""Disposable backend for the 3.0 cut (battle/city/shop). Synthetic SQLite + Vault in TEMP.

Never touches the operational database. Starts the native backend on 8891 and, when
--preview is given, the Web preview proxy on 8892. Ctrl+C / terminate stops both."""
import argparse
import json
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
COMPANION = PROJECT.parent / 'omnisvera-agent'
sys.path[:0] = [str(COMPANION / 'backend/scripts'), str(PROJECT / 'tests')]
from cf01_probe import fixture_environment
from create_fixture import create

THORADIN = 'monster:6624c761ea5b4cbf8062de90dfc40521'
CONCLAVE = 'location:f910fe95a11e478e8e8e4f29e9acd53c'


def augment(fixture):
    database = Path(fixture['database'])
    from app.session_workspace import set_workspace_map, save_workspace_token
    from app.spatial_grid import configure_grid
    from app import map_commerce as shop
    from app.access import AccessContext
    arena = set_workspace_map(database, title='Arena de ensaio', image_path='zz_media/fixture/map.png', visible_to_players=True)
    configure_grid(database, actor_id='master', role='gm', request_id='v3-arena-grid', map_id=arena['id'],
                   config={'cols': 12, 'rows': 8, 'cell_size_m': 1})
    goblins = []
    for index, cell in enumerate([(12, 12), (13, 11)]):
        goblins.append(save_workspace_token(database, map_id='default', token_type='monster', name=f'Goblin {index + 1}',
            latitude=(cell[1] + .5) * 5, longitude=(cell[0] + .5) * 5, current_hp=7, maximum_hp=7,
            sheet={'armor_class': 12, 'saving_throw': 16, 'movement': '6 m',
                   'attacks': [{'name': 'Espada curta', 'damage': '1d6', 'bonus': 1, 'slot': 'melee'}]})['id'])
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("INSERT OR REPLACE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('official:nimalis','Nimalis','zz_media/fixture/map.png',1,'now','now')")
        merchant = db.execute('SELECT id,token_id FROM merchants LIMIT 1').fetchone()
        db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,image_path,latitude,longitude,created_at,updated_at,map_id,sheet_json,visible_to_players) VALUES(?,?,?,?,?,?,'now','now','official:nimalis',?,1)",
                   (THORADIN, 'monster', 'Thoradin', 'zz_media/fixture/portrait.png', 40, 40, json.dumps({'description': 'Ferreiro de ensaio'})))
        db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,image_path,latitude,longitude,created_at,updated_at,map_id,sheet_json,visible_to_players) VALUES(?,?,?,?,?,?,'now','now','official:nimalis',?,1)",
                   (CONCLAVE, 'location', 'Conclave dos Errantes', 'zz_media/fixture/portrait.png', 55, 60, json.dumps({'description': 'Guilda de ensaio'})))
        db.execute('UPDATE merchants SET token_id=? WHERE id=?', (THORADIN, merchant[0]))
    gm = AccessContext(mode='gm')
    guild = 'merc-fixture-conclave'
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("INSERT INTO merchants(id,name,location,buy_pct,created_at,token_id,enabled) VALUES(?,?,?,?,?,?,1)",
                   (guild, 'Conclave dos Errantes', 'Nimalis', 50, 'now', CONCLAVE))
    shop.add_service(database, guild, gm, name='Reserva de quarto coletivo', kind='lodging', price_copper=5)
    fixture.update(arena=arena['id'], goblins=goblins, city='official:nimalis')
    (Path(fixture['directory']) / 'fixture.json').write_text(json.dumps(fixture), encoding='utf-8')
    return fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--resume', help='reuse an existing disposable fixture directory (reconnection tests)')
    args = parser.parse_args()
    if args.resume:
        fixture = json.loads((Path(args.resume) / 'fixture.json').read_text(encoding='utf-8'))
    else:
        fixture = augment(create())
    database = Path(fixture['database'])
    environment = fixture_environment(database)
    environment['LOCALAPPDATA'] = str(Path(fixture['directory']) / 'localappdata')
    print(json.dumps({'fixture': fixture['directory'], 'arena': fixture['arena'], 'gm_token': 'cf01-local-gm'}), flush=True)
    commands = [[sys.executable, '-B', str(COMPANION / 'backend/scripts/cf01_probe.py'), 'serve', '--database', str(database), '--port', '8891']]
    if args.preview:
        commands.append([sys.executable, '-B', str(PROJECT / 'tools/serve_preview.py'), '--backend', 'http://127.0.0.1:8891', '--port', '8892'])
    processes = [subprocess.Popen(command, cwd=COMPANION, env=environment) for command in commands]
    try:
        processes[0].wait()
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()


if __name__ == '__main__':
    main()
