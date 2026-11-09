"""Source-bounded range modifiers, over native positions and attack receipts."""
import math
import unittest


class ItemRangeRuleTests(unittest.TestCase):
    def test_source_boundaries_and_declared_ceiling(self):
        from app.item_range import classify_distance
        for meters,expected in [(0,('adjacent',-4)),(1.5,('adjacent',-4)),(2.999,('adjacent',-4)),(3,('short',0)),(10,('short',0)),(10.001,('medium',-2)),(20,('medium',-2)),(20.001,('long',-5)),(30,('long',-5))]:
            with self.subTest(meters=meters):self.assertEqual(classify_distance(meters,10,30),expected)
        with self.assertRaisesRegex(ValueError,'alcance'):classify_distance(30.001,10,30)
        # 15/30 remains capped at 30, never silently extended to 45 m.
        with self.assertRaisesRegex(ValueError,'alcance'):classify_distance(31,15,30)

    def test_invalid_or_contradictory_dimensions_do_not_produce_a_bonus(self):
        from app.item_range import classify_distance
        for args in [(-1,10,30),(math.nan,10,30),(math.inf,10,30),(5,0,30),(5,20,10),(5,True,30),(5,10,31)]:
            with self.subTest(args=args),self.assertRaises(ValueError):classify_distance(*args)

    def test_melee_and_unconfigured_campaign_powers_do_not_inherit_item_penalties(self):
        from app.item_range import range_context
        for attack in [{'id':'melee','weapon_item_path':'weapon'},{'id':'ranged','weapon_item_path':'hemomancy'}]:
            self.assertIsNone(range_context(None,None,'raziel',attack,[{'item_path':'weapon','mechanics':{'family_schema':1,'short_range_m':10,'range_m':30}}],{'type':'token','id':'target'}))

    def test_critical_notation_is_never_inferred_as_weapon_range(self):
        from app.item_families import descriptor
        item=descriptor({'id':'fixture-unknown-range','category':'arma-distancia','name':'Ensaio','dano':'1d6','description':'Dist. · Alcance - · Crít 19/20x3'})
        self.assertNotIn('short_range_m',item['mechanics'])

    def test_legacy_database_without_map_tables_remains_assisted(self):
        import sqlite3
        from contextlib import closing
        from app.item_range import range_context
        with closing(sqlite3.connect(':memory:')) as db:
            result=range_context(db,None,'vezemir',{'id':'ranged','weapon_item_path':'bow'},[{'item_path':'bow','mechanics':{'family_schema':1,'short_range_m':15,'range_m':30}}],{'type':'token','id':'target'})
        self.assertFalse(result['checked']);self.assertEqual(result['bonus'],0)


class ItemRangeApiTests(unittest.TestCase):
    def setUp(self):
        from test_item_specials import ItemSpecialApiTests
        from app.session_workspace import save_workspace_token,set_workspace_map
        from app.spatial_grid import configure_grid
        ItemSpecialApiTests.setUp(self)
        self.addCleanup(lambda:ItemSpecialApiTests.tearDown(self))
        self.bow=ItemSpecialApiTests.equip(self,'arma-distancia-arco-curto','Arco curto','À distância')
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:arma-distancia-flecha-x20',item_title='Flecha x20',quantity=1,equipped=False,charges_current=20,charges_max=20,notes=None)
        self.map=set_workspace_map(self.db,title='Ensaio de distância',image_path='fixture.svg',visible_to_players=True)['id']
        self.actor=save_workspace_token(self.db,map_id=self.map,token_type='character',character_id='vezemir',name='Atirador',latitude=10,longitude=10)['id']
        self.enemy=save_workspace_token(self.db,map_id=self.map,token_type='monster',name='Alvo',latitude=40,longitude=40,current_hp=100,maximum_hp=100,sheet={'armor_class':17})['id']
        configure_grid(self.db,actor_id='master',role='gm',request_id='range-fixture-grid',map_id=self.map,config={'cols':50,'rows':10,'cell_size_m':1.5})
        self.place(self.actor,0);self.place(self.enemy,10)

    def place(self,token,x):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=1,version=version+1 WHERE token_id=? AND map_id=?',(x,token,self.map))

    def resolve(self,key,d20=10):
        return self.client.post('/characters/vezemir/attacks/resolve',json={'request_id':key,'attack_id':'ranged','weapon_item_path':self.bow,'target_type':'token','target_id':self.enemy,'roll_mode':'physical','d20':d20})

    def test_medium_range_changes_hit_bonus_and_result(self):
        short=self.resolve('range-short-fixture');self.assertEqual(short.status_code,200,short.text)
        self.place(self.enemy,11)
        medium=self.resolve('range-medium-fixture');self.assertEqual(medium.status_code,200,medium.text)
        self.assertEqual(medium.json()['attack_bonus'],short.json()['attack_bonus']-2)
        self.assertEqual(short.json()['result'],'hit');self.assertEqual(medium.json()['result'],'miss')
        self.assertEqual(medium.json()['breakdown']['item_range']['meters'],16.5)

    def test_confirmation_rejects_changed_distance_without_spending_ammunition_or_hp(self):
        rolled=self.resolve('range-stale-fixture',20);self.assertEqual(rolled.status_code,200,rolled.text)
        self.place(self.enemy,11)
        confirmed=self.client.post('/combat/attacks/'+rolled.json()['resolution_id']+'/confirm')
        self.assertNotEqual(confirmed.status_code,200,confirmed.text)
        self.assertIn('distância',confirmed.text.casefold())
        pending=self.client.get('/combat/attacks/pending');self.assertEqual(pending.status_code,200,pending.text)
        self.assertNotIn(rolled.json()['resolution_id'],[r['resolution_id'] for r in pending.json()])
        fresh=self.resolve('range-fresh-after-reposition',20);self.assertEqual(fresh.status_code,200,fresh.text)
        self.assertEqual(fresh.json()['attack_bonus'],6)
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' AND item_path='compendium:arma-distancia-flecha-x20'").fetchone()[0],20)
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0],100)

    def test_adjacent_penalty_natural_twenty_and_confirmed_retry(self):
        self.place(self.enemy,1)
        miss=self.resolve('range-adjacent-fixture');self.assertEqual(miss.status_code,200,miss.text)
        self.assertEqual(miss.json()['attack_bonus'],4)
        hit=self.resolve('range-twenty-fixture',20);self.assertEqual(hit.status_code,200,hit.text)
        self.assertEqual(hit.json()['result'],'hit');self.assertTrue(hit.json()['breakdown']['strikes'][0]['critical'])
        rid=hit.json()['resolution_id'];confirmed=self.client.post('/combat/attacks/'+rid+'/confirm')
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.place(self.enemy,11)
        replay=self.client.post('/combat/attacks/'+rid+'/confirm');self.assertEqual(replay.status_code,200,replay.text)
        self.assertEqual(replay.json()['resolution_id'],rid)
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' AND item_path='compendium:arma-distancia-flecha-x20'").fetchone()[0],19)

    def test_no_grid_is_assisted_and_maximum_range_does_not_expand(self):
        self.place(self.enemy,21)
        rejected=self.resolve('range-too-far-fixture');self.assertNotEqual(rejected.status_code,200)
        self.assertIn('alcance',rejected.text.casefold())
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('DELETE FROM session_workspace_map_grids WHERE map_id=?',(self.map,))
        legacy=self.resolve('range-no-grid-fixture');self.assertEqual(legacy.status_code,200,legacy.text)
        self.assertEqual(legacy.json()['attack_bonus'],8)
        self.assertFalse(legacy.json()['breakdown']['item_range']['checked'])

    def test_equal_distance_after_reposition_still_invalidates_the_old_geometry(self):
        rolled=self.resolve('range-moved-geometry',20);self.assertEqual(rolled.status_code,200,rolled.text)
        self.place(self.actor,1);self.place(self.enemy,11)
        confirmed=self.client.post('/combat/attacks/'+rolled.json()['resolution_id']+'/confirm')
        self.assertNotEqual(confirmed.status_code,200);self.assertIn('distância',confirmed.text.casefold())

    def test_existing_attack_reinforcement_reports_the_effective_range_component(self):
        from unittest.mock import patch
        with patch('app.raziel_pipeline.attack_context',return_value={'multiplier':2}):
            self.place(self.enemy,11)
            result=self.resolve('range-reinforcement-fixture')
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['attack_bonus'],12)
        self.assertEqual(result.json()['breakdown']['item_range']['base_bonus'],-2)
        self.assertEqual(result.json()['breakdown']['item_range']['bonus'],-4)

    def test_in_combat_movement_cannot_invalidate_a_reserved_attack(self):
        import sqlite3,json
        from contextlib import closing
        from app.spatial_grid import move_entity
        from app.combat_effects import readeffects
        with closing(sqlite3.connect(self.db)) as db,db:
            encounter={'active':True,'battle_mode':True,'map_id':self.map,'started_at':'2026-11-01T00:00:00+00:00','turn_sequence':1,'turn_index':0,'participants':[{'target_type':'character','target_id':'vezemir','initiative':20},{'target_type':'token','target_id':self.enemy,'initiative':10}]}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1',(json.dumps(encounter),))
        rolled=self.resolve('range-reserved-turn');self.assertEqual(rolled.status_code,200,rolled.text)
        state=readeffects(self.db);self.assertTrue(state['encounter'].get('pending_attack'))
        with closing(sqlite3.connect(self.db)) as db:
            version=db.execute('SELECT version FROM session_workspace_entity_positions WHERE token_id=?',(self.actor,)).fetchone()[0]
        with self.assertRaisesRegex(ValueError,'pendente'):
            move_entity(self.db,actor_id='vezemir',role='player',request_id='range-move-pending',map_id=self.map,token_id=self.actor,mode='COMBAT_MOVE',cells=[[0,1],[1,1]],expected_position_version=version,expected_grid_version=1,expected_combat_version=state['version'],load_movement=lambda _:'9 m')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT cell_x,version FROM session_workspace_entity_positions WHERE token_id=?',(self.actor,)).fetchone(),(0,version))
        confirmed=self.client.post('/combat/attacks/'+rolled.json()['resolution_id']+'/confirm');self.assertEqual(confirmed.status_code,200,confirmed.text)
        state=readeffects(self.db)
        moved=move_entity(self.db,actor_id='vezemir',role='player',request_id='range-move-confirmed',map_id=self.map,token_id=self.actor,mode='COMBAT_MOVE',cells=[[0,1],[1,1]],expected_position_version=version,expected_grid_version=1,expected_combat_version=state['version'],load_movement=lambda _:'9 m')
        self.assertEqual(moved['movement']['spent_m'],1.5)


if __name__=='__main__':unittest.main()
