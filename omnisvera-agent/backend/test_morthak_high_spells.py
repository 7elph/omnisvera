import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_morthak_sheet as fixtures
from app.combat_effects import effect_command,readeffects,change_hp


class HighSpellTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.MorthakSheetTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.path=self.fixture.db
        from app.spatial_grid import init_spatial
        from app.session_workspace import save_workspace_token
        init_spatial(self.path)
        self.pin=save_workspace_token(self.path,token_type='character',character_id='morthak',name='Morthak',visible_to_players=True,latitude=20,longitude=20)
        with closing(sqlite3.connect(self.path)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            state.update(current_hp=36,maximum_hp=36)
            state['resources'] += [{'key':k,'current':1,'maximum':1,'recharge':'inn_rest'} for k in ['clonagem','magia_da_morte']]
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps(state),))
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='morthak'").fetchone()[0]);data['race']={'movement':'9 m'};data['armor']={'armor_class':12};data['attributes']['strength']=10
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='morthak'",(json.dumps(data),))
            db.execute("INSERT INTO session_workspace_map_grids VALUES('default','square',20,20,1.5,0,0,'chebyshev',1,1)")
            for identity,x in [(self.pin['id'],5),(self.fixture.ogre['id'],6)]:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,5,1,1,1)",(identity,x))
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('morthak','fragment-test','Fragmento de Cristal Arcano',1,0,'now')")
            db.execute("INSERT INTO session_custom_items(name,item_type,description,effects_json,effect_rules_json,mechanics_json,usable,created_at,updated_at) VALUES('Cajado','weapon','','[]','[]','{\"damage_formula\":\"1d6+2\"}',0,'now','now')")
            item=db.execute('SELECT max(id) FROM session_custom_items').fetchone()[0]
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,updated_at) VALUES('morthak',?,'Cajado',1,1,'arma corpo a corpo','now')",('session-item:'+str(item),))

    def command(self,action,payload,request=None):
        state=readeffects(self.path)
        return effect_command(self.path,actor_id='morthak',actor_role='player',request_id=request or 'high-spell-'+str(state['version']),expected_version=state['version'],action=action,payload=payload,allow_player=True)

    def test_clone_atomic_replay_component_and_mundane_stats(self):
        from app.morthak_high_spells import cleanup
        state=readeffects(self.path);args=dict(actor_id='morthak',actor_role='player',request_id='clone-once',expected_version=state['version'],action='necro_spell_cast',payload={'spell_id':'clonagem'},allow_player=True)
        first=effect_command(self.path,**args);self.assertEqual(first,effect_command(self.path,**args))
        with closing(sqlite3.connect(self.path)) as db,db:
            tokens=db.execute("SELECT id,current_hp,sheet_json FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchall()
            self.assertEqual(2,len(tokens));self.assertEqual(9,tokens[0][1]);self.assertEqual('1d6',json.loads(tokens[0][2])['attacks'][0]['damage'])
            self.assertEqual(0,db.execute("SELECT quantity FROM player_inventory WHERE item_path='fragment-test'").fetchone()[0])
            change_hp(db,'token',tokens[0][0],-9,'now');self.assertIsNone(db.execute('SELECT id FROM session_workspace_tokens WHERE id=?',(tokens[0][0],)).fetchone())
            change_hp(db,'character','morthak',-36,'now');cleanup(db,'now')
            self.assertEqual(0,db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])

    def test_component_missing_rolls_back_without_resource_or_tokens(self):
        with closing(sqlite3.connect(self.path)) as db,db:db.execute("UPDATE player_inventory SET quantity=0 WHERE item_path='fragment-test'")
        with self.assertRaisesRegex(ValueError,'fragmento'):self.command('necro_spell_cast',{'spell_id':'clonagem'})
        with closing(sqlite3.connect(self.path)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0]);self.assertEqual(1,next(r['current'] for r in state['resources'] if r['key']=='clonagem'))

    def test_ended_combat_does_not_block_outside_combat_cloning(self):
        with closing(sqlite3.connect(self.path)) as db,db:db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps({'active':False,'attacks_used':1,'action_committed':True}),))
        result=self.command('necro_spell_cast',{'spell_id':'clonagem'});self.assertEqual('Clonagem',result['protocol_result']['spell'])

    def test_clone_one_round_execution_and_five_round_expiry(self):
        state=readeffects(self.path)
        effect_command(self.path,actor_id='master',actor_role='gm',request_id='high-battle',expected_version=state['version'],action='start',payload={'map_id':'default','battle_mode':True,'participants':[{'target_type':'character','target_id':'morthak','name':'Morthak','initiative':20},{'target_type':'token','target_id':self.fixture.ogre['id'],'name':'Ogro','initiative':1}]})
        self.command('necro_spell_cast',{'spell_id':'clonagem'})
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(0,db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])
        for _ in range(2):
            state=readeffects(self.path);effect_command(self.path,actor_id='master',actor_role='gm',request_id='high-next-'+str(state['version']),expected_version=state['version'],action='next_turn',payload={})
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(2,db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])
        for _ in range(5):
            state=readeffects(self.path);effect_command(self.path,actor_id='master',actor_role='gm',request_id='high-round-'+str(state['version']),expected_version=state['version'],action='round',payload={})
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(0,db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])

    def test_ending_clones_removes_their_turns_and_preserves_current_caster_action(self):
        self._start_clone_battle()
        state = self.command('necro_spell_cast', {'spell_id': 'clonagem', 'mode': 'end'})
        members = state['encounter']['participants']
        self.assertEqual(['morthak', self.fixture.ogre['id']], [p['target_id'] for p in members])
        self.assertEqual('morthak', members[state['encounter']['turn_index']]['target_id'])
        self.assertFalse(state['encounter']['action_committed'])

    def _start_clone_battle(self):
        def gm(action, payload):
            state = readeffects(self.path)
            return effect_command(self.path, actor_id='master', actor_role='gm',
                                  request_id='clone-lifecycle-'+str(state['version']),
                                  expected_version=state['version'], action=action, payload=payload)
        gm('start', {'map_id': 'default', 'battle_mode': True, 'participants': [
            {'target_type': 'character', 'target_id': 'morthak', 'name': 'Morthak', 'initiative': 20},
            {'target_type': 'token', 'target_id': self.fixture.ogre['id'], 'name': 'Ogro', 'initiative': 1}]})
        self.command('necro_spell_cast', {'spell_id': 'clonagem'})
        gm('next_turn', {})
        gm('next_turn', {})
        return gm

    def test_clone_zero_hp_removes_only_its_turn_and_advances_to_successor(self):
        gm = self._start_clone_battle()
        state = gm('next_turn', {})
        clone = state['encounter']['participants'][state['encounter']['turn_index']]['target_id']
        with closing(sqlite3.connect(self.path)) as db, db:
            change_hp(db, 'token', clone, -9, 'now')
        after = readeffects(self.path)
        identities = [p['target_id'] for p in after['encounter']['participants']]
        self.assertNotIn(clone, identities)
        self.assertEqual(3, len(identities))
        self.assertEqual(identities[1], after['encounter']['participants'][after['encounter']['turn_index']]['target_id'])
        gm('next_turn', {})
        self.assertEqual(self.fixture.ogre['id'], readeffects(self.path)['encounter']['participants'][readeffects(self.path)['encounter']['turn_index']]['target_id'])

    def test_clone_expiry_via_real_turn_transitions_leaves_no_invisible_turns(self):
        gm = self._start_clone_battle()
        for _ in range(5 * 4):
            gm('next_turn', {})
        state = readeffects(self.path)
        self.assertEqual(['morthak', self.fixture.ogre['id']],
                         [p['target_id'] for p in state['encounter']['participants']])

    def test_clone_owner_attack_and_turn_retries_are_single_use_and_other_player_is_denied(self):
        from app import main
        from app.access import AccessContext
        gm = self._start_clone_battle()
        state = gm('next_turn', {})
        clone = state['encounter']['participants'][state['encounter']['turn_index']]['target_id']
        client = self.fixture.client
        route = f'/gm/combat/tokens/{clone}/attacks/resolve'
        body = {'request_id': 'clone-owned-attack', 'attack_id': '0',
                'target_type': 'token', 'target_id': self.fixture.ogre['id'],
                'roll_mode': 'physical', 'd20': 20}
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='raziel')
        denied = client.post(route, json=body)
        self.assertEqual(403, denied.status_code, denied.text)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
        first = client.post(route, json=body)
        self.assertEqual(200, first.status_code, first.text)
        confirmation = '/combat/attacks/' + first.json()['resolution_id'] + '/confirm'
        applied = client.post(confirmation, json={})
        self.assertEqual(200, applied.status_code, applied.text)
        self.assertEqual(applied.json(), client.post(confirmation, json={}).json())
        blocked = client.post(route, json={**body, 'request_id': 'clone-no-second-attack'})
        self.assertEqual(400, blocked.status_code, blocked.text)
        turn = {'request_id': 'clone-owner-pass', 'expected_version': readeffects(self.path)['version'], 'action': 'next_turn'}
        passed = client.post('/combat/next-turn', json=turn)
        self.assertEqual(200, passed.status_code, passed.text)
        self.assertEqual(passed.json(), client.post('/combat/next-turn', json=turn).json())
        encounter = readeffects(self.path)['encounter']
        self.assertNotEqual(clone, encounter['participants'][encounter['turn_index']]['target_id'])
        self.assertFalse(encounter['action_committed'])

    def test_last_clone_dying_closes_round_once_and_preserves_other_clone(self):
        gm = self._start_clone_battle()
        state = readeffects(self.path)
        gm('initiative', {'participants': [
            {**p, 'initiative': 30 if p['target_id'] == self.fixture.ogre['id'] else 1}
            for p in state['encounter']['participants']]})
        gm('next_turn', {})
        state = gm('next_turn', {})
        encounter = state['encounter']
        clone = encounter['participants'][encounter['turn_index']]['target_id']
        self.assertEqual(len(encounter['participants']) - 1, encounter['turn_index'])
        with closing(sqlite3.connect(self.path)) as db, db:
            change_hp(db, 'token', clone, -9, 'now')
        after = readeffects(self.path)
        self.assertEqual(state['round'] + 1, after['round'])
        self.assertEqual(self.fixture.ogre['id'], after['encounter']['participants'][after['encounter']['turn_index']]['target_id'])
        self.assertEqual(3, len(after['encounter']['participants']))
        self.assertNotIn(clone, [p['target_id'] for p in after['encounter']['participants']])

    def test_death_spell_save_and_ninety_percent_hp_cost(self):
        with patch('app.morthak_high_spells.roll_formula',return_value={'total':2}),patch('app.necromancer_spells.save_difficult',return_value={'success':False,'total':1}):
            result=self.command('necro_spell_cast',{'spell_id':'magia-da-morte'})
        self.assertEqual(3,result['protocol_result']['hp_after'])
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(0,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.fixture.ogre['id'],)).fetchone()[0])

    def test_death_spell_hp_cost_is_not_absorbed_by_temporary_hp(self):
        with closing(sqlite3.connect(self.path)) as db,db:db.execute("UPDATE character_states SET state_json=json_set(state_json,'$.temporary_hp',10) WHERE profile_id='morthak'")
        with patch('app.morthak_high_spells.roll_formula',return_value={'total':2}),patch('app.necromancer_spells.save_difficult',return_value={'success':True,'total':20}):result=self.command('necro_spell_cast',{'spell_id':'magia-da-morte'})
        self.assertEqual(3,result['protocol_result']['hp_after'])
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(10,json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])['temporary_hp'])

    def test_high_spell_wrong_owner_is_rejected(self):
        state=readeffects(self.path)
        with self.assertRaises(PermissionError):effect_command(self.path,actor_id='raziel',actor_role='player',request_id='other-owner-high',expected_version=state['version'],action='necro_spell_cast',payload={'spell_id':'clonagem'},allow_player=True)

    def test_owner_http_route_and_end_concentration_after_spending(self):
        response=self.fixture.client.post('/characters/morthak/techniques/clonagem',json={'request_id':'high-http-once'})
        self.assertEqual(200,response.status_code,response.text)
        repeated=self.fixture.client.post('/characters/morthak/techniques/clonagem',json={'request_id':'high-http-once'})
        self.assertEqual(response.json(),repeated.json())
        ended=self.fixture.client.post('/characters/morthak/techniques/clonagem',json={'request_id':'high-http-end','mode':'end'})
        self.assertEqual(200,ended.status_code,ended.text)
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(0,db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])

    def test_approved_pack_preserves_hp_level_spent_resources_and_is_idempotent(self):
        from app.approved_spell_pack import apply_approved_spell_pack
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("INSERT INTO character_definition_overrides VALUES('dorn7',?,'now')",(json.dumps({'approved_build':'dorn-mage3-approved','level':5,'approved_session_abilities':[{'id':k,'name':k} for k in ['misseis-magicos','levitacao','escuridao','relampago','dorn-reparo']]}),))
            db.execute("INSERT INTO character_states VALUES('dorn7',?,1,'now')",(json.dumps({'current_hp':17,'maximum_hp':35,'resources':[{'key':'dorn_misseis_magicos','current':2,'maximum':3}]}),))
        self.assertEqual(['dorn7','morthak'],apply_approved_spell_pack(self.path));self.assertEqual([],apply_approved_spell_pack(self.path))
        with closing(sqlite3.connect(self.path)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0]);overrides=json.loads(db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()[0])
            self.assertEqual((17,35),(state['current_hp'],state['maximum_hp']));self.assertEqual(2,state['resources'][0]['current']);self.assertEqual(5,overrides['level'])
            self.assertEqual({'misseis-magicos','relampago','dorn-reparo','reflexos','teia','forca-arcana','dissipar-magia'},{a['id'] for a in overrides['approved_session_abilities']})

    def test_skeleton_reanimated_creature_and_clones_can_coexist(self):
        from app import main
        from app.summons import create_summon
        with closing(sqlite3.connect(self.path)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0]);state['resources'].append({'key':'animar_mortos','current':1,'maximum':1})
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps(state),))
            db.execute('UPDATE session_workspace_tokens SET current_hp=0,sheet_json=? WHERE id=?',(json.dumps({'reanimation_allowed':True}),self.fixture.ogre['id']))
        first=create_summon(self.path,caster='morthak',technique='levantar-esqueleto',spec=main._SUMMON_DEFAULTS['levantar-esqueleto'],request_id='coexist-skeleton',actor_id='morthak',actor_role='player')
        second=create_summon(self.path,caster='morthak',technique='animar-mortos',spec=main._SUMMON_DEFAULTS['animar-mortos'],corpse_id=self.fixture.ogre['id'],request_id='coexist-zombie',actor_id='morthak',actor_role='player')
        self.command('necro_spell_cast',{'spell_id':'clonagem'})
        self.command('necro_spell_cast',{'spell_id':'clonagem','mode':'end'})
        with closing(sqlite3.connect(self.path)) as db:
            for token in [first['token']['id'],second['token']['id']]:self.assertGreater(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(token,)).fetchone()[0],0)
