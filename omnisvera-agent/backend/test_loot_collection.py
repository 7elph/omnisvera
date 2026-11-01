"""One-click group loot over synthetic native wallet/inventory/ledger."""
import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_map_commerce
from app.access import AccessContext
from app.session_workspace import save_workspace_token
from app.player_inventory import list_inventory
from app.combat_effects import init_effects


class GroupLootCollectionTests(unittest.TestCase):
    def setUp(self):
        test_map_commerce.MapCommerceTests.setUp(self)
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO character_states(profile_id,state_json,updated_at) VALUES('raziel','{}','now')")
        for name in ['vezemir','raziel']:
            save_workspace_token(self.db,map_id='default',token_type='character',character_id=name,name=name,latitude=40,longitude=40,visible_to_players=True)
        self.source=self.corpse()
        self.generation=patch('app.loot._generate_rewards',return_value=([
            {'id':'money','kind':'PO','name':'Moedas de ouro','quantity':1},
            {'id':'sword','kind':'equipment','name':'Espada longa','item_path':'compendium:arma-corpo-espada-longa','quantity':1}],[]))
        self.generator=self.generation.start();self.addCleanup(self.generation.stop)
        self.expansion=patch('app.loot._expand_digital_rewards',side_effect=lambda rewards,rolls,rng:(rewards,rolls))
        self.expansion.start();self.addCleanup(self.expansion.stop)

    def corpse(self):
        return save_workspace_token(self.db,map_id='default',token_type='monster',name='Synthetic loot source',latitude=40,longitude=40,
            current_hp=0,maximum_hp=10,visible_to_players=True,sheet={'treasure':'Q (G)'})

    def collect(self,key='collect-first',access=None,token=None):
        from app.loot_collection import collect_group_loot
        return collect_group_loot(self.db,access or self.owner,request_id=key,token_id=(token or self.source)['id'])

    def money(self,profile):
        from app.merchant import purse_copper
        with closing(sqlite3.connect(self.db)) as db:
            return purse_copper(json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(profile,)).fetchone()[0]))

    def test_group_division_atomic_receipt_and_reload_retry(self):
        before={p:self.money(p) for p in ['raziel','vezemir']}
        result=self.collect()
        self.assertEqual(self.collect(),result)
        self.assertEqual(self.collect('collect-alias'),result)
        self.assertEqual(self.collect('collect-other-member',AccessContext(mode='player',profile_id='raziel')),result)
        for p in before:self.assertEqual(self.money(p)-before[p],50)
        self.assertEqual(sum(i['quantity'] for p in before for i in list_inventory(self.db,p) if i['item_path']=='compendium:arma-corpo-espada-longa'),1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM loot_resolutions WHERE status='distributed'").fetchone()[0],1)
            self.assertTrue(json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.source['id'],)).fetchone()[0])['loot_collected'])

    def test_indivisible_items_rotate_between_corpses(self):
        first=self.collect();second=self.collect('collect-second-corpse',token=self.corpse())
        recipients=lambda result:[s['character_id'] for s in result['shares'] if any(r['kind']=='equipment' for r in s['rewards'])]
        self.assertNotEqual(recipients(first),recipients(second))

    def test_combat_party_is_preserved_when_pins_return_to_exploration(self):
        from app.battle_mode import retire_defeated
        encounter={'active':True,'battle_mode':True,'map_id':'default','turn_index':0,'participants':[
            {'target_type':'character','target_id':'vezemir','name':'Vezemir'},
            {'target_type':'token','target_id':self.source['id'],'name':'Defeated source'}],
            'defeated':[{'target_type':'character','target_id':'raziel','name':'Raziel'}]}
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
            retire_defeated(db,'now')
            # The existing battle restoration moves the same pins elsewhere.
            db.execute("UPDATE session_workspace_tokens SET map_id='exploration-fixture' WHERE token_type='character'")
            db.execute("UPDATE combat_effect_clock SET encounter_json='{}' WHERE id=1")
        result=self.collect()
        self.assertEqual(sorted(s['character_id'] for s in result['shares']),['raziel','vezemir'])

    def test_coin_remainders_rotate_without_loss_and_command_cannot_change_source(self):
        from app.loot import LootConflictError
        self.generator.return_value=([{'id':'small','kind':'pc','name':'Moedas de cobre','quantity':1}],[])
        before={p:self.money(p) for p in ['raziel','vezemir']}
        self.collect();second=self.corpse()
        with self.assertRaises(LootConflictError):self.collect(token=second)
        self.collect('collect-copper-second',token=second)
        for person in before:self.assertEqual(self.money(person)-before[person],1)

    def test_currency_conversion_preserves_private_source_notes_without_exposing_them(self):
        from app.loot import list_loot
        self.generator.return_value=([{'id':'noted-coin','kind':'po','name':'Moedas de ouro','quantity':1,'gm_notes':'private provenance'}],[])
        receipt=self.collect()
        self.assertIn('private provenance',json.dumps(list_loot(self.db,self.gm)))
        self.assertNotIn('private provenance',json.dumps(list_loot(self.db,self.owner)))
        self.assertNotIn('private provenance',json.dumps(receipt))

    def test_two_members_collect_same_source_only_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self.collect,'race-'+name,AccessContext(mode='player',profile_id=name)) for name in ['vezemir','raziel']]
            results=[f.result() for f in futures]
        self.assertEqual(results[0],results[1])

    def test_unauthorized_hidden_live_summoned_and_lair_only_sources_rejected(self):
        from app.loot import LootConflictError
        with self.assertRaises(PermissionError):self.collect(access=AccessContext(mode='player',profile_id='outsider'))
        for changes in [{'current_hp':1},{'visible_to_players':0},{'sheet_json':json.dumps({'treasure':'Q','summon':{'caster':'morthak'}})},
                        {'sheet_json':json.dumps({'treasure':'(G)'})}]:
            token=self.corpse()
            with closing(sqlite3.connect(self.db)) as db, db:
                for column,value in changes.items():db.execute('UPDATE session_workspace_tokens SET '+column+'=? WHERE id=?',(value,token['id']))
            with self.subTest(changes=changes),self.assertRaises((PermissionError,LootConflictError)):
                self.collect('invalid-'+token['id'],token=token)

    def test_failure_after_generation_rolls_back_wallet_rewards_rotation_and_chest(self):
        with patch('app.item_transfer.grant_item',side_effect=ValueError('synthetic failure')):
            with self.assertRaises(ValueError):self.collect()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM loot_resolutions WHERE status='draft'").fetchone()[0],1)
        self.assertEqual(self.money('raziel'),0)
        self.assertTrue(self.collect())
        self.assertEqual(self.generator.call_count,1)

    def test_existing_private_gm_draft_is_not_revealed_by_player(self):
        from app.loot import resolve_token_loot,LootConflictError
        draft,_=resolve_token_loot(self.db,request_id='private-draft',token_id=self.source['id'],scope='carried',roll_mode='digital')
        with self.assertRaises(LootConflictError):self.collect()
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT status FROM loot_resolutions WHERE resolution_id=?',(draft['resolution_id'],)).fetchone()[0],'draft')

    def test_gm_edit_of_failed_auto_delivery_requires_new_gm_approval(self):
        from app.loot import update_loot_rewards,LootConflictError,list_loot
        with patch('app.item_transfer.grant_item',side_effect=ValueError('blocked inventory')):
            with self.assertRaises(ValueError):self.collect()
        with closing(sqlite3.connect(self.db)) as db:
            resolution=db.execute('SELECT resolution_id FROM loot_resolutions').fetchone()[0]
        update_loot_rewards(self.db,resolution,[{'id':'changed','kind':'equipment','name':'Private GM revision',
            'item_path':'compendium:arma-corpo-espada-longa','quantity':1,'gm_notes':'Private audit'}])
        with self.assertRaises(LootConflictError):self.collect('collect-after-private-edit')
        self.assertEqual(list_loot(self.db,self.owner),[])
        receipt=self.collect('gm-approved-new-edit',self.gm)
        self.assertNotIn('Private audit',json.dumps(receipt))

    def test_http_uses_authorized_group_and_rejects_client_distribution(self):
        from app import main
        from dataclasses import replace
        from fastapi.testclient import TestClient
        with patch.object(main,'settings',replace(main.settings,database_path=self.db)),patch.dict(main.app.dependency_overrides,{main.require_any:lambda:self.owner}):
            client=TestClient(main.app)  # No lifespan/index/workers for this unit test.
            try:
                body={'request_id':'http-collection','token_id':self.source['id']}
                self.assertEqual(client.post('/workspace/loot/collect',json={**body,'recipients':['outsider']}).status_code,422)
                response=client.post('/workspace/loot/collect',json=body)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(client.post('/workspace/loot/collect',json=body).json(),response.json())
                self.assertNotIn('gm_notes',json.dumps(response.json()))
            finally:client.close()

    def test_manual_gm_distribution_also_hides_the_chest(self):
        from app.loot import resolve_token_loot,reveal_loot,distribute_loot
        from app.session_workspace import list_workspace_tokens
        result,_=resolve_token_loot(self.db,request_id='manual-source',token_id=self.source['id'],scope='carried',roll_mode='digital')
        reveal_loot(self.db,result['resolution_id'])
        distribute_loot(self.db,resolution_id=result['resolution_id'],request_id='manual-distribute',allocations=[
            {'reward_id':r['id'],'character_id':'vezemir','quantity':r['quantity']} for r in result['rewards']])
        token=next(t for t in list_workspace_tokens(self.db) if t['id']==self.source['id'])
        self.assertTrue(token['sheet']['loot_collected'])


if __name__=='__main__':unittest.main()
