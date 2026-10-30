"""Deterministic lifecycle proofs on existing disposable native fixtures."""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app.combat_effects import effect_command, readeffects


class TouchTurnLifecycleTests(TestCase):
    def setUp(self):
        import test_necromancer_integrity as fixtures
        self.fixture = fixtures.TouchTransactionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db

    def command(self, action, request_id, payload=None):
        return effect_command(self.db, actor_id='master', actor_role='gm',
            request_id=request_id, expected_version=readeffects(self.db)['version'],
            action=action, payload=payload or {})

    def activate(self):
        self.command('start', 'lifecycle-start', {'participants':[
            {'target_type':'character','target_id':'morthak','name':'Morthak','initiative':20},
            {'target_type':'token','target_id':self.fixture.token['id'],'name':'Alvo vivo','initiative':1}]})
        from app.combat import confirm_attack_resolution
        with patch('app.necromancer_spells.touch_rider', return_value={'dot_hp':True}):
            preview = self.fixture.resolve()
            confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'],
                requested_by_id='morthak', requested_by_role='player')

    def hp(self):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',
                (self.fixture.token['id'],)).fetchone()[0]

    def test_loss_happens_on_target_turn_once_per_command_and_end_clears_it(self):
        self.activate()
        before = self.hp()
        state = readeffects(self.db)
        args = dict(actor_id='master',actor_role='gm',request_id='lifecycle-target-turn',
                    expected_version=state['version'],action='next_turn',payload={})
        with patch('app.necromancer_spells.roll_formula', return_value={'total':1}) as dice:
            first = effect_command(self.db, **args)
            self.assertEqual(first, effect_command(self.db, **args))
            self.assertEqual(before-1, self.hp())
            self.command('next_turn', 'lifecycle-caster-turn')
            self.assertEqual(1, dice.call_count, 'DOT must not run on caster turn or retry')
        with patch('app.necromancer_spells.roll_formula', return_value={'total':6}):
            self.command('next_turn', 'lifecycle-no-loss')
        self.assertEqual(before-1, self.hp())
        self.command('end', 'lifecycle-end')
        self.assertFalse(any(effect.get('dot_hp') for effect in readeffects(self.db)['effects']))

    def test_lethal_tick_removes_dot_and_skips_dead_target(self):
        self.activate()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',
                       (self.fixture.token['id'],))
        with patch('app.necromancer_spells.roll_formula', return_value={'total':1}):
            result = self.command('next_turn', 'lifecycle-lethal')
        self.assertEqual(0, self.hp())
        self.assertFalse(any(effect.get('dot_hp') for effect in result['effects']))
        encounter = result['encounter']
        current = encounter['participants'][encounter['turn_index']]
        self.assertEqual('morthak', current['target_id'])


class CloneConcentrationLifecycleTests(TestCase):
    def test_concentration_end_retries_without_consuming_another_fragment_or_use(self):
        import test_morthak_high_spells as fixtures
        fixture = fixtures.HighSpellTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        route = '/characters/morthak/techniques/clonagem'
        first = fixture.fixture.client.post(route, json={'request_id':'lifecycle-clone-cast'})
        self.assertEqual(200, first.status_code, first.text)
        with closing(sqlite3.connect(fixture.path)) as db:
            self.assertEqual(2, db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])
        body = {'request_id':'lifecycle-clone-end', 'mode':'end'}
        ended = fixture.fixture.client.post(route, json=body)
        self.assertEqual(200, ended.status_code, ended.text)
        self.assertEqual(ended.json(), fixture.fixture.client.post(route, json=body).json())
        with closing(sqlite3.connect(fixture.path)) as db:
            self.assertEqual(0, db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])
            self.assertEqual(0, db.execute("SELECT quantity FROM player_inventory WHERE item_path='fragment-test'").fetchone()[0])
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            self.assertEqual(0, next(r['current'] for r in state['resources'] if r['key']=='clonagem'))


class SummonDismissalLifecycleTests(TestCase):
    def test_dismissing_one_summon_preserves_other_and_never_refunds_on_retry(self):
        import test_opencode_three_sheets_gaps as fixtures
        from app.summons import dismiss_summon
        fixture = fixtures.SummonCoexistenceGapTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        skeleton, zombie = fixture.create_pair()
        with closing(sqlite3.connect(fixture.path)) as db:
            before = db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0]
        args = dict(caster='morthak',token_id=skeleton['id'],request_id='lifecycle-dismiss-skeleton',
                    actor_id='morthak',actor_role='player')
        first = dismiss_summon(fixture.path, **args)
        self.assertEqual(first, dismiss_summon(fixture.path, **args))
        self.assertFalse(first['resource_refunded'])
        with closing(sqlite3.connect(fixture.path)) as db:
            self.assertEqual(before, db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            sheet = json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(skeleton['id'],)).fetchone()[0])
            self.assertTrue(sheet['summon']['dismissed'])
            self.assertGreater(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(zombie['id'],)).fetchone()[0], 0)
