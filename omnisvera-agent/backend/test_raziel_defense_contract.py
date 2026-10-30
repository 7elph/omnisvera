"""Approved blood shield metadata delegates to the existing transactional effect."""
import copy
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app import main
from app.access import AccessContext
from app.combat_effects import effect_command, readeffects
from test_hemomante_techniques import TechniqueFixture


DEFINITION={
    'schema_version':1,'revision':'raziel-sangue-defensivo-campaign-v2',
    'approval':{'kind':'campaign','reference':'docs/ACTION_COMPLETION_2026-10-12.md'},
    'executor':{'binding':'raziel_sangue_defensivo'},
    'targeting':{'kind':'self','min_targets':1,'max_targets':1,'unique_by':'entity','include_self':True},
    'range':{'mode':'self','meters':0},'area':'self','duration':'rounds',
    'action_budget':'native_resource_turn_gate',
    'costs':[{'type':'resource','key':'reserva_de_sangue','amount':1,'recharge':'inn_rest'}],
    'resolution':{'effect':'armor_class_bonus','armor_class_bonus':2,'rounds':1},
}


class BloodDefenseDefinitionTests(TestCase):
    def test_real_catalog_resolves_without_mocking_the_integration(self):
        from app.action_library import native_action_contract
        contract = native_action_contract('technique:raziel:sangue-defensivo', 5)
        self.assertEqual({**DEFINITION, 'level': 5, 'ref': 'technique:raziel:sangue-defensivo'}, contract)

    def test_fixed_approved_definition_resolves_without_new_mechanics(self):
        from app.raziel_action_contracts import resolve_blood_defense_contract
        resolved=resolve_blood_defense_contract(DEFINITION,5)
        self.assertEqual({**DEFINITION,'level':5},resolved)

    def test_arbitrary_bonuses_cost_duration_target_and_code_are_not_allowed(self):
        from app.raziel_action_contracts import resolve_blood_defense_contract
        alterations=[('resolution','armor_class_bonus',3),('resolution','rounds',2),
                     ('resolution','script','eval()'),('targeting','include_self',False),
                     ('range','meters',9)]
        for section,key,value in alterations:
            changed=copy.deepcopy(DEFINITION);changed[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):
                resolve_blood_defense_contract(changed,5)
        changed=copy.deepcopy(DEFINITION);changed['costs'][0]['amount']=2
        with self.assertRaises(ValueError):resolve_blood_defense_contract(changed,5)
        for level in (True,0,21):
            with self.assertRaises(ValueError):resolve_blood_defense_contract(DEFINITION,level)


class BloodDefenseRouteTests(TechniqueFixture):
    def test_effective_sheet_and_description_use_real_catalog_contract(self):
        from app.action_library import describe_action, native_action_contract
        reply = self.client.get('/characters/raziel')
        self.assertEqual(200, reply.status_code, reply.text)
        definition = reply.json()['definition']
        ability = next(a for a in definition['session_abilities'] if a['id'] == 'sangue-defensivo')
        expected = native_action_contract('technique:raziel:sangue-defensivo', definition['level'])
        self.assertEqual(expected, ability['action_contract'])
        description = describe_action(self.db, 'technique:raziel:sangue-defensivo')
        self.assertEqual(expected, description['contract'])
        self.assertFalse(description['executable'])
        self.assertEqual('/characters/raziel/techniques/sangue-defensivo', description['execute']['endpoint'])

    def shield(self,request_id='blood-shield-contract-01',revision=DEFINITION['revision']):
        return self.use('raziel','sangue-defensivo',
            {'request_id':request_id,'definition_revision':revision})

    def state(self):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='raziel'").fetchone()

    def test_stale_new_command_does_not_normalize_roll_spend_or_create_receipt(self):
        before=self.state();effects=readeffects(self.db)
        with patch.object(main,'_playable_character',side_effect=AssertionError('No sheet normalization')), \
             patch('app.combat_effects.roll_formula',side_effect=AssertionError('No RNG')):
            reply=self.shield(revision='stale-client-revision')
        self.assertEqual(400,reply.status_code,reply.text)
        self.assertEqual(before,self.state())
        self.assertEqual(effects,readeffects(self.db))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(0,db.execute("SELECT COUNT(*) FROM combat_effect_commands WHERE request_id='blood-shield-contract-01'").fetchone()[0])

    def test_retry_after_form_state_and_revision_changes_recovers_original_receipt(self):
        first=self.shield();self.assertEqual(200,first.status_code,first.text)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(self.state()[0]);state['animal_form']='corvo'
            state['current_hp']=3
            db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='raziel'",(json.dumps(state),))
        before=self.state()
        with patch.object(main,'_playable_character',side_effect=AssertionError('No normalization on replay')):
            retry=self.shield(revision='obsolete-after-success')
        self.assertEqual(200,retry.status_code,retry.text)
        self.assertEqual(first.json(),retry.json())
        self.assertEqual(before,self.state())
        self.assertEqual(4,self.laminas())

    def test_replay_rejects_another_actor_and_another_source_with_same_id(self):
        first=self.shield();self.assertEqual(200,first.status_code,first.text)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        self.assertEqual(400,self.shield().status_code)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='morthak')
        self.assertEqual(403,self.shield().status_code)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        snapshot=readeffects(self.db)
        effect_command(self.db,actor_id='raziel',actor_role='player',allow_player=True,
            request_id='another-native-source-id',expected_version=snapshot['version'],action='apply',
            payload={'target_type':'character','target_id':'raziel','source':'Another source',
                     'label':'Other effect','duration':'scene','modifiers':{}})
        self.assertEqual(400,self.shield(request_id='another-native-source-id').status_code)
        self.assertEqual(4,self.laminas())

    def test_transaction_recovers_receipt_committed_after_early_lookup(self):
        first=self.shield();self.assertEqual(200,first.status_code,first.text)
        before=self.state()
        # Simulate an identical concurrent command committing after the early
        # lookup. Native effect_command must still recover without spending.
        with patch('app.combat_effects.replay_technique_effect',return_value=None):
            retry=self.shield()
        self.assertEqual(200,retry.status_code,retry.text)
        self.assertEqual(first.json(),retry.json());self.assertEqual(before,self.state())
        self.assertEqual(4,self.laminas())

    def test_missing_revision_keeps_legacy_clients_compatible(self):
        reply=self.use('raziel','sangue-defensivo',{'request_id':'legacy-blood-shield'})
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(4,self.laminas())

    def test_turn_gate_cost_and_one_round_expiry_preserve_native_budget(self):
        encounter={'active':True,'battle_mode':True,'map_id':'default','turn_index':1,
            'participants':[{'target_type':'character','target_id':'raziel'},
                            {'target_type':'token','target_id':self.wounded['id']}],
            'action_committed':False}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        self.assertEqual(400,self.shield(request_id='shield-out-of-turn').status_code)
        self.assertEqual(5,self.laminas())
        encounter['turn_index']=0
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        reply=self.shield();self.assertEqual(200,reply.status_code,reply.text)
        snapshot=readeffects(self.db)
        self.assertFalse(snapshot['encounter']['action_committed'])
        shields=[effect for effect in snapshot['effects'] if effect['source']=='Sangue Defensivo (Raziel)']
        self.assertEqual(1,len(shields));self.assertEqual({'armor_class_bonus':2},shields[0]['modifiers'])
        self.assertEqual(1,shields[0]['rounds']);self.assertEqual(4,self.laminas())
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='shield-elapse-round',
            expected_version=snapshot['version'],action='round',payload={})
        self.assertFalse(any(effect['source']=='Sangue Defensivo (Raziel)' for effect in readeffects(self.db)['effects']))
