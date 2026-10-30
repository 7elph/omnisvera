"""Canonical preparation context: no provider, campaign writes or private DTO leaks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from app.ai_preparation_context import party_context, contextual_task
from app import ai_workshop as workshop


def roster():
    return [dict(id=key, name=name, class_name=cls, race='fixture', level=5,
                 token='secret', gm_fields={'secret': 'hidden'}, notes='private')
            for key, name, cls in [('morthak', 'Morthak', 'Mago'),
                                   ('raziel', 'Raziel', 'Hemomante'),
                                   ('vezemir', 'Vezemir', 'Guerreiro'),
                                   ('dorn7', 'Unidade DORN-7', 'Mago')]]


def job():
    return dict(id=1, queue='text', entity_type='transcript_window',
                entity_id='session:7:00000000:00006000', revision='a'*64,
                purpose='Preparar blocos com evidencia',
                payload_json={'sources': [{'path': 'fixture.txt', 'sha256': 'a'*64,
                                            'text': 'trecho original'}],
                              'facts': [{'session_number': 7}], 'questions': []},
                output_json={'draft': 'INCORRECT OLD MODEL OUTPUT'})


class PreparationContextTests(unittest.TestCase):
    def test_exact_party_and_allowlisted_fields_only(self):
        rows = roster() + [dict(id='varkh', name='Varkh')]
        context = party_context(rows)
        self.assertEqual(len(context['members']), 4)
        encoded = json.dumps(context)
        for forbidden in ('secret', 'hidden', 'private', 'varkh'):
            self.assertNotIn(forbidden, encoded)
        self.assertTrue(all(m['role'] == 'party_member' for m in context['members']))
        self.assertEqual(context['members'][-1]['controller'], 'gm')

    def test_missing_duplicate_or_invalid_roster_rejected(self):
        for rows in (roster()[:-1], roster()+[roster()[0]],
                     [dict(row, level=0) for row in roster()]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                party_context(rows)

    def test_hash_is_stable_but_tracks_current_level(self):
        one = contextual_task(job(), roster())
        self.assertEqual(one, contextual_task(job(), list(reversed(roster()))))
        rows = roster()
        rows[0]['level'] = 6
        self.assertNotEqual(one['revision'], contextual_task(job(), rows)['revision'])

    def test_only_input_evidence_reused_no_generated_output_and_no_mutation(self):
        original = job()
        snapshot = copy.deepcopy(original)
        task = contextual_task(original, roster())
        self.assertEqual(original, snapshot)
        self.assertNotIn('INCORRECT OLD MODEL OUTPUT', json.dumps(task))
        self.assertEqual(task['payload']['sources'], original['payload_json']['sources'])
        self.assertEqual(task['payload']['facts'][0], {'session_number': 7})
        self.assertEqual(task['payload']['facts'][-1]['kind'], 'current_party_snapshot')
        self.assertIn('historical', task['payload']['facts'][-1]['precedence'])

    def test_wrong_job_or_absent_evidence_rejected(self):
        for change in ({'queue': 'code'}, {'entity_type': 'npc'}, {'payload_json': {}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                contextual_task(dict(job(), **change), roster())

    def test_native_enqueue_retry_is_idempotent_and_does_not_replace_old_job(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder)/'workshop.sqlite3'
            task = contextual_task(job(), roster())
            first = workshop.enqueue_job(db, **task)
            again = workshop.enqueue_job(db, **task)
            self.assertEqual(first, again)


if __name__ == '__main__':
    unittest.main()
