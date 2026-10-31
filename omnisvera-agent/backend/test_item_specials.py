"""Item specials run against TEMP fixtures, never operational characters."""
import unittest

from app.map_commerce import catalog_inventory
from app.damage_profiles import attack_profile


class ItemSpecialContractTests(unittest.TestCase):
    def test_madu_has_source_damage_and_keeps_defense_once(self):
        item = catalog_inventory('compendium:arma-corpo-madu')
        self.assertEqual(item['damage_formula'], '1d8')
        self.assertEqual(item['mechanics']['critical_threshold'],19)
        self.assertEqual(item['mechanics']['critical_multiplier'],2)
        self.assertEqual(sum(r['value'] for r in item['effect_rules']
                             if r['kind'] == 'armor_class_bonus'), 1)
        self.assertNotIn('special_effect', item['mechanics']['family_gaps'])

    def test_mixed_weapon_requires_choice_and_rejects_elemental_injection(self):
        from app.item_specials import select_damage_type
        item = {**catalog_inventory('compendium:arma-corpo-espada-bastarda'),
                'item_path': 'compendium:arma-corpo-espada-bastarda'}
        attack = {'weapon_item_path': item['item_path']}
        with self.assertRaisesRegex(ValueError, 'tipo de dano'):
            select_damage_type(attack, [item], None)
        with self.assertRaisesRegex(ValueError, 'tipo de dano'):
            select_damage_type(attack, [item], 'fire')
        selected = select_damage_type(attack, [item], 'bludgeoning')
        self.assertEqual(attack_profile(selected, [item])['damage_type'], 'bludgeoning')
        self.assertNotIn('damage_type', attack)

    def test_fixed_weapon_cannot_be_retyped(self):
        from app.item_specials import select_damage_type
        item = {**catalog_inventory('compendium:arma-corpo-espada-curta'),
                'item_path': 'compendium:arma-corpo-espada-curta'}
        with self.assertRaisesRegex(ValueError, 'tipo de dano'):
            select_damage_type({'weapon_item_path': item['item_path']}, [item], 'fire')

    def test_net_projects_rolls_and_dexterity_without_changing_attributes(self):
        from app.combat_effects import apply_definition_effects
        definition = {'attributes': {'dexterity': 14, 'strength': 12},
            'attribute_modifiers': {'dexterity': 2, 'strength': 1},
            'attacks': [{'id': 'melee', 'attack_bonus': 7, 'damage': '1d6'}],
            'defenses': {'armor_class': 18, 'initiative': 2, 'saving_throw_bonus': 1}}
        effect = {'id': 'fixture-net', 'item_special': 'net', 'modifiers': {}, 'dexterity_ac_bonus': 2}
        result = apply_definition_effects(definition, [effect, effect])
        self.assertEqual(result['defenses']['armor_class'], 16)
        self.assertEqual(result['attacks'][0]['attack_bonus'], 5)
        self.assertEqual(result['attribute_modifiers']['strength'], -1)
        self.assertEqual(result['defenses']['saving_throw_bonus'], -1)
        self.assertEqual(result['defenses']['initiative'], 0)
        self.assertEqual(result['attributes'], definition['attributes'])
        self.assertEqual(definition['defenses']['armor_class'], 18)

    def test_optional_damage_choice_preserves_old_retry_intent(self):
        from app.schemas import AttackResolutionCreate
        from app.item_specials import attack_intent
        request = AttackResolutionCreate(request_id='fixture-legacy-retry', attack_id='melee',
            target_type='token', target_id='enemy', roll_mode='physical', d20=15)
        self.assertNotIn('damage_type', attack_intent(request))

    def test_blowgun_uses_its_own_darts_and_keeps_critical_and_range(self):
        from app.item_families import project_ammunition
        inventory = [{**catalog_inventory('compendium:'+identity), 'item_path':'compendium:'+identity,
                      'quantity':1} for identity in ('arma-distancia-zarabatana','arma-distancia-dardo-zarabatana-x20')]
        project_ammunition(inventory)
        self.assertEqual(inventory[0]['damage_formula'],'1d6')
        self.assertEqual(inventory[0]['mechanics']['range_m'],30)
        self.assertEqual(inventory[0]['mechanics']['critical_multiplier'],3)
        self.assertEqual(inventory[1]['mechanics']['ammunition_kind'],'dart')

    def test_net_cannot_inject_unapproved_damage_through_blood_boost(self):
        from app.item_specials import prepare_attack
        item={'item_path':'compendium:kit-explorador-rede','mechanics':{'special_attack':'net'}}
        with self.assertRaisesRegex(ValueError,'não possui dano'):
            prepare_attack(None,{'weapon_item_path':item['item_path']},[item],{'touch_armor_class':12},blood_boost=1)


if __name__ == '__main__':
    unittest.main()


class ItemSpecialApiTests(unittest.TestCase):
    def setUp(self):
        import test_equip_slots
        import json, sqlite3
        from contextlib import closing
        from app import main
        from app.access import AccessContext
        test_equip_slots.EquipSlotTests.setUp(self)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='gm')
        with closing(sqlite3.connect(self.db)) as db, db:
            data = json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            data.update(attributes={'strength':13, 'dexterity':14}, attacks={'melee_bonus':8,'ranged_bonus':8},
                        armor={'armor_class':16}, character_class={'level':2, 'hit_points':20},
                        race={'race':'Humano', 'movement':'9 m'})
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'", (json.dumps(data),))
        self.client.get('/characters/vezemir')
        from app.session_workspace import update_workspace_table_mode
        update_workspace_table_mode(self.db, 'physical')

    def tearDown(self):
        import test_equip_slots
        test_equip_slots.EquipSlotTests.tearDown(self)

    def equip(self, identity, name, slot='Corpo a corpo'):
        from app.player_inventory import upsert_inventory
        path = 'compendium:' + identity
        upsert_inventory(self.db, profile_id='vezemir', item_path=path, item_title=name,
            equipped=False, quantity=1, notes=None)
        result = self.client.post('/characters/vezemir/actions', json={'action':'equip_item',
            'payload':{'item_path':path, 'equipment_slot':slot}, 'request_id':'special-equip-'+identity})
        self.assertEqual(result.status_code, 200, result.text)
        return path

    def target(self, dexterity=14):
        from app.session_workspace import save_workspace_token
        return save_workspace_token(self.db, token_type='monster', name='Alvo isolado', latitude=40,
            longitude=40, current_hp=100, maximum_hp=100,
            sheet={'armor_class':99, 'attributes': {} if dexterity is None else {'dexterity':dexterity}})['id']

    def request(self, target, key='special-net-hit', **extra):
        return {'request_id':key, 'attack_id':'melee', 'target_type':'token', 'target_id':target,
                'roll_mode':'physical', 'd20':20, **extra}

    def test_net_hits_touch_ac_without_damage_and_is_idempotent(self):
        from app.combat_effects import readeffects
        from app.session_workspace import list_workspace_tokens
        self.equip('kit-explorador-rede','Rede')
        target = self.target()
        request = self.request(target)
        result = self.client.post('/characters/vezemir/attacks/resolve', json=request)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['target_ac'], 12)
        self.assertEqual(result.json()['damage_total'], 0)
        endpoint = '/combat/attacks/' + result.json()['resolution_id'] + '/confirm'
        confirmed = self.client.post(endpoint)
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        self.assertEqual(confirmed.json()['breakdown']['item_special_result']['label'], 'Constrito')
        self.assertEqual(self.client.post(endpoint).status_code, 200)
        replay = self.client.post('/characters/vezemir/attacks/resolve', json=request)
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json()['resolution_id'], result.json()['resolution_id'])
        nets = [e for e in readeffects(self.db)['effects'] if e.get('item_special')=='net']
        self.assertEqual(len(nets), 1)
        self.assertEqual(next(t for t in list_workspace_tokens(self.db) if t['id']==target)['current_hp'],100)
        second = self.client.post('/characters/vezemir/attacks/resolve', json=self.request(target, 'special-net-duplicate'))
        self.assertEqual(second.status_code,400,second.text)
        self.assertIn('Rede indisponível',second.text)

    def test_net_requires_real_dexterity_before_reserving_a_roll(self):
        self.equip('kit-explorador-rede','Rede')
        result = self.client.post('/characters/vezemir/attacks/resolve',json=self.request(self.target(None)))
        self.assertEqual(result.status_code,400,result.text)
        self.assertIn('Destreza',result.text)

    def test_miss_does_not_bind_and_release_restores_use_of_same_net(self):
        from app.combat_effects import readeffects, effect_command
        self.equip('kit-explorador-rede','Rede')
        target=self.target()
        missed=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(target,'special-net-miss',d20=1))
        self.assertEqual(missed.status_code,200,missed.text)
        self.assertEqual(self.client.post('/combat/attacks/'+missed.json()['resolution_id']+'/confirm').status_code,200)
        self.assertFalse(any(e.get('item_special')=='net' for e in readeffects(self.db)['effects']))
        hit=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(target,'special-net-next-hit'))
        confirmed=self.client.post('/combat/attacks/'+hit.json()['resolution_id']+'/confirm')
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        effect_id=confirmed.json()['breakdown']['item_special_result']['effect_id']
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='special-net-release',
            expected_version=readeffects(self.db)['version'],action='remove',payload={'id':effect_id})
        again=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(target,'special-net-reuse'))
        self.assertEqual(again.status_code,200,again.text)

    def test_blowgun_consumes_one_dart_and_records_x3_without_consuming_bolts(self):
        from app.player_inventory import upsert_inventory, list_inventory
        self.equip('arma-distancia-zarabatana','Zarabatana','À distância')
        for identity in ('arma-distancia-dardo-zarabatana-x20','arma-distancia-dardo-x20'):
            upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+identity,
                item_title=identity,quantity=1,equipped=False,notes=None,charges_current=20,charges_max=20)
        request=self.request(self.target(),'special-blowgun-shot',attack_id='ranged')
        result=self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['breakdown']['strikes'][0]['critical_multiplier'],3)
        endpoint='/combat/attacks/'+result.json()['resolution_id']+'/confirm'
        self.assertEqual(self.client.post(endpoint).status_code,200)
        self.assertEqual(self.client.post(endpoint).status_code,200)
        inventory={i['item_path']:i for i in list_inventory(self.db,'vezemir')}
        self.assertEqual(inventory['compendium:arma-distancia-dardo-zarabatana-x20']['charges_current'],19)
        self.assertEqual(inventory['compendium:arma-distancia-dardo-x20']['charges_current'],20)

    def test_selected_damage_is_auditable_and_cannot_change_on_retry(self):
        self.equip('arma-corpo-espada-bastarda','Espada bastarda')
        target = self.target()
        request = self.request(target,'special-mixed-weapon')
        rejected = self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(rejected.status_code,400,rejected.text)
        request['damage_type']='bludgeoning'
        result = self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['breakdown']['damage_profile']['damage_type'],'bludgeoning')
        changed = self.client.post('/characters/vezemir/attacks/resolve',json={**request,'damage_type':'slashing'})
        self.assertEqual(changed.status_code,400,changed.text)
