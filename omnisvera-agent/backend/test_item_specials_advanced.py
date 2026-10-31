"""Approved campaign decisions; all mutations belong to TEMP fixture databases."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_item_specials as fixture


class AdvancedItemTests(unittest.TestCase):
    setUp = fixture.ItemSpecialApiTests.setUp
    tearDown = fixture.ItemSpecialApiTests.tearDown
    equip = fixture.ItemSpecialApiTests.equip
    request = fixture.ItemSpecialApiTests.request

    def arena(self):
        from app.session_workspace import set_workspace_map, save_workspace_token
        from app.spatial_grid import configure_grid
        arena=set_workspace_map(self.db,title='Itens avançados fixture',image_path='fixture.svg',visible_to_players=True)['id']
        actor=save_workspace_token(self.db,token_type='character',character_id='vezemir',name='Vezemir',latitude=15,longitude=15,map_id=arena)
        enemy=save_workspace_token(self.db,token_type='monster',name='Alvo do garrote',latitude=15,longitude=25,map_id=arena,current_hp=100,maximum_hp=100,sheet={'armor_class':10,'saving_throw':12,'size':'M','attributes':{'dexterity':14}})
        configure_grid(self.db,actor_id='master',role='gm',request_id='advanced-item-grid',map_id=arena,config={'cols':10,'rows':10,'cell_size_m':1.5})
        return arena,actor,enemy

    def garrote(self):
        self.equip('arma-corpo-garrote','Garrote')
        arena,actor,enemy=self.arena()
        response=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy['id'],'advanced-garrote-hit'))
        self.assertEqual(response.status_code,200,response.text)
        result=self.client.post('/combat/attacks/'+response.json()['resolution_id']+'/confirm')
        self.assertEqual(result.status_code,200,result.text)
        return arena,actor,enemy,result.json()

    def test_garrote_tick_saves_before_damage_and_cannot_repeat_same_turn(self):
        from app.item_grapple import turn_start
        _,_,enemy,_=self.garrote()
        participant={'target_type':'token','target_id':enemy['id'],'name':enemy['name']}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            with patch('app.dorn_spells.save',return_value={'success':False,'dice':[2]}), patch('app.item_grapple.roll_formula',return_value={'total':3,'individual_results':[3]}):
                turn_start(db,participant,{'started_at':'fixture','turn_sequence':1},'now','garrote-tick')
                turn_start(db,participant,{'started_at':'fixture','turn_sequence':1},'now','retry-garrote-tick')
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0],97)
            with patch('app.dorn_spells.save',return_value={'success':True,'dice':[20]}), patch('app.item_grapple.roll_formula') as damage:
                turn_start(db,participant,{'started_at':'fixture','turn_sequence':2},'now','garrote-escape')
                damage.assert_not_called()
            self.assertEqual(db.execute("SELECT COUNT(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.item_special')='garrote'").fetchone()[0],0)

    def test_tower_blocks_only_declared_side_and_never_player_twenty(self):
        from app.item_defense import apply_tower
        record={'actor_character_id':'vezemir','breakdown':{'tower_shield':{'protected_side':True},'strikes':[{'result':'hit','damage_total':7,'unavoidable':False},{'result':'hit','damage_total':9,'unavoidable':True}]},'damage_total':16}
        with patch('app.item_defense.roll_formula',return_value={'total':1,'individual_results':[1]}):
            result=apply_tower(record)
        self.assertEqual(record['damage_total'],9)
        self.assertEqual(result['blocked_damage'],7)
        self.assertEqual(record['breakdown']['strikes'][1]['damage_total'],9)

    def test_garrote_stowing_releases_and_does_not_repeat_tick(self):
        from app.combat_effects import readeffects
        self.garrote()
        response=self.client.post('/characters/vezemir/actions',json={'action':'unequip_item',
            'payload':{'item_path':'compendium:arma-corpo-garrote'},'request_id':'advanced-stow-garrote'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertFalse(any(e.get('item_special')=='garrote' for e in readeffects(self.db)['effects']))

    def test_garrote_walking_away_and_returning_releases(self):
        from app.item_grapple import prune, assert_can_speak
        arena,actor,enemy,_=self.garrote()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            with self.assertRaisesRegex(ValueError,'falar'):
                assert_can_speak(db,'token',enemy['id'])
            removed=prune(db,'now',moving=(arena,actor['id'],[[1,1],[0,1],[1,1]]))
            self.assertEqual(len(removed),1)
            assert_can_speak(db,'token',enemy['id'])

    def test_garrote_owner_death_releases_on_native_hp_change(self):
        from app.combat_effects import change_hp
        self.garrote()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            change_hp(db,'character','vezemir',-999,'now')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.item_special')='garrote'").fetchone()[0],0)

    def test_garrote_runs_on_actual_next_turn_once_and_logs_save(self):
        from app.combat_effects import effect_command,readeffects
        arena,_,enemy,_=self.garrote()
        start=effect_command(self.db,actor_id='master',actor_role='gm',request_id='advanced-grapple-start',
            expected_version=readeffects(self.db)['version'],action='start',payload={'map_id':arena,'battle_mode':True,'participants':[
                {'target_type':'character','target_id':'vezemir','initiative':20},
                {'target_type':'token','target_id':enemy['id'],'initiative':1}]})
        version=readeffects(self.db)['version']
        with patch('app.dorn_spells.save',return_value={'success':False,'dice':[2]}),patch('app.item_grapple.roll_formula',return_value={'total':3,'individual_results':[3]}) as damage:
            for _ in range(2):
                effect_command(self.db,actor_id='master',actor_role='gm',request_id='advanced-grapple-next',expected_version=version,action='next_turn',payload={})
            self.assertEqual(damage.call_count,1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0],97)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='item_grapple' AND title LIKE 'Garrote %'").fetchone()[0],1)

    def test_garrote_lethal_tick_skips_defeated_victim_without_repeating(self):
        from app.combat_effects import effect_command,readeffects
        arena,_,enemy,_=self.garrote()
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='advanced-grapple-lethal-start',
            expected_version=readeffects(self.db)['version'],action='start',payload={'map_id':arena,'battle_mode':True,'participants':[
                {'target_type':'character','target_id':'vezemir','initiative':20},
                {'target_type':'token','target_id':enemy['id'],'initiative':1}]})
        with closing(sqlite3.connect(self.db)) as db,db: db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(enemy['id'],))
        with patch('app.dorn_spells.save',return_value={'success':False,'dice':[2]}),patch('app.item_grapple.roll_formula',return_value={'total':3,'individual_results':[3]}) as damage:
            effect_command(self.db,actor_id='master',actor_role='gm',request_id='advanced-grapple-lethal-next',
                expected_version=readeffects(self.db)['version'],action='next_turn',payload={})
            self.assertEqual(damage.call_count,1)
        state=readeffects(self.db);encounter=state['encounter']
        self.assertEqual(encounter['participants'][encounter['turn_index']]['target_id'],'vezemir')
        self.assertFalse(any(e.get('item_special')=='garrote' for e in state['effects']))

    def tower_target(self):
        arena,actor,enemy=self.arena()
        with closing(sqlite3.connect(self.db)) as db,db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0])
            sheet['inventory']=[{'equipped':True,'quantity':1,'mechanics':{'special_defense':'tower'}}]
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),enemy['id']))
        self.equip('arma-corpo-madu','Madu')
        return enemy

    def test_tower_requires_explicit_side_before_dice_and_blocks_once(self):
        enemy=self.tower_target()
        request=self.request(enemy['id'],'advanced-tower-block',d20=15)
        with patch('app.combat.roll_formula') as damage:
            missing=self.client.post('/characters/vezemir/attacks/resolve',json=request)
            self.assertEqual(missing.status_code,400,missing.text)
            self.assertIn('TOWER_SIDE_REQUIRED',missing.text)
            damage.assert_not_called()
        request['tower_protected_side']=True
        preview=self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(preview.status_code,200,preview.text)
        endpoint='/combat/attacks/'+preview.json()['resolution_id']+'/confirm'
        with patch('app.item_defense.roll_formula',return_value={'total':1,'individual_results':[1]}) as block:
            result=self.client.post(endpoint);self.assertEqual(result.status_code,200,result.text)
            self.assertEqual(result.json()['damage_total'],0)
            self.assertEqual(self.client.post(endpoint).status_code,200)
            self.assertEqual(block.call_count,1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0],100)
        replay=self.client.post('/characters/vezemir/attacks/resolve',json=request)
        self.assertEqual(replay.status_code,200,replay.text)
        self.assertEqual(replay.json()['resolution_id'],preview.json()['resolution_id'])

    def test_tower_player_twenty_is_unavoidable_and_open_side_has_no_roll(self):
        enemy=self.tower_target()
        for key,die,side in [('critical',20,True),('open',15,False)]:
            preview=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy['id'],'advanced-tower-'+key,d20=die,tower_protected_side=side))
            self.assertEqual(preview.status_code,200,preview.text)
            with patch('app.item_defense.roll_formula') as block:
                result=self.client.post('/combat/attacks/'+preview.json()['resolution_id']+'/confirm')
                self.assertEqual(result.status_code,200,result.text)
                self.assertGreater(result.json()['damage_total'],0)
                block.assert_not_called()

    def shield(self):
        return self.equip('protecao-escudo-de-vibranium','Escudo de Vibranium','Mão secundária')

    def throw(self,enemy,key,die=20):
        preview=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy,key,attack_id='ranged',d20=die,
            weapon_item_path='compendium:protecao-escudo-de-vibranium'))
        self.assertEqual(preview.status_code,200,preview.text)
        response=self.client.post('/combat/attacks/'+preview.json()['resolution_id']+'/confirm')
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_vibranium_hit_returns_and_miss_drops_recoverable_original_item_once(self):
        from app.loot import distribute_loot
        path=self.shield();_,_,enemy=self.arena()
        from app.inventory_conditions import init_schema,save_condition,read_condition
        condition={'kind':'rust','original_bonus':3,'bonus_remaining':2,'enhancement_rule_ids':[],'destroyed':False}
        # Opaque legacy instance history and charges must survive a drop, not be repaired by it.
        with closing(sqlite3.connect(self.db)) as db,db:
            custom_before=db.execute('SELECT COUNT(*) FROM session_custom_items').fetchone()[0]
            init_schema(db);inventory_id=db.execute('SELECT id FROM player_inventory WHERE item_path=?',(path,)).fetchone()[0]
            save_condition(db,inventory_id,condition,'now')
            db.execute('UPDATE player_inventory SET charges_current=1,charges_max=3 WHERE id=?',(inventory_id,))
        hit=self.throw(enemy['id'],'advanced-shield-hit')
        self.assertTrue(hit['breakdown']['item_special_result']['returned'])
        # AC 99 guarantees a non-fumble miss; there is no physical-dice reroll.
        with closing(sqlite3.connect(self.db)) as db,db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0]);sheet['armor_class']=99
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),enemy['id']))
        missed=self.throw(enemy['id'],'advanced-shield-miss',2)
        drop=missed['breakdown']['item_special_result']
        self.assertFalse(drop['returned']);self.assertTrue(drop['pin_id'])
        endpoint='/combat/attacks/'+missed['resolution_id']+'/confirm'
        self.assertEqual(self.client.post(endpoint).status_code,200)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',path)).fetchone(),(0,0))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM loot_resolutions WHERE treasure_code='item-drop'").fetchone()[0],1)
            self.assertEqual(db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE token_id=?',(drop['pin_id'],)).fetchone(),(2,1))
        allocations=[{'reward_id':'dropped-shield','character_id':'vezemir','quantity':1}]
        _,created=distribute_loot(self.db,resolution_id=drop['loot_resolution_id'],request_id='advanced-recover-shield',allocations=allocations)
        self.assertTrue(created)
        _,created=distribute_loot(self.db,resolution_id=drop['loot_resolution_id'],request_id='advanced-recover-shield',allocations=allocations)
        self.assertFalse(created)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?',('vezemir',path)).fetchone(),(1,0))
            self.assertEqual(db.execute('SELECT visible_to_players FROM session_workspace_tokens WHERE id=?',(drop['pin_id'],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM session_custom_items').fetchone()[0],custom_before)
            self.assertEqual({k:v for k,v in read_condition(db,inventory_id).items() if k!='version'},condition)
            self.assertEqual(db.execute('SELECT charges_current,charges_max FROM player_inventory WHERE id=?',(inventory_id,)).fetchone(),(1,3))

    def test_vibranium_protetor_gets_only_one_other_target_without_spending_extra_attack(self):
        from app.combat_effects import effect_command,readeffects
        from app.session_workspace import save_workspace_token
        self.shield();arena,actor,enemy=self.arena()
        second=save_workspace_token(self.db,token_type='monster',name='Segundo alvo',map_id=arena,latitude=15,longitude=35,current_hp=100,maximum_hp=100,sheet={'armor_class':10})
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES('vezemir',?,?) ON CONFLICT(profile_id) DO UPDATE SET data_json=excluded.data_json",(json.dumps({'specialization':'protetor'}),'now'))
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='advanced-throw-start',expected_version=readeffects(self.db)['version'],action='start',payload={'map_id':arena,'battle_mode':True,'participants':[
            {'target_type':'character','target_id':'vezemir','initiative':20},
            {'target_type':'token','target_id':enemy['id'],'initiative':2},
            {'target_type':'token','target_id':second['id'],'initiative':1}]})
        first=self.throw(enemy['id'],'advanced-throw-first')
        self.assertTrue(first['breakdown']['item_special_result']['followup'])
        same=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy['id'],'advanced-throw-same',attack_id='ranged'))
        self.assertEqual(same.status_code,400,same.text)
        following=self.throw(second['id'],'advanced-throw-second')
        self.assertEqual(following['breakdown']['item_special']['followup_of'],first['resolution_id'])
        encounter=readeffects(self.db)['encounter']
        self.assertEqual(encounter['attacks_used'],1)
        self.assertTrue(encounter['action_committed'])
        self.assertFalse(encounter.get('item_followups'))
        third=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy['id'],'advanced-throw-third',attack_id='ranged'))
        self.assertEqual(third.status_code,400,third.text)

    def test_vibranium_uses_strength_and_rejects_beyond_nine_meters_before_roll(self):
        self.shield();arena,_,enemy=self.arena()
        actor=self.client.get('/characters/vezemir').json()
        attack=next(a for a in actor['definition']['attacks'] if a['id']=='ranged')
        self.assertEqual(attack['damage'],'1d6+1')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=8 WHERE token_id=?',(enemy['id'],))
        with patch('app.combat.roll_formula') as dice:
            result=self.client.post('/characters/vezemir/attacks/resolve',json=self.request(enemy['id'],'advanced-shield-too-far',attack_id='ranged'))
            self.assertEqual(result.status_code,400,result.text)
            self.assertIn('alcance',result.text)
            dice.assert_not_called()

    def test_legacy_equipped_shield_without_slot_keeps_sheet_readable_and_ranged_only(self):
        path=self.shield()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET equipment_slot=NULL WHERE item_path=?',(path,))
        response=self.client.get('/characters/vezemir')
        self.assertEqual(response.status_code,200,response.text)
        attacks={a['id']:a for a in response.json()['definition']['attacks']}
        self.assertEqual(attacks['ranged']['weapon_item_path'],path)
        self.assertNotEqual(attacks['melee'].get('weapon_item_path'),path)

    def test_private_map_throw_does_not_reveal_drop_to_players(self):
        self.shield();arena,_,enemy=self.arena()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_maps SET visible_to_players=0 WHERE id=?',(arena,))
            raw=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(enemy['id'],)).fetchone()[0]);raw['armor_class']=99
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(raw),enemy['id']))
        result=self.throw(enemy['id'],'advanced-private-shield',2)
        drop=result['breakdown']['item_special_result']
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT status FROM loot_resolutions WHERE resolution_id=?',(drop['loot_resolution_id'],)).fetchone()[0],'draft')
            self.assertEqual(db.execute('SELECT visible_to_players FROM session_workspace_tokens WHERE id=?',(drop['pin_id'],)).fetchone()[0],0)

    def test_selected_shield_does_not_inherit_another_weapons_exclusive_bonus(self):
        from app.combat import resolve_attack
        path=self.shield();_,_,enemy=self.arena()
        character=self.client.get('/characters/vezemir').json();definition=character['definition']
        attack=next(a for a in definition['attacks'] if a['id']=='ranged')
        expected=attack['attack_bonus']
        # A primary weapon's exclusive contribution is not a global ranged buff.
        attack.update(weapon_item_path='fixture:other-bow',attack_bonus=expected+7,item_attack_bonus=7)
        definition['item_effects']['totals']['attack_bonus:fixture:other-bow']=7
        result,_=resolve_attack(self.db,request_id='advanced-shield-selected-bonus',actor_character_id='vezemir',actor_name='Vezemir',
            requested_by_id='master',requested_by_role='gm',definition=definition,inventory=character['inventory'],attack_id='ranged',
            target={'type':'token','id':enemy['id'],'name':enemy['name'],'armor_class':10,'current_hp':100,'maximum_hp':100},roll_mode='physical',physical_d20=10,weapon_item_path=path)
        self.assertEqual(result['attack_bonus'],expected)


if __name__ == '__main__':
    unittest.main()
