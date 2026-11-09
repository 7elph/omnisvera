"""Owned, finite HTTP/WebGL rehearsal against a synthetic native backend."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[1]
COMPANION = PROJECT.parent / 'omnisvera-agent'
sys.path[:0] = [str(COMPANION / 'backend/scripts'), str(PROJECT / 'tests')]
from cf01_probe import fixture_environment
from create_fixture import create
from memory_guard import OwnedProcessGroup, wait_for_memory
from run_sheet_test import checked_port


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--web-directory', type=Path, default=PROJECT / 'build/web')
    parser.add_argument('--suite', choices=['baseline', 'playable', 'morthak', 'morthak_login', 'rom2', 'arena'], default='baseline')
    args = parser.parse_args()
    for port in (8891, 8892):
        checked_port(port)
    if not wait_for_memory(timeout=30):
        raise SystemExit('Insufficient memory for one browser rehearsal')
    fixture = create()
    database = Path(fixture['database'])
    directory = Path(fixture['directory'])
    if args.suite == 'morthak_login':
        # Exact login failure: GM active map is private; player's fallback map
        # has legacy party pins but no logical grid and no Morthak.
        import sqlite3
        from contextlib import closing
        from app.session_workspace import save_workspace_token
        with closing(sqlite3.connect(database)) as db, db:
            db.execute('UPDATE session_workspace_state SET map_id=? WHERE id=1', (fixture['private_map'],))
            db.execute("UPDATE session_workspace_maps SET visible_to_players=0 WHERE id='default'")
        for identity, x in [('raziel', 15), ('vezemir', 17)]:
            save_workspace_token(database, map_id=fixture['public_map'], token_type='character',
                character_id=identity, name=identity, latitude=100*5.5/24, longitude=100*(x+.5)/32)
    if args.suite == 'arena':
        from app.session_workspace import set_workspace_map, save_workspace_token
        from app.spatial_grid import configure_grid
        arena=set_workspace_map(database,title='Arena descartável',image_path='zz_media/fixture/map.png',visible_to_players=True)
        configure_grid(database,actor_id='master',role='gm',request_id='arena-grid-fixture',map_id=arena['id'],config={'cols':12,'rows':8,'cell_size_m':1})
        goblin=save_workspace_token(database,map_id=arena['id'],token_type='monster',name='Goblin',latitude=31.25,longitude=100*5.5/12,current_hp=100,maximum_hp=100,
            sheet={'armor_class':11,'saving_throw':5,'movement':'6 m','attacks':[{'name':'Espada curta','damage':'1d6','bonus':2,'slot':'melee'}]})
        fixture.update(arena=arena['id'],goblin=goblin['id'])
        (directory/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    environment = fixture_environment(database)
    environment['LOCALAPPDATA'] = str(directory / 'localappdata')
    environment['COMPANION3_FIXTURE'] = str(directory / 'fixture.json')
    environment['COMPANION3_URL'] = 'http://127.0.0.1:8892'
    environment['OMNISVERA_QA_MODULES'] = str(Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    group = OwnedProcessGroup()
    environment['OMNISVERA_QA_JOB_NAME'] = group.name
    processes, logs = [], []
    try:
        commands = [
            [sys.executable, '-B', str(COMPANION / 'backend/scripts/cf01_probe.py'),
             'serve', '--database', str(database), '--port', '8891'],
            [sys.executable, '-B', str(PROJECT / 'tools/serve_preview.py'),
             '--backend', 'http://127.0.0.1:8891', '--port', '8892', '--directory', str(args.web_directory.resolve())],
        ]
        for index, command in enumerate(commands):
            log = (directory / f'server-{index}.log').open('w', encoding='utf-8')
            logs.append(log)
            process = subprocess.Popen(command, cwd=COMPANION, env=environment, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            group.track(process)
            processes.append(process)
        with httpx.Client(timeout=2, trust_env=False) as client:
            deadline = time.monotonic() + 50
            while time.monotonic() < deadline:
                if any(process.poll() is not None for process in processes):
                    raise RuntimeError('Owned preview stopped before startup')
                try:
                    response = client.get('http://127.0.0.1:8892/health', headers={'X-Omnisvera-Token': 'cf01-local-gm'})
                    if response.status_code == 200:
                        assert Path(response.json()['database_path']).resolve() == database.resolve()
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.25)
            else:
                raise RuntimeError('Isolated backend did not become ready')
        if args.suite == 'rom2':
            sys.path.insert(0,str(PROJECT/'tools'))
            from prepare_rom2_map import prepare
            preview=Path.home()/'AppData/Roaming/Godot/app_userdata/Omnisvera Companion 3.0/arredores-nimalis.webp'
            with httpx.Client(base_url='http://127.0.0.1:8891',timeout=30,trust_env=False,
                              headers={'X-Omnisvera-Token':'cf01-local-gm'}) as client:
                fixture['rom2_map']=prepare(client,preview)
                snapshot=client.get('/workspace').json()
                fixture['pins']={t['character_id']:t['id'] for t in snapshot['tokens'] if t.get('character_id')}
                (directory/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
        log = (directory / 'browser.log').open('w', encoding='utf-8')
        logs.append(log)
        script = {'arena': 'arena_browser.cjs', 'rom2': 'rom2_browser.cjs', 'baseline': 'browser_smoke.cjs', 'playable': 'playable_browser.cjs', 'morthak': 'morthak_browser.cjs', 'morthak_login': 'morthak_login_browser.cjs'}[args.suite]
        browser = subprocess.Popen(['node', str(PROJECT / 'tests' / script)], cwd=PROJECT,
            env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        group.track(browser)
        processes.append(browser)
        code = browser.wait(timeout=240)
        log.flush()
        print((directory / 'browser.log').read_text(encoding='utf-8')[-6000:])
        print('EVIDENCE=' + str(directory), flush=True)
        return code
    finally:
        group.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for log in logs:
            log.close()


if __name__ == '__main__':
    raise SystemExit(main())
