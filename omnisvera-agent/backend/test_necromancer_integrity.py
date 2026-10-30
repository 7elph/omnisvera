import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch
from test_session8_necromancer import AterrorizarTests
from app.combat_effects import effect_command, readeffects
import test_combat as combat_fixture


class TouchTransactionTests(TestCase):
    def setUp(self):
        self.fixture=combat_fixture.CombatAttackResolutionTests();self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown);self.db=self.fixture.database
        self.fixture._insert_character('morthak',10,10)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",
                (json.dumps({'current_hp':10,'maximum_hp':10,'resources':[{'key':'toque_sombrio','current':1,'maximum':1}]}),))
            db.execute('INSERT INTO character_definition_overrides VALUES(?,?,?)',
                ('morthak',json.dumps({'specialization':'necromante','level':5}),'now'))
        from app.session_workspace import save_workspace_token
        self.token=save_workspace_token(self.db,token_type='monster',name='Alvo vivo',latitude=10,longitude=10,
            current_hp=10,maximum_hp=10,visible_to_players=True,
            sheet={'armor_class':10,'saving_throw':99,'attributes':{'strength':10,'constitution':10}})

    def resolve(self):
        from app.combat import resolve_attack
        return resolve_attack(self.db,request_id='touch-transaction-fixture',actor_character_id='morthak',actor_name='Morthak',
            requested_by_id='morthak',requested_by_role='player',definition={'id':'morthak','name':'Morthak','attacks':[
                {'id':'toque-sombrio','name':'Toque Sombrio','attack_bonus':1,'damage':'1d4','weapon_item_path':'technique:toque-sombrio'}]},
            inventory=[],attack_id='toque-sombrio',target={'type':'token','id':self.token['id'],'name':'Alvo vivo','armor_class':10,'current_hp':10},
            roll_mode='physical',physical_d20=15,rng=combat_fixture.SequenceRng(2))[0]

    def test_touch_retry_never_rerolls_or_requires_spent_daily_resource(self):
        from app.combat import confirm_attack_resolution
        with patch('app.necromancer_spells.touch_rider',return_value={'dot_hp':True}) as rider:
            first=self.resolve()
            confirmed,_=confirm_attack_resolution(self.db,resolution_id=first['resolution_id'],requested_by_id='morthak',requested_by_role='player')
            replay=self.resolve()
            confirm_attack_resolution(self.db,resolution_id=first['resolution_id'],requested_by_id='morthak',requested_by_role='player')
            self.assertEqual(confirmed['resolution_id'],replay['resolution_id']);self.assertEqual(1,rider.call_count)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            self.assertEqual(0,state['resources'][0]['current'])
            self.assertEqual(8,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.token['id'],)).fetchone()[0])
        self.assertEqual(1,len([e for e in readeffects(self.db)['effects'] if e.get('dot_hp')]))

    def test_touch_rejects_undead_before_dice(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',
                (json.dumps({'armor_class':10,'saving_throw':99,'is_undead':True,'attributes':{'strength':10}}),self.token['id']))
        with patch('app.necromancer_spells.touch_rider') as rider:
            with self.assertRaisesRegex(ValueError,'vivo'):self.resolve()
            rider.assert_not_called()


class NecromancerIntegrityTests(AterrorizarTests):
    def setUp(self):
        super().setUp()
        from app.session_ledger import init_session_ledger
        from app.dice_rolls import init_dice_rolls
        init_dice_rolls(self.db)
        init_session_ledger(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=1 WHERE id='gob'")

    def cast(self, request_id='necro-fixture-command', **extra):
        state = readeffects(self.db)
        return effect_command(self.db, actor_id='morthak', actor_role='player',
            request_id=request_id, expected_version=state['version'], allow_player=True,
            action='necro_spell_cast', payload={'spell_id':'aterrorizar',
                'position_confirmed':True, 'targets':[{'type':'token','id':'gob','distance_meters':5, 'dv':1}], **extra})

    def test_missing_jp_rejects_without_spending_or_effect(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob'",
                (json.dumps({'hit_dice':1,'attributes':{'wisdom':10}}),))
        with self.assertRaisesRegex(ValueError,'Proteção|JP'):
            self.cast()
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
        self.assertEqual(1,state['resources'][0]['current'])
        self.assertEqual([],readeffects(self.db)['effects'])

    def test_hidden_target_cannot_be_cast_by_player(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id='gob'")
        with self.assertRaises(PermissionError): self.cast()

    def test_fear_penalizes_attacks_and_saves_without_changing_damage(self):
        from app.combat_effects import apply_definition_effects
        definition={'attacks':[{'id':'0','attack_bonus':3,'damage':'1d6'}],
            'defenses':{'saving_throw':13,'saving_throw_bonus':1}}
        result=apply_definition_effects(definition,[{'id':'fear','modifiers':{},'difficult_tests':True}])
        self.assertEqual(1,result['attacks'][0]['attack_bonus'])
        self.assertEqual('1d6',result['attacks'][0]['damage'])
        self.assertEqual(-1,result['defenses']['saving_throw_bonus'])

    def test_persisted_dv_cannot_be_lowered_by_player(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob'",
                (json.dumps({'hit_dice':2,'saving_throw':99,'attributes':{'wisdom':10}}),))
        result=self.cast()
        self.assertIn('imune', result['protocol_result']['results'][0]['skipped'])
        self.assertEqual([],result['effects'])

    def test_retry_returns_receipt_and_public_cast_is_logged_once(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob'",
                (json.dumps({'hit_dice':1,'saving_throw':99,'attributes':{'wisdom':10}}),))
        first=self.cast(); second=self.cast()
        self.assertEqual(first,second)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute("SELECT count(*) FROM session_ledger WHERE source_type='ability_activation' AND source_id='necro-fixture-command'").fetchone()[0])

    def test_exploration_clock_does_not_age_new_fear_and_replay_is_safe(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob'",
                (json.dumps({'hit_dice':1,'saving_throw':99,'attributes':{'wisdom':10}}),))
        self.cast()
        state=readeffects(self.db)
        request=dict(actor_id='master',actor_role='gm',request_id='necro-time-fixture',
            expected_version=state['version'],action='necro_spell_time',payload={'turns':100})
        first=effect_command(self.db,**request)
        self.assertEqual(state['effects'],first['effects'])
        self.assertEqual(first,effect_command(self.db,**request))
