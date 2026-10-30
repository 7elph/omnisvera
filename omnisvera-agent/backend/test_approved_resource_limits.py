import json
import sqlite3
import unittest
from contextlib import closing

import test_session6_rewards as fixture
from app.approved_resource_limits import apply_approved_resource_limits
from app.character_play import init_character_play


class ApprovedResourceLimitsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.RewardTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        init_character_play(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            for profile, key, maximum, current in [('raziel', 'reserva_de_sangue', 5, 3), ('dorn7', 'dorn_misseis_magicos', 1, 0)]:
                state = {'current_hp': 7, 'maximum_hp': 20, 'session_notes': 'keep', 'resources': [{'key': key, 'maximum': maximum, 'current': current}]}
                db.execute('INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?) ON CONFLICT(profile_id) DO UPDATE SET state_json=excluded.state_json', (profile, json.dumps(state), 'now'))
            db.execute("UPDATE player_inventory SET charges_current=0,charges_max=1 WHERE item_title='Pulseira de Vinhas'")

    def test_preserves_spent_uses_hp_combat_and_is_idempotent(self):
        with closing(sqlite3.connect(self.db)) as db:
            combat = db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0]
        self.assertEqual(apply_approved_resource_limits(self.db), ['raziel', 'dorn7', 'vezemir'])
        self.assertEqual(apply_approved_resource_limits(self.db), [])
        with closing(sqlite3.connect(self.db)) as db:
            for profile, maximum, current in [('raziel', 10, 8), ('dorn7', 3, 2)]:
                state = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (profile,)).fetchone()[0])
                self.assertEqual((state['resources'][0]['maximum'], state['resources'][0]['current']), (maximum, current))
                self.assertEqual((state['current_hp'], state['session_notes']), (7, 'keep'))
            self.assertEqual(db.execute("SELECT charges_max,charges_current,recharge FROM player_inventory WHERE item_title='Pulseira de Vinhas'").fetchone(), (2, 1, 'inn_rest'))
            self.assertEqual(db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0], combat)
            self.assertEqual(db.execute("SELECT count(*) FROM character_events WHERE event_type='approved_resource_limit'").fetchone()[0], 3)
