"""Vanished summons cannot keep turns in the legacy initiative interface."""
import json
import sqlite3
from unittest import TestCase

from app.battle_mode import retire_defeated


class SummonRetirementCompatibilityTests(TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript('''
            CREATE TABLE combat_effect_clock(id INTEGER PRIMARY KEY, encounter_json TEXT, version INTEGER);
            CREATE TABLE character_states(profile_id TEXT, state_json TEXT);
            CREATE TABLE session_workspace_tokens(id TEXT, current_hp INTEGER, sheet_json TEXT, updated_at TEXT);
            INSERT INTO character_states VALUES('morthak','{"current_hp":10}');
            INSERT INTO session_workspace_tokens VALUES('enemy',30,'{}','before');
        ''')
        self.members = [
            {'target_type': 'character', 'target_id': 'morthak', 'name': 'Morthak'},
            {'target_type': 'token', 'target_id': 'expired-clone', 'name': 'Clone de Morthak'},
            {'target_type': 'token', 'target_id': 'enemy', 'name': 'Ogro'},
        ]

    def encounter(self, *, current=0, active=True, battle_mode=False):
        state = {'active': active, 'participants': self.members, 'turn_index': current,
                 'turn_sequence': 4, 'action_committed': True, 'attacks_used': 1,
                 'pending_attack': 'pending-original', 'consumable_used': True,
                 'movement': {'spent_m': 3}}
        if battle_mode:
            state['battle_mode'] = True
        self.db.execute('INSERT INTO combat_effect_clock VALUES(1,?,1)', (json.dumps(state),))
        return state

    def state(self):
        return json.loads(self.db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0])

    def test_legacy_combat_removes_missing_clone_without_resetting_current_budget(self):
        before = self.encounter()
        removed = retire_defeated(self.db, 'after')
        self.assertEqual(['expired-clone'], [p['target_id'] for p in removed])
        after = self.state()
        self.assertEqual(['morthak', 'enemy'], [p['target_id'] for p in after['participants']])
        for field in ('turn_index', 'turn_sequence', 'action_committed', 'attacks_used',
                      'pending_attack', 'consumable_used', 'movement'):
            self.assertEqual(before[field], after[field], field)
        self.assertEqual([], retire_defeated(self.db, 'retry'))

    def test_current_missing_clone_advances_once_and_clears_only_its_budget(self):
        self.encounter(current=1)
        retire_defeated(self.db, 'after')
        after = self.state()
        self.assertEqual('enemy', after['participants'][after['turn_index']]['target_id'])
        self.assertEqual(5, after['turn_sequence'])
        self.assertFalse(after['action_committed'])
        self.assertEqual(0, after['attacks_used'])
        for field in ('pending_attack', 'consumable_used', 'movement'):
            self.assertNotIn(field, after)

    def test_inactive_combat_is_not_rewritten(self):
        before = self.encounter(active=False)
        self.assertEqual([], retire_defeated(self.db, 'after'))
        self.assertEqual(before, self.state())

    def test_legacy_nonmissing_zero_hp_participant_keeps_existing_behavior(self):
        self.members = [self.members[0], self.members[2]]
        before = self.encounter()
        self.db.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE id='enemy'")
        self.assertEqual([], retire_defeated(self.db, 'after'))
        self.assertEqual(before, self.state())

    def test_native_clone_cleanup_retires_zero_hp_or_ended_clone_in_both_interfaces(self):
        from app.morthak_high_spells import cleanup
        self.db.execute('CREATE TABLE combat_effects(id TEXT, active INTEGER, data_json TEXT)')
        for battle_mode in (False, True):
            for ended in (False, True):
                with self.subTest(battle_mode=battle_mode, concentration_ended=ended):
                    self.db.execute('DELETE FROM combat_effect_clock')
                    self.db.execute('DELETE FROM combat_effects')
                    self.db.execute('DELETE FROM session_workspace_tokens WHERE id=?', ('expired-clone',))
                    self.encounter(current=1, battle_mode=battle_mode)
                    self.db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,?,?)',
                        ('expired-clone', 5 if ended else 0,
                         json.dumps({'clone_effect_id': 'clone-effect'}), 'before'))
                    self.db.execute('INSERT INTO combat_effects VALUES(?,?,?)',
                        ('clone-effect', 0 if ended else 1, json.dumps({
                            'necro_spell': 'clonagem', 'clone_ids': ['expired-clone']})))
                    cleanup(self.db, 'after')
                    after = self.state()
                    self.assertEqual(['morthak', 'enemy'], [p['target_id'] for p in after['participants']])
                    self.assertEqual('enemy', after['participants'][after['turn_index']]['target_id'])
                    self.assertIsNone(self.db.execute(
                        'SELECT id FROM session_workspace_tokens WHERE id=?', ('expired-clone',)).fetchone())
                    cleanup(self.db, 'retry')
                    self.assertEqual(after, self.state())
