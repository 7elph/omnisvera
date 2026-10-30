"""Certification is stricter than a successful scenario or a rendered card."""
from unittest import TestCase
from scripts.sheet_rehearsal import build_report, attach_ui_evidence


class SheetCertificationTests(TestCase):
    def sheet(self):
        return {'definition': {'name': 'Teste', 'attacks': [{'id': 'melee', 'damage': '1d6'}],
                'session_abilities': [{'id': 'velocidade', 'active': True, 'uses': {'resource_key': 'speed'}}]},
                'state': {'resources': [{'key': 'speed', 'current': 1, 'maximum': 1}]}}

    def report(self, checks=()):
        return build_report({'vezemir': self.sheet()}, [{'actor': 'vezemir', 'scenario_id': 'native',
            'status': 'PASS', 'covers': ['attack:melee', 'ability:velocidade'], 'verified_checks': list(checks)}], actors=['vezemir'])

    def test_green_api_without_per_action_evidence_is_not_certification(self):
        report = self.report()
        self.assertFalse(report['certification']['ready'])
        action = next(a for a in report['certification']['gaps'] if a['key'] == 'attack:melee')
        self.assertIn('execution', action['missing_checks'])
        self.assertIn('ui', action['missing_checks'])

    def test_target_query_does_not_certify_execution(self):
        report = self.report(['range'])
        action = next(a for a in report['certification']['gaps'] if a['key'] == 'attack:melee')
        self.assertNotIn('range', action['missing_checks'])
        self.assertIn('execution', action['missing_checks'])

    def test_effect_and_resource_require_cost_and_expiration(self):
        report = self.report(['execution', 'persistence', 'idempotency'])
        action = next(a for a in report['certification']['gaps'] if a['key'] == 'ability:velocidade')
        self.assertIn('cost', action['missing_checks'])
        self.assertIn('expiration', action['missing_checks'])

    def test_layout_pass_cannot_certify_unexecuted_actions(self):
        report = self.report()
        attach_ui_evidence(report, {'status': 'PASS', 'checks': [{'script': 'layout', 'status': 'PASS'}]})
        self.assertTrue(all('ui' in a['missing_checks'] for a in report['certification']['gaps']))

    def test_exact_actor_and_action_ui_coverage_only(self):
        report = self.report(['execution', 'persistence', 'idempotency', 'range'])
        attach_ui_evidence(report, {'status': 'PASS', 'checks': [{'script': 'native', 'status': 'PASS',
            'action_coverage': [{'actor': 'vezemir', 'key': 'attack:melee', 'verified_checks': ['ui']},
                                {'actor': 'morthak', 'key': 'ability:velocidade', 'verified_checks': ['ui']}]}]})
        self.assertNotIn('attack:melee', [a['key'] for a in report['certification']['gaps']])
        self.assertIn('ability:velocidade', [a['key'] for a in report['certification']['gaps']])

    def test_failed_ui_or_scenario_is_never_hidden(self):
        report = self.report(['execution', 'persistence', 'idempotency', 'range'])
        attach_ui_evidence(report, {'status': 'FAIL', 'checks': [{'script': 'native', 'status': 'FAIL',
            'action_coverage': [{'actor': 'vezemir', 'key': 'attack:melee', 'verified_checks': ['ui']}]}]})
        self.assertFalse(report['certification']['ready'])
        self.assertIn('attack:melee', [a['key'] for a in report['certification']['gaps']])

    def test_ui_coverage_cannot_smuggle_unverified_backend_checks(self):
        report = self.report()
        attach_ui_evidence(report, {'status': 'PASS', 'checks': [{'script': 'native', 'status': 'PASS',
            'action_coverage': [{'actor': 'vezemir', 'key': 'attack:melee', 'verified_checks': ['execution', 'ui'], 'private': 'SECRET'}]}]})
        action = next(a for a in report['certification']['gaps'] if a['key'] == 'attack:melee')
        self.assertIn('execution', action['missing_checks'])
        self.assertNotIn('SECRET', str(report))

    def test_certificate_is_bound_to_inventory_and_level_without_exporting_notes(self):
        sheet = self.sheet(); sheet['definition']['level'] = 5
        first = build_report({'vezemir': sheet}, [], actors=['vezemir'])
        sheet['definition']['level'] = 6
        second = build_report({'vezemir': sheet}, [], actors=['vezemir'])
        self.assertNotEqual(first['certification']['sheet_fingerprints'], second['certification']['sheet_fingerprints'])

    def test_four_actor_certificate_requires_exact_api_and_ui_proofs(self):
        actors=['vezemir','morthak','raziel','dorn7']
        sheets={a:{'definition':{'attacks':[{'id':'melee','damage':'1d6'}]}} for a in actors}
        results=[{'actor':a,'scenario_id':a+':hit','status':'PASS','covers':['attack:melee'],
                  'verified_checks':['execution','persistence','idempotency','range']} for a in actors]
        report=build_report(sheets,results,actors=actors)
        self.assertFalse(report['certification']['ready'])
        attach_ui_evidence(report,{'status':'PASS','checks':[{'script':'native','status':'PASS',
            'action_coverage':[{'actor':a,'key':'attack:melee','verified_checks':['ui']} for a in actors]}]})
        self.assertTrue(report['certification']['ready'])
        self.assertTrue(report['all_actions_certified'])
        self.assertEqual('INCONCLUSIVE',report['certification']['real_table_validation'])
