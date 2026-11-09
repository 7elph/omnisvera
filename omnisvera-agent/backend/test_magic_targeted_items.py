"""Source-backed item actions through native APIs, synthetic fixtures only."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch


class TargetedMagicTests(unittest.TestCase):
    def setUp(self):
        from test_magic_combat_items import DrumTests
        DrumTests.setUp(self)
        self.enemy=self.listeners[0]

    def seed(self,suffix,quantity=1):
        from app.player_inventory import upsert_inventory
        path='compendium:item-magico-'+suffix
        upsert_inventory(self.db,profile_id='vezemir',item_path=path,item_title=suffix,
            quantity=quantity,equipped=False,notes=None)
        return path

    def use(self,path,key='magic-targeted-request',**options):
        return self.client.post('/characters/vezemir/actions',json={'action':'use_item',
            'payload':{'item_path':path,'magic_options':options},'request_id':key})

    def row(self,path):
        with closing(sqlite3.connect(self.db)) as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM player_inventory WHERE item_path=?',(path,)).fetchone())

    def test_ram_uses_selected_charges_damage_once_and_preserves_retry_intent(self):
        path=self.seed('anel-ariete')
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':7}) as rng:
            r=self.use(path,target_token_id=self.enemy,charges=2)
            self.assertEqual(r.status_code,200,r.text)
            replay=self.use(path,target_token_id=self.enemy,charges=2)
            self.assertEqual(replay.status_code,200,replay.text)
            rng.assert_called_once_with('2d6')
        self.assertEqual(self.row(path)['charges_current'],1)
        self.assertEqual(self.use(path,target_token_id=self.enemy,charges=1).status_code,400)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0],13)

    def test_ram_rejects_invalid_range_hidden_target_or_client_damage_without_spending(self):
        path=self.seed('anel-ariete')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=19,cell_y=19 WHERE token_id=?',(self.enemy,))
        # 14 cells * 1.5 m is in range; force a grid scale of 3 m for this fixture.
            db.execute('UPDATE session_workspace_map_grids SET cell_size_m=3')
        r=self.use(path,target_token_id=self.enemy)
        self.assertEqual(r.status_code,400,r.text)
        self.assertIsNone(self.row(path)['charges_current'])
        r=self.use(path,'magic-client-damage',target_token_id=self.enemy,damage=999)
        self.assertEqual(r.status_code,400,r.text)

    def test_spider_bracelet_creates_native_web_with_three_uses_and_two_hour_expiry(self):
        path=self.seed('bracelete-do-aracnideo')
        r=self.use(path,target_token_id=self.enemy)
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.row(path)['charges_current'],2)
        from app.combat_effects import readeffects
        web=next(e for e in readeffects(self.db)['effects'] if e.get('magic_item')=='item-magico-bracelete-do-aracnideo' and e.get('web_area'))
        self.assertEqual(web['remaining_seconds'],7200)
        self.assertEqual((web['web_area']['width_m'],web['web_area']['height_m']),(3,3))

    def test_appearance_powder_clears_optical_effects_but_not_poison(self):
        path=self.seed('po-do-aparecimento',quantity=2)
        with closing(sqlite3.connect(self.db)) as db,db:
            for key,extras in [('invisible',{'optical_kind':'invisibility'}),('poison',{'monster_condition':'poisoned'})]:
                e={'id':key,'target_type':'character','target_id':'vezemir','duration':'manual','rounds':None,'label':key,'modifiers':{},**extras}
                db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(key,'character','vezemir',json.dumps(e)))
        r=self.use(path)
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.row(path)['quantity'],1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT active FROM combat_effects WHERE id=?',('invisible',)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT active FROM combat_effects WHERE id=?',('poison',)).fetchone()[0],1)

    def test_contracts_expose_targeting_and_reviewed_door_support(self):
        from app.map_commerce import catalog_inventory
        for suffix in ['anel-ariete','bracelete-do-aracnideo','po-do-aparecimento']:
            with self.subTest(item=suffix):
                item=catalog_inventory('compendium:item-magico-'+suffix)
                self.assertTrue(item['usable'])
                self.assertEqual(item['mechanics']['magic_activation_schema'],1)
        from app.item_catalog import get_catalog_item
        ram=get_catalog_item('item-magico-anel-ariete')
        self.assertEqual(ram['mechanics']['magic_readiness']['blocking_gaps'],[])

    def test_inquisitor_result_is_owner_only_and_target_gets_separate_notice(self):
        path=self.seed('anel-inquisidor')
        with closing(sqlite3.connect(self.db)) as db,db:
            row=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()
            sheet=json.loads(row[0]);sheet['magic_capability']=True
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),self.enemy))
        r=self.use(path,target_token_id=self.enemy);self.assertEqual(r.status_code,200,r.text)
        with closing(sqlite3.connect(self.db)) as db:
            entries=db.execute("SELECT visibility,title,detail_json FROM session_ledger WHERE source_type='item_use'").fetchall()
            self.assertEqual(len(entries),1);self.assertEqual(entries[0][0],'owner')
            self.assertIn('possui capacidade mágica',entries[0][1])
            self.assertTrue(json.loads(entries[0][2])['rules'][0]['magic_capability'])
            notice=db.execute("SELECT visibility,detail_json FROM session_ledger WHERE source_type='magic_detection_notice'").fetchone()
            self.assertEqual(notice[0],'gm');self.assertNotIn('magic_capability',json.loads(notice[1]))

    def test_illusion_bomb_rolls_once_consumes_one_and_does_not_damage_or_block(self):
        path=self.seed('bomba-de-ilusao',quantity=2)
        with patch('app.magic_targeted_items.roll_formula',return_value={'total':2}) as rng:
            r=self.use(path);self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(self.use(path).status_code,200);rng.assert_called_once_with('1d4')
        self.assertEqual(self.row(path)['quantity'],1)
        from app.combat_effects import readeffects
        effect=next(e for e in readeffects(self.db)['effects'] if e.get('visual_area'))
        inventory=next(i for i in self.client.get('/characters/vezemir?read_only=true').json()['inventory'] if i['item_path']==path)
        self.assertIsNone(inventory.get('damage_formula'))
        self.assertEqual(effect['remaining_seconds'],20);self.assertEqual(effect['modifiers'],{})
        self.assertNotIn('web_area',effect)
        view=self.client.get('/combat/effects').json()
        projected=next((e for e in view['map_spell_effects'] if e.get('visual_area')),None)
        self.assertIsNotNone(projected)
        self.assertNotIn('item_path',projected)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0],20)

    def test_wrong_owner_hidden_target_and_empty_option_list_are_rejected(self):
        from app import main
        from app.access import AccessContext
        path=self.seed('anel-ariete')
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='raziel')
        self.assertEqual(self.use(path,target_token_id=self.enemy).status_code,403)
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='vezemir')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id=?',(self.enemy,))
        self.assertEqual(self.use(path,target_token_id=self.enemy).status_code,403)
        response=self.client.post('/characters/vezemir/actions',json={'action':'use_item','request_id':'malformed-options-array','payload':{'item_path':path,'magic_options':[]}})
        self.assertEqual(response.status_code,400);self.assertIsNone(self.row(path)['charges_current'])

    def test_ledger_error_rolls_back_damage_and_charges(self):
        path=self.seed('anel-ariete')
        with patch('app.combat_consumables.append_session_ledger_event',side_effect=RuntimeError('fixture-ledger-fault')):
            with self.assertRaises(RuntimeError):self.use(path,target_token_id=self.enemy)
        self.assertIsNone(self.row(path)['charges_current'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy,)).fetchone()[0],20)

    def test_range_preview_uses_canonical_item_range_and_requires_ownership(self):
        path=self.seed('anel-ariete')
        response=self.client.get('/gm/grid/range',params={'ref':'technique:vezemir:magic-item:item-magico-anel-ariete',
            'attacker_character_id':'vezemir','map_id':'default','range_override_m':999})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['range_m'],30)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE player_inventory SET quantity=0 WHERE item_path=?',(path,))
        self.assertEqual(self.client.get('/gm/grid/range',params={'ref':'technique:vezemir:magic-item:item-magico-anel-ariete','attacker_character_id':'vezemir','map_id':'default'}).status_code,403)

    def test_offensive_item_and_web_cannot_bypass_instrument_action_restriction(self):
        from test_magic_combat_items import DRUMS
        r=self.client.post('/characters/vezemir/actions',json={'action':'use_item','payload':{'item_path':DRUMS},'request_id':'items-during-music'})
        self.assertEqual(r.status_code,200,r.text)
        for suffix in ['anel-ariete','bracelete-do-aracnideo']:
            path=self.seed(suffix)
            response=self.use(path,'music-reject-'+suffix,target_token_id=self.enemy)
            self.assertEqual(response.status_code,400,response.text)
            self.assertIsNone(self.row(path)['charges_current'])

    def test_animal_form_cannot_use_ring_damage_as_a_replacement_attack(self):
        from app.night_form import start
        from app.magic_targeted_items import apply,RAM
        with closing(sqlite3.connect(self.db)) as db,db:
            state={'current_hp':20,'maximum_hp':20,'temporary_hp':0,'conditions':[]}
            start(state,'morcego')
            db.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES('raziel',?,1,'fixture')",(json.dumps(state),))
            with self.assertRaisesRegex(ValueError,'Forma da Noite'):
                apply(db,{'effects':[]},'raziel',RAM,{}, {},3,'fixture',{'target_token_id':self.enemy},'gm')
