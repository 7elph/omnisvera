"""Native journeys: TEMP-only composition, replay and optimistic concurrency."""
import json
import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import test_map_commerce
from app import world_travel as travel


class JourneyCompositionTests(unittest.TestCase):
    def setUp(self):
        test_map_commerce.MapCommerceTests.setUp(self)
        travel.init_world_travel(self.db)
        self.campaign='synthetic-foundation'
        self.locations=[travel.create_location(self.db,request_id='p1-location-'+str(i),campaign_id=self.campaign,
            actor_id='master',fields={'name':name,'visibility':'table','discovered_by_default':True})[0]
            for i,name in enumerate(['Nimalia (fixture)','Destination (fixture)'])]
        self.journey=self.create('p1-journey-one')

    def create(self,key):
        return travel.create_journey(self.db,request_id=key,campaign_id=self.campaign,actor_id='master',
            fields={'title':'Synthetic route','origin_location_id':self.locations[0]['id'],
                'destination_location_id':self.locations[1]['id'],'progress_target':2,'visibility':'table'})[0]

    def transition(self,action,key,journey=None):
        journey=journey or self.journey
        return travel.transition_journey(self.db,journey['id'],request_id=key,actor_id='master',
            expected_version=journey['version'],action=action)

    def test_changed_advance_cannot_reuse_request(self):
        active=self.transition('start','p1-start')
        args=dict(request_id='p1-advance',actor_id='master',expected_version=active['version'])
        first=travel.advance_journey(self.db,active['id'],amount=1,**args)
        self.assertEqual(travel.advance_journey(self.db,active['id'],amount=1,**args),first)
        with self.assertRaises(ValueError):travel.advance_journey(self.db,active['id'],amount=.5,**args)

    def test_transition_request_cannot_be_reused_for_other_journey_or_actor(self):
        self.transition('start','p1-start-bound')
        other=self.create('p1-other-journey')
        with self.assertRaises(ValueError):self.transition('start','p1-start-bound',other)
        with self.assertRaises(ValueError):
            travel.transition_journey(self.db,self.journey['id'],request_id='p1-start-bound',actor_id='other-master',expected_version=1,action='start')

    def test_two_advances_with_same_version_apply_once(self):
        active=self.transition('start','p1-race-start');gate=Barrier(2)
        def advance(key):
            gate.wait(timeout=10)
            try:
                travel.advance_journey(self.db,active['id'],request_id=key,actor_id='master',expected_version=active['version'],amount=1)
                return 'applied'
            except RuntimeError:return 'stale'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(advance,['p1-race-a','p1-race-b']))
        self.assertEqual(sorted(results),['applied','stale'])
        self.assertEqual(travel.get_journey(self.db,active['id'],access_mode='gm')['progress_current'],1)
        events=travel.list_journey_events(self.db,active['id'],access_mode='gm')
        self.assertEqual(sum(e['event_type']=='advanced' for e in events),1)

    def test_arrival_and_cancellation_retries_reject_changed_intent(self):
        active=self.transition('start','p1-complete-start')
        travel.complete_journey(self.db,active['id'],request_id='p1-complete-bound',actor_id='master',expected_version=active['version'])
        other=self.create('p1-complete-other')
        with self.assertRaises(ValueError):
            travel.complete_journey(self.db,other['id'],request_id='p1-complete-bound',actor_id='master',expected_version=other['version'])
        args=dict(request_id='p1-cancel-bound',actor_id='master',expected_version=other['version'],action='cancel')
        first=travel.transition_journey(self.db,other['id'],reason='Synthetic reason',**args)
        self.assertEqual(travel.transition_journey(self.db,other['id'],reason='Synthetic reason',**args),first)
        with self.assertRaises(ValueError):travel.transition_journey(self.db,other['id'],reason='Changed reason',**args)

    def test_legacy_fractional_progress_event_replays_without_input_metadata(self):
        active=self.transition('start','p1-legacy-start')
        first=travel.advance_journey(self.db,active['id'],request_id='p1-legacy-prefix',actor_id='master',expected_version=active['version'],amount=.1)
        args=dict(request_id='p1-legacy-event',actor_id='master',expected_version=first['version'],amount=.2)
        result=travel.advance_journey(self.db,active['id'],**args)
        with closing(sqlite3.connect(self.db)) as db, db:
            after={'progress':result['progress_current']}
            db.execute("UPDATE journey_events SET after_json=? WHERE event_key='journey:advance:p1-legacy-event'",(json.dumps(after),))
        self.assertEqual(travel.advance_journey(self.db,active['id'],**args),result)

    def test_private_scene_link_never_leaks_through_player_journey_events(self):
        from app.scene_play import create_scene
        ids={}
        for visibility in ['gm','table']:
            scene=create_scene(self.db,request_id='p1-scene-'+visibility,campaign_id=self.campaign,title='Synthetic '+visibility,
                location_name='Fixture',created_by='master',visibility=visibility)[0]
            ids[visibility]=scene['id']
            travel.link_journey_scene(self.db,self.journey['id'],request_id='p1-link-'+visibility,actor_id='master',scene_id=scene['id'])
        player=travel.get_journey(self.db,self.journey['id'],access_mode='player',profile_id='vezemir')
        self.assertEqual([s['scene_id'] for s in player['scene_links']],[ids['table']])
        events=travel.list_journey_events(self.db,self.journey['id'],access_mode='player')
        self.assertNotIn(ids['gm'],[e['scene_id'] for e in events if e.get('scene_id')])
        self.assertIn(ids['table'],[e['scene_id'] for e in events if e.get('scene_id')])
        gm_events=travel.list_journey_events(self.db,self.journey['id'],access_mode='gm')
        self.assertIn(ids['gm'],[e['scene_id'] for e in gm_events if e.get('scene_id')])

    def test_pause_encounter_resume_arrival_preserves_resources_and_privacy(self):
        travel.add_journey_participant(self.db,self.journey['id'],request_id='p1-traveler',actor_id='master',
            fields={'participant_type':'player_character','character_id':'vezemir','public_label':'Synthetic traveler'})
        with closing(sqlite3.connect(self.db)) as db:
            before=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
        active=self.transition('start','p1-cycle-start')
        advanced=travel.advance_journey(self.db,active['id'],request_id='p1-cycle-stage',actor_id='master',expected_version=active['version'],amount=1)
        paused=self.transition('pause','p1-cycle-pause',advanced)
        with self.assertRaises(ValueError):
            travel.advance_journey(self.db,paused['id'],request_id='p1-paused-invalid',actor_id='master',expected_version=paused['version'],amount=1)
        resumed=self.transition('resume','p1-cycle-resume',paused)
        arrived=travel.complete_journey(self.db,resumed['id'],request_id='p1-cycle-arrive',actor_id='master',expected_version=resumed['version'])
        self.assertEqual(arrived['status'],'completed')
        self.assertEqual(travel.complete_journey(self.db,resumed['id'],request_id='p1-cycle-arrive',actor_id='master',expected_version=resumed['version']),arrived)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_location_id'],self.locations[1]['id'])
            self.assertIsNone(state['active_journey_id'])
            self.assertEqual({k:state[k] for k in before},{k:before[k] for k in before})
            self.assertEqual(db.execute("SELECT count(*) FROM character_events WHERE event_type='journey_arrival'").fetchone()[0],1)
        for event in travel.list_journey_events(self.db,arrived['id'],access_mode='player'):
            self.assertNotIn('before_json',event);self.assertNotIn('after_json',event)


if __name__=='__main__':unittest.main()
