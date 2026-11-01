"""Operational foundation regressions: disposable SQLite, synthetic actors only."""
import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch

from app import loot, merchant
from app.player_inventory import list_inventory, upsert_inventory
import test_loot
import test_merchant
import test_map_commerce


class LootFoundationTests(unittest.TestCase):
    setUp = test_loot.LootResolutionTests.setUp
    tearDown = test_loot.LootResolutionTests.tearDown

    def prepare(self, rewards, key='foundation-loot'):
        result, _ = loot.resolve_token_loot(self.database, request_id=key,
            token_id=self.token['id'], scope='carried', roll_mode='digital',
            rng=test_loot.SequenceRng(1, 1, 1))
        loot.update_loot_rewards(self.database, result['resolution_id'], rewards)
        loot.reveal_loot(self.database, result['resolution_id'])
        allocations = [dict(reward_id=r['id'], character_id='vezemir', quantity=r['quantity']) for r in rewards]
        return result['resolution_id'], allocations

    def distribute(self, resolution, allocations, request='foundation-distribute'):
        return loot.distribute_loot(self.database, resolution_id=resolution,
            request_id=request, allocations=allocations)

    def test_unique_weapon_uses_catalog_identity_and_native_attack_rules(self):
        resolution, allocations = self.prepare([dict(id='sword', kind='equipment', name='Espada longa', quantity=1)])
        self.distribute(resolution, allocations)
        item = list_inventory(self.database, 'vezemir')[0]
        self.assertEqual(item['item_path'], 'compendium:arma-corpo-espada-longa')
        from app.map_commerce import catalog_inventory
        self.assertEqual(catalog_inventory(item['item_path'])['damage_formula'], '1d8')
        self.assertFalse(self.distribute(resolution, allocations, 'foundation-retry')[1])
        self.assertEqual(list_inventory(self.database, 'vezemir')[0]['quantity'], 1)

    def test_explicit_identity_preserves_instance_fields(self):
        reward = dict(id='sword', kind='equipment', name='Espada encontrada', quantity=1,
            item_path='compendium:arma-corpo-espada-longa', charges_current=1, charges_max=3,
            recharge='daily', inventory_condition={'kind':'rust','bonus_remaining':0})
        resolution, allocations = self.prepare([reward])
        self.distribute(resolution, allocations)
        item = list_inventory(self.database, 'vezemir')[0]
        self.assertEqual(item['item_path'], reward['item_path'])
        self.assertEqual((item['charges_current'], item['charges_max'], item['recharge']), (1, 3, 'daily'))
        from app.inventory_conditions import read_condition
        with closing(sqlite3.connect(self.database)) as db:
            db.row_factory = sqlite3.Row
            self.assertEqual(read_condition(db, item['id'])['bonus_remaining'], 0)

    def test_unknown_explicit_identity_rejects_entire_distribution(self):
        rewards = [dict(id='gold', kind='po', name='Ouro', quantity=2),
            dict(id='unknown', kind='item', name='Espada longa', quantity=1, item_path='compendium:does-not-exist')]
        resolution, allocations = self.prepare(rewards)
        with self.assertRaises(ValueError): self.distribute(resolution, allocations)
        self.assertEqual(list_inventory(self.database, 'vezemir'), [])
        with closing(sqlite3.connect(self.database)) as db:
            state = json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])
            self.assertEqual(state.get('coins', 0), 0)
            self.assertEqual(db.execute("SELECT status FROM loot_resolutions WHERE resolution_id=?", (resolution,)).fetchone()[0], 'revealed')

    def test_incompatible_instances_cannot_silently_merge(self):
        path='compendium:arma-corpo-espada-longa'
        upsert_inventory(self.database, profile_id='vezemir', item_path=path, item_title='Espada longa',
            quantity=1, equipped=False, notes=None, charges_current=3, charges_max=3)
        resolution, allocations = self.prepare([dict(id='sword', kind='equipment', name='Espada longa', quantity=1,
            item_path=path, charges_current=1, charges_max=3)])
        with self.assertRaises(ValueError): self.distribute(resolution, allocations)
        self.assertEqual(list_inventory(self.database,'vezemir')[0]['quantity'], 1)

    def test_equal_partial_ammunition_packs_cannot_mint_projectiles_on_merge(self):
        from app.item_catalog import load_item_catalog
        raw=next(item for item in load_item_catalog()['items'] if item['name']=='Flecha x20')
        path='compendium:'+raw['id']
        upsert_inventory(self.database,profile_id='vezemir',item_path=path,item_title=raw['name'],
            quantity=1,equipped=False,notes=None,charges_current=1,charges_max=20)
        resolution,allocations=self.prepare([dict(id='arrows',kind='equipment',name=raw['name'],quantity=1,
            item_path=path,charges_current=1,charges_max=20)])
        with self.assertRaises(ValueError):self.distribute(resolution,allocations)
        row=list_inventory(self.database,'vezemir')[0]
        self.assertEqual((row['quantity'],row['charges_current']),(1,1))

    def test_multiple_partial_packs_need_separate_instance_review(self):
        resolution,allocations=self.prepare([dict(id='partial',kind='equipment',name='Espada longa',quantity=2,
            item_path='compendium:arma-corpo-espada-longa',charges_current=1,charges_max=3)])
        with self.assertRaises(ValueError):self.distribute(resolution,allocations)
        self.assertEqual(list_inventory(self.database,'vezemir'),[])

    def test_ammunition_cannot_override_the_catalog_pack_size(self):
        from app.item_catalog import load_item_catalog
        raw=next(item for item in load_item_catalog()['items'] if item['name']=='Flecha x20')
        resolution,allocations=self.prepare([dict(id='arrows',kind='equipment',name=raw['name'],quantity=1,
            item_path='compendium:'+raw['id'],charges_current=1,charges_max=3)])
        with self.assertRaises(ValueError):self.distribute(resolution,allocations)

    def test_ambiguous_name_remains_a_narrative_item(self):
        resolution, allocations = self.prepare([dict(id='relic',kind='item',name='Relíquia ambígua',quantity=1)])
        entries = {str(i):dict(id=str(i),name='Relíquia ambígua',item_path=f'compendium:{i}',catalog_entry_kind='item',source_kind='book') for i in (1,2)}
        with patch('app.item_registry.registry', return_value={'entries':entries,'by_path':{}}):
            self.distribute(resolution, allocations)
        self.assertTrue(list_inventory(self.database,'vezemir')[0]['item_path'].startswith('session-item:'))
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT usable,mechanics_json FROM session_custom_items').fetchone(), (0,'{}'))

    def test_distribution_request_cannot_be_reused_for_another_resolution(self):
        first, allocations = self.prepare([dict(id='gold',kind='po',name='Ouro',quantity=1)])
        self.distribute(first, allocations)
        with self.assertRaises(ValueError): self.distribute('different-resolution', allocations)

    def test_distribution_retry_cannot_change_its_allocation(self):
        resolution, allocations = self.prepare([dict(id='gold',kind='po',name='Ouro',quantity=1)])
        self.distribute(resolution, allocations)
        with self.assertRaises(ValueError): self.distribute(resolution, [{**allocations[0],'quantity':2}])

    def test_alias_retry_is_bound_to_the_original_distribution(self):
        resolution, allocations = self.prepare([dict(id='gold',kind='po',name='Ouro',quantity=1)])
        self.distribute(resolution, allocations)
        self.distribute(resolution, allocations, 'foundation-alias-retry')
        from app.session_workspace import save_workspace_token
        self.token=save_workspace_token(self.database,token_type='monster',name='Outro orc',latitude=20,longitude=20,
            current_hp=0,maximum_hp=8,sheet={'treasure':'Q'})
        second, other=self.prepare([dict(id='gold',kind='po',name='Ouro',quantity=1)],key='foundation-second-loot')
        with self.assertRaises(ValueError): self.distribute(second, other, 'foundation-alias-retry')

    def test_duplicate_reward_ids_are_rejected_before_reveal(self):
        result,_=loot.resolve_token_loot(self.database,request_id='foundation-draft-loot',token_id=self.token['id'],
            scope='carried',roll_mode='digital',rng=test_loot.SequenceRng(1,1,1))
        resolution=result['resolution_id']
        with self.assertRaises(ValueError):
            loot.update_loot_rewards(self.database, resolution, [dict(id='x',name='A',quantity=1),dict(id='x',name='B',quantity=1)])

    def test_concurrent_distribution_credits_currency_only_once(self):
        resolution,allocations=self.prepare([dict(id='platinum',kind='pl',name='Platina',quantity=1)])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda i:self.distribute(resolution,allocations,f'parallel-distribution-{i}'),range(2)))
        self.assertEqual(sum(result[1] for result in results),1)
        with closing(sqlite3.connect(self.database)) as db:
            state=json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])
            self.assertEqual(merchant.purse_copper(state),10000)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='loot_distribution'").fetchone()[0],1)

    def test_unidentified_known_name_is_not_automatically_activated(self):
        resolution,allocations=self.prepare([dict(id='sword',kind='item',name='Espada longa',quantity=1,requires_identification=True,gm_notes='hidden-fixture-note')])
        self.distribute(resolution,allocations)
        self.assertTrue(list_inventory(self.database,'vezemir')[0]['item_path'].startswith('session-item:'))
        from app.access import AccessContext
        self.assertNotIn('hidden-fixture-note',json.dumps(loot.list_loot(self.database,AccessContext(mode='player',profile_id='vezemir'))))

    def test_legacy_distributed_record_replays_without_rewriting_its_wallet(self):
        resolution,allocations=self.prepare([dict(id='gold',kind='po',name='Ouro',quantity=2)])
        first=self.distribute(resolution,allocations)
        with closing(sqlite3.connect(self.database)) as db,db: db.execute('DELETE FROM loot_distribution_commands')
        again=self.distribute(resolution,allocations)
        self.assertFalse(again[1]);self.assertEqual(first[0],again[0])

    def test_conflicting_explicit_item_references_reject_without_guessing(self):
        resolution,allocations=self.prepare([dict(id='sword',kind='equipment',name='Espada longa',quantity=1,
            item_path='compendium:arma-corpo-espada-longa',catalog_id='arma-corpo-alabarda')])
        with self.assertRaises(ValueError):self.distribute(resolution,allocations)

    def test_generation_request_cannot_change_source_or_mode(self):
        kwargs=dict(request_id='generation-intent',token_id=self.token['id'],scope='carried',roll_mode='quick')
        loot.resolve_token_loot(self.database,**kwargs)
        for changes in ({'token_id':'another-token'},{'roll_mode':'digital'}):
            with self.assertRaises(ValueError):loot.resolve_token_loot(self.database,**{**kwargs,**changes})

    def test_generation_alias_is_bound_to_its_source(self):
        kwargs=dict(token_id=self.token['id'],scope='carried',roll_mode='quick')
        loot.resolve_token_loot(self.database,request_id='generation-first',**kwargs)
        loot.resolve_token_loot(self.database,request_id='generation-alias',**kwargs)
        self.assertFalse(loot.resolve_token_loot(self.database,request_id='generation-alias',**kwargs)[1])
        from app.session_workspace import save_workspace_token
        other=save_workspace_token(self.database,token_type='monster',name='Other fixture',latitude=20,longitude=20,
            current_hp=0,maximum_hp=8,sheet={'treasure':'Q'})
        with self.assertRaises(ValueError):
            loot.resolve_token_loot(self.database,request_id='generation-alias',**{**kwargs,'token_id':other['id']})

    def test_requested_loot_roll_creation_is_atomic_on_failure(self):
        native=loot.create_roll_request;calls=[]
        def fail_second(*args,**kwargs):
            calls.append(1)
            if len(calls)==2:raise ValueError('Injected second-request failure')
            return native(*args,**kwargs)
        from app.session_workspace import save_workspace_token
        self.token=save_workspace_token(self.database,token_type='monster',name='Fixture',latitude=20,longitude=20,
            current_hp=0,maximum_hp=8,sheet={'treasure':'B'})
        with patch('app.loot.create_roll_request',side_effect=fail_second):
            with self.assertRaises(ValueError):
                loot.resolve_requested_token_loot(self.database,request_id='requested-atomicity',token_id=self.token['id'],
                    scope='lair',lair_id='fixture-lair',roller_character_id='vezemir')
        self.assertEqual(len(calls),2,'The fixture must exercise failure after one request was created')
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM dice_roll_requests').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM loot_resolutions').fetchone()[0],0)


class LegacyCommerceFoundationTests(unittest.TestCase):
    setUp = test_merchant.MerchantTests.setUp
    purse = test_merchant.MerchantTests.purse

    def purchase(self, line, **changes):
        return merchant.buy(self.db, merchant_id=self.merchant['id'], stock_id=line['id'],
            character_id='vezemir', quantity=1, final_price_po=1, **changes)

    def stock(self):
        return merchant.add_stock(self.db,merchant_id=self.merchant['id'],compendium_item_id='arma-corpo-espada-longa',quantity=3)

    def test_legacy_buy_requires_a_retry_identity(self):
        line=self.stock()
        with self.assertRaises(ValueError): self.purchase(line)

    def test_legacy_buy_recovers_same_receipt_and_rejects_conflicting_payload(self):
        line=self.stock(); before=merchant.purse_copper(self.purse())
        first=self.purchase(line,request_id='legacy-buy-retry')
        self.assertEqual(self.purchase(line,request_id='legacy-buy-retry',expected_purse=self.purse()), first)
        self.assertEqual(merchant.purse_copper(self.purse()), before-100)
        self.assertEqual(first['balance_after_copper'], before-100)
        with self.assertRaises(ValueError):
            merchant.buy(self.db,merchant_id=self.merchant['id'],stock_id=line['id'],character_id='vezemir',
                quantity=2,final_price_po=1,request_id='legacy-buy-retry')
        self.assertEqual(sum(i['quantity'] for i in list_inventory(self.db,'vezemir')),1)

    def test_concurrent_legacy_buy_applies_only_once(self):
        line=self.stock()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.purchase(line,request_id='legacy-concurrent-buy'),range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(sum(i['quantity'] for i in list_inventory(self.db,'vezemir')),1)

    def test_legacy_sale_is_replayable_and_rejects_equipped_item(self):
        item_path='compendium:arma-corpo-espada-longa'
        upsert_inventory(self.db,profile_id='vezemir',item_path=item_path,item_title='Espada longa',quantity=2,equipped=False,notes=None)
        kwargs=dict(merchant_id=self.merchant['id'],character_id='vezemir',item_path=item_path,quantity=1,unit_price_po=1,request_id='legacy-sale-retry')
        first=merchant.sell(self.db,**kwargs)
        self.assertEqual(merchant.sell(self.db,**kwargs),first)
        self.assertEqual(list_inventory(self.db,'vezemir')[0]['quantity'],1)
        with closing(sqlite3.connect(self.db)) as db,db: db.execute('UPDATE player_inventory SET equipped=1')
        with self.assertRaises(ValueError): merchant.sell(self.db,**{**kwargs,'request_id':'legacy-equipped-sale'})

    def test_two_distinct_purchases_create_two_audit_events(self):
        line=self.stock()
        self.purchase(line,request_id='distinct-purchase-one')
        self.purchase(line,request_id='distinct-purchase-two')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='merchant_buy'").fetchone()[0],2)

    def test_sale_keeps_item_in_the_merchants_stock_and_buyback_uses_its_identity(self):
        item_path='compendium:arma-corpo-espada-longa'
        upsert_inventory(self.db,profile_id='vezemir',item_path=item_path,item_title='Espada longa',quantity=1,equipped=False,notes=None)
        merchant.sell(self.db,merchant_id=self.merchant['id'],character_id='vezemir',item_path=item_path,
            unit_price_po=1,request_id='sale-stock-identity')
        line=merchant.list_merchants(self.db)[0]['stock'][0]
        self.purchase(line,request_id='buy-back-identity')
        self.assertEqual(list_inventory(self.db,'vezemir')[0]['item_path'],item_path)
        self.assertEqual(merchant.list_merchants(self.db)[0]['stock'][0]['quantity'],0)

    def test_native_http_legacy_contract_checks_authorization_and_retry(self):
        from app import main
        from app.access import AccessContext
        from dataclasses import replace
        from fastapi.testclient import TestClient
        line=self.stock();body=dict(character_id='vezemir',stock_id=line['id'],quantity=1,final_price_po=1)
        endpoint=f"/gm/merchants/{self.merchant['id']}/buy"
        with patch.object(main,'settings',replace(main.settings,database_path=self.db,master_token='synthetic-p0-master')):
            client=TestClient(main.app,headers={'X-Omnisvera-Token':'synthetic-p0-master'})
            try:
                self.assertEqual(client.post(endpoint,json=body).status_code,422)
                body['request_id']='http-purchase-retry'
                first=client.post(endpoint,json=body)
                self.assertEqual(first.status_code,200,first.text)
                self.assertEqual(client.post(endpoint,json=body).json(),first.json())
                client.headers['X-Omnisvera-Token']='synthetic-other-player'
                main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
                self.assertIn(client.post(endpoint,json={**body,'request_id':'foreign-purchase-id'}).status_code,(401,403))
                self.assertEqual(client.get('/commerce/characters/vezemir/history').status_code,403)
            finally:
                client.close();main.app.dependency_overrides.clear()
                import gc
                gc.collect()


class CurrencyFoundationTests(unittest.TestCase):
    def test_approved_rate_and_integer_change_conserve_value(self):
        from app.currency import rule_snapshot,COPPER_PER
        from app.item_registry import price
        self.assertEqual(COPPER_PER['platinum_coins'],100*COPPER_PER['coins'])
        self.assertEqual(price('1 PL'),10000)
        self.assertEqual(rule_snapshot()['copper_per']['platinum_coins'],10000)
        before=dict(platinum_coins=2,coins=3,silver_coins=7,copper_coins=9)
        total=merchant.purse_copper(before)
        for cost in range(0,total+1,29):
            after=merchant.transaction_purse(before,total-cost)
            self.assertEqual(merchant.purse_copper(after)+cost,total)
        self.assertEqual(before,dict(platinum_coins=2,coins=3,silver_coins=7,copper_coins=9))

    def test_http_models_preserve_item_instance_and_require_command_identity(self):
        from app.schemas import LootRewardWrite,MerchantBuyRequest,MerchantSellRequest
        from pydantic import ValidationError
        data=dict(id='fixture',kind='item',name='Fixture',quantity=1,item_path='compendium:arma-corpo-espada-longa',
            charges_current=1,charges_max=3,recharge='daily',inventory_condition={'kind':'rust','bonus_remaining':0})
        self.assertEqual(LootRewardWrite(**data).model_dump()['item_path'],data['item_path'])
        for schema,payload in [(MerchantBuyRequest,dict(character_id='fixture',stock_id='stock',final_price_po=1)),
                              (MerchantSellRequest,dict(character_id='fixture',item_path='item',unit_price_po=1))]:
            with self.assertRaises(ValidationError): schema(**payload)


class CommerceInstanceFoundationTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp
    purse=test_map_commerce.MapCommerceTests.purse
    quote=test_map_commerce.MapCommerceTests.quote

    def test_new_purchase_cannot_merge_with_depleted_instance_or_charge_wallet(self):
        from app import map_commerce as shop
        first=shop.confirm(self.db,self.quote()['id'],self.owner,request_id='instance-first-buy')
        path=first['inventory_changes'][0]['item_path']
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=1,charges_max=3 WHERE item_path=?',(path,))
        before=self.purse();q=self.quote('instance-second-buy')
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='instance-conflicting-buy')
        self.assertEqual(self.purse(),before)
        self.assertEqual(list_inventory(self.db,'vezemir')[0]['quantity'],1)
        self.assertEqual(merchant.list_merchants(self.db)[0]['stock'][0]['quantity'],1)

    def test_charged_instances_require_individual_appraisal_even_when_full(self):
        from app import map_commerce as shop
        first=shop.confirm(self.db,self.quote()['id'],self.owner,request_id='charged-first-buy')
        path=first['inventory_changes'][0]['item_path']
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=3,charges_max=3 WHERE item_path=?',(path,))
        with self.assertRaises(ValueError):self.quote('charged-sale-quote',kind='sell',target_id=path)
