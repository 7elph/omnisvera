import sqlite3
from contextlib import closing
from unittest import TestCase
import test_catalog_condition_cure as baseline
from app.action_range import enforce_action_range

class CurrentMapTargetTests(TestCase):
    setUp=baseline.CatalogConditionCureTests.setUp
    grid=baseline.CatalogConditionCureTests.grid
    def test_another_maps_older_pin_cannot_hide_the_target_on_this_map(self):
        self.grid(target_x=1)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,character_id,map_id,created_at,updated_at) VALUES('000-old-pin','character','Old pin','vezemir','other-map','now','now')")
        result=enforce_action_range(self.db,attacker_token_id='gob1',target_type='character',target_id='vezemir',mode='ranged',range_m=100)
        self.assertTrue(result['checked'])
