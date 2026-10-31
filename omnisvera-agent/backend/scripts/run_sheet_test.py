"""One command: read-only backup, private loopback fixture, native sheet tests.

Never starts a battle on production or loads operational access tokens.
Evidence stays in TEMP. Only the child server created here is stopped.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import json
import os
import re
import shutil
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

try:
    from .cf01_probe import BACKEND, TOKENS, checked_database, fixture_environment, startup_checkpoint
    from .memory_guard import OwnedProcessGroup, register_owned_process, wait_for_memory, workload_slot
except ImportError:
    from cf01_probe import BACKEND, TOKENS, checked_database, fixture_environment, startup_checkpoint
    from memory_guard import OwnedProcessGroup, register_owned_process, wait_for_memory, workload_slot


def backup_readonly(source, destination):
    destination = checked_database(destination)
    if destination.exists():
        raise ValueError('Refusing to overwrite a rehearsal database')
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError('Source database not found')
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro', uri=True)) as original, closing(sqlite3.connect(destination)) as copy:
        original.backup(copy)


def checked_port(port):
    if not 1024 <= port <= 65535 or port in (8787, 8788):
        raise ValueError('Use a separate rehearsal port (default 8871), not 8787/8788')
    with socket.socket() as probe:
        # Windows has permissive reuse defaults; exclusive reservation detects
        # an existing listener. Release before launching, verify child liveness.
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(('127.0.0.1',port))
        except OSError as error:
            raise ValueError('Rehearsal port is occupied; no existing service will be stopped') from error
    return port


def stop_owned_server(server):
    if server.poll() is not None:
        return
    if os.name == 'nt':
        # venv Python may be a redirector. Kill only this newly created tree;
        # never find/kill a process by port or send console-group Ctrl+C.
        subprocess.run(['taskkill','/PID',str(server.pid),'/T','/F'], capture_output=True, check=False)
    else:
        server.terminate()
    server.wait(timeout=15)


def run_scenario_worker(command, *, cwd, env):
    """Contain the API sibling separately from the already-running fixture.

    A Windows process cannot join an unrelated nested job just because its
    name was inherited in the environment. Mirror the fixture bootstrap: a
    fresh group, original Popen handle, and real-venv self-join before work.
    """
    group = OwnedProcessGroup()
    process = None
    try:
        scenario_env = dict(env)
        scenario_env['OMNISVERA_QA_JOB_NAME'] = group.name
        process = subprocess.Popen(command, cwd=cwd, env=scenario_env,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        group.track(process)
        return subprocess.CompletedProcess(command, process.wait())
    finally:
        try:
            if process is not None:
                stop_owned_server(process)
        finally:
            group.close()


UI_SUITES = ('full', 'combat', 'lightning', 'hemomancy', 'vampiric', 'necromancy', 'rest', 'passives', 'summon_turns', 'friday', 'oct24', 'monster_defaults', 'active_spells', 'catalog', 'inventory_summons', 'sprite_studio','item_families')


def save_progress(output, **progress):
    file = Path(output) / 'progress.json'
    temporary = file.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(progress, ensure_ascii=False), encoding='utf-8')
    temporary.replace(file)


def runner_exit_code(api_exit_code, ui=None):
    if api_exit_code:
        return api_exit_code
    if ui and ui.get('status') != 'PASS':
        return 1 if ui.get('status') == 'FAIL' else 2
    return 0


def visual_process_result(stdout, stderr, returncode):
    """Read only a terminal native receipt, including pretty-printed JSON.

    Exit 2 alone is not uncertainty: require the script's explicit receipt.
    Never accept action coverage from a failed process or an earlier log entry.
    """
    tail = stdout[-1_000_000:]
    receipt = {}
    starts = [match.start() for match in re.finditer(r'(?m)^\{', tail)]
    for start in reversed(starts[-64:]):
        try:
            value = json.loads(tail[start:])
        except (ValueError, RecursionError):
            continue
        if (isinstance(value, dict) and isinstance(value.get('status'), str)
                and value['status'] in {'PASS', 'FAIL', 'INCONCLUSIVE'}):
            receipt = value
            break
    declared = receipt.get('status')
    missing = 'Cannot find module' in stderr or 'Executable doesn' in stderr
    if declared == 'FAIL':
        status = 'FAIL'
    elif declared == 'INCONCLUSIVE' and returncode in (0, 2):
        status = 'INCONCLUSIVE'
    elif returncode == 0:
        status = 'PASS'
    else:
        status = 'INCONCLUSIVE' if missing and not receipt else 'FAIL'
    result = {'status': status}
    if status == 'PASS' and declared == 'PASS' and isinstance(receipt.get('action_coverage'), list):
        result['action_coverage'] = receipt['action_coverage']
    if status == 'INCONCLUSIVE' and isinstance(receipt.get('reason'), str):
        result['reason'] = receipt['reason'][:2000]
    return result


def run_visual_checks(output, port, actors, *, ui_suite='full', on_progress=None):
    with workload_slot() as acquired:
        if not acquired:
            return {'status': 'INCONCLUSIVE', 'reason': 'resource_busy; no visual driver started'}
        return _run_visual_checks(output, port, actors, ui_suite=ui_suite, on_progress=on_progress)


def _run_visual_checks(output, port, actors, *, ui_suite='full', on_progress=None):
    """Fixed built-UI scripts on our temporary server, never model-provided code."""
    output=checked_database(output)
    if type(port) is not int or not 1024<=port<=65535 or port in (8787,8788):
        raise ValueError('UI smoke must use an isolated loopback port')
    if ui_suite not in UI_SUITES:
        raise ValueError('Unknown UI suite')
    if ui_suite != 'full' and set(actors) != {'vezemir','morthak','raziel','dorn7'}:
        raise ValueError('Combat UI suite requires all four actors')
    frontend=BACKEND.parent/'frontend'
    node=shutil.which('node')
    if not node:return {'status':'INCONCLUSIVE','reason':'Node runtime unavailable'}
    media_fixture = None
    database = output/'simulation.sqlite3'
    if database.is_file():
        try:
            from .fixture_media import copy_fixture_media
        except ImportError:
            from fixture_media import copy_fixture_media
        try:
            media_fixture = copy_fixture_media(database, BACKEND.parent.parent,
                                              output/'simulation.vault')
        except (OSError, ValueError):
            return {'status':'INCONCLUSIVE','reason':'Isolated media fixture unavailable'}
    env=fixture_environment(output/'simulation.sqlite3')
    # Debug filters must not silently narrow an agent's requested evidence.
    env.pop('OMNISVERA_QA_ACTION_ACTOR', None)
    env.pop('OMNISVERA_QA_EXTENDED_ACTIONS', None)
    env.pop('OMNISVERA_QA_THREE_SHEET_BATCH', None)
    env['OMNISVERA_QA_HEMOMANCY_BATCH'] = 'first'
    env['OMNISVERA_QA_VAMPIRIC_BATCH'] = 'first'
    env['OMNISVERA_QA_NECROMANCY_BATCH'] = 'first'
    env['OMNISVERA_SHEET_QA_URL']=f'http://127.0.0.1:{port}'
    env['OMNISVERA_SHEET_QA_ACTORS']=','.join(actors)
    env['OMNISVERA_SIMULATION_EVIDENCE']=str(output/'all-actions-evidence.json')
    bundled=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
    env.setdefault('OMNISVERA_QA_MODULES',str(bundled))
    scripts=['sheet-combat-readiness-smoke.cjs']
    if set(actors)=={'vezemir','morthak','raziel','dorn7'}:
        # Only our verified TEMP copy receives approved presentation/resources.
        # This never touches --source-db or the operational process.
        sys.path.insert(0,str(BACKEND))
        from app.approved_spell_pack import apply_approved_spell_pack
        try:apply_approved_spell_pack(checked_database(output/'simulation.sqlite3'))
        except ValueError as error:return {'status':'INCONCLUSIVE','reason':'Approved spell fixture unavailable: '+str(error)}
        scripts.append('grid-action-flow-smoke.cjs')
        scripts.append('compact-sheet-smoke.cjs')
        scripts.append('range-multitarget-smoke.cjs')
        scripts.append('approved-spells-smoke.cjs')
        scripts.append('design-system-smoke.cjs')
        scripts.append('morthak-new-spell-art-smoke.cjs')
        scripts.append('vezemir-inventory-smoke.cjs')
        scripts.append('map-toolbar-rest-smoke.cjs')
        scripts.append('map-commerce-smoke.cjs')
        scripts.append('shop-header-library-smoke.cjs')
        scripts.append('three-sheet-actions-smoke.cjs')
    if ui_suite == 'combat':
        # Split the ten extended actions into two fixed halves; neither the
        # per-script budget nor the overall rehearsal ceiling is raised.
        scripts = ['sheet-combat-readiness-smoke.cjs', 'three-sheet-actions-smoke.cjs',
                   'three-sheet-actions-second-smoke.cjs']
        env['OMNISVERA_QA_EXTENDED_ACTIONS'] = '1'
        env['OMNISVERA_QA_THREE_SHEET_BATCH'] = 'first'
    elif ui_suite == 'lightning':
        scripts = ['sheet-combat-readiness-smoke.cjs', 'range-multitarget-smoke.cjs']
    elif ui_suite == 'hemomancy':
        scripts = ['hemomancy-weapons-smoke.cjs', 'hemomancy-weapons-second-smoke.cjs']
    elif ui_suite == 'vampiric':
        scripts = ['raziel-vampiric-smoke.cjs', 'raziel-vampiric-second-smoke.cjs']
    elif ui_suite == 'necromancy':
        scripts = ['morthak-necromancy-smoke.cjs', 'morthak-summons-smoke.cjs',
                   'morthak-high-spells-smoke.cjs']
    elif ui_suite == 'rest':
        scripts = ['map-toolbar-rest-smoke.cjs', 'four-sheet-rest-smoke.cjs']
    elif ui_suite == 'passives':
        scripts = ['hemomancy-passives-smoke.cjs']
    elif ui_suite == 'summon_turns':
        scripts = ['summon-turns-smoke.cjs']
    elif ui_suite == 'sprite_studio':
        scripts = ['sprite-studio-smoke.cjs']
    elif ui_suite == 'item_families':
        scripts=['item-families-smoke.cjs','item-specials-smoke.cjs']
    elif ui_suite == 'inventory_summons':
        try:
            from .market_followup_fixture import prepare
        except ImportError:
            from market_followup_fixture import prepare
        try:prepare(checked_database(database))
        except ValueError as error:return {'status':'INCONCLUSIVE','reason':'Market fixture unavailable: '+str(error)}
        scripts = ['potion-skeleton-smoke.cjs', 'economy-market-smoke.cjs', 'market-followup-smoke.cjs','item-families-smoke.cjs']
    elif ui_suite == 'catalog':
        scripts = ['sheet-combat-readiness-smoke.cjs', 'catalog-recovery-smoke.cjs']
    elif ui_suite == 'active_spells':
        scripts = ['active-spell-effects-smoke.cjs']
    elif ui_suite == 'monster_defaults':
        scripts = ['monster-defaults-smoke.cjs']
    elif ui_suite == 'friday':
        scripts = ['scene-preparation-smoke.cjs','thoradin-wallet-smoke.cjs',
                   'three-sheet-actions-smoke.cjs','three-sheet-actions-second-smoke.cjs',
                   'hemomancy-passives-smoke.cjs','summon-turns-smoke.cjs','four-sheet-rest-smoke.cjs']
        env['OMNISVERA_QA_EXTENDED_ACTIONS'] = '1'
        env['OMNISVERA_QA_THREE_SHEET_BATCH'] = 'first'
    if ui_suite=='oct24':
        from app.approved_resource_limits import apply_approved_resource_limits
        apply_approved_resource_limits(checked_database(output/'simulation.sqlite3'))
        scripts=['table-balance-oct24-smoke.cjs','monster-exposure-poison-smoke.cjs']
    checks=[]
    started = time.monotonic()

    def checkpoint(status='INCONCLUSIVE', current=None, reason=None):
        result = {'status': status, 'suite': ui_suite, 'checks': list(checks),
                  'physical_actions': False, 'grid_actions': len(scripts)>1 or ui_suite in {'hemomancy', 'passives', 'summon_turns'}}
        if media_fixture is not None: result['media_fixture'] = media_fixture
        if reason: result['reason'] = reason
        file = output/'ui-progress.json'
        temporary = file.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        temporary.replace(file)
        save_progress(output, phase='ui', current=current, completed=len(checks),
                      total=len(scripts), elapsed_seconds=round(time.monotonic()-started, 3))
        if on_progress: on_progress(result)
        return result

    for script in scripts:
        checkpoint(current=script)
        if not wait_for_memory(timeout=30):
            return checkpoint(reason='Insufficient or unknown memory; no browser driver started', current=script)
        step_started = time.monotonic()
        group = None
        process = None
        try:
            group = OwnedProcessGroup()
            process=subprocess.Popen([node,'--require',str(frontend/'tests'/'owned-ui-preload.cjs'),str(frontend/'tests'/script)],cwd=frontend,env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            group.track(process)
            process.stdin.write('1'); process.stdin.close(); process.stdin = None
            register_owned_process(output, process.pid, 'ui')
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired as error:
            stop_owned_server(process)
            def readable(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''
            (output/(script+'.private.log')).write_text(
                readable(error.stdout)+'\n'+readable(error.stderr), encoding='utf-8')
            checks.append({'script':script, 'status':'INCONCLUSIVE',
                           'duration_seconds':round(time.monotonic()-step_started, 3)})
            return checkpoint(reason='UI runner timed out; only its owned process tree was stopped', current=script)
        except OSError:
            if process is not None:
                stop_owned_server(process)
            checks.append({'script':script, 'status':'INCONCLUSIVE',
                           'duration_seconds':round(time.monotonic()-step_started, 3)})
            return checkpoint(reason='UI runner unavailable', current=script)
        finally:
            if process is not None and getattr(process, 'stdin', None) is not None:
                process.stdin.close(); process.stdin = None
            if group is not None:
                group.close()
        (output/(script+'.private.log')).write_text(stdout+'\n'+stderr,encoding='utf-8')
        check={'script':script, **visual_process_result(stdout, stderr, process.returncode),
               'duration_seconds':round(time.monotonic()-step_started, 3)}
        checks.append(check)
        if check['status'] != 'PASS':return checkpoint(status=check['status'], current=script)
        checkpoint(current=script)
    return checkpoint(status='PASS')


def main():
    with workload_slot() as acquired:
        if not acquired:
            print('RESOURCE_BUSY: another managed workload is running; no rehearsal started', flush=True)
            return 2
        return _main()


def _main():
    startup_checkpoint('runner_main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actors', nargs='+', choices=('raziel','morthak','vezemir','dorn7'), default=['raziel','morthak'])
    parser.add_argument('--port', type=int, default=8871)
    parser.add_argument('--scenarios', nargs='+', help='Replay exact scenario_id entries from a report')
    parser.add_argument('--source-db', type=Path, default=BACKEND/'data'/'omnisvera_companion.sqlite3')
    parser.add_argument('--output-dir', type=Path, help='New TEMP evidence directory, used by the bounded local AI tool')
    parser.add_argument('--keep-server', action='store_true', help='Keep only the temporary server for a subsequent browser smoke; Ctrl+C stops it')
    parser.add_argument('--ui', action='store_true', help='Check built sheet layout; all four actors also exercise physical combat buttons')
    parser.add_argument('--ui-suite', choices=UI_SUITES, default='full', help='Explicit bounded visual batch; full preserves all existing checks')
    args = parser.parse_args()
    if args.ui_suite != 'full' and (not args.ui or set(args.actors) != {'vezemir','morthak','raziel','dorn7'}):
        parser.error('Combat UI suite requires --ui and all four actors')
    port = checked_port(args.port)
    if args.output_dir:
        output=checked_database(args.output_dir)
        output.mkdir(parents=True,exist_ok=False)
    else:
        output = Path(tempfile.mkdtemp(prefix='omnisvera-sheet-test-'))
    database = output/'simulation.sqlite3'
    save_progress(output, phase='waiting_memory', current='minimum_1024_mb', completed=0, total=1)
    if not wait_for_memory(timeout=120):
        print('MEMORY_UNAVAILABLE: rehearsal not started; no source database or service changed', flush=True)
        return 2
    backup_readonly(args.source_db, database)
    if args.ui and args.ui_suite in {'inventory_summons','item_families'}:
        try:from .item_family_fixture import prepare as prepare_item_family
        except ImportError:from item_family_fixture import prepare as prepare_item_family
        prepare_item_family(database)
    save_progress(output, phase='startup', completed=0, total=1)
    print('ISOLATED_EVIDENCE='+str(output), flush=True)
    server = None
    server_group = None
    try:
        with (output/'server.private.log').open('w',encoding='utf-8') as log:
            startup_checkpoint('fixture_spawn_requested')
            server_group = OwnedProcessGroup()
            child_env = fixture_environment(database)
            child_env['OMNISVERA_QA_JOB_NAME'] = server_group.name
            server = subprocess.Popen([sys.executable,str(BACKEND/'scripts'/'cf01_probe.py'),'serve',
                '--database',str(database),'--port',str(port)],cwd=BACKEND,stdout=log,stderr=log,
                # The fixture never reads input. Do not carry the long-lived
                # MCP host's protocol pipe into a nested Windows launcher.
                stdin=subprocess.DEVNULL,
                env=child_env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            server_group.track(server)
            startup_checkpoint('fixture_spawned',process=server)
            register_owned_process(output, server.pid, 'fixture')
            import httpx
            deadline = time.monotonic()+45
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',headers={'X-Omnisvera-Token':TOKENS['gm']},timeout=2,trust_env=False) as client:
                while True:
                    if server.poll() is not None:
                        startup_checkpoint('fixture_health_stopped',process=server)
                        raise RuntimeError('Isolated server stopped at startup; inspect server.private.log in TEMP')
                    try:
                        health = client.get('/health')
                        if health.status_code==200 and health.json().get('access_mode')=='gm':
                            if Path(health.json().get('database_path') or '').resolve()!=database.resolve():
                                raise RuntimeError('Port belongs to another database; no rehearsal commands sent')
                            startup_checkpoint('fixture_health_ready',process=server)
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic()>=deadline:
                        startup_checkpoint('fixture_health_timeout',process=server)
                        raise RuntimeError('Isolated server did not become ready; no production service was restarted')
                    time.sleep(.2)
            if server.poll() is not None:
                raise RuntimeError('Isolated server lost its listening port')
            command=[sys.executable,str(BACKEND/'scripts'/'all_actions_simulation.py'),
                '--database',str(database),'--port',str(port),'--actors',*args.actors]
            if args.scenarios:
                command.extend(['--scenarios',*args.scenarios])
            save_progress(output, phase='api', completed=0, total=None)
            # Scenario workers never read input; keep the MCP protocol pipe
            # out of every nested native Python launch, not only the server.
            result = run_scenario_worker(command, cwd=BACKEND, env=child_env)
            report_path=output/'sheet-test-report.json'
            if report_path.is_file():
                report=json.loads(report_path.read_text(encoding='utf-8'))
                if args.ui:
                    from sheet_rehearsal import attach_ui_evidence, render_report
                    def checkpoint_report(ui):
                        attach_ui_evidence(report, ui)
                        temporary = report_path.with_suffix('.json.tmp')
                        temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                        temporary.replace(report_path)
                        (output/'sheet-test-report.md').write_text(render_report(report),encoding='utf-8')
                    ui = run_visual_checks(output,port,args.actors,ui_suite=args.ui_suite,on_progress=checkpoint_report) if result.returncode==0 else {'status':'INCONCLUSIVE','reason':'API scenarios failed; UI acceptance not run'}
                    checkpoint_report(ui)
                    print('UI_SMOKE='+json.dumps(report['ui_smoke']),flush=True)
                print('SHEET_SCENARIOS='+json.dumps(report['scenario_counts']),flush=True)
                print('REPORT='+str(output/'sheet-test-report.md'),flush=True)
                save_progress(output, phase='finished', completed=len(report.get('scenarios') or []), total=len(report.get('scenarios') or []))
            if args.keep_server and result.returncode==0:
                print(f'FIXTURE_ONLY=http://127.0.0.1:{port} (Ctrl+C to stop this test server)',flush=True)
                while server.poll() is None:
                    time.sleep(1)
            return runner_exit_code(result.returncode,
                report.get('ui_smoke') if args.ui and report_path.is_file() else None)
    except KeyboardInterrupt:
        return 130
    finally:
        try:
            if server is not None:
                stop_owned_server(server)
        finally:
            if server_group is not None:
                server_group.close()


if __name__=='__main__':
    raise SystemExit(main())
