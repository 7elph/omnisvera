"""GM-approved October 24 deltas, never touching the live database."""
import unittest
import test_combat as fixtures
from app.combat import confirm_attack_resolution
from app.session_workspace import save_workspace_token

class CriticalRulesTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.CombatAttackResolutionTests();self.f.setUp();self.addCleanup(self.f.tearDown)
        self.monster=save_workspace_token(self.f.database,token_type='monster',name='Alvo',latitude=50,longitude=50,current_hp=100,maximum_hp=100,sheet={'armor_class':99})
        self.target={'type':'token','id':self.monster['id'],'name':'Alvo','armor_class':99,'current_hp':100}
    def test_twenty_triples_only_grisalma_base_dice_even_against_high_ac(self):
        result=self.f._resolve(target=self.target,request_id='critical-grisalma-24',d20=20,rng=fixtures.SequenceRng(2,3,4))
        self.assertEqual('hit',result['result']);self.assertEqual(11,result['damage_total'])
        self.assertEqual(3,result['breakdown']['strikes'][0]['critical_multiplier'])
    def test_one_damages_attacker_once_only_after_confirmation(self):
        result=self.f._resolve(target=self.target,request_id='fumble-self-24',d20=1,rng=fixtures.SequenceRng(4))
        self.assertEqual(20,self.f._character_hp('vezemir'))
        kwargs=dict(resolution_id=result['resolution_id'],requested_by_id='vezemir',requested_by_role='player')
        # Existing native confirmation signature is deliberately used below.
        first=confirm_attack_resolution(self.f.database,**kwargs)[0]
        self.assertEqual(14,self.f._character_hp('vezemir'))
        self.assertEqual(first,confirm_attack_resolution(self.f.database,**kwargs)[0])
        self.assertEqual(14,self.f._character_hp('vezemir'))
        self.assertEqual(100,first['hp_after'])

class BalanceMetadataTests(unittest.TestCase):
    def test_natural_twenty_damage_survives_immunity_and_retry_does_not_repeat(self):
        import json,sqlite3
        from contextlib import closing
        import test_hemomancy_weapons as hemof
        f=hemof.HemomancyWeaponsTests();f.setUp();self.addCleanup(f.tearDown)
        f.durable_target()
        with closing(sqlite3.connect(f.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',
                (json.dumps({'armor_class':99,'damage_reduction':999,'damage_immunities':['piercing']}),f.wounded['id']))
        preview=f.attack('arco',request='unavoidable-bow-24',die=20)
        self.assertEqual(200,preview.status_code,preview.text)
        expected=preview.json()['damage_total'];self.assertGreater(expected,0)
        first=f.confirm(preview).json();self.assertEqual(expected,first['damage_total'])
        self.assertEqual(100-expected,first['hp_after'])
        self.assertEqual(first,f.confirm(preview).json())

    def test_carrasco_uses_pre_attack_twenty_five_percent_boundary(self):
        import sqlite3
        from contextlib import closing
        import test_hemomancy_weapons as hemof
        f=hemof.HemomancyWeaponsTests();f.setUp();self.addCleanup(f.tearDown)
        f.durable_target()
        for hp,expected in [(25,1),(26,0)]:
            with closing(sqlite3.connect(f.db)) as db,db:
                db.execute('UPDATE session_workspace_tokens SET current_hp=? WHERE id=?',(hp,f.wounded['id']))
            reply=f.attack('foice','skill',request='carrasco-boundary-'+str(hp),die=15)
            self.assertEqual(200,reply.status_code,reply.text)
            self.assertEqual(expected,reply.json()['breakdown']['hemomancy']['passive_d6'])

    def test_default_critical_doubles_base_dice_only_and_does_not_change_monsters(self):
        from app.critical_rules import augment_strike
        strike={'d20':20,'result':'hit','damage_total':7,'damage_rolls':[3]}
        attack={'damage':'1d8+4','weapon_item_path':'fixture:plain'}
        augment_strike(strike,attack,[],fixtures.SequenceRng(5),player_attack=True)
        self.assertEqual(12,strike['damage_total']);self.assertEqual(2,strike['critical_multiplier'])
        npc={'d20':1,'result':'miss','damage_total':0,'damage_rolls':[]}
        augment_strike(npc,attack,[],fixtures.SequenceRng(),player_attack=False)
        self.assertNotIn('fumble_damage',npc)
    def test_bleeding_icon_keeps_two_target_turns_without_legacy_card(self):
        from app.action_cards import active_effect_icons
        effect={'id':'bleed','target_type':'token','target_id':'enemy','label':'Sangramento — Ceifa Rubra','source':'Hemomancia (Raziel)','duration':'scene','remaining_turns':2,'hemomancy_kind':'bleed'}
        icons=active_effect_icons([effect],lambda _:[],['raziel'])
        self.assertEqual(2,icons[0]['turns_remaining']);self.assertEqual('Ceifa Rubra',icons[0]['card']['name'])
    def test_natural_twenty_is_not_redirected_to_a_reflection(self):
        from app.dorn_spell_pack import redirect_hits
        from unittest.mock import Mock
        db=Mock();db.execute.return_value.fetchone.return_value=('reflex','{"id":"reflex","images_remaining":3}')
        value,details=redirect_hits(db,'character','dorn7',[{'d20':20,'result':'hit','damage_total':12,'unavoidable':True}],'now')
        self.assertEqual(12,value);self.assertEqual([],details['rolls']);self.assertEqual(3,details['images_remaining'])
    def test_first_skill_and_shield_each_cost_one_not_invocation_plus_skill(self):
        from app.hemomancy import weapons, blood_cost
        for weapon in weapons():
            self.assertEqual(1,blood_cost(weapon,True,False))
            self.assertEqual(1,blood_cost(weapon,True,True))
            self.assertEqual(1,weapon['invocation_cost'])
    def test_floor_and_reserve_are_authoritative_sheet_data(self):
        from app.character_play import build_character_definition
        definition=build_character_definition(profile_id='raziel',note={'title':'Raziel','frontmatter':{},'content':''},sheet={'steps':[{'key':'attacks','fields':{'melee_bonus':2,'ranged_bonus':4}}]},inventory=[])
        self.assertEqual(10,definition['progression']['resource_maxima']['reserva_de_sangue'])
        self.assertTrue(all(a['base_attack_bonus']>=6 for a in definition['attacks']))

if __name__=='__main__':unittest.main()
