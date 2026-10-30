import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from app.combat_effects import effect_command, readeffects
from app.scene_play import change_session_status
from app.session_ledger import list_session_ledger
from app.access import AccessContext
import test_session_coherence as fixture
import test_battle_mode as battle_fixture


class EffectLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.SessionCoherenceTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.database
        self.fixture._character()
        self.session = self.fixture._session('effects')
        change_session_status(self.db, self.session['id'], 'active')

    def command(self, action, **payload):
        state = readeffects(self.db)
        return effect_command(self.db, actor_id='master', actor_role='gm',
            request_id=f"lifecycle-{state['version']:04}", expected_version=state['version'], action=action, payload=payload)

    def add_effects(self):
        for duration in ('rounds', 'scene', 'manual', 'rest', 'next_attack'):
            self.command('apply', target_type='character', target_id='vezemir', label=duration,
                source='fixture', duration=duration, rounds=3, modifiers={'armor_class_bonus': 2})
        with closing(sqlite3.connect(self.db)) as db, db:
            from app.dorn_spells import add_effect
            add_effect(db, {'type': 'character', 'id': 'vezemir'}, 'escuridao', 590, 'fixture')

    def start(self):
        return self.command('start', participants=[{'target_type': 'character', 'target_id': 'vezemir', 'initiative': 10}])

    def test_combat_end_removes_round_bonuses_but_preserves_exploration_time(self):
        self.start()
        self.add_effects()
        result = self.command('end')
        self.assertFalse(result['encounter']['active'])
        self.assertEqual({'scene', 'manual', 'rest', 'next_attack', 'fictional_time'}, {e['duration'] for e in result['effects']})
        self.assertEqual(result, readeffects(self.db))

    def test_session_completion_closes_combat_and_timed_effects_without_healing_or_recharging(self):
        self.start()
        self.add_effects()
        with closing(sqlite3.connect(self.db)) as db:
            before = db.execute('SELECT state_json FROM character_states').fetchall()
        change_session_status(self.db, self.session['id'], 'completed')
        state = readeffects(self.db)
        self.assertFalse(state['encounter']['active'])
        self.assertEqual({'manual', 'rest'}, {e['duration'] for e in state['effects']})
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(before, db.execute('SELECT state_json FROM character_states').fetchall())
            self.assertEqual(4, db.execute('SELECT COUNT(*) FROM combat_effects WHERE active=0').fetchone()[0])
        self.assertFalse(any(e['title'] == 'Efeitos temporários encerrados com a sessão'
            for e in list_session_ledger(self.db, AccessContext(mode='player', profile_id='vezemir'))))

    def test_pause_preserves_effects_and_current_turn(self):
        self.start()
        self.add_effects()
        before = readeffects(self.db)
        change_session_status(self.db, self.session['id'], 'paused')
        self.assertEqual(before, readeffects(self.db))

    def test_recompleting_legacy_closed_session_repairs_once(self):
        self.start()
        self.add_effects()
        self.command('end')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE game_sessions SET status='completed' WHERE id=?", (self.session['id'],))
        change_session_status(self.db, self.session['id'], 'completed')
        state = readeffects(self.db)
        self.assertEqual({'manual', 'rest'}, {e['duration'] for e in state['effects']})
        change_session_status(self.db, self.session['id'], 'completed')
        self.assertEqual(state, readeffects(self.db))

    def test_closing_old_session_cannot_clear_new_session_effects(self):
        change_session_status(self.db, self.session['id'], 'completed')
        newer = self.fixture._session('newer')
        change_session_status(self.db, newer['id'], 'active')
        self.start()
        self.add_effects()
        state = readeffects(self.db)
        change_session_status(self.db, self.session['id'], 'completed')
        self.assertEqual(state, readeffects(self.db))

    def test_foreign_encounter_is_not_closed_even_without_active_session(self):
        self.start()
        self.add_effects()
        with closing(sqlite3.connect(self.db)) as db, db:
            state = readeffects(self.db)
            state['encounter']['game_session_id'] = 999
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(state['encounter']),))
        before = readeffects(self.db)
        change_session_status(self.db, self.session['id'], 'completed')
        self.assertEqual(before, readeffects(self.db))

    def test_current_exploration_session_expires_even_with_old_inactive_encounter(self):
        self.start()
        self.command('end')
        change_session_status(self.db, self.session['id'], 'completed')
        newer = self.fixture._session('exploration')
        change_session_status(self.db, newer['id'], 'active')
        self.add_effects()
        change_session_status(self.db, newer['id'], 'completed')
        self.assertEqual({'manual', 'rest'}, {e['duration'] for e in readeffects(self.db)['effects']})

    def test_session_completion_restores_battle_map_and_pins_without_healing(self):
        from app.scene_play import create_session
        from app.session_workspace import get_workspace_snapshot
        from app.combat import confirm_attack_resolution
        battle = battle_fixture.BattleModeTests()
        battle.setUp()
        self.addCleanup(battle.doCleanups)
        session = create_session(battle.db, request_id='close-battle-session', campaign_id='fixture',
            title='Arena', created_by='master')[0]
        change_session_status(battle.db, session['id'], 'active')
        battle.start()
        attack = battle.attack()
        confirm_attack_resolution(battle.db, resolution_id=attack['resolution_id'], requested_by_id='vezemir', requested_by_role='player')
        hp = next(t['current_hp'] for t in get_workspace_snapshot(battle.db, is_gm=True)['tokens'] if t['id'] == battle.enemy['id'])
        change_session_status(battle.db, session['id'], 'completed')
        restored = get_workspace_snapshot(battle.db, is_gm=True)
        self.assertEqual(restored['map']['id'], battle.initial['map']['id'])
        enemy = next(t for t in restored['tokens'] if t['id'] == battle.enemy['id'])
        self.assertEqual((enemy['latitude'], enemy['longitude'], enemy['current_hp']), (35, 60, hp))
        self.assertFalse(readeffects(battle.db)['encounter']['active'])

    def test_cleanup_failure_rolls_back_session_and_effects_together(self):
        self.start()
        self.add_effects()
        before = readeffects(self.db)
        with patch('app.combat_effects.expire_session_effects', side_effect=RuntimeError('fixture failure')):
            with self.assertRaises(RuntimeError):
                change_session_status(self.db, self.session['id'], 'completed')
        self.assertEqual(before, readeffects(self.db))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual('active', db.execute('SELECT status FROM game_sessions WHERE id=?', (self.session['id'],)).fetchone()[0])
