import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from dataclasses import replace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat import (list_pending_attack_resolutions, magic_missile_definition,
                        resolve_attack, confirm_attack_resolution, CombatExpiredError, _now)
from app.character_play import load_session_abilities
from test_combat import CombatAttackResolutionTests, SequenceRng


class ActionRecoveryTests(CombatAttackResolutionTests):
    def setUp(self):
        super().setUp()
        self._insert_character('morthak', 4, 4)
        with closing(sqlite3.connect(self.database)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            state['resources'] = [{'key': 'misseis_magicos', 'current': 3, 'maximum': 3}]
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'", (json.dumps(state),))
        self.mage = {'id': 'morthak', 'name': 'Morthak', 'level': 2, 'session_abilities': load_session_abilities('morthak')}

    def mage_state(self):
        with closing(sqlite3.connect(self.database)) as db:
            return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])

    def missiles(self, request_id='spell-test-001'):
        return resolve_attack(self.database, request_id=request_id, actor_character_id='morthak',
            actor_name='Morthak', requested_by_id='morthak', requested_by_role='player',
            definition=magic_missile_definition(self.mage, self.mage_state()['resources']), inventory=[],
            attack_id='misseis-magicos', target={'type': 'character', 'id': 'raziel', 'name': 'Raziel', 'armor_class': 99, 'current_hp': 14},
            roll_mode='digital', rng=SequenceRng(3))[0]

    def test_spell_automatic_hit_and_atomic_resource_damage_retry(self):
        resolution = self.missiles()
        self.assertEqual((resolution['d20'], resolution['damage_total'], resolution['result']), (0, 5, 'hit'))
        self.assertEqual(self.mage_state()['resources'][0]['current'], 3)
        self.assertEqual(self._character_hp('raziel'), 14)
        pending = list_pending_attack_resolutions(self.database, requested_by_id='morthak', requested_by_role='player')
        self.assertEqual([r['resolution_id'] for r in pending], [resolution['resolution_id']])
        for index in range(2):
            _, applied = confirm_attack_resolution(self.database, resolution_id=resolution['resolution_id'], requested_by_id='morthak', requested_by_role='player')
            self.assertEqual(applied, index == 0)
        self.assertEqual(self.mage_state()['resources'][0]['current'], 2)
        self.assertEqual(self._character_hp('raziel'), 9)
        self.assertEqual(list_pending_attack_resolutions(self.database, requested_by_id='morthak', requested_by_role='player'), [])

    def test_pending_private_expired_and_master_recovery(self):
        self.missiles()
        self.assertEqual(list_pending_attack_resolutions(self.database, requested_by_id='raziel', requested_by_role='player'), [])
        self.assertEqual(len(list_pending_attack_resolutions(self.database, requested_by_id='master', requested_by_role='gm')), 1)
        self.assertEqual(list_pending_attack_resolutions(self.database, requested_by_id='morthak', requested_by_role='player', now=_now()+timedelta(minutes=16)), [])

    def test_resource_change_invalidates_without_damaging_target(self):
        resolution = self.missiles()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("UPDATE character_states SET version=version+1 WHERE profile_id='morthak'")
        with self.assertRaises(CombatExpiredError):
            confirm_attack_resolution(self.database, resolution_id=resolution['resolution_id'], requested_by_id='morthak', requested_by_role='player')
        self.assertEqual(self._character_hp('raziel'), 14)
        self.assertEqual(self.mage_state()['resources'][0]['current'], 3)
        self.assertEqual(list_pending_attack_resolutions(self.database, requested_by_id='morthak', requested_by_role='player'), [])

    def test_two_previews_cannot_spend_same_resource_snapshot(self):
        first = self.missiles('spell-first')
        second = self.missiles('spell-second')
        confirm_attack_resolution(self.database, resolution_id=first['resolution_id'], requested_by_id='morthak', requested_by_role='player')
        with self.assertRaises(CombatExpiredError):
            confirm_attack_resolution(self.database, resolution_id=second['resolution_id'], requested_by_id='morthak', requested_by_role='player')
        self.assertEqual(self.mage_state()['resources'][0]['current'], 2)
        self.assertEqual(self._character_hp('raziel'), 9)

    def test_no_resource_cannot_roll_magic(self):
        state = self.mage_state()
        state['resources'][0]['current'] = 0
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'", (json.dumps(state),))
        with self.assertRaises(ValueError):
            self.missiles()
        self.assertEqual(self._character_hp('raziel'), 14)

    def test_target_failure_rolls_back_resource_consumption(self):
        resolution = self.missiles()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("DELETE FROM character_states WHERE profile_id='raziel'")
        with self.assertRaises(ValueError):
            confirm_attack_resolution(self.database, resolution_id=resolution['resolution_id'], requested_by_id='morthak', requested_by_role='player')
        self.assertEqual(self.mage_state()['resources'][0]['current'], 3)

    def test_unsupported_level_and_blocked_magic_do_not_guess(self):
        with self.assertRaises(ValueError):
            magic_missile_definition({**self.mage, 'level': 4}, self.mage_state()['resources'])
        with self.assertRaises(ValueError):
            magic_missile_definition({**self.mage, 'id': 'raziel'}, self.mage_state()['resources'])
        with self.assertRaises(ValueError):
            magic_missile_definition({**self.mage, 'session_abilities': []}, self.mage_state()['resources'])

    def test_pending_api_requires_auth_and_filters_owner(self):
        self.missiles()
        settings = replace(main.settings, database_path=self.database, master_token='fixture-master')
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main, 'settings', settings), closing(TestClient(main.app)) as client:
            self.assertEqual(client.get('/combat/attacks/pending').status_code, 401)
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='raziel')
            self.assertEqual(client.get('/combat/attacks/pending').json(), [])
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
            self.assertEqual(len(client.get('/combat/attacks/pending').json()), 1)
