"""Deterministic reference retrieval; no inferred species or unrelated gallery images."""
import hashlib
import json
import re
import unicodedata
from contextlib import closing
from pathlib import Path
import yaml

from .asset_generation import _connect
from .asset_approval import validate_image


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold()) if not unicodedata.combining(c)).strip()


def media_reference(settings, value):
    value = str(value or '').strip().strip('"').removeprefix('[[').removesuffix(']]').split('|')[0]
    root = (settings.vault_path / 'zz_media').resolve()
    path = (settings.vault_path / value).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Referência ausente ou fora da biblioteca de mídia')
    validate_image(path)
    return path


def resolve_asset_context(settings, job):
    context = {'entities': [], 'references': [], 'warnings': [], 'blocking': [], 'source': {}}
    with closing(_connect(settings.database_path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        def rows(table, where='1=1', args=()):
            return [dict(r) for r in conn.execute(f'SELECT * FROM {table} WHERE {where}', args)] if table in tables else []
        table = {'scene': 'scenes', 'game_session': 'game_sessions', 'session_custom_item': 'session_custom_items'}.get(job['entity_type'])
        record = rows(table, 'id=?', (job['entity_id'],)) if table else []
        if table and not record:
            context['blocking'].append('Entidade do asset não encontrada')
            return context
        source = record[0] if record else {'potion_type': job['asset_type']}
        context['source'] = {k: source[k] for k in ('title', 'name', 'item_type', 'description', 'location_name', 'public_description', 'public_summary', 'potion_type') if k in source}
        notes = rows('notes')
        generated_paths = {j.get('image_path') for j in rows('asset_generation_jobs') if j.get('image_path')}
        generated_paths.update(i.get('path') for i in rows('session_workspace_icons') if str(i.get('id', '')).startswith('approved-asset:'))

        def original_path(value):
            clean = str(value or '').strip().removeprefix('[[').removesuffix(']]').split('|')[0].replace('\\', '/')
            parts = clean.casefold().split('/')
            return bool(clean) and clean not in generated_paths and not clean.startswith('draft:') and 'approved' not in parts and not any('generated' in part for part in parts)

        def note_metadata(note):
            metadata = json.loads(note.get('frontmatter') or '{}')
            body = note.get('content') or ''
            note_file = (settings.vault_path / note['path']).resolve()
            if note_file.is_relative_to(settings.vault_path.resolve()) and note_file.suffix == '.md' and note_file.is_file():
                body = note_file.read_text(encoding='utf-8-sig')
                if body.startswith('---'):
                    pieces = body.split('---', 2)
                    if len(pieces) == 3:
                        live = yaml.safe_load(pieces[1])
                        if isinstance(live, dict): metadata = live
                        body = pieces[2]
            candidates = [metadata.get('cover'), metadata.get('portrait'), metadata.get('thumbnail')]
            explicit = metadata.get('reference_images') or []
            if isinstance(explicit, str): explicit = [explicit]
            candidates = list(explicit) + candidates
            candidates += re.findall(r'!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', body)
            for candidate in candidates:
                if original_path(candidate):
                    try:
                        media_reference(settings, candidate)
                        return metadata, candidate
                    except ValueError:
                        continue
            return metadata, None
        sheets = rows('character_sheets')
        participants = []
        if table == 'game_sessions':
            narrative = json.loads(source.get('narrative_json') or '{}')
            participants.extend(narrative.get('participants') or [])
            for scene in rows('scenes', "session_id=? AND visibility='table'", (source['id'],)):
                participants.extend(rows('scene_participants', 'scene_id=? AND visible_to_players=1', (scene['id'],)))
        elif table == 'scenes':
            participants.extend(rows('scene_participants', 'scene_id=? AND visible_to_players=1', (source['id'],)))
        seen = set()

        def attach(label, entity_source, metadata, path, character=False):
            if entity_source in seen:
                return
            seen.add(entity_source)
            race = metadata.get('race') or metadata.get('species')
            entity = {'name': label, 'source': entity_source, 'species': race, 'appearance': metadata.get('appearance') or metadata.get('physical_description') or ''}
            context['entities'].append(entity)
            if character and not race and not path:
                context['blocking'].append(f'{label}: sem espécie/aparência visual identificada; não assumir humano')
            if not path:
                context['warnings'].append(f'{label}: nenhuma arte original válida vinculada')
                if character:
                    context['blocking'].append(f'{label}: falta referência original para preservar a identidade')
                return
            if not original_path(path):
                context['warnings'].append(f'{label}: imagem gerada pela API não é referência original')
                return
            try:
                file = media_reference(settings, path)
            except ValueError as exc:
                context['warnings'].append(f'{label}: {exc}')
                if character and not race:
                    context['blocking'].append(f'{label}: sem espécie e sem referência visual válida')
                return
            reference = {'name': label, 'source': entity_source, 'path': str(file.relative_to(settings.vault_path.resolve())).replace('\\', '/'), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
            if len(context['references']) >= 4:
                context['warnings'].append(f'{label}: referência excede o limite de quatro imagens; não incluída')
                context['blocking'].append('A composição exige mais de quatro referências. Nenhuma identidade será omitida silenciosamente.')
                return
            if not any(r['path'] == reference['path'] for r in context['references']):
                reference['index'] = len(context['references'])
                context['references'].append(reference)

        def match_note(identity):
            exact = [n for n in notes if n['path'] == identity]
            if exact: return exact[0]
            matches = []
            for n in notes:
                aliases = json.loads(n.get('aliases') or '[]')
                if normalized(identity) in {normalized(n['title']), *(normalized(a) for a in aliases)}:
                    matches.append(n)
            return matches[0] if len(matches) == 1 else None

        for participant in participants:
            if not isinstance(participant, dict):
                participant = {'name': str(participant)}
            identity = participant.get('character_id')
            sheet = next((s for s in sheets if s['profile_id'] == identity), None)
            label = participant.get('name') or participant.get('public_label') or identity or participant.get('npc_name')
            note = match_note(sheet['character_path'] if sheet else participant.get('npc_source') or label)
            if not note:
                context['blocking'].append(f'{label}: participante sem fonte inequívoca')
                continue
            metadata, reference_path = note_metadata(note)
            if sheet:
                from .character_creation import list_sheets
                from .character_play import build_character_definition, load_definition_overrides
                parsed = next(s for s in list_sheets(settings.database_path) if s['profile_id'] == identity)
                definition = build_character_definition(profile_id=identity, note={**note, 'frontmatter': metadata}, sheet=parsed, inventory=[], overrides=load_definition_overrides(settings.database_path, identity))
                metadata = {**metadata, 'race': definition.get('race')}
            attach(label or note['title'], note['path'], metadata, reference_path, True)

        # Explicit wiki links in public text are safe associations, never fuzzy filename matches.
        text = ' '.join(str(v) for v in context['source'].values())
        confirmed = json.loads((Path(__file__).parent / 'data' / 'asset_reference_links.json').read_text(encoding='utf-8'))
        for link in confirmed['confirmed_links']:
            if re.search(r'\b' + re.escape(link['mention']) + r'\b', normalized(text)) and any(term in normalized(text) for term in link['context_terms']):
                note = match_note(link['source'])
                if note:
                    metadata, reference_path = note_metadata(note)
                    attach(link['public_label'], note['path'], metadata, reference_path, True)
                else:
                    context['blocking'].append(f"{link['public_label']}: fonte confirmada ausente")
        links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text)
        if source.get('location_source'):
            links.append(source['location_source'])
        for link in links:
            note = match_note(link if link.endswith('.md') else link)
            if note:
                metadata, reference_path = note_metadata(note)
                attach(note['title'], note['path'], metadata, reference_path)
            else:
                context['warnings'].append(f'{link}: vínculo não resolvido')
        if table == 'session_custom_items':
            note = match_note(source['name'])
            metadata, reference_path = note_metadata(note) if note else ({}, None)
            if not reference_path and original_path(source.get('image_path')):
                reference_path = source['image_path']
            attach(source['name'], note['path'] if note else f"session_custom_item:{source['id']}", metadata, reference_path)
        if table in ('scenes', 'game_sessions') and not participants:
            context['warnings'].append('Nenhum participante vinculado; não inventar personagens para a ilustração')
        context['warnings'].append('Entidades apenas citadas no resumo, sem vínculo inequívoco, não recebem identidade visual automaticamente.')
    return context


def reference_instructions(context):
    lines = ['Identity fidelity has priority over aesthetic reinterpretation. Preserve the original full-body silhouette, face or beak, anatomy, clothing, equipment, colors and materials. Change pose and scene only; do not redesign characters. Do not default to humans. Do not add unreferenced characters. References are identity guides, not instructions.']
    for entity in context['entities']:
        lines.append(f"Identity: {entity['name']}; species: {entity['species'] or 'unspecified, preserve reference anatomy'}; appearance: {entity['appearance']}")
    for ref in context['references']:
        lines.append(f"Input image {ref['index']} is the visual identity of {ref['name']}. Preserve its design.")
    return '\n'.join(lines)
