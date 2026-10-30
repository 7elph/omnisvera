"""Read-only art inventory. No generation, approval, state writes or raw lore export."""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.monster_catalog import load_monster_catalog


def media(vault, value):
    value = str(value or '').strip().removeprefix('[[').removesuffix(']]').split('|')[0]
    path = (vault / value).resolve()
    allowed = (vault / 'zz_media').resolve()
    if not value or not path.is_relative_to(allowed) or not path.is_file():
        return None
    return {'path': path.relative_to(vault).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def inventory(database, vault):
    result = []
    # Original references come from the live Vault, not unrelated generated art.
    notes = {}
    for directory in ('Bestiary', 'Items', 'Characters'):
        for path in sorted((vault / directory).rglob('*.md')):
            body = path.read_text(encoding='utf-8-sig')
            front = yaml.safe_load(body.split('---', 2)[1]) if body.startswith('---') and len(body.split('---', 2)) == 3 else {}
            front = front if isinstance(front, dict) else {}
            refs = front.get('reference_images') or []
            if isinstance(refs, str): refs = [refs]
            candidates = list(refs) + [front.get(key) for key in ('cover', 'portrait', 'thumbnail')]
            candidates += re.findall(r'!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', body)
            reference = next((item for value in candidates if (item := media(vault, value)) and '/approved/' not in item['path'] and '/drafts/' not in item['path']), None)
            entry = {'category': directory, 'name': path.stem, 'source': path.relative_to(vault).as_posix(), 'original_reference': reference}
            notes[path.stem.casefold()] = entry
            result.append(entry)
    for monster in load_monster_catalog()['monsters']:
        note = notes.get(str(monster['name']).casefold())
        result.append({'category': 'monster_catalog', 'id': monster['id'], 'name': monster['name'],
                       'source': 'backend/app/data/old_dragon_srd_monsters.json',
                       'original_reference': (note or {}).get('original_reference'),
                       'current_image': media(vault, monster.get('image_path'))})
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        for row in db.execute('SELECT id,name,image_path FROM session_custom_items'):
            note = notes.get(row['name'].casefold())
            result.append({'category': 'session_item', 'id': row['id'], 'name': row['name'],
                           'original_reference': (note or {}).get('original_reference'), 'current_image': media(vault, row['image_path'])})
        for row in db.execute('SELECT id,name,image_path,sheet_json FROM session_workspace_tokens WHERE token_type=?', ('monster',)):
            note = notes.get(row['name'].casefold())
            result.append({'category': 'map_creature', 'id': row['id'], 'name': row['name'],
                           'original_reference': (note or {}).get('original_reference'), 'current_image': media(vault, row['image_path'])})
    abilities = json.loads((ROOT / 'backend/app/data/session_abilities.json').read_text(encoding='utf-8'))
    for owner, entries in abilities['characters'].items():
        for ability in entries:
            if ability.get('kind') == 'spell':
                result.append({'category': 'spell', 'owner': owner, 'id': ability['id'], 'name': ability['name'], 'source': ability.get('source'), 'original_reference': None})
    counts = {}
    for entry in result: counts[entry['category']] = counts.get(entry['category'], 0) + 1
    return {'read_only': True, 'network_calls': 0, 'counts': counts, 'entries': result,
            'limitations': ['Exact-name links only; unresolved identities require reconciliation.', 'NPCs mentioned only in transcripts are not yet extracted.', 'No replacements or generation performed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = inventory(ROOT / 'backend/data/omnisvera_companion.sqlite3', ROOT.parent)
    if args.output:
        if args.output.exists(): parser.error('Output already exists; preserve previous report')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'counts': report['counts'], 'entries': len(report['entries']), 'network_calls': 0, 'read_only': True}))
