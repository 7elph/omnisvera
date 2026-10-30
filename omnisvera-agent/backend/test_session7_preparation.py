import json
from pathlib import Path
import sqlite3
from contextlib import closing
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from prepare_session7 import install, start_encounter
from app.scene_play import create_session, change_session_status, change_scene_status, scene_view, update_element, list_sessions, get_scene, SCENE_CHECKLIST_KEYS
from app.session_workspace import list_workspace_tokens, get_workspace_snapshot
from app.combat import monster_attack_definition


class Session7PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault=Path(self.temp.name)
        self.db=self.vault/'test.sqlite3'
        self.old,_=create_session(self.db,request_id='fixture-session6',campaign_id='omnisvera',session_number=6,title='Sessão 6',created_by='master')
        self.prepared=install(self.db,self.vault)

    def test_create_only_reinstall_preserves_history_and_played_positions(self):
        with closing(sqlite3.connect(self.db)) as db:
            before=db.execute('SELECT * FROM game_sessions WHERE id=?',(self.old['id'],)).fetchone()
        first=self.prepared
        second=install(self.db,self.vault)
        self.assertEqual(first,second)
        self.assertEqual(9,len(first['scenes']))
        self.assertEqual(6,len(first['maps']))
        for sid in first['scenes']:
            self.assertTrue(all(get_scene(self.db,sid)['checklist'].get(k) for k in SCENE_CHECKLIST_KEYS))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(before,db.execute('SELECT * FROM game_sessions WHERE id=?',(self.old['id'],)).fetchone())
            self.assertEqual(5,db.execute("SELECT count(*) FROM scene_elements WHERE request_id LIKE 'session7-handout-%'").fetchone()[0])
            narrative=json.loads(db.execute('SELECT narrative_json FROM game_sessions WHERE id=?',(first['session_id'],)).fetchone()[0])
            self.assertEqual(['Vezemir','Morthak','Raziel'],[p['name'] for p in narrative['participants']])
            self.assertTrue(all(t['title'] for t in narrative['open_threads']))
        for m in first['maps'].values():
            roster=[t['character_id'] for t in list_workspace_tokens(self.db,m) if t['token_type']=='character']
            self.assertEqual({'vezemir','morthak','raziel','dorn7'},set(roster))

    def test_privacy_opening_reveal_reload_and_no_player_script(self):
        sid=self.prepared['scenes'][6]
        self.assertIsNone(scene_view(self.db,sid,access_mode='player',profile_id='raziel'))
        change_session_status(self.db,self.prepared['session_id'],'active')
        change_scene_status(self.db,sid,'active')
        player=scene_view(self.db,sid,access_mode='player',profile_id='raziel')
        self.assertEqual([],player['elements'])
        self.assertNotIn('private_notes',player)
        gm=scene_view(self.db,sid,access_mode='gm',profile_id=None)
        document=next(e for e in gm['elements'] if e['title']=='Ordem de captura parcialmente destruída')
        update_element(self.db,document['id'],fields={},reveal=True)
        reloaded=scene_view(self.db,sid,access_mode='player',profile_id='morthak')
        self.assertEqual(1,len(reloaded['elements']))
        self.assertNotIn('private_description',reloaded['elements'][0])
        self.assertIn('NÃO ENFRENTAR C',reloaded['elements'][0]['public_description'])
        self.assertNotIn('mandante',reloaded['elements'][0]['public_description'])

    def test_attack_definitions_maps_hidden_and_encounter_guard(self):
        snapshot=get_workspace_snapshot(self.db,is_gm=False,map_id=self.prepared['maps']['inside'])
        self.assertFalse(any(t['token_type']=='monster' for t in snapshot['tokens']))
        for token in list_workspace_tokens(self.db,self.prepared['maps']['inside']):
            if token['token_type']=='monster':
                attack=monster_attack_definition(token,'0')['attacks'][0]
                self.assertGreaterEqual(attack['attack_bonus'],1)
                self.assertEqual(1,token['sheet']['action_budget'])
        for key in self.prepared['maps']:
            self.assertIn('<svg',(self.vault/f'zz_media/session7/{key}.svg').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,'Inicie Sessão 7'):
            start_encounter(self.db)
        self.assertEqual('planned',next(s for s in list_sessions(self.db) if s['session_number']==7)['status'])

    def test_conflicting_session7_is_not_overwritten(self):
        other=self.vault/'conflict.sqlite3'
        create_session(other,request_id='existing-session7',campaign_id='omnisvera',session_number=7,title='Outra preparação',created_by='master')
        with self.assertRaisesRegex(ValueError,'outra Sessão 7'):
            install(other,self.vault)

    def test_scene_listing_reuses_sheets_only_within_one_viewer_request(self):
        from app import main
        def view(_db, scene_id, **_kwargs):
            return {'id': scene_id, 'participants': [{'character_id': 'morthak'}], 'events': []}
        with patch.object(main, 'list_scenes', return_value=[{'id': 1}, {'id': 2}]), \
             patch.object(main, 'scene_view', side_effect=view), \
             patch.object(main, 'scene_contract_links', return_value=[]), \
             patch.object(main, '_character_summary', side_effect=lambda character: character), \
             patch.object(main, '_playable_character', side_effect=lambda cid, access, *, read_only=False: {'id': cid, 'viewer': access.mode, 'read_only':read_only}) as playable:
            gm = main.authorized_scenes(main.AccessContext(mode='gm'))
            self.assertEqual(1, playable.call_count)
            player = main.authorized_scenes(main.AccessContext(mode='player', profile_id='morthak'))
            self.assertEqual(2, playable.call_count)
            self.assertEqual('gm', gm[0]['participants'][0]['character']['viewer'])
            self.assertEqual('player', player[0]['participants'][0]['character']['viewer'])
            self.assertTrue(gm[0]['participants'][0]['character']['read_only'])
            self.assertTrue(player[0]['participants'][0]['character']['read_only'])


if __name__=='__main__':
    unittest.main()
