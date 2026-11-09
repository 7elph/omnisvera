"""Campaign phase and Sisters' buckle; native transactions on TEMP only."""
import sqlite3
import unittest
from contextlib import closing


class WorldPhaseItemTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_master]=lambda:AccessContext(mode='gm')
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:item-magico-fivela-das-irmas',
            item_title='Fivela das Irmãs',quantity=1,equipped=True,equipment_slot='Acessório',notes=None)

    def phase(self,value,key=None):
        from app.combat_effects import readeffects
        return self.client.post('/gm/combat/effects',json={'request_id':key or 'phase-'+value+'-fixture',
            'expected_version':readeffects(self.db)['version'],'action':'world_phase','payload':{'phase':value}})

    def damage(self,kind,amount=9,context=None):
        from app.monster_runtime import damage_response
        with closing(sqlite3.connect(self.db)) as db:return damage_response(db,'character','vezemir',amount,kind,context)

    def test_day_and_night_reduce_only_the_matching_damage_and_never_below_zero(self):
        self.assertEqual(self.phase('day').status_code,200)
        self.assertEqual(self.damage('fire'),4);self.assertEqual(self.damage('lightning'),9)
        self.assertEqual(self.damage('fire',2),0)
        self.assertEqual(self.phase('night').status_code,200)
        self.assertEqual(self.damage('lightning'),4);self.assertEqual(self.damage('fire'),9)

    def test_phase_persists_and_retry_does_not_bump_clock_again(self):
        from app.combat_effects import readeffects
        first=self.phase('day','phase-retry-test');self.assertEqual(first.status_code,200,first.text)
        again=self.phase('day','phase-retry-test');self.assertEqual(again.status_code,200,again.text)
        self.assertEqual(first.json()['version'],again.json()['version'])
        self.assertEqual(readeffects(self.db)['world_phase'],'day')

    def test_unavoidable_damage_bypasses_buckle_and_stowing_removes_reduction(self):
        self.assertEqual(self.phase('day').status_code,200)
        self.assertEqual(self.damage('fire',9,{'unavoidable_damage':9}),9)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute("UPDATE player_inventory SET equipped=0 WHERE item_path='compendium:item-magico-fivela-das-irmas'")
        self.assertEqual(self.damage('fire'),9)

    def test_player_cannot_change_phase_and_invalid_phase_is_rejected(self):
        from app import main
        from app.access import AccessContext
        self.assertEqual(self.phase('eclipse').status_code,409)
        self.assertEqual(self.phase(['day'],'bad-world-phase-list').status_code,409)
        # Direct service permission must remain authoritative even behind another caller.
        from app.combat_effects import effect_command
        with self.assertRaises(PermissionError):effect_command(self.db,actor_id='vezemir',actor_role='player',
            request_id='phase-forbidden-player',expected_version=0,action='world_phase',payload={'phase':'day'},allow_player=True)
