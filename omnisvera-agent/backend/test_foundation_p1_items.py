"""P1 item composition. Synthetic SQLite only; source prices, native commands."""
import json
import sqlite3
import unittest
from contextlib import closing

import test_map_commerce
from app import map_commerce as shop
from app.item_families import consume_ammunition
from app.item_registry import registry, resolve_item
from app.item_transfer import grant_item
from app.merchant import add_stock, purse_copper
from app.player_inventory import list_inventory


class AmmunitionReplenishmentTests(unittest.TestCase):
    setUp = test_map_commerce.MapCommerceTests.setUp
    purse = test_map_commerce.MapCommerceTests.purse

    def _buy(self, line, key):
        q = shop.quote(self.db, self.mid, self.owner, request_id=key+'-quote',
            character_id='vezemir', kind='buy', target_id=line['id'], quantity=1)
        return shop.confirm(self.db, q['id'], self.owner, request_id=key+'-confirm'), q

    def _open_pack(self, remaining=13):
        with closing(sqlite3.connect(self.db)) as db, db:
            state=self.purse();state['coins']=30
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        line=add_stock(self.db, merchant_id=self.mid,
            compendium_item_id='arma-distancia-flecha-x20', quantity=4)
        self._buy(line, 'initial-arrows')
        self.path='compendium:arma-distancia-flecha-x20'
        with closing(sqlite3.connect(self.db)) as db, db:
            consume_ammunition(db, 'vezemir', dict(item_path=self.path,pack_size=20,amount=20-remaining), 'now', apply=True)
        return line

    def _count(self):
        row=next(i for i in list_inventory(self.db,'vezemir') if i['item_path']==self.path)
        return (row['quantity']-1)*20+row['charges_current'], row

    def test_buy_fresh_pack_after_shooting_preserves_open_pack_and_retries(self):
        line=self._open_pack(); before=purse_copper(self.purse())
        receipt,q=self._buy(line,'replenish-arrows')
        self.assertEqual(self._count()[0],33)
        self.assertEqual(self._count()[1]['charges_current'],13)
        self.assertEqual(purse_copper(self.purse()),before-q['total_copper'])
        self.assertEqual(shop.confirm(self.db,q['id'],self.owner,request_id='replenish-other-retry'),receipt)
        self.assertEqual(self._count()[0],33)
        change=receipt['inventory_changes'][0]
        self.assertEqual((change['charges_current'],change['charges_max']),(13,20))

    def test_reward_of_full_pack_merges_without_resetting_partial_pack(self):
        self._open_pack(1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE')
            item=resolve_item(registry(db),self.path)
            grant_item(db,item,'vezemir',2,'now',origin='synthetic reward',
                instance={'charges_current':20,'charges_max':20})
            consume_ammunition(db,'vezemir',dict(item_path=self.path,pack_size=20,amount=2),'now',apply=True)
        self.assertEqual(self._count()[0],39)
        self.assertEqual((self._count()[1]['quantity'],self._count()[1]['charges_current']),(2,19))

    def test_partial_new_pack_still_cannot_merge_or_spend_wallet(self):
        self._open_pack(); before=self._count(); wallet=self.purse()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE')
            with self.assertRaises(ValueError):
                grant_item(db,resolve_item(registry(db),self.path),'vezemir',1,'now',origin='invalid partial',
                    instance={'charges_current':13,'charges_max':20})
        self.assertEqual(self._count(),before);self.assertEqual(self.purse(),wallet)

    def test_corrupt_pack_metadata_cannot_be_normalized_by_purchase(self):
        line=self._open_pack()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE player_inventory SET charges_max=99 WHERE item_path=?',(self.path,))
        wallet=self.purse()
        with self.assertRaises(ValueError):self._buy(line,'corrupt-replenish')
        self.assertEqual(self.purse(),wallet)


class ItemFamilyCircuitTests(unittest.TestCase):
    """Public action routes and native quote/loot commands share one TEMP DB."""
    def setUp(self):
        import test_item_families
        from app.access import AccessContext
        from app.merchant import create_merchant
        from app.session_workspace import save_workspace_token, set_workspace_map
        test_item_families.ItemFamilyApiTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db, db:
            raw=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            raw['attacks']={'melee_bonus':5,'ranged_bonus':5}
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(raw),))
        self.client.get('/characters/vezemir').raise_for_status()
        with closing(sqlite3.connect(self.db)) as db, db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(coins=100000,current_hp=1,maximum_hp=20)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        self.gm=AccessContext(mode='gm');self.owner=AccessContext(mode='player',profile_id='vezemir')
        map_id=set_workspace_map(self.db,title='Synthetic item circuit',image_path='fixture.svg',visible_to_players=True)['id']
        self.map_id=map_id
        pin=save_workspace_token(self.db,token_type='location',name='Synthetic counter',latitude=40,longitude=40,map_id=map_id,visible_to_players=True)
        self.mid=create_merchant(self.db,name='Synthetic family merchant',location='Fixture')['id']
        shop.configure(self.db,self.mid,self.gm,token_id=pin['id'],enabled=True,buy_pct=50)
        self.sequence=0

    def tearDown(self):
        import test_item_families
        test_item_families.ItemFamilyApiTests.tearDown(self)

    def key(self):
        self.sequence+=1
        return 'p1-family-'+str(self.sequence)

    def trade(self,kind,target,quantity=1):
        q=shop.quote(self.db,self.mid,self.owner,request_id=self.key(),character_id='vezemir',kind=kind,target_id=target,quantity=quantity)
        receipt=shop.confirm(self.db,q['id'],self.owner,request_id=self.key())
        self.assertEqual(shop.confirm(self.db,q['id'],self.owner,request_id=self.key()),receipt)
        return receipt

    def buy(self,catalog_id,quantity=1):
        line=add_stock(self.db,merchant_id=self.mid,compendium_item_id=catalog_id,quantity=3)
        receipt=self.trade('buy',line['id'],quantity)
        return receipt['inventory_changes'][0]['item_path']

    def reward(self,path,token=None):
        from app import loot
        from app.session_workspace import save_workspace_token
        from test_loot import SequenceRng
        loot.init_loot(self.db)
        token=token or save_workspace_token(self.db,token_type='monster',name='Synthetic defeated source',latitude=45,longitude=45,current_hp=0,maximum_hp=1,sheet={'treasure':'Q'})
        result,_=loot.resolve_token_loot(self.db,request_id=self.key(),token_id=token['id'],scope='carried',roll_mode='digital',rng=SequenceRng(1,1,1))
        rid=result['resolution_id']
        loot.update_loot_rewards(self.db,rid,[dict(id='item',kind='equipment',name='Synthetic reward',item_path=path,quantity=1)])
        self.assertNotIn(rid,[entry['resolution_id'] for entry in loot.list_loot(self.db,self.owner)])
        loot.reveal_loot(self.db,rid)
        args=dict(resolution_id=rid,allocations=[dict(reward_id='item',character_id='vezemir',quantity=1)])
        self.assertTrue(loot.distribute_loot(self.db,request_id=self.key(),**args)[1])
        self.assertFalse(loot.distribute_loot(self.db,request_id=self.key(),**args)[1])

    def action(self,action,path,slot=None):
        response=self.client.post('/characters/vezemir/actions',json={'action':action,'request_id':self.key(),
            'payload':{'item_path':path,**({'equipment_slot':slot} if slot else {})}})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def owned(self,path):
        return next(i for i in list_inventory(self.db,'vezemir',include_empty=True) if i['item_path']==path)

    def test_combat_defeat_loot_equip_attack_sale_persists_without_duplicates(self):
        from app.combat_effects import effect_command, readeffects
        from app.session_workspace import save_workspace_token, update_workspace_table_mode, list_workspace_tokens
        from app import world_travel as travel
        from app.scene_play import create_scene
        locations=[travel.create_location(self.db,request_id=self.key(),campaign_id='synthetic-foundation',actor_id='master',
            fields={'name':name,'visibility':'table','discovered_by_default':True})[0]
            for name in ['Nimalia (fixture)','Destination (fixture)']]
        journey=travel.create_journey(self.db,request_id=self.key(),campaign_id='synthetic-foundation',actor_id='master',fields={
            'origin_location_id':locations[0]['id'],'destination_location_id':locations[1]['id'],'title':'Synthetic encounter journey','progress_target':2})[0]
        travel.add_journey_participant(self.db,journey['id'],request_id=self.key(),actor_id='master',fields={
            'participant_type':'player_character','character_id':'vezemir','public_label':'Synthetic traveler'})
        scene=create_scene(self.db,request_id=self.key(),campaign_id='synthetic-foundation',title='Synthetic encounter',
            location_name='Fixture',created_by='master',visibility='gm',private_notes='Synthetic hidden objective')[0]
        travel.link_journey_scene(self.db,journey['id'],request_id=self.key(),actor_id='master',scene_id=scene['id'],stage_label='Encounter',progress_value=1)
        journey=travel.transition_journey(self.db,journey['id'],request_id=self.key(),actor_id='master',action='start',expected_version=journey['version'])
        journey=travel.advance_journey(self.db,journey['id'],request_id=self.key(),actor_id='master',amount=1,expected_version=journey['version'])
        journey=travel.transition_journey(self.db,journey['id'],request_id=self.key(),actor_id='master',action='pause',expected_version=journey['version'])
        self.assertEqual(travel.get_journey(self.db,journey['id'],access_mode='player',profile_id='vezemir')['scene_links'],[])
        update_workspace_table_mode(self.db,'physical')
        initial_weapon=self.buy('arma-corpo-espada-curta')
        self.action('equip_item',initial_weapon,'Corpo a corpo')
        sword='compendium:arma-corpo-espada-longa'
        victim=save_workspace_token(self.db,token_type='monster',name='Synthetic orc',latitude=45,longitude=45,map_id=self.map_id,
            current_hp=1,maximum_hp=1,sheet={'armor_class':10,'treasure':'Q'})
        effect_command(self.db,actor_id='master',actor_role='gm',request_id=self.key(),expected_version=readeffects(self.db)['version'],action='start',
            payload={'map_id':self.map_id,'participants':[{'target_type':'character','target_id':'vezemir','initiative':10},
                {'target_type':'token','target_id':victim['id'],'initiative':1}]})
        command={'request_id':self.key(),'attack_id':'melee','weapon_item_path':initial_weapon,'target_type':'token','target_id':victim['id'],'roll_mode':'physical','d20':20}
        attack=self.client.post('/characters/vezemir/attacks/resolve',json=command)
        self.assertEqual(attack.status_code,200,attack.text)
        endpoint='/combat/attacks/'+attack.json()['resolution_id']+'/confirm'
        first=self.client.post(endpoint);self.assertEqual(first.status_code,200,first.text)
        self.assertEqual(self.client.post(endpoint).status_code,200)
        dead=next(t for t in list_workspace_tokens(self.db) if t['id']==victim['id'])
        self.assertEqual(dead['current_hp'],0)
        self.reward(sword,dead)
        self.assertEqual(self.owned(sword)['quantity'],1)
        effect_command(self.db,actor_id='master',actor_role='gm',request_id=self.key(),expected_version=readeffects(self.db)['version'],action='end',payload={})
        self.action('unequip_item',initial_weapon)
        self.action('equip_item',sword,'Corpo a corpo')
        dummy=save_workspace_token(self.db,token_type='monster',name='Synthetic sword target',latitude=45,longitude=45,map_id=self.map_id,current_hp=1,maximum_hp=1,sheet={'armor_class':10})
        command.update(request_id=self.key(),weapon_item_path=sword,target_id=dummy['id'])
        attack=self.client.post('/characters/vezemir/attacks/resolve',json=command)
        self.assertEqual(attack.status_code,200,attack.text)
        confirmed=self.client.post('/combat/attacks/'+attack.json()['resolution_id']+'/confirm')
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.assertEqual(next(t for t in list_workspace_tokens(self.db) if t['id']==dummy['id'])['current_hp'],0)
        journey=travel.transition_journey(self.db,journey['id'],request_id=self.key(),actor_id='master',action='resume',expected_version=journey['version'])
        travel.complete_journey(self.db,journey['id'],request_id=self.key(),actor_id='master',expected_version=journey['version'])
        self.assertEqual(self._wallet()['current_location_id'],locations[1]['id'])
        self.action('unequip_item',sword)
        before=shop.purse_copper(self._wallet())
        receipt=self.trade('sell',sword)
        self.assertEqual(self.owned(sword)['quantity'],0)
        self.assertEqual(shop.purse_copper(self._wallet()),before+receipt['total_copper'])
        # Fresh reads, not response objects, prove persisted inventory and audit.
        self.assertEqual(self.client.get('/characters/vezemir?read_only=true').status_code,200)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM loot_resolutions WHERE status='distributed'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='commerce' AND source_id=?",(receipt['receipt_id'],)).fetchone()[0],1)

    def _wallet(self):
        with closing(sqlite3.connect(self.db)) as db:
            return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])

    def test_armor_and_shield_buy_reward_equip_effect_unequip_resell(self):
        for identity,slot,expected in [('kit-basico-armadura-de-couro-2-6-7-kg-20-po','Armadura',12),('kit-basico-escudo-de-madeira-1-3-kg-8-po','Mão secundária',11)]:
            with self.subTest(identity=identity):
                path=self.buy(identity);self.reward(path)
                self.assertEqual(self.owned(path)['quantity'],2)
                sheet=self.action('equip_item',path,slot)
                self.assertEqual(sheet['definition']['defenses']['armor_class'],expected)
                with self.assertRaises(ValueError):self.trade('sell',path)
                self.assertEqual(self.action('unequip_item',path)['definition']['defenses']['armor_class'],10)
                self.trade('sell',path,2)
                self.assertEqual(self.owned(path)['quantity'],0)

    def test_hp_potion_buy_resource_use_retry_and_resell_remaining(self):
        path=self.buy('campanha-pocao-hp',2)
        response=self.client.post('/characters/vezemir/actions',json={'action':'use_item','request_id':'p1-potion-use', 'payload':{'item_path':path}})
        self.assertEqual(response.status_code,200,response.text)
        self.assertGreater(response.json()['state']['current_hp'],1)
        self.assertEqual(self.owned(path)['quantity'],1)
        again=self.client.post('/characters/vezemir/actions',json={'action':'use_item','request_id':'p1-potion-use','payload':{'item_path':path}})
        self.assertEqual(again.status_code,200,again.text)
        self.assertEqual(again.json()['state']['current_hp'],response.json()['state']['current_hp'])
        self.assertEqual(self.owned(path)['quantity'],1)
        self.trade('sell',path);self.assertEqual(self.owned(path)['quantity'],0)

    def test_descriptive_families_have_native_identity_and_no_invented_action(self):
        from app.item_catalog import load_item_catalog
        catalog=load_item_catalog()['items']
        prefixes=['kit-basico-corda-','propriedades-carroca-','propriedades-cavalo-de-montaria-','item-magico-tapete-voador']
        for prefix in prefixes:
            with self.subTest(family=prefix):
                item=next(i for i in catalog if i['id'].startswith(prefix))
                path=self.buy(item['id']);self.reward(path)
                self.assertEqual(self.owned(path)['quantity'],2)
                projection=shop.catalog_inventory(path)
                self.assertFalse(projection['usable'])
                self.trade('sell',path,2)
                self.assertEqual(self.owned(path)['quantity'],0)

    def test_structured_magic_item_uses_charges_and_requires_individual_resale(self):
        from app.session_workspace import save_session_item
        from app.merchant_appraisals import appraise
        item=save_session_item(self.db,name='Synthetic charged talisman',item_type='item',description='QA only',effects=[],usable=True,
            mechanics={'base_price_po':2,'magical':True,'consume_mode':'charges','charges_max':3,'recharge':'daily'},
            effect_rules=[{'trigger':'on_use','kind':'temporary_hp','value':4}])
        path=self.buy(item['item_path'])
        used=self.action('use_item',path)
        self.assertEqual(used['state']['temporary_hp'],4)
        self.assertEqual((self.owned(path)['quantity'],self.owned(path)['charges_current']),(1,2))
        with self.assertRaises(ValueError):self.trade('sell',path)
        appraisal=appraise(self.db,self.mid,self.gm,character_id='vezemir',item_path=path,unit_copper=50,request_id=self.key())
        self.assertTrue(appraisal['id'])
        self.trade('sell',path)
        with closing(sqlite3.connect(self.db)) as db:
            instance=json.loads(db.execute('SELECT instance_json FROM merchant_stock WHERE instance_json IS NOT NULL').fetchone()[0])
        self.assertEqual((instance['charges_current'],instance['charges_max'],instance['recharge']),(2,3,'daily'))


if __name__=='__main__':unittest.main()
