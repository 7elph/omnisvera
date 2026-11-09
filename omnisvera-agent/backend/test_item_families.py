import unittest
from app.item_catalog import get_catalog_item,load_item_catalog
from app.map_commerce import catalog_inventory
from app.player_inventory import normalize_inventory_item_mechanics

class ItemFamilyTests(unittest.TestCase):
    def test_reviewed_melee_reach_and_critical_are_projected_without_name_guess(self):
        item=catalog_inventory('compendium:arma-corpo-alabarda')
        self.assertEqual(item['mechanics']['melee_reach_m'],3)
        self.assertEqual(item['mechanics']['critical_multiplier'],3)
        self.assertEqual(item['mechanics']['approved_equipment_slots'],['Corpo a corpo'])

    def test_body_armor_and_shield_have_native_rules_and_slots(self):
        items=load_item_catalog()['items']
        for name,bonus,slot in [('Cota de malha',4,'Armadura'),('Escudo de aço',2,'Mão secundária')]:
            raw=next(i for i in items if i['name']==name)
            item=catalog_inventory('compendium:'+raw['id'])
            enriched=normalize_inventory_item_mechanics({**item,'item_title':name})
            self.assertEqual(enriched['mechanics']['equipment_slots'],[slot])
            self.assertEqual(next(r['value'] for r in enriched['effect_rules'] if r['kind']=='armor_class_bonus'),bonus)

    def test_ranged_launcher_is_not_invented_as_a_damaging_weapon_without_ammo(self):
        item=catalog_inventory('compendium:arma-distancia-arco-curto')
        self.assertIsNone(item.get('damage_formula'))
        self.assertIn('ammunition',item['mechanics']['family_gaps'])

    def test_special_weapon_keeps_a_visible_gap(self):
        # Unknown multi-formula weapons must remain pending. Bagh Naja now
        # has a separately approved, explicitly marked campaign override.
        from app.item_families import descriptor
        item=descriptor({'id':'fixture-unreviewed-weapon','name':'Arma indefinida',
                         'category':'arma-corpo','dano':'1d6/1d4','description':''})
        self.assertIn('special_effect',item['mechanics']['family_gaps'])

    def test_all_numeric_catalog_weapons_keep_damage_critical_and_slots(self):
        import re
        for raw in load_item_catalog()['items']:
            if raw['category'] not in {'arma-corpo','arma-distancia'}:continue
            item=catalog_inventory('compendium:'+raw['id']);m=item['mechanics']
            self.assertEqual(m['family_schema'],1)
            if re.fullmatch(r'\d+d\d+(?:[+-]\d+)?',str(raw.get('dano','')).lower()):
                self.assertEqual(m['damage_formula'] if m['family']=='ammunition' else item['damage_formula'],str(raw['dano']).lower(),raw['id'])
            self.assertIn(m['critical_multiplier'],[2,3,4])

    def test_armor_reference_excludes_temporary_bonus_and_replaces_embedded_legacy_armor(self):
        from app.item_families import armor_anchor,anchored_defense
        character={'definition':{'attributes':{'dexterity':14},'base_attributes':{'dexterity':14},'defenses':{
            'base_armor_class':20,'armor_class':24,'armor_modifier':8,'armor_modifier_source':{'applied_value':2,'included_in_sheet':True}}}}
        anchor=armor_anchor(character)
        self.assertEqual(anchor['neutral'],14)
        self.assertEqual(anchored_defense(anchor,20,8,{'dexterity':14},[]),22)
        self.assertEqual(anchored_defense(anchor,20,6,{'dexterity':14},[]),20)
        self.assertEqual(anchored_defense(anchor,22,6,{'dexterity':14},[]),22)

    def test_native_armor_modifier_combines_shield_and_does_not_stack_cloak_with_leather(self):
        from app.character_play import _equipped_armor_modifier
        def armor(name):
            raw=next(i for i in load_item_catalog()['items'] if i['name']==name)
            return normalize_inventory_item_mechanics({**catalog_inventory('compendium:'+raw['id']),'item_path':'compendium:'+raw['id'],'item_title':name,'equipped':True,'quantity':1})
        self.assertEqual(_equipped_armor_modifier([armor('Cota de malha'),armor('Escudo de aço')])['value'],6)
        cloak={'item_path':'cloak','item_title':'Manto Primordial','equipped':True,'quantity':1}
        self.assertEqual(_equipped_armor_modifier([armor('Armadura de couro'),cloak])['value'],2)

    def test_frontmatter_consumable_rules_reject_unknown_and_conditional_effects(self):
        from app.main import _parse_frontmatter_effect_rules
        raw=[{'trigger':'on_use','kind':'heal_hp','formula':'1d4'},
             {'trigger':'on_use','kind':'invented','value':99},
             {'trigger':'on_use','kind':'heal_hp','value':9,'condition':'target dying'}]
        rules=_parse_frontmatter_effect_rules(raw,source_path='Items/Potion.md')
        self.assertEqual(len(rules),1);self.assertEqual(rules[0]['formula'],'1d4')

    def test_crossbow_reload_uses_existing_movement_key_and_rejects_prior_movement(self):
        from app.item_families import reload_movement
        s={'encounter':{'active':True,'started_at':'now','turn_sequence':7,'turn_index':0,'participants':[{'target_type':'character','target_id':'vezemir'}]}}
        contract={'reload_movement':True,'reload_budget_m':9}
        reload_movement(s,contract,apply=True)
        self.assertEqual(s['encounter']['movement']['spent_m'],9)
        with self.assertRaisesRegex(ValueError,'já se moveu'):reload_movement(s,contract)

    def test_arrow_packs_cannot_be_equipped_as_weapons_and_keep_ammo_damage(self):
        from app.item_families import project_ammunition
        ammo=normalize_inventory_item_mechanics({**catalog_inventory('compendium:arma-distancia-flecha-x20'),'item_path':'compendium:arma-distancia-flecha-x20','item_title':'Flecha x20','quantity':1,'charges_current':1})
        bow={**catalog_inventory('compendium:arma-distancia-arco-curto'),'item_path':'compendium:arma-distancia-arco-curto','quantity':1}
        self.assertIsNone(ammo['damage_formula'])
        project_ammunition([ammo,bow]);self.assertEqual(bow['damage_formula'],'1d8')

    def test_crossbow_cannot_bundle_multiple_reloads_in_one_attack(self):
        from app.item_families import ammunition_contract
        inventory=[{'item_path':'crossbow','mechanics':{'requires_ammunition':'bolt','ammunition_path':'bolts','ammunition_pack_size':20,'reload_movement':True}}]
        with self.assertRaisesRegex(ValueError,'único ataque'):ammunition_contract(inventory,'crossbow',2,'9 m')

    def test_madu_keeps_its_explicit_defense_and_mixed_damage_requires_a_choice(self):
        madu=catalog_inventory('compendium:arma-corpo-madu')
        self.assertEqual(sum(r['value'] for r in madu['effect_rules'] if r['kind']=='armor_class_bonus'),1)
        sword=catalog_inventory('compendium:arma-corpo-espada-bastarda')
        self.assertEqual(sword['mechanics']['damage_types'],['slashing','bludgeoning'])
        self.assertIn('damage_type_choice',sword['mechanics']['family_gaps'])

class ItemFamilyApiTests(unittest.TestCase):
    def setUp(self):
        import test_equip_slots,json,sqlite3
        from contextlib import closing
        test_equip_slots.EquipSlotTests.setUp(self)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR REPLACE INTO character_definition_overrides VALUES('vezemir',?,'now')",(json.dumps({'armor_class':10,'maximum_hp':20}),))

    def tearDown(self):
        import test_equip_slots
        test_equip_slots.EquipSlotTests.tearDown(self)

    def action(self,action,path,slot=None,key=None):
        return self.client.post('/characters/vezemir/actions',json={'action':action,'payload':{'item_path':path,**({'equipment_slot':slot} if slot else {})},'request_id':key})

    def test_body_shield_unequip_and_reload_preserve_non_equipment_base(self):
        from app.player_inventory import upsert_inventory
        paths=[]
        for name,slot,expected in [('Cota de malha','Armadura',14),('Escudo de aço','Mão secundária',16)]:
            raw=next(i for i in load_item_catalog()['items'] if i['name']==name);path='compendium:'+raw['id'];paths.append(path)
            upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title=name,quantity=1,equipped=False,notes=None)
            response=self.action('equip_item',path,slot,'family-equip-'+str(expected));self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['definition']['defenses']['armor_class'],expected)
        self.assertEqual(self.action('unequip_item',paths[0],key='family-unequip-body').json()['definition']['defenses']['armor_class'],12)
        self.assertEqual(self.action('unequip_item',paths[1],key='family-unequip-shield').json()['definition']['defenses']['armor_class'],10)
        self.assertEqual(self.client.get('/characters/vezemir?read_only=true').json()['definition']['defenses']['armor_class'],10)

    def test_vault_consume_uses_native_hp_inventory_and_receipt_without_session_alias(self):
        import json,sqlite3
        from contextlib import closing
        from app.player_inventory import upsert_inventory
        path='Items/Fixture restorative.md'
        metadata={'visibility':'jogadores','item_type':'Poção','usable':True,'mechanics':{'consume_mode':'quantity'},'effect_rules':[{'trigger':'on_use','kind':'heal_hp','value':3}]}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,'[]','item','[]',?,'Fixture','now')",(path,'Fixture restorative',json.dumps(metadata)))
        upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title='Fixture restorative',quantity=1,equipped=False,notes=None)
        self.client.get('/characters/vezemir')
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state.update(current_hp=1,maximum_hp=20)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        first=self.action('use_item',path,key='family-use-vault-1');self.assertEqual(first.status_code,200,first.text)
        replay=self.action('use_item',path,key='family-use-vault-1');self.assertEqual(replay.status_code,200,replay.text)
        self.assertEqual(replay.json()['state']['current_hp'],4)
        self.assertEqual(sum(i['quantity'] for i in replay.json()['inventory'] if i['item_path']==path),0)

    def test_last_arrow_is_consumed_once_and_attack_replays_after_empty_inventory(self):
        import sqlite3,json
        from contextlib import closing
        from app.player_inventory import upsert_inventory
        from app import main
        from app.access import AccessContext
        from app.session_workspace import save_workspace_token,get_workspace_snapshot
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        with closing(sqlite3.connect(self.db)) as db,db:
            raw=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]);raw['attacks']={'melee_bonus':5,'ranged_bonus':5};raw['race']={'movement':'9 m','race':'Humano'}
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(raw),))
        for id,name,charges in [('arma-distancia-arco-curto','Arco curto',None),('arma-distancia-flecha-x20','Flecha x20',1)]:
            upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+id,item_title=name,quantity=1,equipped=id.endswith('arco-curto'),equipment_slot='À distância' if id.endswith('arco-curto') else None,charges_current=charges,charges_max=20 if charges else None,notes=None)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo',latitude=40,longitude=40,current_hp=200,maximum_hp=200,sheet={'armor_class':10})
        mode=get_workspace_snapshot(self.db)['table_mode'];request={'request_id':'family-last-arrow','attack_id':'ranged','target_type':'token','target_id':enemy['id'],'roll_mode':mode,**({'d20':20} if mode=='physical' else {})}
        response=self.client.post('/characters/vezemir/attacks/resolve',json=request);self.assertEqual(response.status_code,200,response.text)
        rid=response.json()['resolution_id']
        first=self.client.post('/combat/attacks/'+rid+'/confirm');self.assertEqual(first.status_code,200,first.text)
        replay=self.client.post('/characters/vezemir/attacks/resolve',json=request);self.assertEqual(replay.status_code,200,replay.text)
        self.assertEqual(replay.json()['resolution_id'],rid)
        again=self.client.post('/combat/attacks/'+rid+'/confirm');self.assertEqual(again.status_code,200,again.text)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute("SELECT quantity,charges_current FROM player_inventory WHERE item_path='compendium:arma-distancia-flecha-x20'").fetchone(),(0,0))

    def test_crossbow_reload_is_atomic_with_native_turn_movement_and_ammunition(self):
        import sqlite3,json
        from contextlib import closing
        from app import main
        from app.access import AccessContext
        from app.player_inventory import upsert_inventory
        from app.session_workspace import set_workspace_map,save_workspace_token,get_workspace_snapshot
        from app.spatial_grid import configure_grid,move_entity
        from app.combat_effects import readeffects,effect_command
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        with closing(sqlite3.connect(self.db)) as db,db:
            raw=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]);raw['attacks']={'ranged_bonus':5};raw['race']={'movement':'9 m','race':'Humano'}
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(raw),))
        for id,name,slot in [('arma-distancia-besta','Besta','À distância'),('arma-distancia-dardo-x20','Dardo x20',None)]:
            upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+id,item_title=name,quantity=1,equipped=bool(slot),equipment_slot=slot,charges_current=None if slot else 20,charges_max=None if slot else 20,notes=None)
        self.client.get('/characters/vezemir')
        map_id=set_workspace_map(self.db,title='Besta fixture',image_path='fixture.svg',visible_to_players=True)['id']
        actor=save_workspace_token(self.db,token_type='character',character_id='vezemir',name='Vezemir',latitude=15,longitude=15,map_id=map_id)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo da besta',latitude=15,longitude=25,map_id=map_id,current_hp=200,maximum_hp=200,sheet={'armor_class':10})
        configure_grid(self.db,actor_id='master',role='gm',request_id='family-reload-grid',map_id=map_id,config={'cols':10,'rows':10,'cell_size_m':1.5})
        def combat(action,key):return effect_command(self.db,actor_id='master',actor_role='gm',request_id=key,expected_version=readeffects(self.db)['version'],action=action,payload={'map_id':map_id,'battle_mode':getattr(self,'_family_battle_mode',False),'participants':[{'target_type':'character','target_id':'vezemir','initiative':10},{'target_type':'token','target_id':enemy['id'],'initiative':1}]})
        combat('start','family-reload-start')
        position=next(t for t in get_workspace_snapshot(self.db,map_id=map_id)['tokens'] if t['id']==actor['id'])['grid_position']
        move_entity(self.db,actor_id='master',role='gm',request_id='family-walk-before-reload',map_id=map_id,token_id=actor['id'],mode='COMBAT_MOVE',cells=[[position['cell_x'],position['cell_y']],[position['cell_x'],position['cell_y']+1]],expected_position_version=position['version'],expected_grid_version=1,expected_combat_version=readeffects(self.db)['version'],load_movement=lambda _:'9 m')
        mode=get_workspace_snapshot(self.db)['table_mode'];request={'request_id':'family-reload-after-walk','attack_id':'ranged','target_type':'token','target_id':enemy['id'],'roll_mode':mode,**({'d20':20} if mode=='physical' else {})}
        rejected=self.client.post('/characters/vezemir/attacks/resolve',json=request);self.assertEqual(rejected.status_code,400,rejected.text);self.assertIn('já se moveu',rejected.text)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE item_path='compendium:arma-distancia-dardo-x20'").fetchone()[0],20)
        combat('end','family-reload-end');combat('start','family-reload-restart')
        request['request_id']='family-reload-unmoved';resolved=self.client.post('/characters/vezemir/attacks/resolve',json=request);self.assertEqual(resolved.status_code,200,resolved.text)
        endpoint='/combat/attacks/'+resolved.json()['resolution_id']+'/confirm'
        confirmed=self.client.post(endpoint);self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.assertEqual(self.client.post(endpoint).status_code,200)
        budget=readeffects(self.db)['encounter']['movement'];self.assertEqual(budget['spent_m'],9);self.assertEqual(budget['budget_m'],9)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE item_path='compendium:arma-distancia-dardo-x20'").fetchone()[0],19)

    def test_crossbow_reload_also_persists_in_battle_mode(self):
        self._family_battle_mode=True
        self.test_crossbow_reload_is_atomic_with_native_turn_movement_and_ammunition()

if __name__=='__main__':unittest.main()
