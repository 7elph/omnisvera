"""New party guard uses real pins, current map, native attacks and receipts."""
import json,sqlite3,unittest
from contextlib import closing
from dataclasses import replace
from unittest.mock import patch
import test_dorn_protocols as fixture
from app import main
from app.access import AccessContext
from app.combat import resolve_attack,confirm_attack_resolution
from app.dorn_protocols import protects_ally
from app.session_workspace import save_workspace_token
from app.spatial_grid import configure_grid
from app.combat_effects import readeffects

class GuardAreaTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.DornProtocolTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.db=self.f.db
        self.dorn=save_workspace_token(self.db,token_type='character',character_id='dorn7',name='Dorn',map_id='arena',longitude=25,latitude=25)
        self.ally=save_workspace_token(self.db,token_type='character',character_id='ally',name='Aliado',map_id='arena',longitude=30,latitude=25)
        self.enemy=save_workspace_token(self.db,token_type='monster',name='Inimigo',map_id='arena',longitude=35,latitude=25,current_hp=20,maximum_hp=20,sheet={'armor_class':11,'movement':9})
        configure_grid(self.db,actor_id='master',role='gm',request_id='area-guard-grid',map_id='arena',config={'cols':20,'rows':20,'cell_size_m':1.5})
        self.f.command('start',map_id='arena',participants=[{'target_type':'character','target_id':'dorn7','initiative':20},
            {'target_type':'token','target_id':self.enemy['id'],'initiative':10},{'target_type':'character','target_id':'ally','initiative':1}])
        self.f.command('dorn_guard')

    def test_range_fails_closed_and_uses_only_combat_map(self):
        effect=next(e for e in readeffects(self.db)['effects'] if e.get('protocol')=='guard')
        with closing(sqlite3.connect(self.db)) as db,db:
            self.assertTrue(protects_ally(db,effect,'ally'))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=19 WHERE token_id=?',(self.ally['id'],))
            self.assertFalse(protects_ally(db,effect,'ally'))
            db.execute('DELETE FROM session_workspace_entity_positions WHERE token_id=?',(self.ally['id'],))
            self.assertFalse(protects_ally(db,effect,'ally'))

    def test_two_attacks_intercepted_half_damage_and_retry_once(self):
        self.f.command('next_turn')
        for i in (1,2):
            req=main.AttackResolutionCreate(request_id=f'area-guard-hit-{i}',attack_id='claw',target_type='character',target_id='ally',roll_mode='physical',d20=15)
            with patch.object(main,'settings',replace(main.settings,database_path=self.db)),patch.object(main,'_combat_target',side_effect=lambda kind,key:{'type':kind,'id':key,'name':key,'armor_class':11,'current_hp':20}):
                target=main._guard_attack_target(req,AccessContext(mode='gm'))
            record,_=resolve_attack(self.db,request_id=req.request_id,actor_character_id=self.enemy['id'],actor_name='Inimigo',requested_by_id='master',requested_by_role='gm',
                definition={'attacks':[{'id':'claw','name':'Garra','attack_bonus':2,'damage':'1d4','weapon_item_path':'natural:claw'}]},inventory=[],attack_id='claw',
                target=target,roll_mode='physical',physical_d20=15,guard_effect_id=req.guard_effect_id,rng=lambda a,b:4)
            result,created=confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id='master',requested_by_role='gm')
            self.assertTrue(created);self.assertEqual(2,result['damage_total'])
            self.assertEqual(result,confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id='master',requested_by_role='gm')[0])
            self.assertTrue(any(e.get('area_guard') for e in readeffects(self.db)['effects']))

if __name__=='__main__':unittest.main()
