"""Bounded local AI adapter around the EXISTING native HTTP rehearsal.

This stores only test jobs in TEMP, never campaign content or access tokens.
No arbitrary commands, URLs, code, database paths or live mutations are accepted.
"""
from __future__ import annotations
import hashlib
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid

try:
    from .cf01_probe import BACKEND, checked_database, startup_checkpoint
    from .run_sheet_test import stop_owned_server, UI_SUITES
except ImportError:
    from cf01_probe import BACKEND, checked_database, startup_checkpoint
    from run_sheet_test import stop_owned_server, UI_SUITES

ACTORS=('raziel','morthak','vezemir','dorn7')
RUN_ID=re.compile(r'^test-[a-f0-9]{32}$')


def backend_runner_python():
    """The observer SDK is not the app runtime; no PATH/client/install fallback."""
    executable=BACKEND/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    if not executable.is_file():
        raise FileNotFoundError('Native backend virtualenv interpreter unavailable')
    return executable


def capabilities():
    return {'schema_version':1,'transport':'local_mcp_stdio','actors':list(ACTORS),
        'suite':'native_sheet_actions','default_actors':['raziel','morthak'],
        'ui_checks':'Optional ui=true runs built desktop/mobile sheet checks; all four actors additionally exercise native physical combat buttons. Requires Node, Playwright, Edge and current frontend build.',
        'tools':['companion_test_capabilities','companion_test_start','companion_test_status'],
        'input_policy':'Actor allowlist and optional exact scenario_ids; no arbitrary script, URL, SQL or source path.',
        'isolation':'Read-only SQLite backup; native API in temporary loopback fixture; no operational tokens.',
        'limits':{'parallel_runs':1,'timeout_seconds':1200,'maximum_saved_runs':100},
        'ui_suites':list(UI_SUITES),
        'ui_suite_policy':'full preserves every existing UI smoke; combat runs readiness and both fixed halves of the extended sheet actions; lightning runs readiness and native multi-target Relampago; hemomancy runs the five-weapon flow only; vampiric runs Regeneration, Bite, Coffin and Night Form in two fixed halves; necromancy runs touch/fear, controlled summons and high spells in three fixed scripts; rest runs map controls and four-sheet full-rest cleanup/counter checks in two fixed scripts; passives runs approved hemomancy passive triggers; summon_turns runs controlled summon attacks and turn lifecycle; friday runs preparation previews, copied real Thoradin purchase, combat, passives, summons and rest sequentially. Partial evidence is not certification.',
        'certification_contract': {'field':'report.certification', 'ready_field':'certification_ready',
            'checks':['execution','persistence','idempotency','cost','range','expiration','ui'],
            'meaning':'PASS describes executed scenarios; certification_ready requires explicit per-action proof for all four sheets.',
            'gaps_field':'report.certification.gaps','real_table_validation':'INCONCLUSIVE'},
        'status_contract':{'states':['RUNNING','COMPLETED','ERROR','CANCELLED','INTERRUPTED'],
            'verdicts':['PASS','FAIL','INCONCLUSIVE'],'scenario_results':['PASS','FAIL','EXPECTED_BLOCK'],
            'coverage':['PASS','FAIL','PENDING','ASSISTED','RULE_BLOCKED','UNAVAILABLE']},
        'workflow':['Call start with a unique request_id; retain run_id.',
            'Poll status until terminal; repeat start with SAME inputs/id after a lost response.',
            'Read report.scenarios and characters; structured does not mean automated.',
            'Fix scoped code only when authorized, then rerun with a NEW request_id.',
            'Do not use these tests as evidence of human dice or external-network stability.'],
        'not_available':['Arbitrary character/scenario generation','AI approval of RPG rules',
            'Applying proposals to live state','Executing Scene Lab proposal JSON','Remote/public MCP endpoint'],
        'code_index':'docs/AI_COMPONENT_MAP.json','agent_guide':'docs/AI_TEST_TOOLS.md'}


class TestJobs:
    def __init__(self, root=None, *, spawn=None, stop=None, watch=True, clock=None):
        digest=hashlib.sha256(str(BACKEND.parent.resolve()).encode()).hexdigest()[:12]
        self.root=checked_database(root or Path(tempfile.gettempdir())/('omnisvera-ai-tests-'+digest))
        self.root.mkdir(parents=True,exist_ok=True)
        self._lease=(self.root/'server.lock').open('a+b')
        try:
            if self._lease.seek(0,2)==0:
                self._lease.write(b'0');self._lease.flush()
            self._lease.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self._lease.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self._lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as error:
            self._lease.close()
            raise RuntimeError('BUSY: another test server owns this checkout') from error
        self._lock=threading.RLock();self._stop_event=threading.Event();self._closed=False
        self._spawn=spawn or subprocess.Popen;self._stop=stop or stop_owned_server;self._clock=clock or time.monotonic
        self._processes={};self._started={};self._jobs={};self._requests={}
        for file in self.root.glob('test-*/job.json'):
            if not RUN_ID.fullmatch(file.parent.name):continue
            record=json.loads(file.read_text(encoding='utf-8'))
            if record['state']=='RUNNING':
                record.update(state='INTERRUPTED',verdict='INCONCLUSIVE',error='Prior tool server ended without a result')
                self._save(record)
            self._jobs[record['run_id']]=record
            self._requests[record['request_id']]=record['run_id']
        self._watcher=None
        if watch:
            self._watcher=threading.Thread(target=self._watch,name='companion-test-watch',daemon=True)
            self._watcher.start()

    def _save(self, record):
        file=self.root/record['run_id']/'job.json'
        temp=file.with_suffix('.json.tmp')
        temp.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(file)

    def start(self, *, request_id, actors, scenarios=None, ui=False, ui_suite='full'):
        if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{8,120}',request_id):
            raise ValueError('request_id must be 8-120 safe characters')
        if not isinstance(actors,list) or not 1<=len(actors)<=4 or any(a not in ACTORS for a in actors):
            raise ValueError('Select 1-4 supported actors')
        if scenarios is not None and (not isinstance(scenarios,list) or not 1<=len(scenarios)<=100 or
            any(not isinstance(s,str) or not 1<=len(s)<=240 or any(ord(c)<32 for c in s) for s in scenarios)):
            raise ValueError('scenarios must be exact nonempty scenario_id strings')
        if type(ui) is not bool:raise ValueError('ui must be a boolean')
        if ui_suite not in UI_SUITES or (not ui and ui_suite != 'full'):
            raise ValueError('Unknown UI suite or suite requested without UI')
        if ui_suite != 'full' and set(actors) != set(ACTORS):
            raise ValueError('Combat UI suite requires all four actors')
        inputs={'actors':sorted(set(actors)),'scenarios':sorted(set(scenarios or []))}
        if ui:inputs['ui']=True  # Preserve old receipt fingerprints when omitted.
        if ui_suite != 'full':inputs['ui_suite']=ui_suite
        fingerprint=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
        with self._lock:
            if self._closed:raise RuntimeError('Tool server is closed')
            existing=self._requests.get(request_id)
            if existing:
                if self._jobs[existing]['fingerprint']!=fingerprint:
                    raise ValueError('request_id already used with different inputs')
                return self.status(existing)
            self._refresh()
            if any(r['state']=='RUNNING' for r in self._jobs.values()):
                raise RuntimeError('BUSY: one isolated rehearsal is already running')
            if len(self._jobs)>=100:
                raise RuntimeError('CAPACITY: saved test jobs reached limit; no automatic deletion performed')
            run_id='test-'+uuid.uuid4().hex
            folder=self.root/run_id;folder.mkdir()
            record={'schema_version':1,'run_id':run_id,'request_id':request_id,'fingerprint':fingerprint,
                    **inputs,'state':'RUNNING','verdict':'INCONCLUSIVE','created_at':time.time()}
            self._jobs[run_id]=record;self._requests[request_id]=run_id;self._save(record)
            try:
                runtime=backend_runner_python()
            except FileNotFoundError:
                record.update(state='ERROR',verdict='INCONCLUSIVE',finished_at=time.time(),
                    error='RUNTIME_UNAVAILABLE: native backend/.venv interpreter missing; no process started')
                self._save(record)
                return self._view(record)
            command=[str(runtime),str(BACKEND/'scripts'/'run_sheet_test.py'),
                     '--output-dir',str(folder/'evidence'),'--actors',*inputs['actors']]
            if inputs['scenarios']:command.extend(['--scenarios',*inputs['scenarios']])
            if ui:command.append('--ui')
            if ui_suite != 'full':command.extend(['--ui-suite',ui_suite])
            try:
                with (folder/'runner.private.log').open('w',encoding='utf-8') as log:
                    startup_checkpoint('runner_spawn_requested',stream=log)
                    process=self._spawn(command,cwd=BACKEND,stdout=log,stderr=log,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                    startup_checkpoint('runner_spawned',process=process,stream=log)
                self._processes[run_id]=process;self._started[run_id]=self._clock()
            except Exception:
                record.update(state='ERROR',error='Could not launch isolated runner');self._save(record)
            return self._view(record)

    def _refresh(self):
        for run_id,process in list(self._processes.items()):
            record=self._jobs[run_id]
            if record['state']!='RUNNING':continue
            exit_code=process.poll()
            if exit_code is None and self._clock()-self._started[run_id]<1200:continue
            if exit_code is None:
                self._stop(process)
                record.update(state='ERROR',error='TIMEOUT: owned test process tree stopped',verdict='INCONCLUSIVE')
            else:
                record['exit_code']=exit_code
                try:
                    report=self._read_report(run_id)
                    counts=report['scenario_counts']
                    ui_status=(report.get('ui_smoke') or {}).get('status')
                    if record.get('ui') and ui_status not in ('PASS','FAIL') and not counts.get('FAIL'):
                        raise ValueError('Requested UI checks have no conclusive evidence')
                    failed=bool(counts.get('FAIL')) or (record.get('ui') and ui_status=='FAIL')
                    if exit_code!=(1 if failed else 0):raise ValueError('Exit code/report mismatch')
                    record.update(state='COMPLETED',verdict='FAIL' if failed else 'PASS')
                except (OSError,ValueError,KeyError,TypeError):
                    error='HARNESS_ERROR: missing, invalid or inconsistent report'
                    if exit_code==2 and self._memory_gate_stopped(run_id):
                        error='MEMORY_UNAVAILABLE: minimum 1024 MB not reached; fixture and browser were not started'
                    record.update(state='ERROR',verdict='INCONCLUSIVE',error=error)
            record['finished_at']=time.time();self._save(record)

    def _memory_gate_stopped(self, run_id):
        """Exit 2 alone is not resource evidence and must not hide real failures."""
        folder=self.root/run_id
        try:
            if (folder/'evidence/sheet-test-report.json').exists():return False
            progress=json.loads((folder/'evidence/progress.json').read_text(encoding='utf-8'))
            with (folder/'runner.private.log').open('rb') as stream:
                stream.seek(0,2);stream.seek(max(0,stream.tell()-4096))
                tail=stream.read().decode('utf-8',errors='replace')
            return progress.get('phase')=='waiting_memory' and any(
                line.startswith('MEMORY_UNAVAILABLE: rehearsal not started;') for line in tail.splitlines())
        except (OSError,ValueError):return False

    def _read_report(self, run_id):
        report=json.loads((self.root/run_id/'evidence'/'sheet-test-report.json').read_text(encoding='utf-8'))
        if not isinstance(report,dict) or report.get('kind')!='sheet_test_evidence' or report.get('schema_version')!=1:
            raise ValueError('Unsupported report')
        counts=report['scenario_counts']
        if not isinstance(counts,dict) or any(k not in {'PASS','FAIL','EXPECTED_BLOCK'} or
            not isinstance(v,int) or isinstance(v,bool) or v<0 for k,v in counts.items()):
            raise ValueError('Invalid scenario counts')
        if {k:v for k,v in counts.items() if v}!=dict(Counter(s['status'] for s in report['scenarios'])):
            raise ValueError('Counts do not match executed scenarios')
        if not sum(counts.values()):raise ValueError('Empty run is not evidence')
        return report

    def _view(self, record):
        view={k:record[k] for k in ('schema_version','run_id','request_id','actors','scenarios','state',
            'verdict','created_at','finished_at','exit_code','error') if k in record}
        if record['state']=='COMPLETED':
            view['report']=self._read_report(record['run_id'])
        elif record['state'] in {'ERROR','CANCELLED','INTERRUPTED'}:
            try:
                partial=self._read_report(record['run_id'])
                partial['all_actions_certified']=False
                partial['certification']={**partial.get('certification',{}),'ready':False,'status':'INCOMPLETE'}
                view['partial_report']=partial
            except (OSError, ValueError, KeyError, TypeError):pass
        try:
            progress=json.loads((self.root/record['run_id']/'evidence'/'progress.json').read_text(encoding='utf-8'))
            view['progress']={k:progress[k] for k in ('phase','current','completed','total','elapsed_seconds') if k in progress}
        except (OSError, ValueError, TypeError):pass
        view['production_modified']=False
        view['ui']=bool(record.get('ui'))
        view['ui_suite']=record.get('ui_suite','full')
        view['certification_ready']=bool((view.get('report') or {}).get('certification',{}).get('ready'))
        return view

    def status(self, run_id):
        if not isinstance(run_id,str) or not RUN_ID.fullmatch(run_id):raise ValueError('Invalid run_id')
        with self._lock:
            self._refresh()
            if run_id not in self._jobs:raise KeyError('Test run not found')
            return self._view(self._jobs[run_id])

    def _watch(self):
        while not self._stop_event.wait(1):
            with self._lock:
                if self._closed:return
                self._refresh()

    def close(self):
        with self._lock:
            if self._closed:return
            self._refresh();self._closed=True;self._stop_event.set()
            for run_id,process in self._processes.items():
                record=self._jobs[run_id]
                if record['state']=='RUNNING':
                    self._stop(process)
                    record.update(state='CANCELLED',verdict='INCONCLUSIVE',error='Tool host disconnected before completion')
                    self._save(record)
        if self._watcher:self._watcher.join(timeout=3)
        self._lease.close()
