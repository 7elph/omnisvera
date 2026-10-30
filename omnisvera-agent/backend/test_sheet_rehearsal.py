"""Coverage must come from executed evidence, not a hardcoded 'tested' list."""
from unittest import TestCase
from scripts.sheet_rehearsal import build_report
from scripts.run_sheet_test import backup_readonly, checked_port
from scripts.all_actions_simulation import Simulation
from contextlib import closing
from pathlib import Path
import socket
import sqlite3
from tempfile import TemporaryDirectory
import json


class SheetRehearsalReportTests(TestCase):
    def sheet(self):
        return {'definition': {'name': 'Raziel', 'level': 5,
            'attacks': [{'id': 'melee', 'name': 'Adagas', 'damage': '2d6+2'}],
            'session_abilities': [
                {'id': 'arma-de-sangue', 'name': 'Arma', 'active': True, 'mechanics_status': 'structured'},
                {'id': 'future', 'name': 'Nova magia', 'active': True, 'mechanics_status': 'structured'},
                {'id': 'vision', 'name': 'Visão', 'active': False},
                {'id': 'locked', 'name': 'Bloqueado', 'blocked': True}]},
            'state': {'resources': [{'key': 'reserva_de_sangue', 'current': 10, 'maximum': 10}]},
            'inventory': [{'item_path': 'potion', 'item_title': 'Poção', 'quantity': 2, 'equipped': False}]}

    def report(self, results):
        return build_report({'raziel': self.sheet()}, results, actors=('raziel',))

    def test_unexecuted_structured_ability_is_pending_not_pass(self):
        report = self.report([])
        entries = {e['key']: e for e in report['characters']['raziel']['entries']}
        self.assertEqual('PENDING', entries['ability:arma-de-sangue']['status'])
        self.assertEqual('PENDING', entries['ability:future']['status'])
        self.assertEqual('ASSISTED', entries['ability:vision']['status'])
        self.assertEqual('RULE_BLOCKED', entries['ability:locked']['status'])
        self.assertFalse(report['all_actions_certified'])

    def test_empty_sheet_is_not_certified(self):
        report=build_report({'raziel':{'definition':{}}},[],actors=('raziel',))
        self.assertFalse(report['all_actions_certified'])

    def test_failed_scenario_is_not_certified_even_if_another_passes(self):
        report = self.report([
            {'actor': 'raziel', 'scenario_id': 'hit', 'status': 'PASS', 'covers': ['ability:arma-de-sangue']},
            {'actor': 'raziel', 'scenario_id': 'miss', 'status': 'FAIL', 'covers': ['ability:arma-de-sangue'], 'error': 'wrong cost'}])
        entry = next(e for e in report['characters']['raziel']['entries'] if e['key'] == 'ability:arma-de-sangue')
        self.assertEqual('FAIL', entry['status'])
        self.assertEqual(['hit', 'miss'], entry['scenarios'])

    def test_expected_rejection_is_not_successful_execution(self):
        report = self.report([{'actor': 'raziel', 'scenario_id': 'reject', 'status': 'EXPECTED_BLOCK', 'covers': ['attack:melee']}])
        entry = next(e for e in report['characters']['raziel']['entries'] if e['key'] == 'attack:melee')
        self.assertEqual('UNAVAILABLE', entry['status'])

    def test_every_inventory_item_resource_and_attack_is_listed(self):
        entries = self.report([])['characters']['raziel']['entries']
        self.assertEqual(7, len(entries))
        self.assertIn('item:potion', {e['key'] for e in entries})
        self.assertIn('resource:reserva_de_sangue', {e['key'] for e in entries})

    def test_coverage_is_per_actor_not_reused_across_characters(self):
        report = self.report([{'actor': 'morthak', 'status': 'PASS', 'covers': ['attack:melee']}])
        entry = next(e for e in report['characters']['raziel']['entries'] if e['key'] == 'attack:melee')
        self.assertEqual('PENDING', entry['status'])

    def test_does_not_export_private_notes_or_full_sheet(self):
        sheet = self.sheet(); sheet['inventory'][0]['notes'] = 'GM SECRET'
        sheet['definition']['gm_notes'] = 'GM SECRET'
        report = build_report({'raziel': sheet}, [], actors=('raziel',))
        self.assertNotIn('GM SECRET', str(report))

    def test_native_attack_proves_weapon_use_not_all_equipment(self):
        report=self.report([{'actor':'raziel','status':'PASS','scenario_id':'native',
            'result':{'breakdown':{'attack':{'weapon_item_path':'potion'}}}}])
        entry=next(e for e in report['characters']['raziel']['entries'] if e['key']=='item:potion')
        self.assertEqual('PASS',entry['status'])
        self.assertEqual(['native'],entry['scenarios'])


class SheetRehearsalIsolationTests(TestCase):
    def target_simulation(self, gridded):
        simulation=Simulation.__new__(Simulation)
        simulation.map_id='arena';simulation.checks=set()
        simulation.sheets={'vezemir':{'definition':{'attacks':[{'id':'melee','damage':'1d6'}]}}}
        calls=[]
        def get(route,*args):
            calls.append(route)
            if route.startswith('/workspace'):
                return {'tokens':[{'id':'correct-pin','character_id':'vezemir'}]}
            return {'slot':'melee','gridded':gridded,'targets':[{'valid':True}]}
        simulation.get=get
        return simulation,calls

    def test_target_probe_uses_exact_map_and_pin_instead_of_an_old_campaign_pin(self):
        simulation,calls=self.target_simulation(True)
        simulation.targets('vezemir')
        self.assertIn('map_id=arena',calls[-1])
        self.assertIn('attacker_token_id=correct-pin',calls[-1])
        self.assertIn('range',simulation.verified_checks)

    def test_assisted_grid_fallback_is_not_a_successful_grid_test(self):
        simulation,_=self.target_simulation(False)
        with self.assertRaisesRegex(AssertionError,'grid'):
            simulation.targets('vezemir')

    def simulation_case(self, *, mutate=False):
        simulation=Simulation.__new__(Simulation)
        simulation.actors=('vezemir',);simulation.scenarios=set();simulation.available_scenarios=set()
        simulation.results=[];simulation.trace=[]
        simulation.snapshot=lambda:{}
        simulation.get=lambda *args:[]
        simulation.reset=lambda *args:simulation.trace.append({'method':'POST','status':200,'route':'setup'})
        simulation.check_persisted=lambda *args:None
        fingerprints=iter(('after-setup','changed' if mutate else 'after-setup'))
        simulation.persisted_fingerprint=lambda:next(fingerprints)
        return simulation

    def test_setup_and_target_query_do_not_prove_action_execution(self):
        simulation=self.simulation_case()
        simulation.case('range','vezemir',lambda:simulation.verify('range'))
        self.assertEqual(['range'],simulation.results[0]['verified_checks'])

    def test_accepted_command_and_durable_change_prove_execution(self):
        simulation=self.simulation_case(mutate=True)
        simulation.case('use','vezemir',lambda:simulation.trace.append({'method':'POST','status':200,'route':'use'}))
        self.assertEqual(['execution','persistence'],simulation.results[0]['verified_checks'])

    def test_post_without_durable_application_does_not_prove_execution(self):
        simulation=self.simulation_case()
        simulation.case('preview','vezemir',lambda:simulation.trace.append({'method':'POST','status':200,'route':'preview'}))
        self.assertEqual([],simulation.results[0]['verified_checks'])

    def test_display_label_can_change_without_breaking_existing_scenario_ids(self):
        simulation=Simulation.__new__(Simulation)
        simulation.actors=('morthak',);simulation.scenarios={'morthak:other'};simulation.available_scenarios=set()
        simulation.results=[]
        simulation.case('Novo nome','morthak',lambda:self.fail('Filtered'),scenario_id='morthak:legacy')
        self.assertEqual({'morthak:legacy'},simulation.available_scenarios)

    def test_scenario_filter_does_not_execute_other_cases_or_claim_their_coverage(self):
        simulation=Simulation.__new__(Simulation)
        simulation.actors=('raziel',);simulation.scenarios={'raziel:selected'};simulation.available_scenarios=set()
        simulation.results=[]
        simulation.case('other','raziel',lambda:self.fail('Must not execute'))
        self.assertEqual([],simulation.results)
        self.assertEqual({'raziel:other'},simulation.available_scenarios)

    def test_last_consumable_disappearing_from_native_inventory_is_success(self):
        simulation=Simulation.__new__(Simulation)
        simulation.prefix='last-potion'; simulation.checks=set()
        before={'inventory':[{'item_title':'Poção de HP','item_path':'potion','quantity':1}],
                'state':{'current_hp':5,'maximum_hp':10}}
        after={'inventory':[],'state':{'current_hp':9,'maximum_hp':10}}
        responses=iter((before,before,after))
        simulation.get=lambda *args:next(responses)
        simulation.repeated=lambda *args:None
        self.assertEqual({'item':'Poção de HP'},simulation.item('vezemir','Poção de HP'))

    def test_missing_potion_selects_rejection_without_claiming_consumption(self):
        from unittest.mock import Mock
        simulation=Simulation.__new__(Simulation)
        simulation.sheets={'vezemir':{'inventory':[]}}
        simulation.case=Mock()
        simulation.potion_case('vezemir')
        options=simulation.case.call_args.kwargs
        self.assertTrue(options['blocked'])
        self.assertEqual('vezemir:Poção de HP + ataque no mesmo turno',options['scenario_id'])
        self.assertEqual((),options.get('covers',()))

    def test_exhausted_potion_is_rejected_natively_without_restocking(self):
        from unittest.mock import Mock
        with TemporaryDirectory() as folder:
            simulation=Simulation.__new__(Simulation)
            simulation.database=Path(folder)/'fixture.sqlite3'
            simulation.prefix='empty-potion';simulation.checks=set()
            simulation.persisted_fingerprint=Mock(return_value='unchanged')
            simulation.post=Mock(return_value={'detail':'Item sem quantidade disponível'})
            with closing(sqlite3.connect(simulation.database)) as db, db:
                db.execute('CREATE TABLE player_inventory(profile_id TEXT,item_path TEXT,item_title TEXT,quantity INTEGER)')
                db.execute('INSERT INTO player_inventory VALUES(?,?,?,0)',('vezemir','potion','Poção de HP'))
            result=simulation.missing_consumable('vezemir','Poção de HP')
            self.assertIn('Sem estoque',result['detail'])
            self.assertEqual(2,simulation.post.call_count)
            for call in simulation.post.call_args_list:
                self.assertEqual('/characters/vezemir/actions',call.args[0])
                self.assertEqual('potion',call.args[1]['payload']['item_path'])
                self.assertEqual((400,),call.kwargs['accepted'])
            with closing(sqlite3.connect(simulation.database)) as db:
                self.assertEqual(0,db.execute('SELECT quantity FROM player_inventory').fetchone()[0])

    def test_insufficient_attack_uses_attack_dto_not_technique_only_fields(self):
        with TemporaryDirectory() as folder:
            simulation=Simulation.__new__(Simulation)
            simulation.database=Path(folder)/'dto.sqlite3'
            simulation.prefix='test'; simulation.enemy={'id':'enemy'}; simulation.checks=set()
            simulation.snapshot=lambda: {}
            calls=[]
            simulation.post=lambda route,body,*args,**kwargs: calls.append((route,body))
            with closing(sqlite3.connect(simulation.database)) as db,db:
                db.execute('CREATE TABLE character_states(profile_id TEXT,state_json TEXT,version INTEGER)')
                db.execute('INSERT INTO character_states VALUES(?,?,1)',('morthak',json.dumps({'resources':[{'key':'misseis_magicos','current':4}]})))
            simulation.insufficient('morthak',attack_id='misseis-magicos',resource=('misseis_magicos',))
            self.assertEqual('/characters/morthak/attacks/resolve',calls[0][0])
            self.assertNotIn('position_confirmed',calls[0][1])
            self.assertEqual('misseis-magicos',calls[0][1]['attack_id'])

    def test_retry_fingerprint_detects_hp_inventory_position_and_ledger_mutations(self):
        with TemporaryDirectory() as folder:
            simulation = Simulation.__new__(Simulation)
            simulation.database = Path(folder)/'hash.sqlite3'
            tables = ('character_states','player_inventory','session_workspace_entity_positions','session_ledger')
            with closing(sqlite3.connect(simulation.database)) as db, db:
                for table in tables:
                    db.execute('CREATE TABLE '+table+'(value TEXT)')
                    db.execute('INSERT INTO '+table+' VALUES(?)',('initial',))
            last = simulation.persisted_fingerprint()
            self.assertEqual(last,simulation.persisted_fingerprint())
            for table in tables:
                with closing(sqlite3.connect(simulation.database)) as db, db:
                    db.execute('UPDATE '+table+' SET value=?',('changed',))
                current = simulation.persisted_fingerprint()
                self.assertNotEqual(last,current,table)
                last=current

    def test_backup_only_reads_source_and_never_overwrites_an_existing_copy(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)/'source.sqlite3'; target = Path(folder)/'copy.sqlite3'
            with closing(sqlite3.connect(source)) as db, db:
                db.execute('CREATE TABLE evidence(value TEXT)'); db.execute("INSERT INTO evidence VALUES('preserved')")
            original = source.read_bytes()
            backup_readonly(source, target)
            self.assertEqual(original, source.read_bytes())
            with closing(sqlite3.connect(target)) as db:
                self.assertEqual('preserved', db.execute('SELECT value FROM evidence').fetchone()[0])
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                backup_readonly(source, target)

    def test_refuses_operational_database_destination(self):
        outside_temp = Path(__file__).resolve().parent/'data'/'never-created-by-test.sqlite3'
        with self.assertRaisesRegex(ValueError, 'temporary'):
            backup_readonly(Path('unused'), outside_temp)
        self.assertFalse(outside_temp.exists())

    def test_live_ports_and_occupied_port_are_refused_without_stopping_service(self):
        for port in (8787,8788,80):
            with self.assertRaises(ValueError): checked_port(port)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0)); listener.listen()
            port = listener.getsockname()[1]
            with self.assertRaisesRegex(ValueError, 'occupied'): checked_port(port)
            self.assertEqual(port, listener.getsockname()[1])

