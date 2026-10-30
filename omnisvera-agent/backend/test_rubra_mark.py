"""Marca Rubra uses the native effect receipt, blood resource and grid."""
import json
import sqlite3
from contextlib import closing

from app import main
from app.access import AccessContext
from app.combat_effects import readeffects
from test_hemomancy_weapons import HemomancyGridFixture


class RubraMarkTests(HemomancyGridFixture):
    def mark(self, request='rubra-native-001', target=None):
        return self.use('raziel','marca-rubra',dict(request_id=request,
            target_type='token',target_id=target or self.wounded['id']))

    def update_target(self, **values):
        with closing(sqlite3.connect(self.db)) as db,db:
            for field,value in values.items():
                assert field in {'current_hp','sheet_json','visible_to_players','map_id'}
                db.execute(f'UPDATE session_workspace_tokens SET {field}=? WHERE id=?',(value,self.wounded['id']))

    def test_mark_retry_survives_target_healing_and_spends_once(self):
        first=self.mark();self.assertEqual(200,first.status_code,first.text)
        self.update_target(current_hp=12)
        retry=self.mark();self.assertEqual(200,retry.status_code,retry.text)
        self.assertEqual(first.json(),retry.json());self.assertEqual(4,self.laminas())

    def test_mark_rejects_dead_bloodless_hidden_and_wrong_map_without_spending(self):
        for values in ({'current_hp':0},{'sheet_json':json.dumps({'has_blood':False})},
                       {'visible_to_players':0},{'map_id':'elsewhere'}):
            with self.subTest(values=values):
                self.update_target(current_hp=6,sheet_json='{}',visible_to_players=1,map_id='default')
                self.update_target(**values)
                self.assertEqual(400,self.mark().status_code)
                self.assertEqual(5,self.laminas());self.assertEqual([],readeffects(self.db)['effects'])

    def test_mark_rejects_target_beyond_nine_meters(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=12 WHERE token_id=?',(self.wounded['id'],))
        reply=self.mark();self.assertEqual(400,reply.status_code,reply.text);self.assertEqual(5,self.laminas())

    def test_mark_is_map_scoped_persisted_and_audited_once(self):
        self.assertEqual(200,self.mark().status_code)
        self.assertEqual(200,self.mark().status_code)
        snapshot=readeffects(self.db)
        effect=next(e for e in snapshot['effects'] if e['source']=='Marca Rubra (Lâminas de Sangue)')
        self.assertEqual('default',effect.get('map_id'))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute("SELECT count(*) FROM session_ledger WHERE source_id='rubra-native-001' AND source_type='ability_activation'").fetchone()[0])

    def test_mark_conflicting_retry_and_other_player_are_rejected(self):
        self.assertEqual(200,self.mark().status_code)
        self.assertEqual(400,self.mark(target=self.healthy['id']).status_code)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='morthak')
        self.assertEqual(403,self.mark('rubra-owner-002').status_code);self.assertEqual(4,self.laminas())

    def test_mark_follows_turn_guard_but_keeps_existing_non_attack_cost(self):
        self.start_combat()
        self.assertEqual(200,self.mark().status_code)
        self.assertFalse(readeffects(self.db)['encounter'].get('action_committed',False))
        shot=self.attack('arco','skill',request='rubra-heartshot-002')
        self.assertEqual(200,shot.status_code,shot.text)
        self.assertEqual(200,self.confirm(shot).status_code)
        self.assertEqual(3,self.laminas())
        self.assertEqual(400,self.mark('rubra-after-attack').status_code)
        self.assertEqual(200,self.mark().status_code,'Accepted receipt survives committed attack')

    def test_mark_counter_cannot_go_negative(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['resources'][0]['current']=0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        self.assertEqual(400,self.mark().status_code)
        self.assertEqual(0,self.laminas());self.assertEqual([],readeffects(self.db)['effects'])

    def test_mark_clears_at_combat_end_and_cannot_boost_other_targets(self):
        self.start_combat();self.assertEqual(200,self.mark().status_code)
        self.command('end','rubra-end-native')
        self.assertFalse(any(e.get('hemomancy_kind')=='mark' for e in readeffects(self.db)['effects']))
        self.assertEqual(4,self.laminas(),'Ending combat never refills blood')

    def test_mark_reply_does_not_expose_private_effects(self):
        self.command('apply','rubra-private-effect',target_type='token',target_id=self.healthy['id'],
                     label='Objetivo secreto',source='Mestre',duration='scene',modifiers={})
        reply=self.mark();self.assertEqual(200,reply.status_code)
        self.assertNotIn('Objetivo secreto',reply.text)

    def test_mark_ring_cannot_be_extended_by_client(self):
        reply=self.client.get('/gm/grid/range',params={'ref':'technique:raziel:marca-rubra',
            'attacker_character_id':'raziel','map_id':'default','slot':'ranged'})
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual('ranged',reply.json()['mode'])
        self.assertEqual(6,reply.json()['range_cells'])


