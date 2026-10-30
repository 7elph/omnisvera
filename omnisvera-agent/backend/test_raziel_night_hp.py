import json,sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
from unittest import TestCase
from app.night_form import start,end,current_form
from app.character_play import init_character_play
from app.session_workspace import init_session_workspace
from app.combat_effects import change_hp

class NightHpTests(TestCase):
    def test_each_form_uses_approved_profile_and_manual_return_keeps_normal_hp(self):
        for animal in ('corvo','coruja','morcego'):
            state={'current_hp':22,'maximum_hp':22,'temporary_hp':0};start(state,animal)
            self.assertEqual((1,14,4,'9V'),tuple(current_form(state)[k] for k in ('maximum_hp','armor_class','saving_throw','movement')))
            end(state);self.assertEqual(22,state['current_hp']);self.assertNotIn('night_form',state)
    def test_central_damage_exact_zero_and_overflow(self):
        for damage,expected in ((1,22),(5,18),(30,0)):
            with TemporaryDirectory() as temp:
                path=Path(temp)/'db';init_character_play(path);init_session_workspace(path)
                state={'current_hp':22,'maximum_hp':22,'temporary_hp':0};start(state,'morcego')
                with closing(sqlite3.connect(path)) as db,db:
                    db.execute('INSERT INTO character_states VALUES(?,?,1,?)',('raziel',json.dumps(state),'fixture'))
                    result=change_hp(db,'character','raziel',-damage,'now')
                    saved=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
                    self.assertEqual(expected,saved['current_hp']);self.assertNotIn('animal_form',saved)
                    self.assertEqual(min(damage,23),result['damage_taken'])
                    self.assertTrue(result['night_form_returned'])
    def test_healing_in_animal_form_does_not_heal_normal_body(self):
        from app.night_form import change_animal_hp
        state={'current_hp':10,'maximum_hp':22,'temporary_hp':0};start(state,'coruja')
        change_animal_hp(state,10);self.assertEqual(10,state['current_hp']);self.assertEqual(1,current_form(state)['current_hp'])
    def test_switching_animals_does_not_refill_temporary_hp(self):
        state={'current_hp':22,'maximum_hp':22,'temporary_hp':0};start(state,'corvo')
        state['night_form']['temporary_hp']=2;start(state,'coruja');self.assertEqual(2,current_form(state)['temporary_hp'])
