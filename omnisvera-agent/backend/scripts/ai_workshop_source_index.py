"""Build a private metadata index; never modify the campaign or read all Vault."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai_workshop_sources import inspect_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--allow-root', action='append', type=Path, required=True)
    parser.add_argument('--bindings', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    bindings = {}
    if args.bindings:
        data = json.loads(args.bindings.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or len(data) > 100:
            parser.error('Invalid explicit source bindings')
        for number, paths in data.items():
            if not str(number).isdigit() or not isinstance(paths, list) or len(paths) > 20:
                parser.error('Invalid explicit source bindings')
            if not all(isinstance(path, str) for path in paths):
                parser.error('Invalid explicit source bindings')
            bindings[int(number)] = [Path(path) for path in paths]
    report = inspect_sources(args.database, args.workspace, args.allow_root, bindings)
    if args.report:
        output = args.report.resolve()
        runtime = (ROOT / '.autonomy/runtime').resolve()
        if (not runtime.is_relative_to(ROOT) or not output.is_relative_to(runtime)
                or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                       for p in (args.report.absolute(), *args.report.absolute().parents))):
            parser.error('Private report must remain in .autonomy/runtime')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'source_count': report['source_count'],
                      'ready_sessions': report['ready_sessions'],
                      'sessions': [{'number': row['session_number'], 'status': row['status']}
                                   for row in report['sessions']],
                      'mutated_campaign': report['mutated_campaign']}))
    return 0 if report['sessions'] and all(row['status'] == 'ready' for row in report['sessions']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
