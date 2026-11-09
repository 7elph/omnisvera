"""Pure DTO migration inventory; no application, database or operational state."""
from copy import deepcopy
import unittest

from app.native_action_manifest import sheet_action_manifest, token_action_manifest


class NativeActionManifestTests(unittest.TestCase):
    def test_quantity_magic_items_are_available_and_describe_cell_targeting(self):
        from app.map_commerce import catalog_inventory
        path='compendium:item-magico-bomba-de-ilusao'
        item={**catalog_inventory(path),'item_path':path,'item_title':'Bomba de Ilusão','quantity':2,'equipped':False}
        entry=self.sheet('vezemir',[],inventory=[item])[0]
        self.assertEqual('available',entry['availability']['state'])
        self.assertEqual('cell',entry['targeting']['selection'])
        self.assertEqual(['map_id','target_cell','expected_grid_version'],entry['targeting']['options'])
        self.assertEqual('technique:vezemir:magic-item:item-magico-bomba-de-ilusao',entry['targeting']['action_ref'])

    def test_magic_activation_availability_matches_equipment_and_instance_guards(self):
        from app.map_commerce import catalog_inventory
        path='compendium:item-magico-botas-da-velocidade'
        item={**catalog_inventory(path),'item_path':path,'item_title':'Botas da velocidade','quantity':1,'equipped':False}
        entry=self.sheet('vezemir',[],inventory=[item])[0]
        self.assertEqual(entry['binding'],'inventory_item')
        self.assertEqual(entry['availability']['state'],'unavailable')
        item['equipped']=True;item['quantity']=2
        self.assertEqual(self.sheet('vezemir',[],inventory=[item])[0]['availability']['state'],'unavailable')

    def test_shield_shared_command_is_listed_as_the_fifth_current_skill(self):
        from app.hemomancy import pack
        definition=dict(id='raziel',hemomancy=pack())
        entries=sheet_action_manifest('raziel',definition,dict(resources=[dict(key='reserva_de_sangue',current=10)]),[])
        shield=next(e for e in entries if e['ref']=='technique:raziel:hemomancia-escudo')
        self.assertEqual('Bastião Carmesim',shield['label'])
        self.assertEqual('Habilidades',shield['group'])
        self.assertEqual('hemomancy_shield',shield['binding'])

    def test_known_inventory_executors_are_mapped_without_name_guessing(self):
        items = [dict(item_path='potion',item_title='Poção',quantity=1,usable=True,
                      effect_rules=[dict(trigger='on_use',kind='heal_hp',formula='1d8')]),
                 dict(item_path='bracelet',item_title='Pulseira de Vinhas',quantity=1,equipped=True,charges_max=2,charges_current=1),
                 dict(item_path='unknown',item_title='Poção inventada',quantity=1,usable=True)]
        entries = self.sheet('vezemir', [], inventory=items)
        self.assertEqual(['inventory_item','vine_bracelet',None],[e['binding'] for e in entries])
        self.assertEqual('use_item',entries[0]['execution']['action'])
        self.assertEqual('/characters/vezemir/vines',entries[1]['execution']['endpoint'])

    def test_effective_blood_cost_and_zero_cost_do_not_use_legacy_constants(self):
        entry = self.sheet('raziel',[dict(id='sangue-defensivo',uses=dict(resource_key='reserva_de_sangue',cost=1))],
                           [dict(key='reserva_de_sangue',current=1)])[0]
        self.assertEqual('available',entry['availability']['state'])
        entry = self.sheet('raziel',[dict(id='marca-rubra',uses=dict(resource_key='reserva_de_sangue',cost=0))],
                           [dict(key='reserva_de_sangue',current=0)])[0]
        self.assertEqual('available',entry['availability']['state'])

    def test_item_component_stock_and_equipment_requirements_remain_native(self):
        kit=self.sheet('dorn7',[],inventory=[dict(item_path='kit',item_title='Kit de Reparo',quantity=0)])[0]
        self.assertEqual('character_technique',kit['binding'])
        self.assertEqual('unavailable',kit['availability']['state'])
        vine=self.sheet('vezemir',[],inventory=[dict(item_path='vine',item_title='Pulseira de Vinhas',quantity=1,equipped=False)])[0]
        self.assertEqual('unavailable',vine['availability']['state'])

    def test_display_metadata_is_allowlisted_and_never_exposes_private_annotations(self):
        entry=self.sheet('vezemir',[dict(id='frenesi',name='Frenesi',description='Regra pública',image_path='icon.jpg',
                                       group='Habilidades',private_notes='SECRET')])[0]
        self.assertEqual('Regra pública',entry['description'])
        self.assertEqual('icon.jpg',entry['image_path'])
        self.assertNotIn('SECRET',str(entry))

    def sheet(self, actor, abilities, resources=None, inventory=None):
        return sheet_action_manifest(actor, {'session_abilities': abilities},
                                     {'resources': resources or []}, inventory or [])

    def test_all_four_actor_bindings_use_existing_routes(self):
        for actor, ability, binding in [('vezemir', 'frenesi', 'vezemir_skill'),
                                         ('morthak', 'aterrorizar', 'necromancer_spell'),
                                         ('raziel', 'mordida', 'character_technique'),
                                         ('dorn7', 'reflexos', 'dorn_spell')]:
            with self.subTest(actor=actor):
                result = self.sheet(actor, [{'id': ability, 'name': ability, 'active': True}])[0]
                self.assertEqual(result['binding'], binding)
                self.assertEqual(result['automation_scope'], 'native')
                self.assertEqual(result['execution']['method'], 'POST')
                self.assertEqual(result['certification'], 'not_assessed')

    def test_unknown_override_or_level_ability_is_kept_without_endpoint(self):
        result = self.sheet('morthak', [{'id': 'new-level-override', 'name': 'Nova',
                                        'mechanics_status': 'structured'}])[0]
        self.assertEqual(result['label'], 'Nova')
        self.assertEqual(result['automation_scope'], 'assisted')
        self.assertIsNone(result['binding'])
        self.assertIsNone(result['execution'])

    def test_wrong_owner_cannot_gain_native_binding_by_name(self):
        result = self.sheet('raziel', [{'id': 'clonagem', 'name': 'Clonagem'}])[0]
        self.assertIsNone(result['execution'])

    def test_exhausted_resource_keeps_entry_but_disables_availability(self):
        result = self.sheet('vezemir', [{'id': 'velocidade', 'uses': {'resource_key': 'velocidade'}}],
                            [{'key': 'velocidade', 'current': 0, 'maximum': 1}])[0]
        self.assertEqual(result['availability']['state'], 'unavailable')
        self.assertEqual(result['automation_scope'], 'native')
        self.assertIn('velocidade', result['availability']['reason'])

    def test_fear_memorized_alternative_is_not_falsely_declared_unavailable(self):
        result = self.sheet('morthak', [{'id': 'aterrorizar', 'uses': {'resource_key': 'fear'}}],
                            [{'key': 'fear', 'current': 0}])[0]
        self.assertEqual(result['availability']['state'], 'unknown')
        self.assertIn('memoriz', result['availability']['reason'])

    def test_passive_and_explicit_rule_block_are_not_executable(self):
        entries = self.sheet('vezemir', [{'id': 'maestria-em-arma', 'kind': 'passive'},
                                        {'id': 'frenesi', 'blocked': True}])
        self.assertEqual([e['automation_scope'] for e in entries], ['passive', 'blocked'])
        self.assertTrue(all(e['execution'] is None for e in entries))

    def test_weapon_missing_damage_stays_unavailable(self):
        entries = sheet_action_manifest('vezemir', {'attacks': [{'id': 'ranged', 'name': 'Distância',
                                                               'attack_bonus': 5, 'damage': None}]}, {}, [])
        self.assertEqual(entries[0]['availability']['state'], 'unavailable')
        self.assertEqual(entries[0]['automation_scope'], 'blocked')

    def test_native_attack_uses_resolve_and_existing_confirmation(self):
        entry = sheet_action_manifest('vezemir', {'attacks': [{'id': 'melee', 'damage': '1d8+2',
                                                               'attack_bonus': 10}]}, {}, [])[0]
        self.assertEqual(entry['execution']['endpoint'], '/characters/vezemir/attacks/resolve')
        self.assertEqual(entry['execution']['confirmation_endpoint'], '/combat/attacks/{resolution_id}/confirm')

    def test_fragment_and_kit_are_checked_without_granting_items(self):
        self.assertEqual(self.sheet('morthak', [{'id': 'clonagem'}])[0]['availability']['state'], 'unavailable')
        self.assertEqual(self.sheet('dorn7', [{'id': 'dorn-reparo'}])[0]['availability']['state'], 'unavailable')
        entry = self.sheet('morthak', [{'id': 'clonagem'}], inventory=[{
            'item_title': 'Fragmento de Cristal Arcano', 'quantity': 1}])[0]
        self.assertEqual(entry['availability']['state'], 'available')

    def test_pure_inputs_and_only_safe_output_fields(self):
        definition = {'session_abilities': [{'id': 'frenesi', 'name': 'Frenesi', 'private_notes': 'secret'}],
                      'gm_fields': {'secret': 'private'}}
        state = {'resources': [], 'session_notes': 'private'}
        inventory = [{'quantity': 1, 'gm_notes': 'private'}]
        before = deepcopy((definition, state, inventory))
        result = sheet_action_manifest('vezemir', definition, state, inventory)
        self.assertEqual((definition, state, inventory), before)
        self.assertNotIn('private', str(result))
        self.assertEqual(result[0]['origin'], 'effective_sheet')

    def test_token_ready_attack_with_rider_is_native_but_rider_manual(self):
        entries = token_action_manifest({'id': 'npc:test', 'name': 'Teste', 'sheet': {
            'attacks': [{'name': 'Garra', 'bonus': 2, 'damage': '1d6+veneno'}]}})
        entry = entries[0]
        self.assertEqual(entry['automation_scope'], 'native')
        self.assertEqual(entry['execution']['endpoint'], '/gm/combat/tokens/npc:test/attacks/resolve')
        self.assertTrue(any('veneno' in limit for limit in entry['limitations']))

    def test_token_frequency_does_not_become_an_automated_cost(self):
        entries = token_action_manifest({'id': 'npc:test', 'sheet': {'abilities': [
            {'name': 'Sopro', 'description': 'Uma vez ao dia, JPD, dano 2d6 a 9 metros.'}]}})
        entry = entries[0]
        self.assertEqual(entry['automation_scope'], 'assisted')
        self.assertIsNone(entry['execution'])
        self.assertTrue(any('frequência' in limit for limit in entry['limitations']))

    def test_token_without_attack_damage_is_not_native(self):
        entry = token_action_manifest({'id': 'npc:test', 'sheet': {'attacks': [
            {'name': 'Espada', 'bonus': 2, 'damage': 'Arma +2'}]}})[0]
        self.assertEqual(entry['automation_scope'], 'blocked')
        self.assertIsNone(entry['execution'])

    def test_missing_token_identity_never_emits_route(self):
        entry = token_action_manifest({'sheet': {'attacks': [{'name': 'Garra', 'bonus': 2, 'damage': '1d6'}]}})[0]
        self.assertIsNone(entry['execution'])

    def test_native_token_executor_rejects_extra_dice_and_native_formula_limits(self):
        for damage in ['1d6+2d4', '21d6', '1d1001', '1d6+1001']:
            with self.subTest(damage=damage):
                entry = token_action_manifest({'id': 'npc:test', 'name': 'Teste', 'token_type': 'monster',
                    'sheet': {'attacks': [{'name': 'Garra', 'bonus': 2, 'damage': damage}]}})[0]
                self.assertEqual('blocked', entry['automation_scope'])
                self.assertIsNone(entry['execution'])

    def test_non_monster_token_type_is_not_executable_but_missing_legacy_type_is_allowed(self):
        token = {'id': 'npc:test', 'name': 'Teste', 'sheet': {
            'attacks': [{'name': 'Garra', 'bonus': 2, 'damage': '1d6'}]}}
        for kind in ['location', 'character', 'npc']:
            with self.subTest(kind=kind):
                entry = token_action_manifest({**token, 'token_type': kind})[0]
                self.assertIsNone(entry['execution'])
        self.assertEqual('native', token_action_manifest(token)[0]['automation_scope'])

    def test_touch_exposes_native_attack_confirmation(self):
        entry = self.sheet('morthak', [{'id': 'toque-sombrio'}])[0]
        self.assertEqual('/combat/attacks/{resolution_id}/confirm', entry['execution']['confirmation_endpoint'])

    def test_inventory_usables_are_visible_but_assisted_without_new_bindings(self):
        inventory = [
            {'item_path': 'item:vine', 'item_title': 'Pulseira', 'quantity': 1, 'charges_max': 2, 'charges_current': 0,
             'notes': 'secret', 'gm_fields': {'private': 'private'}},
            {'item_path': 'item:potion', 'item_title': 'Poção', 'quantity': 2, 'usable': True},
            {'item_path': 'item:ring', 'item_title': 'Anel', 'quantity': 1, 'effect_rules': [{'trigger': 'on_use'}]},
            {'item_path': 'item:armor', 'item_title': 'Armadura', 'quantity': 1, 'equipped': True}]
        entries = self.sheet('vezemir', [], inventory=inventory)
        self.assertEqual(['Pulseira', 'Poção', 'Anel'], [entry['label'] for entry in entries])
        self.assertTrue(all(entry['automation_scope'] == 'assisted' and entry['binding'] is None
                            and entry['execution'] is None for entry in entries))
        self.assertEqual('unavailable', entries[0]['availability']['state'])
        self.assertNotIn('secret', str(entries))
        self.assertNotIn('private', str(entries))

    def test_missing_state_never_asserts_available_native_actions(self):
        entries = sheet_action_manifest('dorn7', {'attacks': [{'id': 'melee', 'damage': '1d6', 'attack_bonus': 2}],
                     'session_abilities': [{'id': 'dorn_guard'}]}, {}, [])
        self.assertEqual(['unknown', 'unknown'], [entry['availability']['state'] for entry in entries])

    def test_sheet_attack_uses_native_formula_limits(self):
        entry = sheet_action_manifest('vezemir', {'attacks': [{'id': 'melee', 'damage': '21d6',
                                  'attack_bonus': 2}]}, {'resources': []}, [])[0]
        self.assertIsNone(entry['execution'])


if __name__ == '__main__':
    unittest.main()
