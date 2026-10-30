"""Bounded, read-only transcript index for the private AI workshop.

Explicit references/bindings only. Does not scan the Vault, write a campaign DB,
summarize text, execute transcript instructions or send data to a provider.
Chunk offsets refer to UTF-8-sig decoded text with CRLF normalized to LF.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

MAX_SOURCE_BYTES = 4 * 1024 * 1024


def _safe_path(path: Path, roots: list[Path]) -> Path:
    if '..' in path.parts or path.suffix.lower() not in {'.txt', '.md'}:
        raise ValueError('blocked_path')
    # Reject links/junctions before resolution, including a linked parent.
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ValueError('blocked_path')
    resolved = path.resolve()
    if not any(resolved.is_relative_to(Path(root).resolve()) for root in roots):
        raise ValueError('blocked_path')
    return resolved


def _source(path: Path, roots: list[Path], expected_hash=None,
            max_bytes: int = MAX_SOURCE_BYTES) -> tuple[dict, str]:
    path = _safe_path(path, roots)
    if not path.is_file():
        raise ValueError('missing_file')
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_SOURCE_BYTES:
        raise ValueError('invalid_size_limit')
    if path.stat().st_size > max_bytes:
        raise ValueError('source_too_large')
    with path.open('rb') as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('source_too_large')
    digest = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None:
        if not isinstance(expected_hash, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected_hash):
            raise ValueError('invalid_reference')
        if expected_hash.lower() != digest:
            raise ValueError('source_changed')
    text = raw.decode('utf-8-sig', errors='replace').replace('\r\n', '\n')
    if not text.strip():
        raise ValueError('empty_source')
    return {'path': str(path), 'sha256': digest, 'bytes': len(raw),
            'characters': len(text), 'lines': text.count('\n') + 1,
            'role': 'source_data_not_instructions'}, text


def inspect_sources(database: Path, workspace: Path, allowed_roots: list[Path],
                    bindings: dict[int, list[Path]] | None = None, *,
                    max_bytes: int = MAX_SOURCE_BYTES) -> dict:
    """Index existing sessions using stored refs plus explicitly selected files.

    Bindings don't repair production refs. Missing sources remain visible rather
    than silently replacing a transcript with a summary. Returns metadata only.
    """
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError('Source database unavailable')
    workspace = Path(workspace).resolve()
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute('SELECT id,session_number,source_refs_json FROM '
                                  'game_sessions ORDER BY session_number,id').fetchall()
    result = []
    for row in rows:
        item = {'session_id': row['id'], 'session_number': row['session_number'],
                'status': 'missing_source', 'documents': [], 'issues': []}
        try:
            refs = json.loads(row['source_refs_json'] or '[]')
            if not isinstance(refs, list) or len(refs) > 100:
                raise ValueError('invalid_reference')
        except (ValueError, TypeError):
            item['issues'].append('invalid_reference')
            refs = []
        refs = refs + [{'path': str(p)} for p in (bindings or {}).get(row['session_number'], [])]
        seen = set()
        for reference in refs:
            try:
                if not isinstance(reference, dict) or not isinstance(reference.get('path'), str):
                    raise ValueError('invalid_reference')
                path = Path(reference['path'])
                if not path.is_absolute():
                    path = workspace / path
                meta, _ = _source(path, allowed_roots, reference.get('sha256'), max_bytes)
                if meta['sha256'] not in seen:
                    seen.add(meta['sha256'])
                    item['documents'].append(meta)
            except (OSError, ValueError) as error:
                # Never include arbitrary exception text, filenames or contents.
                reason = str(error) if isinstance(error, ValueError) else 'source_unavailable'
                known = {'blocked_path', 'missing_file', 'source_too_large', 'invalid_size_limit',
                         'invalid_reference', 'source_changed', 'empty_source'}
                item['issues'].append(reason if reason in known else 'source_unavailable')
        if item['issues']:
            item['status'] = item['issues'][0]
        elif item['documents']:
            item['status'] = 'ready'
        result.append(item)
    return {'sessions': result, 'source_count': sum(len(r['documents']) for r in result),
            'ready_sessions': sum(r['status'] == 'ready' for r in result),
            'mutated_campaign': False}


def source_chunk(path: Path, allowed_roots: list[Path], expected_hash: str, *,
                 offset: int = 0, limit: int = 6000) -> dict:
    if not isinstance(expected_hash, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected_hash):
        raise ValueError('Source revision hash required')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 16000:
        raise ValueError('Invalid chunk bounds')
    meta, text = _source(Path(path), allowed_roots, expected_hash)
    if offset > len(text):
        raise ValueError('Invalid chunk offset')
    end = min(offset + limit, len(text))
    return {'source_sha256': meta['sha256'], 'offset': offset, 'end': end,
            'next_offset': end if end < len(text) else None,
            'text': text[offset:end], 'role': 'source_data_not_instructions'}


def source_tasks(index: dict, allowed_roots: list[Path], *, chunk_chars: int = 6000):
    """Finite native enqueue descriptors, recent sessions first; no execution.

    Call the native workshop enqueue with these fields and its own request_id.
    Source version + window form stable identities for retries/deduplication.
    All windows are planned, not just the opening paragraph of a transcript.
    """
    sessions = index.get('sessions')
    if not isinstance(sessions, list) or not sessions or any(r.get('status') != 'ready' for r in sessions):
        raise ValueError('Complete explicit source index required')
    if type(chunk_chars) is not int or not 1 <= chunk_chars <= 12000:
        raise ValueError('Invalid chunk size')
    for session in sorted(sessions, key=lambda r: r['session_number'], reverse=True):
        for document in session['documents']:
            meta, text = _source(Path(document['path']), allowed_roots, document['sha256'])
            for start in range(0, len(text), chunk_chars):
                end = min(start + chunk_chars, len(text))
                number = session['session_number']
                yield {
                    'queue': 'text', 'entity_type': 'transcript_window',
                    'entity_id': f"session:{session['session_id']}:{start:08d}:{end:08d}",
                    'revision': meta['sha256'],
                    'purpose': 'Identificar NPCs, monstros, itens, locais e ações citados; apontar lacunas para mestrar, com evidência; separar fato de sugestão, sem inventar regras.',
                    'priority': max(0, 1000 - number), 'gap': True,
                    'payload': {
                        'sources': [{'path': meta['path'], 'sha256': meta['sha256'],
                                     'text': text[start:end], 'offset': start, 'end': end}],
                        'facts': [{'session_number': number, 'source_window': [start, end]}],
                        'questions': ['Este trecho descreve fato ocorrido, hipótese, decisão do Mestre ou problema da ferramenta?'],
                    },
                }
