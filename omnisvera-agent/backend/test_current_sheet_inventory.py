"""The AI audit must see the current sheet, without granting rules or coverage."""
from copy import deepcopy
from unittest import TestCase

from app.hemomancy import pack
from app.native_action_manifest import sheet_action_manifest
from scripts.sheet_rehearsal import build_report


class CurrentSheetInventoryTests(TestCase):
    def sheet(self):
        return {'definition':{'id':'raziel','name':'Raziel','level':5,'hemomancy':pack(),
            'session_abilities':[{'id':'marca-rubra','name':'Marca Rubra','active':True,'group':'Habilidades'},
                {'id':'arma-de-sangue','name':'Arma antiga','active':True,'group':'Habilidades'},
                {'id':'visao','name':'Visão','active':False,'group':'Traços vampíricos'}]},
            'state':{'resources':[{'key':'reserva_de_sangue','current':1,'maximum':10}]},'inventory':[]}

    def manifest(self,sheet):
        return sheet_action_manifest('raziel',sheet['definition'],sheet['state'],sheet['inventory'])

    def test_manifest_includes_nine_native_commands_and_five_non_executable_passives(self):
        actions=self.manifest(self.sheet())
        commands=[a for a in actions if a['ref'].startswith('technique:raziel:hemomancia-') and a['automation_scope']=='native']
        self.assertEqual(9,len(commands))
        self.assertTrue(all('/characters/raziel/techniques/hemomancia-' in a['execution']['endpoint'] for a in commands))
        self.assertTrue(all(a['certification']=='not_assessed' for a in commands))
        passives=[a for a in actions if ':hemomancia-passiva-' in a['ref']]
        self.assertEqual(5,len(passives));self.assertTrue(all(a['execution'] is None for a in passives))

    def test_legacy_is_retained_but_distinguished_from_the_current_card(self):
        actions={a['ref']:a for a in self.manifest(self.sheet())}
        self.assertFalse(actions['technique:raziel:arma-de-sangue']['visible_on_sheet'])
        self.assertTrue(actions['technique:raziel:marca-rubra']['visible_on_sheet'])

    def test_report_does_not_lose_current_actions_or_falsely_certify_them(self):
        report=build_report({'raziel':self.sheet()},[],actors=['raziel'])
        entries={e['key']:e for e in report['characters']['raziel']['entries']}
        self.assertEqual('PENDING',entries['ability:hemomancia-arco-habilidade']['status'])
        self.assertIn('cost',entries['ability:hemomancia-arco-habilidade']['required_checks'])
        self.assertIn('expiration',entries['ability:hemomancia-arco-habilidade']['required_checks'])
        self.assertFalse(entries['ability:arma-de-sangue']['visible_on_sheet'])
        self.assertNotIn('ability:arma-de-sangue',[g['key'] for g in report['certification']['gaps']])
        self.assertFalse(report['certification']['ready'])

    def test_missing_private_pack_does_not_fabricate_actions(self):
        sheet=self.sheet();sheet['definition'].pop('hemomancy')
        self.assertFalse(any(':hemomancia-' in a['ref'] for a in self.manifest(sheet)))

    def test_held_weapon_cost_is_zero_for_basic_and_additional_for_skill(self):
        sheet=self.sheet();sheet['definition']['active_effects']=[{'hemomancy_kind':'weapon','target_id':'raziel','weapon':'arco'}]
        actions={a['ref']:a for a in self.manifest(sheet)}
        basic=actions['technique:raziel:hemomancia-arco'];skill=actions['technique:raziel:hemomancia-arco-habilidade']
        self.assertEqual('available',basic['availability']['state'])
        self.assertEqual('available',skill['availability']['state'])
        sheet['state']['resources'][0]['current']=0
        actions={a['ref']:a for a in self.manifest(sheet)}
        self.assertEqual('available',actions[basic['ref']]['availability']['state'])
        self.assertEqual('unavailable',actions[skill['ref']]['availability']['state'])

    def test_audit_is_pure_and_never_exports_private_descriptions(self):
        sheet=self.sheet();sheet['definition']['gm_notes']='SECRET';sheet['definition']['hemomancy']['weapons'][0]['description']='SECRET'
        before=deepcopy(sheet)
        self.assertNotIn('SECRET',str(self.manifest(sheet)))
        self.assertEqual(before,sheet)

    def test_dorn_retired_cards_remain_auditable_without_becoming_current_ui_gaps(self):
        definition={'id':'dorn7','session_abilities':[{'id':key,'active':True} for key in ('levitacao','escuridao','dorn_diagnose','dorn_guard')]}
        actions={a['ref']:a for a in sheet_action_manifest('dorn7',definition,{'resources':[]},[])}
        for key in ('levitacao','escuridao','dorn_diagnose'):
            self.assertFalse(actions['technique:dorn7:'+key]['visible_on_sheet'])
        self.assertTrue(actions['technique:dorn7:dorn_guard']['visible_on_sheet'])
