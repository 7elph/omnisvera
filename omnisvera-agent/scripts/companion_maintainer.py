"""Manual preparation only; no agent, commit, push, scheduler or product edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'PASS', 'FAIL', 'INCONCLUSIVE'}
SKIP = {'node_modules', '__pycache__', 'dist', 'dist-omnisvera', 'public', 'data', '.git'}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def source_files(root):
    for folder in ('backend', 'frontend/src', 'frontend/tests'):
        for base, dirs, files in os.walk(root / folder, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.')
                             and not (Path(base) / d).is_symlink())
            for name in sorted(files):
                path = Path(base) / name
                if path.suffix in {'.py', '.ts', '.tsx', '.css', '.cjs'} and not path.is_symlink():
                    yield path
    for name in ('frontend/package.json', 'frontend/package-lock.json', 'frontend/tsconfig.json',
                 'frontend/vite.config.ts', 'backend/requirements.txt', 'AGENTS.md'):
        path = root / name
        if path.is_file() and not path.is_symlink():
            yield path


def fingerprint(root):
    result = hashlib.sha256()
    for path in sorted(source_files(root)):
        result.update(path.relative_to(root).as_posix().encode())
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def git(root, *args):
    p = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    if p.returncode:
        raise RuntimeError('Git metadata unavailable')
    return p.stdout.strip()


def write_report(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        temporary = f.name
    os.replace(temporary, path)


def commands(root, build_dir):
    frontend = root / 'frontend'
    node = shutil.which('node') or 'node'
    return {
        'backend': ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'backend', '-p', 'test_*.py'], root),
        'frontend': ([node, '--test', *[str(p) for p in sorted((frontend / 'tests').glob('*.test.cjs'))]], frontend),
        'typescript': ([node, 'node_modules/typescript/bin/tsc', '--noEmit', '--incremental', 'false'], frontend),
        'build': ([node, 'node_modules/vite/bin/vite.js', 'build', '--outDir', str(build_dir)], frontend),
    }


def inspect(root=ROOT):
    before = fingerprint(root)
    status = git(root, 'status', '--porcelain=v1', '--untracked-files=normal')
    markers = []
    for path in source_files(root):
        for number, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if re.search(r'\b(TODO|FIXME)\b', line):
                # Never export source lines, log contents or environment variables.
                markers.append({'file': path.relative_to(root).as_posix(), 'line': number,
                                'kind': 'marker_requires_reproduction'})
    report = {'created_at': stamp(), 'branch': git(root, 'branch', '--show-current'),
              'head': git(root, 'rev-parse', 'HEAD'), 'dirty': bool(status),
              'changed_entries': len(status.splitlines()), 'source_fingerprint': before,
              'tests': {name: 'INCONCLUSIVE' for name in commands(root, Path('<temporary-build>'))},
              'tests_reason': 'NOT_RUN: inspect never executes tests or builds',
              'test_inventory': {'backend': len(list((root / 'backend').glob('test_*.py'))),
                                 'frontend': len(list((root / 'frontend/tests').glob('*.test.cjs')))},
              'markers': markers[:100], 'marker_count': len(markers),
              'issues': [], 'logs': 'NOT_READ: private runtime data excluded',
              'manual_cycle_gate': 'BLOCKED_DIRTY' if status else 'VERIFY_REQUIRED'}
    prior = root / '.autonomy/runtime/verification.json'
    if prior.is_file():
        try:
            old = json.loads(prior.read_text(encoding='utf-8'))
            report['previous_verification'] = {
                'matches_source': old.get('source_fingerprint') == before and old.get('head') == report['head'],
                'checks': {k: v.get('status') if v.get('status') in STATUSES else 'INCONCLUSIVE'
                           for k, v in old.get('checks', {}).items() if k in report['tests'] and isinstance(v, dict)}}
        except (ValueError, AttributeError):
            report['previous_verification'] = {'status': 'INCONCLUSIVE'}
    if before != fingerprint(root):
        raise RuntimeError('Source changed concurrently; discard inspection')
    write_report(root / '.autonomy/runtime/inspection.json', report)
    return report


def run_check(command, cwd, timeout=600):
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'INCONCLUSIVE', 'reason': 'DEPENDENCY_OR_TIMEOUT'}
    output = proc.stdout + proc.stderr
    missing = any(x in output for x in ('ModuleNotFoundError', 'Cannot find module', 'No module named'))
    status = 'INCONCLUSIVE' if missing else ('PASS' if proc.returncode == 0 else 'FAIL')
    counts = re.findall(r'Ran (\d+) tests?|(?:#|ℹ) tests (\d+)', output)
    # Raw subprocess output can contain credentials or private fixtures: never persist it.
    return {'status': status, 'exit_code': proc.returncode,
            'reason': 'MISSING_DEPENDENCY' if missing else 'PROCESS_EXIT',
            'test_count': int(next(x for x in counts[-1] if x)) if counts else None}


def verify(root=ROOT):
    before = fingerprint(root)
    head = git(root, 'rev-parse', 'HEAD')
    with tempfile.TemporaryDirectory(prefix='companion-maintainer-build-') as build:
        checks = {name: run_check(command, cwd) for name, (command, cwd) in commands(root, Path(build)).items()}
    unchanged = before == fingerprint(root) and head == git(root, 'rev-parse', 'HEAD')
    report = {'created_at': stamp(), 'head': head, 'source_fingerprint': before,
              'product_source_unchanged': unchanged, 'checks': checks}
    write_report(root / '.autonomy/runtime/verification.json', report)
    return report


def validate_history(data):
    schema = json.loads((ROOT / '.autonomy/history.schema.json').read_text())
    if not isinstance(data, dict) or set(data) != set(schema['required']):
        raise ValueError('History fields do not match schema')
    for key, rule in schema['properties'].items():
        val = data[key]
        if 'enum' in rule and val not in rule['enum']:
            raise ValueError('Invalid enum')
        if rule.get('type') == 'string':
            if not isinstance(val, str) or len(val) > rule.get('maxLength', 80):
                raise ValueError('Invalid text')
            if 'pattern' in rule and not re.fullmatch(rule['pattern'], val):
                raise ValueError('Invalid cycle ID')
        if rule.get('type') == 'null' and val is not None:
            raise ValueError('No autonomous commits')
        if rule.get('type') == 'object' and (not isinstance(val, dict) or any(not isinstance(v, str) or v not in STATUSES for v in val.values())):
            raise ValueError('Invalid test statuses')
        if rule.get('type') == 'array':
            if not isinstance(val, list) or len(val) > 5 or any(not isinstance(p, str) or '..' in p or ':' in p or p.startswith(('/', '\\')) for p in val):
                raise ValueError('Invalid file list')
    serialized = json.dumps(data)
    if re.search(r'(?i)(bearer\s|sk-[a-z0-9]|password\s*[:=]|api[_-]?key\s*[:=]|token\s*[:=])', serialized):
        raise ValueError('Potential secret; sanitize manually')
    if data['result'] == 'PASS' and (data['classification'] != 'GREEN' or not data['tests_after'] or any(v != 'PASS' for v in data['tests_after'].values())):
        raise ValueError('PASS requires GREEN and executed passing checks')
    if data['classification'] != 'GREEN' and data['files_changed']:
        raise ValueError('YELLOW/RED cannot implement')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'verify', 'record'])
    parser.add_argument('report', nargs='?')
    args = parser.parse_args()
    if args.action == 'record':
        if not args.report:
            parser.error('record requires a sanitized report file')
        data = validate_history(json.loads(Path(args.report).read_text(encoding='utf-8')))
        target = ROOT / '.autonomy/history' / (data['cycle_id'] + '.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('History recorded; no product operation executed')
    else:
        report = inspect() if args.action == 'inspect' else verify()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.action == 'verify' and (not report['product_source_unchanged'] or any(v['status'] != 'PASS' for v in report['checks'].values())):
            sys.exit(1)


if __name__ == '__main__':
    main()
