import unittest
from app.player_inventory import normalize_inventory_item_mechanics
from app.character_play import available_attack_weapons

class EquipmentUpdatesTests(unittest.TestCase):
    def test_repair_healing_dice_are_not_inferred_as_weapon_damage(self):
        for title in ('Kit de Reparo', 'Poção de cura'):
            item = normalize_inventory_item_mechanics({'item_title': title, 'item_type': 'consumível', 'description': 'Recupera 1d4 PV.', 'mechanics': {'equipment_slots': []}})
            self.assertFalse(item.get('damage_formula'))
            self.assertEqual([], item['mechanics']['equipment_slots'])
    def test_weapon_bonus_does_not_copy_its_icon_to_other_attack(self):
        from app.character_play import _attack_equipment_sources
        dagger = {'item_path':'dagger','item_title':'Adagas','equipped':True,'damage_formula':'1d4','equipment_slot':'Corpo a corpo'}
        ring = {'item_path':'ring','item_title':'Anel','equipped':True}
        effects = {'breakdown':[{'active':True,'kind':'attack_bonus','target':'all','item_path':item['item_path']} for item in (dagger,ring)]}
        self.assertEqual([entry['item_path'] for entry in _attack_equipment_sources([dagger,ring],effects,'ranged',None)], ['ring'])
        self.assertEqual([entry['item_path'] for entry in _attack_equipment_sources([dagger,ring],effects,'melee',dagger)], ['dagger','ring'])
    def test_primordial_cloak_is_accessory_without_changing_mechanics(self):
        item={'item_title':'Manto Primordial do Ancião','item_type':'manto','mechanics':{'damage_formula':'','slot_limit':1},'effect_rules':[{'kind':'armor_class_bonus','value':2}]}
        normalized=normalize_inventory_item_mechanics(item)
        self.assertEqual(['Acessório'],normalized['mechanics']['equipment_slots'])
        self.assertEqual(item['effect_rules'],normalized['effect_rules'])
        self.assertEqual(['Armadura'],normalize_inventory_item_mechanics({'item_title':'Armadura de couro'})['mechanics']['equipment_slots'])

    def test_explicit_throwing_slot_is_exclusive_but_legacy_is_preserved(self):
        dagger={'item_path':'Items/Adagas de Espectro Fantasma.md','item_title':'Adagas','item_type':'Arma','equipped':True,'quantity':1,'damage_formula':'1d4','mechanics':{'thrown_damage_formula':'1d4'}}
        self.assertFalse(available_attack_weapons([{**dagger,'equipment_slot':'Corpo a corpo'}],'ranged'))
        self.assertFalse(available_attack_weapons([{**dagger,'equipment_slot':'À distância'}],'melee'))
        self.assertTrue(available_attack_weapons([dagger],'ranged'))
