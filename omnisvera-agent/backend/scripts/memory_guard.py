"""Local Windows resource guard. Standard library only; no model, MCP or WMI.

Monitoring does not manufacture free RAM. Admission waits are bounded and only
registered children of finished native test jobs can be reclaimed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
import uuid

MB = 1024 * 1024
MIN_FREE_MB = 1024
RUN_ID = re.compile(r'test-[a-f0-9]{32}')
TERMINAL = {'COMPLETED', 'ERROR', 'CANCELLED', 'INTERRUPTED'}


def test_job_root():
    checkout = Path(__file__).resolve().parents[2]
    digest = hashlib.sha256(str(checkout).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / ('omnisvera-ai-tests-' + digest)


def state_directory():
    return Path(os.environ.get('LOCALAPPDATA', tempfile.gettempdir())) / 'Omnisvera' / 'memory-guard'


class Performance(c.Structure):
    _fields_ = [('cb', w.DWORD)] + [(name, c.c_size_t) for name in (
        'CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable',
        'SystemCache', 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')
    ] + [(name, w.DWORD) for name in ('HandleCount', 'ProcessCount', 'ThreadCount')]


class ProcessMemory(c.Structure):
    _fields_ = [('cb', w.DWORD), ('PageFaultCount', w.DWORD)] + [
        (name, c.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


class WindowsMetrics:
    def __init__(self):
        if os.name != 'nt':
            raise OSError('Windows metrics unavailable')
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.psapi = c.WinDLL('psapi', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
        self.kernel.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
        self.kernel.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.kernel.WaitForSingleObject.restype = w.DWORD
        self.kernel.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
        self.psapi.GetPerformanceInfo.argtypes = [c.POINTER(Performance), w.DWORD]
        self.psapi.EnumProcesses.argtypes = [c.POINTER(w.DWORD), w.DWORD, c.POINTER(w.DWORD)]
        self.psapi.GetProcessMemoryInfo.argtypes = [w.HANDLE, c.POINTER(ProcessMemory), w.DWORD]

    def memory(self):
        perf = Performance(); perf.cb = c.sizeof(perf)
        if not self.psapi.GetPerformanceInfo(c.byref(perf), perf.cb):
            raise c.WinError(c.get_last_error())
        return dict(free_ram_mb=perf.PhysicalAvailable * perf.PageSize // MB,
                    total_ram_mb=perf.PhysicalTotal * perf.PageSize // MB,
                    committed_mb=perf.CommitTotal * perf.PageSize // MB,
                    commit_limit_mb=perf.CommitLimit * perf.PageSize // MB)

    def _identity(self, handle, pid):
        created, exited, kernel, user = (w.FILETIME() for _ in range(4))
        buf = c.create_unicode_buffer(32768); length = w.DWORD(len(buf))
        if not self.kernel.GetProcessTimes(handle, c.byref(created), c.byref(exited), c.byref(kernel), c.byref(user)):
            raise c.WinError(c.get_last_error())
        if not self.kernel.QueryFullProcessImageNameW(handle, 0, buf, c.byref(length)):
            raise c.WinError(c.get_last_error())
        return dict(pid=pid, created_ticks=(created.dwHighDateTime << 32) | created.dwLowDateTime,
                    executable=buf.value)

    @contextmanager
    def _handle(self, pid, *, terminate=False):
        handle = self.kernel.OpenProcess(0x1000 | (0x100001 if terminate else 0), False, pid)
        if not handle:
            error = c.get_last_error()
            if error == 87:  # Nonexistent PID, not permission failure.
                yield None
                return
            raise c.WinError(error)
        try:
            yield handle
        finally:
            self.kernel.CloseHandle(handle)

    def identity(self, pid):
        with self._handle(pid) as handle:
            if not handle: return None
            code = w.DWORD()
            if not self.kernel.GetExitCodeProcess(handle, c.byref(code)):
                raise c.WinError(c.get_last_error())
            if code.value != 259: return None
            return self._identity(handle, pid)

    def processes(self):
        ids = (w.DWORD * 8192)(); needed = w.DWORD()
        if not self.psapi.EnumProcesses(ids, c.sizeof(ids), c.byref(needed)):
            return []
        result = []
        for pid in ids[:min(needed.value // c.sizeof(w.DWORD), len(ids))]:
            if not pid: continue
            try:
                with self._handle(pid) as handle:
                    if not handle: continue
                    info = self._identity(handle, pid)
                    mem = ProcessMemory(); mem.cb = c.sizeof(mem)
                    if self.psapi.GetProcessMemoryInfo(handle, c.byref(mem), mem.cb):
                        result.append(dict(name=Path(info['executable']).name,
                                           private_mb=mem.PrivateUsage // MB,
                                           working_mb=mem.WorkingSetSize // MB))
            except OSError:
                continue  # Protected/unreadable processes are never escalated.
        return result

    def stop_if_matches(self, receipt):
        if not safe_receipt(receipt) or receipt['pid'] == os.getpid(): return False
        try:
            # Verification and termination use the SAME handle, not a new PID
            # lookup after validation. PID reuse cannot redirect the stop.
            with self._handle(receipt['pid'], terminate=True) as handle:
                if not handle: return False
                info = self._identity(handle, receipt['pid'])
                if info['created_ticks'] != receipt['created_ticks']: return False
                if os.path.normcase(info['executable']) != os.path.normcase(receipt['executable']): return False
                if self.kernel.WaitForSingleObject(handle, 0) != 258: return False
                if not self.kernel.TerminateProcess(handle, 3): return False
                return self.kernel.WaitForSingleObject(handle, 1000) == 0
        except OSError:
            return False


def memory_snapshot():
    try:
        return WindowsMetrics().memory()
    except (OSError, AttributeError):
        return {'free_ram_mb': None}


def memory_ready(sample, min_free_mb=MIN_FREE_MB):
    free = sample.get('free_ram_mb')
    return type(free) is int and free >= min_free_mb


def wait_for_memory(*, timeout=120, min_free_mb=MIN_FREE_MB, read=None,
                    sleep=time.sleep, clock=time.monotonic):
    read = read or memory_snapshot
    deadline = clock() + max(0, timeout)
    while True:
        if memory_ready(read(), min_free_mb): return True
        remaining = deadline - clock()
        if remaining <= 0: return False
        sleep(min(5, remaining))


def read_json(path, limit=16384):
    try:
        path = Path(path)
        if path.is_symlink() or path.stat().st_size > limit: return {}
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, RecursionError):
        return {}


def write_state(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=True, separators=(',', ':')), encoding='utf-8')
    temp.replace(path)


@contextmanager
def instance_lock(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    file = path.open('a+b'); acquired = False
    try:
        if file.seek(0, 2) == 0: file.write(b'0'); file.flush()
        file.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            pass
        yield acquired
    finally:
        file.close()


_workload_context = threading.local()


@contextmanager
def workload_slot():
    """One heavy workload across QA and workshop; no resident scheduler."""
    if getattr(_workload_context, 'owner', None) == (os.getpid(), threading.get_ident()):
        yield True
        return
    with instance_lock(state_directory() / 'workload.lock') as acquired:
        if not acquired:
            yield False
            return
        _workload_context.owner = (os.getpid(), threading.get_ident())
        try:
            yield True
        finally:
            _workload_context.owner = None


class JobBasicLimits(c.Structure):
    _fields_ = [('process_time', c.c_longlong), ('job_time', c.c_longlong),
                ('flags', w.DWORD), ('minimum_ws', c.c_size_t), ('maximum_ws', c.c_size_t),
                ('active_processes', w.DWORD), ('affinity', c.c_size_t),
                ('priority', w.DWORD), ('scheduling', w.DWORD)]


class JobLimits(c.Structure):
    _fields_ = [('basic', JobBasicLimits), ('io', c.c_ulonglong * 6)] + [
        (name, c.c_size_t) for name in ('process_memory', 'job_memory', 'peak_process', 'peak_job')]


class OwnedProcessGroup:
    """Release only children assigned with their original Popen handles.

    A group per UI step also reaps browser descendants left by an exited driver.
    No lookup by generic name, port, memory usage or an unverified PID.
    """
    def __init__(self):
        self.handle = None
        self.kernel = None
        self.name = 'Local\\OmnisveraQA-' + uuid.uuid4().hex
        if os.name != 'nt': return
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [w.LPVOID, w.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = w.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [w.HANDLE, c.c_int, w.LPVOID, w.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, self.name)
        if not self.handle: raise c.WinError(c.get_last_error())
        limits = JobLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits)):
            error = c.WinError(c.get_last_error()); self.close(); raise error

    def track(self, process):
        if os.name != 'nt': return
        if not self.handle: raise OSError('Owned process group is closed')
        child = getattr(process, '_handle', None)
        if child is None: raise OSError('Original child handle unavailable')
        if not self.kernel.AssignProcessToJobObject(self.handle, int(child)):
            raise c.WinError(c.get_last_error())

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def join_owned_job_from_env():
    """The real venv worker joins too, even if its redirector started first."""
    name = os.environ.get('OMNISVERA_QA_JOB_NAME')
    if not name or os.name != 'nt': return
    if not re.fullmatch(r'Local\\OmnisveraQA-[a-f0-9]{32}', name):
        raise OSError('Invalid private QA job')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.OpenJobObjectW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
    kernel.OpenJobObjectW.restype = w.HANDLE
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, c.POINTER(w.BOOL)]
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.OpenJobObjectW(0x0001 | 0x0004, False, name)
    if not handle: raise c.WinError(c.get_last_error())
    try:
        current = kernel.GetCurrentProcess(); joined = w.BOOL()
        if not kernel.IsProcessInJob(current, handle, c.byref(joined)):
            raise c.WinError(c.get_last_error())
        if not joined.value and not kernel.AssignProcessToJobObject(handle, current):
            raise c.WinError(c.get_last_error())
    finally:
        kernel.CloseHandle(handle)


def safe_receipt(receipt):
    return (receipt.get('schema_version') == 1 and receipt.get('source') == 'native_sheet_runner'
            and receipt.get('role') in {'fixture', 'ui'}
            and Path(str(receipt.get('executable', ''))).name.lower() in {'python.exe', 'pythonw.exe', 'node.exe'}
            and all(type(receipt.get(k)) is int and receipt[k] > 0
                    for k in ('pid', 'created_ticks', 'launcher_pid', 'launcher_created_ticks')))


def register_owned_process(output, pid, role):
    """Only our MCP TEMP job receives receipts, never arbitrary user processes."""
    try:
        job = Path(output).parent
        if job.parent.resolve() != test_job_root().resolve() or not RUN_ID.fullmatch(job.name): return False
        record = read_json(job / 'job.json')
        if record.get('run_id') != job.name or record.get('state') != 'RUNNING': return False
        native = WindowsMetrics(); info = native.identity(pid); owner = native.identity(os.getpid())
        if not info or not owner: return False
        receipt = dict(schema_version=1, source='native_sheet_runner', run_id=job.name,
                       role=role, **info, launcher_pid=os.getpid(),
                       launcher_created_ticks=owner['created_ticks'], registered_at=time.time())
        if not safe_receipt(receipt): return False
        write_state(job / 'memory-owners' / f'{pid}-{info["created_ticks"]}.json', receipt)
        return True
    except (OSError, ValueError, TypeError):
        return False  # Admission/owned normal cleanup do not depend on registration.


def cleanup_finished_tests(root, native, *, now=None):
    """Never scan/kill generic idle processes, connectors or other job roots."""
    root = Path(root); now = time.time() if now is None else now
    if root.is_symlink() or not root.is_dir(): return []
    stopped = []
    for job in islice(root.glob('test-*'), 100):
        if job.is_symlink() or not RUN_ID.fullmatch(job.name): continue
        record = read_json(job / 'job.json')
        finished, created = record.get('finished_at'), record.get('created_at')
        if record.get('run_id') != job.name or record.get('state') not in TERMINAL: continue
        if type(finished) not in (int, float) or type(created) not in (int, float): continue
        if not 0 <= created <= finished <= now - 60: continue
        directory = job / 'memory-owners'
        if directory.is_symlink(): continue
        for path in islice(directory.glob('*.json'), 16):
            receipt = read_json(path)
            if not safe_receipt(receipt) or receipt.get('run_id') != job.name: continue
            registered = receipt.get('registered_at')
            if type(registered) not in (int, float) or not created <= registered <= finished: continue
            try:
                owner = native.identity(receipt['launcher_pid'])
                if owner and owner['created_ticks'] == receipt['launcher_created_ticks']: continue
                if native.stop_if_matches(receipt): stopped.append(receipt['pid'])
            except (OSError, ValueError, KeyError):
                continue
    return stopped


def make_state(sample, previous, processes, stopped, *, min_free_mb=MIN_FREE_MB):
    groups = {}
    for proc in processes:
        group = groups.setdefault(proc['name'], dict(name=proc['name'], count=0, private_mb=0, working_mb=0))
        group['count'] += 1
        for field in ('private_mb', 'working_mb'): group[field] += proc[field]
    result = dict(schema_version=1, checked_at=datetime.now(timezone.utc).isoformat(),
                  monitor_pid=os.getpid(), **sample, target_free_mb=min_free_mb,
                  status='ready' if memory_ready(sample, min_free_mb) else 'waiting_for_memory',
                  consumers=sorted(groups.values(), key=lambda g: g['private_mb'], reverse=True)[:5],
                  cleaned_pids=stopped[:16], cleanup_count=(previous.get('cleanup_count', 0)
                      if type(previous.get('cleanup_count', 0)) is int else 0)+len(stopped))
    for field, label in (('free_ram_mb', 'delta_free_mb'), ('committed_mb', 'delta_committed_mb')):
        old, current = previous.get(field), sample.get(field)
        if type(old) is int and type(current) is int: result[label] = current - old
    # Keep just one compact sample. No argv, tokens, chat history or AI output.
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ('once', 'watch', 'check', 'stop', 'status'): mode.add_argument('--' + name, action='store_true')
    parser.add_argument('--state-dir', type=Path, default=state_directory())
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--min-free-mb', type=int, default=MIN_FREE_MB)
    parser.add_argument('--wait', type=int, default=0)
    args = parser.parse_args(argv)
    if not 15 <= args.interval <= 3600 or not 128 <= args.min_free_mb <= 262144 or not 0 <= args.wait <= 300:
        parser.error('Invalid finite resource limits')
    state = args.state_dir / 'state.json'; stop = args.state_dir / 'stop.request'
    if args.stop:
        args.state_dir.mkdir(parents=True, exist_ok=True); stop.touch(); return 0
    if args.status:
        print(json.dumps(read_json(state))); return 0
    if args.check:
        ready = wait_for_memory(timeout=args.wait, min_free_mb=args.min_free_mb)
        print(json.dumps(dict(status='ready' if ready else 'waiting_for_memory', **memory_snapshot())))
        return 0 if ready else 2
    native = WindowsMetrics()
    with instance_lock(args.state_dir / 'guard.lock') as acquired:
        if not acquired: return 0
        if stop.exists(): stop.unlink()
        while True:
            sample = native.memory()
            cleaned = []
            if not memory_ready(sample, args.min_free_mb):
                cleaned = cleanup_finished_tests(test_job_root(), native)
                if cleaned: sample = native.memory()
            value = make_state(sample, read_json(state), native.processes(), cleaned,
                               min_free_mb=args.min_free_mb)
            write_state(state, value)
            if args.once:
                print(json.dumps(value)); return 0
            # Sleep only in this deterministic worker, never in an AI loop.
            time.sleep(args.interval)
            if stop.exists(): stop.unlink(); return 0


if __name__ == '__main__':
    raise SystemExit(main())
