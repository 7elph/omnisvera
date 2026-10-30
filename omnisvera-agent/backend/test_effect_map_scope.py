"""Area occupancy belongs to its map; personal effects retain their own duration."""
import sqlite3
import unittest
from app.dorn_spell_pack import expand_web_effects
from app.action_cards import active_effect_icons


class EffectMapScopeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript('''
          CREATE TABLE session_workspace_state(id INTEGER, map_id TEXT);
          INSERT INTO session_workspace_state VALUES(1,'map-a');
          CREATE TABLE session_workspace_tokens(id TEXT,character_id TEXT,map_id TEXT,token_type TEXT,current_hp INTEGER);
          INSERT INTO session_workspace_tokens VALUES('pin','vezemir','map-a','character',20);
          CREATE TABLE session_workspace_entity_positions(token_id TEXT,map_id TEXT,cell_x INTEGER,cell_y INTEGER,footprint_w INTEGER,footprint_h INTEGER);
          INSERT INTO session_workspace_entity_positions VALUES('pin','map-a',1,1,1,1);
          CREATE TABLE session_workspace_map_grids(map_id TEXT,cell_size_m REAL);
          INSERT INTO session_workspace_map_grids VALUES('map-a',1.5);
        ''')
        self.area = dict(id='web',target_type='character',target_id='dorn7',label='Teia',source='Dorn',
                         duration='fictional_time',remaining_seconds=100,modifiers={},
                         web_area=dict(map_id='map-a',x_m=0,y_m=0,width_m=3,height_m=3))

    def test_area_is_persisted_but_old_pins_do_not_apply_status_on_a_different_active_map(self):
        self.assertEqual(2,len(expand_web_effects(self.db,[self.area])))
        self.db.execute("UPDATE session_workspace_state SET map_id='map-b'")
        self.assertEqual([self.area],expand_web_effects(self.db,[self.area]))
        self.db.execute("UPDATE session_workspace_state SET map_id='map-a'")
        self.assertEqual(2,len(expand_web_effects(self.db,[self.area])))

    def test_area_anchor_is_not_a_personal_status_but_occupant_is(self):
        effects=expand_web_effects(self.db,[self.area])
        cards=lambda _: [dict(id='teia',name='Teia',description='Área de teia',image_path='web.png')]
        icons=active_effect_icons(effects,cards,['dorn7'])
        self.assertEqual(['vezemir'],[icon['target_id'] for icon in icons])

    def test_character_occupancy_uses_live_sheet_hp_not_stale_pin_hp(self):
        self.db.executescript('''CREATE TABLE character_states(profile_id TEXT,state_json TEXT);
          INSERT INTO character_states VALUES('vezemir','{"current_hp":20}');
          UPDATE session_workspace_tokens SET current_hp=0;''')
        self.assertEqual(2,len(expand_web_effects(self.db,[self.area])))
        self.db.execute("UPDATE character_states SET state_json='{"+'"current_hp":0'+"}'")
        self.assertEqual([self.area],expand_web_effects(self.db,[self.area]))


if __name__ == '__main__':
    unittest.main()
