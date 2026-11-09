"""Special ammunition, native HTTP receipts and victim-turn effects, TEMP only."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch


class DartCatalogTests(unittest.TestCase):
    def test_bagh_naja_uses_approved_base_without_extra_attack_or_erasing_source(self):
        from app.item_catalog import get_catalog_item
        item=get_catalog_item('arma-corpo-bagh-naja')
        self.assertEqual(item['dano'],'1D6/1D4')
        self.assertEqual(item['damage_formula'],'1d6')
        self.assertEqual(item['mechanics']['critical_threshold'],19)
        self.assertEqual(item['mechanics']['critical_multiplier'],2)
        self.assertIn('provisória',item['mechanics']['campaign_rule'])
        self.assertNotIn('special_effect',item['mechanics']['family_gaps'])
    def test_expansion_common_dart_is_ammunition_not_an_equippable_weapon(self):
        from app.map_commerce import catalog_inventory
        item = catalog_inventory('compendium:arma-distancia-dardo-x20-expansao')
        self.assertEqual(item['item_type'], 'ammunition')
        self.assertEqual(item['mechanics']['ammunition_kind'], 'dart')
        self.assertEqual(item['mechanics']['pack_size'], 20)

    def test_all_eight_special_darts_have_explicit_reviewed_contracts(self):
        from app.map_commerce import catalog_inventory
        for name in ('alucinante', 'cegante', 'de-assobio', 'de-sono', 'ensandecido',
                     'envenenado', 'fluorescente', 'paralisante'):
            with self.subTest(name=name):
                item = catalog_inventory('compendium:arma-distancia-dardo-' + name + '-x10')
                m = item['mechanics']
                self.assertEqual(item['item_type'], 'ammunition')
                self.assertEqual(m['pack_size'], 10)
                self.assertTrue(m['ammunition_effect']['campaign_rule'])
                self.assertNotIn('ammunition', m['family_gaps'])


class DartApiTests(unittest.TestCase):
    def setUp(self):
        from test_item_specials import ItemSpecialApiTests
        ItemSpecialApiTests.setUp(self)
        self.addCleanup(lambda: ItemSpecialApiTests.tearDown(self))
        self.weapon = ItemSpecialApiTests.equip(self, 'arma-distancia-zarabatana', 'Zarabatana', 'À distância')
        from app.player_inventory import upsert_inventory
        for name in ('cegante', 'envenenado', 'de-sono'):
            upsert_inventory(self.db, profile_id='vezemir',
                item_path='compendium:arma-distancia-dardo-' + name + '-x10',
                item_title='Dardo ' + name, quantity=1, equipped=False, notes=None)
        from test_item_specials_advanced import AdvancedItemTests
        self.arena, self.actor, self.enemy = AdvancedItemTests.arena(self)

    def resolve(self, name='cegante', key='dart-fixture-hit', d20=20):
        return self.client.post('/characters/vezemir/attacks/resolve', json={
            'request_id': key, 'attack_id': 'ranged', 'weapon_item_path': self.weapon,
            'ammunition_item_path': 'compendium:arma-distancia-dardo-' + name + '-x10',
            'target_type': 'token', 'target_id': self.enemy['id'], 'roll_mode': 'physical', 'd20': d20})

    def effects(self):
        from app.combat_effects import readeffects
        return [e for e in readeffects(self.db)['effects'] if e.get('item_special') == 'dart']

    def test_selected_dart_hits_without_inventing_base_damage_and_retry_consumes_once(self):
        with patch('app.dorn_spells.save', return_value={'success': False, 'dice': [1], 'total': 1, 'target': 12}), \
             patch('app.item_darts.roll_formula', return_value={'total': 2, 'individual_results': [2]}):
            rolled = self.resolve()
            self.assertEqual(rolled.status_code, 200, rolled.text)
            self.assertEqual(rolled.json()['damage_total'], 0)
            endpoint = '/combat/attacks/' + rolled.json()['resolution_id'] + '/confirm'
            result = self.client.post(endpoint)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['breakdown']['item_dart_results'][0]['turns_remaining'], 2)
            self.assertEqual(self.client.post(endpoint).json(), result.json())
        self.assertEqual(len(self.effects()), 1)
        with closing(sqlite3.connect(self.db)) as db:
            row = db.execute("SELECT quantity,charges_current FROM player_inventory WHERE profile_id='vezemir' AND item_path='compendium:arma-distancia-dardo-cegante-x10'").fetchone()
            self.assertEqual(tuple(row), (1, 9))
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()[0], 100)

    def test_multiple_ammunition_types_require_a_choice_without_reserving_or_spending(self):
        response = self.client.post('/characters/vezemir/attacks/resolve', json={
            'request_id': 'dart-no-silent-selection', 'attack_id': 'ranged', 'weapon_item_path': self.weapon,
            'target_type': 'token', 'target_id': self.enemy['id'], 'roll_mode': 'physical', 'd20': 20})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn('munição', response.text.casefold())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM combat_attack_resolutions').fetchone()[0], 0)

    def hit(self, name='envenenado', *, resisted=False, turns=2, key=None, d20=20):
        key = key or 'dart-hit-' + name
        with patch('app.dorn_spells.save', return_value={'success': resisted, 'dice': [15 if resisted else 1], 'total': 15 if resisted else 1, 'target': 12}), \
             patch('app.item_darts.roll_formula', return_value={'total': turns, 'individual_results': [turns]}):
            rolled = self.resolve(name, key, d20)
            self.assertEqual(rolled.status_code, 200, rolled.text)
            response = self.client.post('/combat/attacks/' + rolled.json()['resolution_id'] + '/confirm')
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()

    def test_save_and_miss_consume_the_projectile_but_do_not_create_a_condition(self):
        self.hit(resisted=True)
        self.hit('cegante', d20=1)
        self.assertEqual(self.effects(), [])
        with closing(sqlite3.connect(self.db)) as db:
            for name in ('cegante', 'envenenado'):
                self.assertEqual(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',
                    ('compendium:arma-distancia-dardo-' + name + '-x10',)).fetchone()[0], 9)

    def test_poison_ticks_before_target_turn_once_and_expires_after_its_second_turn(self):
        from app.combat_effects import effect_command, readeffects
        def command(action, key, payload=None):
            return effect_command(self.db, actor_id='master', actor_role='gm', request_id=key,
                expected_version=readeffects(self.db)['version'], action=action, payload=payload or {})
        command('start', 'dart-start-turns', {'map_id': self.arena, 'participants': [
            {'target_type': 'character', 'target_id': 'vezemir', 'initiative': 20},
            {'target_type': 'token', 'target_id': self.enemy['id'], 'initiative': 1}]})
        self.hit()
        with patch('app.item_darts.roll_formula', return_value={'total': 3, 'individual_results': [3]}) as roll:
            first = command('next_turn', 'dart-turn-1')
            with closing(sqlite3.connect(self.db)) as db:
                self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()[0], 97)
            self.assertEqual(command('next_turn', 'dart-turn-1'), first)
            self.assertEqual(roll.call_count, 1)
            command('next_turn', 'dart-turn-2')
            self.assertEqual(self.effects()[0]['turns_remaining'], 1)
            command('next_turn', 'dart-turn-3')
            self.assertEqual(roll.call_count, 2)
            command('next_turn', 'dart-turn-4')
            self.assertEqual(self.effects(), [])
            command('next_turn', 'dart-turn-5')
            self.assertEqual(roll.call_count, 2)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='item_dart'").fetchone()[0], 2)

    def test_sleep_blocks_actions_and_movement_for_one_whole_victim_turn(self):
        from app.combat_effects import effect_command, readeffects
        from app.monster_conditions import assert_can_act
        from app.item_darts import finish_turn
        self.hit('de-sono', turns=1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.row_factory = sqlite3.Row
            with self.assertRaisesRegex(ValueError, 'agir'):
                assert_can_act(db, self.enemy['id'])
            participant = {'target_type': 'token', 'target_id': self.enemy['id']}
            encounter = {'started_at': 'test', 'turn_sequence': 2}
            finish_turn(db, participant, encounter, 'now')
            finish_turn(db, participant, encounter, 'now')
            assert_can_act(db, self.enemy['id'])
        self.assertFalse(self.effects())

    def test_natural_poison_immunity_is_checked_before_save(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            sheet = json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()[0])
            sheet['damage_immunities'] = ['poison']
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?', (json.dumps(sheet), self.enemy['id']))
        with patch('app.dorn_spells.save', side_effect=AssertionError('Immune target must not roll')):
            rolled = self.resolve('envenenado')
            self.assertEqual(rolled.status_code, 200, rolled.text)
            result = self.client.post('/combat/attacks/' + rolled.json()['resolution_id'] + '/confirm')
            self.assertEqual(result.status_code, 200, result.text)
            self.assertIn('immune', result.json()['breakdown']['item_dart_results'][0])
        self.assertEqual(self.effects(), [])

    def test_ammunition_from_another_inventory_or_incompatible_kind_is_rejected(self):
        from app.player_inventory import upsert_inventory
        for identity, owner in [('arma-distancia-flecha-x20', 'vezemir'), ('arma-distancia-dardo-paralisante-x10', 'raziel')]:
            upsert_inventory(self.db, profile_id=owner, item_path='compendium:' + identity,
                item_title=identity, quantity=1, equipped=False, notes=None)
            response = self.resolve(identity.removeprefix('arma-distancia-dardo-').removesuffix('-x10')) if owner == 'raziel' else self.client.post('/characters/vezemir/attacks/resolve', json={
                'request_id': 'dart-incompatible-ammo', 'attack_id': 'ranged', 'weapon_item_path': self.weapon,
                'ammunition_item_path': 'compendium:' + identity, 'target_type': 'token', 'target_id': self.enemy['id'], 'roll_mode': 'physical', 'd20': 20})
            self.assertEqual(response.status_code, 400, response.text)

    def test_missing_save_rolls_back_consumption_and_effect(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            sheet = json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (self.enemy['id'],)).fetchone()[0])
            sheet.pop('saving_throw')
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?', (json.dumps(sheet), self.enemy['id']))
        rolled = self.resolve()
        self.assertEqual(rolled.status_code, 200, rolled.text)
        result = self.client.post('/combat/attacks/' + rolled.json()['resolution_id'] + '/confirm')
        self.assertEqual(result.status_code, 400, result.text)
        self.assertEqual(self.effects(), [])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIsNone(db.execute("SELECT charges_current FROM player_inventory WHERE item_path='compendium:arma-distancia-dardo-cegante-x10'").fetchone()[0])

    def test_end_combat_cleans_darts_without_editing_base_sheet(self):
        from app.combat_effects import effect_command, readeffects
        effect_command(self.db, actor_id='master', actor_role='gm', request_id='dart-end-start',
            expected_version=readeffects(self.db)['version'], action='start', payload={'map_id': self.arena,
            'participants': [{'target_type': 'character', 'target_id': 'vezemir', 'initiative': 20},
                             {'target_type': 'token', 'target_id': self.enemy['id'], 'initiative': 1}]})
        self.hit()
        effect_command(self.db, actor_id='master', actor_role='gm', request_id='dart-end-finish',
            expected_version=readeffects(self.db)['version'], action='end', payload={})
        self.assertEqual(self.effects(), [])

    def test_cannot_retry_same_command_with_another_ammunition(self):
        self.hit('cegante', key='dart-retry-payload')
        result = self.resolve('envenenado', key='dart-retry-payload')
        self.assertEqual(result.status_code, 400, result.text)
        self.assertIn('request_id', result.text)

    def test_all_eight_execute_and_keep_the_approved_saves_and_signals(self):
        from app.player_inventory import upsert_inventory
        cases={'alucinante': ('wisdom','d20_penalty'), 'ensandecido': ('wisdom','d20_penalty'),
               'cegante': ('constitution','blinded'), 'de-sono': ('constitution','asleep'),
               'paralisante': ('constitution','paralyzed'), 'envenenado': ('constitution','poison_damage'),
               'de-assobio': (None,'whistle'), 'fluorescente': (None,'fluorescent')}
        for name,(attribute,kind) in cases.items():
            with self.subTest(name=name):
                upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:arma-distancia-dardo-'+name+'-x10',
                    item_title='Dardo '+name,quantity=1,equipped=False,notes=None)
                with patch('app.dorn_spells.save',return_value={'success':False,'dice':[1],'total':1,'target':12}) as save, \
                     patch('app.item_darts.roll_formula',return_value={'total':2,'individual_results':[2]}):
                    rolled=self.resolve(name,key='dart-all-eight-'+name)
                    self.assertEqual(rolled.status_code,200,rolled.text)
                    response=self.client.post('/combat/attacks/'+rolled.json()['resolution_id']+'/confirm')
                    self.assertEqual(response.status_code,200,response.text)
                    result=response.json()['breakdown']['item_dart_results'][0]
                    self.assertEqual(result['effect'],kind)
                    if attribute:self.assertEqual(save.call_args.args[2],attribute)
                    else:save.assert_not_called()
                    self.assertEqual(response.json()['damage_total'],0)
        self.assertEqual(len(self.effects()),7)  # The whistle is an instantaneous signal.

    def test_bagh_naja_native_attack_uses_its_own_base_and_critical(self):
        from test_item_specials import ItemSpecialApiTests
        path=ItemSpecialApiTests.equip(self,'arma-corpo-bagh-naja','Bagh Naja')
        response=self.client.post('/characters/vezemir/attacks/resolve',json={
            'request_id':'bagh-native-base','attack_id':'melee','weapon_item_path':path,
            'target_type':'token','target_id':self.enemy['id'],'roll_mode':'physical','d20':20})
        self.assertEqual(response.status_code,200,response.text)
        strike=response.json()['breakdown']['strikes'][0]
        self.assertEqual(strike['critical_multiplier'],2)
        self.assertEqual(len(strike['damage_rolls']),2)
        self.assertTrue(all(1<=die<=6 for die in strike['damage_rolls']))
        self.assertEqual(len(response.json()['breakdown']['strikes']),1)

    def test_private_target_does_not_publish_dart_status_or_ledger_to_players(self):
        from app.access import AccessContext
        from app.main import _combat_snapshot_for_access
        from app.combat_effects import readeffects
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id=?',(self.enemy['id'],))
        result=self.hit()
        public=_combat_snapshot_for_access(readeffects(self.db),AccessContext(mode='player',profile_id='vezemir'))
        self.assertFalse(any(i['target_id']==self.enemy['id'] for i in public['active_effect_icons']))
        self.assertFalse(any(i['target_id']==self.enemy['id'] for i in public['effects']))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT visibility FROM session_ledger WHERE id=?',(result['ledger_id'],)).fetchone()[0],'gm')

    def test_mental_dart_penalty_projects_without_rewriting_attributes_or_stacking_twice(self):
        from app.combat_effects import apply_definition_effects
        effect={'id':'dart-mental','modifiers':{},'difficult_tests':True,'d20_penalty':-2}
        original={'attributes':{'strength':13,'dexterity':14},'attribute_modifiers':{'strength':1,'dexterity':2},
            'attacks':[{'id':'melee','attack_bonus':8,'damage':'1d6'}],
            'defenses':{'armor_class':16,'saving_throw_bonus':1,'initiative':2}}
        projected=apply_definition_effects(original,[effect,{**effect,'id':'other-dart'}])
        self.assertEqual(projected['attacks'][0]['attack_bonus'],6)
        self.assertEqual(projected['defenses']['saving_throw_bonus'],-1)
        self.assertEqual(projected['attribute_modifiers']['dexterity'],0)
        self.assertEqual(projected['attributes'],original['attributes'])
        self.assertEqual(original['attacks'][0]['attack_bonus'],8)


class DartMarketTests(unittest.TestCase):
    def setUp(self):
        from test_map_commerce import MapCommerceTests
        MapCommerceTests.setUp(self)

    def test_purchase_sale_and_retry_use_one_pack_and_native_wallet_receipts(self):
        from app import map_commerce as shop
        from app.merchant import add_stock, purse_copper
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id='arma-distancia-dardo-envenenado-x10',quantity=2)
        def purse():
            with closing(sqlite3.connect(self.db)) as db:
                return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
        before=purse_copper(purse())
        q=shop.quote(self.db,self.mid,self.owner,request_id='dart-buy-quote',character_id='vezemir',kind='buy',target_id=line['id'],quantity=1)
        result=shop.confirm(self.db,q['id'],self.owner,request_id='dart-buy-confirm')
        self.assertEqual(shop.confirm(self.db,q['id'],self.owner,request_id='dart-buy-confirm'),result)
        self.assertEqual(purse_copper(purse()),before-q['total_copper'])
        path='compendium:arma-distancia-dardo-envenenado-x10'
        self.assertEqual(shop.catalog_inventory(path)['mechanics']['pack_size'],10)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',path)).fetchone()[0],1)
        sale=shop.quote(self.db,self.mid,self.owner,request_id='dart-sale-quote',character_id='vezemir',kind='sell',target_id=path,quantity=1)
        sold=shop.confirm(self.db,sale['id'],self.owner,request_id='dart-sale-confirm')
        self.assertEqual(shop.confirm(self.db,sale['id'],self.owner,request_id='dart-sale-confirm'),sold)
        self.assertEqual(purse_copper(purse()),before-q['total_copper']+sale['total_copper'])


if __name__ == '__main__':
    unittest.main()
