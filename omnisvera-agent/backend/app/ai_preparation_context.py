"""Small current-party snapshot for the existing private preparation queue.

Callers supply an authorized /characters roster, never raw sheet state. Historical
transcripts remain evidence, not authority to change the current sheets or rules.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

PARTY_IDS = ('morthak', 'raziel', 'vezemir', 'dorn7')


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def party_context(roster: list[dict]) -> dict:
    """Allowlist identity fields; incomplete/ambiguous party fails closed."""
    if not isinstance(roster, list):
        raise ValueError('authorized_roster_required')
    members = []
    for key in PARTY_IDS:
        matches = [row for row in roster if isinstance(row, dict) and row.get('id') == key]
        if len(matches) != 1:
            raise ValueError('party_member_missing_or_duplicate')
        row = matches[0]
        member = {'id': key, 'role': 'party_member',
                  'controller': 'gm' if key == 'dorn7' else 'player'}
        for field in ('name', 'class_name', 'race'):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise ValueError('invalid_party_identity')
            member[field] = value.strip()
        if type(row.get('level')) is not int or not 1 <= row['level'] <= 100:
            raise ValueError('invalid_party_level')
        member['level'] = row['level']
        members.append(member)
    return {'kind': 'current_party_snapshot', 'schema_version': 1,
            'source': 'authorized_companion_characters', 'members': members,
            'precedence': 'Current party identities and levels override historical transcript observations. '
                          'Transcripts do not authorize rules or sheet changes. '
                          'Ambiguous ASR names remain questions; do not invent aliases or entities.'}


def contextual_task(source_job: dict, roster: list[dict]) -> dict:
    """Build one new native job from original evidence, NEVER prior AI output."""
    if (source_job.get('queue') != 'text'
            or source_job.get('entity_type') != 'transcript_window'):
        raise ValueError('transcript_text_job_required')
    payload = copy.deepcopy(source_job.get('payload_json') or {})
    if not isinstance(payload.get('sources'), list) or not payload['sources']:
        raise ValueError('original_evidence_required')
    facts = payload.get('facts', [])
    if not isinstance(facts, list):
        raise ValueError('invalid_source_facts')
    payload['facts'] = [fact for fact in facts if not (
        isinstance(fact, dict) and fact.get('kind') == 'current_party_snapshot')]
    payload['facts'].append(party_context(roster))
    revision = _hash({'context_version': 1, 'source_revision': source_job.get('revision'),
                      'payload': payload})
    return {'queue': 'text', 'entity_type': 'transcript_window',
            'entity_id': source_job['entity_id'], 'revision': revision,
            'purpose': source_job['purpose'], 'priority': 0, 'gap': True,
            'request_id': 'party-context:' + _hash([source_job['entity_id'],
                                                   source_job['purpose'], revision]),
            'payload': payload}
