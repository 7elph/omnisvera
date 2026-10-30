import unittest
from app.character_play import build_character_definition


class SheetRevisionTests(unittest.TestCase):
    def test_vezemir_ba_uses_level_attribute_enhancement_and_passive_mastery(self):
        weapon={'item_path':'Items/Grisalma.md','item_title':'Grisalma','item_type':'arma','equipped':True,'quantity':1,'equipment_slot':'Corpo a corpo','damage_formula':'2d6+2','effect_rules':[{'id':'enhancement','trigger':'while_equipped','kind':'attack_bonus','target':'melee','value':2,'stacking':'stack'}]}
        sheet={'steps':[{'key':key,'fields':fields} for key,fields in {'attributes':{'strength':14},'character_class':{'level':5,'class_name':'Guerreiro'},'attacks':{'melee_bonus':4}}.items()]}
        overrides={'level':5,'advancement_base_attack':5,'specialization_mastery':{'weapon_item_path':weapon['item_path'],'attack_bonus':1,'damage_bonus':1},'specialization_abilities':[{'id':'maestria-em-arma','name':'Maestria em Arma','active':True,'kind':'ability'}]}
        result=build_character_definition(profile_id='vezemir',note={'title':'Vezemir'},sheet=sheet,inventory=[weapon],overrides=overrides)
        self.assertEqual(10,result['attacks'][0]['attack_bonus'])
        self.assertFalse(next(a for a in result['session_abilities'] if a['id']=='maestria-em-arma')['active'])

    def test_racial_passives_have_supplied_art(self):
        result=build_character_definition(profile_id='vezemir',note={'title':'Vezemir'},sheet={},inventory=[],overrides={})
        for identity in ['visao-no-escuro-elfica','percepcao-de-portas-escondidas','descanso-elfico']:
            self.assertTrue(next(a for a in result['session_abilities'] if a['id']==identity).get('image_path'))
