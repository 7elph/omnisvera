"""Individual trade and reviewed spell services: disposable native fixtures."""
import json,sqlite3,unittest
from contextlib import closing
from unittest.mock import patch
from app import map_commerce as shop
from app.access import AccessContext
from app.combat_effects import init_effects
import test_map_commerce


class MarketFollowupTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp
    purse=test_map_commerce.MapCommerceTests.purse
    quote=test_map_commerce.MapCommerceTests.quote

    def test_market_fixture_refuses_operational_and_unowned_paths_before_connecting(self):
        from scripts.market_followup_fixture import prepare
        from pathlib import Path
        with patch('sqlite3.connect') as connect:
            for target in [Path.cwd()/'data/omnisvera_companion.sqlite3',self.db]:
                with self.assertRaises(ValueError):prepare(target)
            connect.assert_not_called()

    def used_item(self):
        from app.inventory_conditions import init_schema,save_condition
        with closing(sqlite3.connect(self.db)) as db,db:
            init_schema(db)
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,charges_current,charges_max,updated_at) VALUES('vezemir','compendium:arma-corpo-espada-longa','Espada usada',1,0,1,3,'now')")
            identity=db.execute('SELECT max(id) FROM player_inventory').fetchone()[0]
            save_condition(db,identity,{'kind':'rust','original_bonus':2,'bonus_remaining':1},'now')
        return 'compendium:arma-corpo-espada-longa',identity

    def test_individual_offer_preserves_condition_and_never_restock_as_new(self):
        path,identity=self.used_item()
        approval=shop.appraise_item(self.db,self.mid,self.gm,character_id='vezemir',item_path=path,unit_copper=125,request_id='individual-approve-01')
        self.assertEqual(approval,shop.appraise_item(self.db,self.mid,self.gm,character_id='vezemir',item_path=path,unit_copper=125,request_id='individual-approve-01'))
        q=self.quote(key='used-sale-quote',kind='sell',target_id=path);self.assertEqual(q['total_copper'],125)
        r=shop.confirm(self.db,q['id'],self.owner,request_id='used-sale-confirm')
        self.assertEqual(r,shop.confirm(self.db,q['id'],self.owner,request_id='used-sale-confirm'))
        with closing(sqlite3.connect(self.db)) as db:
            stock=db.execute('SELECT instance_json,quantity FROM merchant_stock WHERE id=?',(r['stock_id'],)).fetchone()
            data=json.loads(stock[0]);self.assertEqual(data['condition']['bonus_remaining'],1);self.assertEqual(data['charges_current'],1);self.assertEqual(stock[1],1)
        with self.assertRaises(ValueError):self.quote(key='cannot-buy-as-new',target_id=r['stock_id'])

    def test_appraisal_rejects_player_and_stale_equipment_or_condition(self):
        path,identity=self.used_item()
        with self.assertRaises(PermissionError):shop.appraise_item(self.db,self.mid,self.owner,character_id='vezemir',item_path=path,unit_copper=125,request_id='player-cannot-appraise')
        shop.appraise_item(self.db,self.mid,self.gm,character_id='vezemir',item_path=path,unit_copper=125,request_id='master-appraise-001')
        q=self.quote(key='stale-appraisal-01',kind='sell',target_id=path)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET charges_current=0 WHERE id=?',(identity,))
        before=self.purse()
        with self.assertRaises(ValueError):shop.confirm(self.db,q['id'],self.owner,request_id='stale-appraisal-confirm')
        self.assertEqual(before,self.purse())

    def test_reviewed_healing_service_uses_native_hp_once_and_book_tariff(self):
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=self.purse();state.update(current_hp=1,maximum_hp=20,coins=100)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",(json.dumps({'race':'Meio-Elfo'}),))
        s=shop.add_service(self.db,self.mid,self.gm,name='Cura',kind='spell',price_copper=3000,spell_id='divina-curar-ferimentos-leves-r')
        q=self.quote(key='healing-service-quote',kind='service',target_id=s['id'])
        with patch('app.merchant_magic.roll_formula',return_value={'total':5,'rolls':[5],'formula':'1d8'}):
            r=shop.confirm(self.db,q['id'],self.owner,request_id='healing-service-confirm')
            again=shop.confirm(self.db,q['id'],self.owner,request_id='healing-service-confirm')
        self.assertEqual(r,again);self.assertEqual(self.purse()['current_hp'],6);self.assertEqual(self.purse()['coins'],70)
        self.assertEqual(r['service_effect']['healing_applied'],5)

    def test_unreviewed_spell_service_is_rejected_without_charge(self):
        with self.assertRaises(ValueError):shop.add_service(self.db,self.mid,self.gm,name='Não automatizada',kind='spell',price_copper=3000,spell_id='arcana-desejo')

    def test_legacy_buy_cannot_turn_acquired_instance_into_new_item(self):
        path,_=self.used_item();shop.appraise_item(self.db,self.mid,self.gm,character_id='vezemir',item_path=path,unit_copper=100,request_id='legacy-appraisal-01')
        q=self.quote(key='legacy-used-sale',kind='sell',target_id=path);r=shop.confirm(self.db,q['id'],self.owner,request_id='legacy-used-confirm')
        from app.merchant import buy
        with self.assertRaises(ValueError):buy(self.db,request_id='used-buy-test-001',merchant_id=self.mid,stock_id=r['stock_id'],character_id='vezemir',quantity=1,final_price_po=1)

    def test_service_defaults_repeat_without_duplicates_and_keep_owner_money(self):
        from app.merchant_magic import configure_defaults
        before=self.purse();a=configure_defaults(self.db,self.mid,self.gm);b=configure_defaults(self.db,self.mid,self.gm)
        self.assertEqual(a,b);self.assertEqual(len(a),4);self.assertEqual(before,self.purse())
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute("SELECT count(*) FROM merchant_services WHERE kind='spell'").fetchone()[0],4)

    def test_healing_rejects_undead_and_active_combat_before_payment(self):
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=self.purse();state.update(current_hp=1,maximum_hp=20,coins=100)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",(json.dumps({'race':'Vampiro'}),))
        s=shop.add_service(self.db,self.mid,self.gm,name='Cura',kind='spell',price_copper=3000,spell_id='divina-curar-ferimentos-leves-r')
        before=self.purse()
        with self.assertRaises(ValueError):self.quote(key='undead-service-quote',kind='service',target_id=s['id'])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",(json.dumps({'race':'Meio-Elfo'}),))
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps({'active':True}),))
        with self.assertRaises(ValueError):self.quote(key='combat-service-quote',kind='service',target_id=s['id'])
        self.assertEqual(before,self.purse())

    def test_healing_reads_existing_root_race_without_rewriting_sheet(self):
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=self.purse();state.update(current_hp=1,maximum_hp=20,coins=100)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            raw=db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]
            sheet=json.loads(raw);sheet['race']={'race':'Meio-Elfo'};raw=json.dumps(sheet)
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(raw,))
        s=shop.add_service(self.db,self.mid,self.gm,name='Cura',kind='spell',price_copper=3000,spell_id='divina-curar-ferimentos-leves-r')
        q=self.quote(key='legacy-race-healing',kind='service',target_id=s['id'])
        shop.confirm(self.db,q['id'],self.owner,request_id='legacy-race-heal-confirm')
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0],raw)

    def test_paralysis_service_removes_only_the_identified_condition(self):
        init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=self.purse();state.update(coins=100,conditions=['Paralisia','Envenenado'])
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        s=shop.add_service(self.db,self.mid,self.gm,name='Remover paralisia',kind='spell',price_copper=9000,spell_id='divina-remover-paralisia')
        q=self.quote(key='paralysis-service-quote',kind='service',target_id=s['id']);r=shop.confirm(self.db,q['id'],self.owner,request_id='paralysis-service-confirm')
        self.assertEqual(self.purse()['conditions'],['Envenenado']);self.assertEqual(self.purse()['coins'],10)
        self.assertEqual(r['service_effect']['removed_conditions'],['Paralisia'])
        with self.assertRaises(ValueError):self.quote(key='no-paralysis-service',kind='service',target_id=s['id'])

    def test_http_authorization_strict_prices_and_default_idempotency(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.commerce_routes import register
        app=FastAPI();active=[self.owner];register(app,lambda:self.db,lambda:active[0])
        path,_=self.used_item()
        with TestClient(app) as client:
            url=f'/gm/merchants/{self.mid}/individual-appraisals'
            body={'request_id':'http-individual-001','character_id':'vezemir','item_path':path,'unit_copper':120}
            self.assertEqual(client.post(url,json=body).status_code,403)
            self.assertEqual(client.get('/gm/merchants/magic-services/catalog').status_code,403)
            active[0]=self.gm
            self.assertEqual(client.post(url,json={**body,'unit_copper':120.5}).status_code,422)
            r=client.post(url,json=body);self.assertEqual(r.status_code,200);self.assertEqual(r.json(),client.post(url,json=body).json())
            url=f'/gm/merchants/{self.mid}/magic-services/defaults'
            self.assertEqual(client.post(url,json={'request_id':'defaults-http-001'}).json(),client.post(url,json={'request_id':'defaults-http-001'}).json())


class KlhaussProfileTests(unittest.TestCase):
    setUp=test_map_commerce.MapCommerceTests.setUp

    def test_profile_preserves_identity_and_does_not_reset_on_reapplication(self):
        from app.npc_memory import init_npc_memory,create_npc
        from app.session_workspace import save_workspace_token
        from app.npc_campaign_profile import apply
        init_npc_memory(self.db)
        npc,_=create_npc(self.db,request_id='klhauss-profile-fixture',campaign_id='omnisvera',actor_id='master',fields={'name':'Klhauss','private_description':'SEGREDO'})
        shop.configure(self.db,self.mid,self.gm,token_id=self.pin['id'],npc_id=npc['id'])
        token=save_workspace_token(self.db,token_type='monster',name='Klhauss',latitude=44,longitude=42,current_hp=10,maximum_hp=10,image_path='portrait.png',sheet={'level':1,'embedded_in_location':self.pin['id']})
        result=apply(self.db,npc['id'],self.gm,request_id='klhauss-profile-apply')
        self.assertEqual(result['token_id'],token['id']);self.assertEqual(result['maximum_hp'],65)
        with closing(sqlite3.connect(self.db)) as db,db:
            raw=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()
            db.execute('UPDATE session_workspace_tokens SET current_hp=20 WHERE id=?',(token['id'],))
        again=apply(self.db,npc['id'],self.gm,request_id='klhauss-profile-next')
        self.assertEqual(again['status'],'already_configured')
        with closing(sqlite3.connect(self.db)) as db:
            row=db.execute('SELECT current_hp,latitude,longitude,image_path,sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()
            self.assertEqual(row[:4],(20,44,42,'portrait.png'));data=json.loads(row[4]);self.assertEqual(data['embedded_in_location'],self.pin['id'])
        from app.monster_actions import build_action_map
        actions=build_action_map('Klhauss',data['attacks'],data['abilities'])
        self.assertEqual(actions['summary']['attacks_ready'],2);self.assertTrue(actions['spellcasting'])
        from scripts.market_followup_fixture import prepare
        fixture=self.db.with_name('simulation.sqlite3')
        with closing(sqlite3.connect(self.db)) as source,closing(sqlite3.connect(fixture)) as target:source.backup(target)
        with closing(sqlite3.connect(fixture)) as db,db:db.execute("UPDATE merchants SET name='Conclave dos Errantes' WHERE id=?",(self.mid,))
        prepare(fixture);prepare(fixture)
        with closing(sqlite3.connect(fixture)) as db:
            self.assertEqual(db.execute("SELECT quantity,charges_current,charges_max,equipped FROM player_inventory WHERE profile_id='vezemir' AND item_path='compendium:arma-corpo-espada-longa'").fetchone(),(1,1,3,0))
        with closing(sqlite3.connect(self.db)) as db:self.assertIsNone(db.execute("SELECT id FROM player_inventory WHERE item_path='compendium:arma-corpo-espada-longa'").fetchone())

    def test_spell_budget_is_atomic_replayed_and_refilled_by_existing_rest(self):
        from app.session_workspace import save_workspace_token
        from app.spell_engine import cast_spell
        from app.npc_campaign_profile import PROFILE
        from app.monster_runtime import full_rest
        init_effects(self.db)
        token=save_workspace_token(self.db,token_type='monster',name='Klhauss',latitude=20,longitude=20,current_hp=65,maximum_hp=65,sheet=PROFILE)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo',latitude=20,longitude=21,current_hp=100,maximum_hp=100,sheet={'armor_class':10})
        def cast(key,spell='arcana-dardos-misticos'):
            return cast_spell(self.db,spell_id=spell,caster_type='token',caster_id=token['id'],targets=[{'type':'token','id':enemy['id']}],request_id=key)
        first=cast('npc-cast-first');self.assertEqual(first,cast('npc-cast-first'))
        self.assertEqual(first['caster_resource']['remaining'],2)
        cast('npc-cast-second');cast('npc-cast-third')
        with self.assertRaises(ValueError):cast('npc-cast-fourth')
        with self.assertRaises(ValueError):cast('npc-cast-unknown','arcana-relampago')
        with closing(sqlite3.connect(self.db)) as db,db:full_rest(db,'now')
        self.assertEqual(cast('npc-cast-after-rest')['caster_resource']['remaining'],2)

    def test_explicit_repertoire_cannot_use_generic_conjuration_bypass(self):
        from app.session_workspace import save_workspace_token
        from app.spell_engine import execute_token_action
        from app.npc_campaign_profile import PROFILE
        init_effects(self.db)
        token=save_workspace_token(self.db,token_type='monster',name='Klhauss',latitude=20,longitude=20,current_hp=65,maximum_hp=65,sheet=PROFILE)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo',latitude=20,longitude=21,current_hp=100,maximum_hp=100,sheet={'armor_class':10})
        with self.assertRaisesRegex(ValueError,'magia específica'):
            execute_token_action(self.db,token_id=token['id'],ability_name='Magias',targets=[{'type':'token','id':enemy['id']}],damage_override='1d4',request_id='npc-spell-legacy-bypass')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0],100)

    def test_npc_spell_obeys_existing_turn_budget_and_failed_target_spends_nothing(self):
        from app.session_workspace import save_workspace_token
        from app.spell_engine import cast_spell
        from app.npc_campaign_profile import PROFILE
        init_effects(self.db)
        token=save_workspace_token(self.db,token_type='monster',name='Klhauss',latitude=20,longitude=20,current_hp=65,maximum_hp=65,sheet=PROFILE)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo',latitude=20,longitude=21,current_hp=100,maximum_hp=100,sheet={'armor_class':10})
        def cast(key,target):return cast_spell(self.db,spell_id='arcana-dardos-misticos',caster_type='token',caster_id=token['id'],targets=[{'type':'token','id':target}],request_id=key)
        with self.assertRaises(ValueError):cast('bad-target-npc-cast','not-present')
        encounter={'active':True,'battle_mode':True,'map_id':'default','participants':[{'target_type':'token','target_id':token['id']},{'target_type':'token','target_id':enemy['id']}],'turn_index':0,'attack_limit':1,'attacks_used':0}
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        result=cast('battle-npc-cast-once',enemy['id']);self.assertEqual(result['caster_resource']['used_before'],0)
        with self.assertRaises(ValueError):cast('battle-npc-cast-twice',enemy['id'])
        with closing(sqlite3.connect(self.db)) as db:
            used=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0])['monster_runtime']['usage']
            turn=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0])
        self.assertEqual(used['spell:arcana-dardos-misticos'],1);self.assertEqual(turn['attacks_used'],1)

if __name__=='__main__':unittest.main()
