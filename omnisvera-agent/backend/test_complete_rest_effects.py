import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.character_play import apply_character_action, init_character_play
from app.combat_effects import init_effects, readeffects


class CompleteRestEffectsTests(TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / 'rest.sqlite3'
        init_character_play(self.db)
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            for character in ('vezemir', 'morthak', 'raziel', 'dorn7'):
                state = dict(current_hp=3, maximum_hp=20, conditions=['ferido'], temporary_hp=2,
                             resources=[], daily_skill_flags={'frenesi_auto_used': True})
                db.execute('INSERT INTO character_states VALUES(?,?,?,?)', (character, json.dumps(state), 1, 'fixture'))
                for duration in ('rest', 'rounds', 'scene', 'manual', 'next_attack', 'fictional_time'):
                    identity = character + ':' + duration
                    effect = dict(id=identity, target_type='character', target_id=character,
                                  label=duration, duration=duration, rounds=3, modifiers={'attack_bonus': 2})
                    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',
                               (identity, 'character', character, json.dumps(effect)))
            effect = dict(id='enemy', target_type='token', target_id='enemy', label='NPC', duration='manual')
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', ('enemy', 'token', 'enemy', json.dumps(effect)))

    def rest(self, character, request_id):
        return apply_character_action(self.db, character_id=character, actor_id='master', actor_role='gm',
                                      action='rest_at_inn', payload={}, request_id=request_id)

    def test_rest_removes_every_temporary_status_for_each_character_and_persists(self):
        for character in ('vezemir', 'morthak', 'raziel', 'dorn7'):
            self.rest(character, 'rest-' + character)
            self.assertFalse([e for e in readeffects(self.db)['effects'] if e.get('target_id') == character])
        self.assertEqual(['enemy'], [e['id'] for e in readeffects(self.db)['effects']])
        with closing(sqlite3.connect(self.db)) as db:
            for raw, in db.execute('SELECT state_json FROM character_states'):
                state = json.loads(raw)
                self.assertEqual(20, state['current_hp'])
                self.assertEqual([], state['conditions'])
                self.assertEqual(0, state['temporary_hp'])

    def test_other_characters_are_untouched_and_retry_does_not_clear_a_new_effect(self):
        self.rest('vezemir', 'rest-one')
        self.assertEqual(19, len(readeffects(self.db)['effects']))
        with closing(sqlite3.connect(self.db)) as db, db:
            effect = dict(id='new', target_type='character', target_id='vezemir', duration='rounds', rounds=3)
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', ('new', 'character', 'vezemir', json.dumps(effect)))
        version = readeffects(self.db)['version']
        self.assertTrue(self.rest('vezemir', 'rest-one')['replayed'])
        self.assertEqual(version, readeffects(self.db)['version'])
        self.assertIn('new', [e['id'] for e in readeffects(self.db)['effects']])

    def test_full_rest_cleans_up_clones_but_not_unrelated_tokens(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('CREATE TABLE session_workspace_tokens(id TEXT, sheet_json TEXT, current_hp INTEGER)')
            db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,?)', ('clone', json.dumps({'clone_effect_id': 'clonagem'}), 3))
            db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,?)', ('npc', '{}', 10))
            effect = dict(id='clonagem', target_type='character', target_id='morthak', duration='rounds',
                          necro_spell='clonagem', clone_ids=['clone'])
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', ('clonagem', 'character', 'morthak', json.dumps(effect)))
        self.rest('morthak', 'rest-clones')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual([('npc',)], db.execute('SELECT id FROM session_workspace_tokens').fetchall())

    def test_player_cannot_invoke_gm_full_rest(self):
        with self.assertRaises(PermissionError):
            apply_character_action(self.db, character_id='vezemir', actor_id='vezemir', actor_role='player',
                                   action='rest_at_inn', payload={}, request_id='player-rest')
        self.assertEqual(25, len(readeffects(self.db)['effects']))
