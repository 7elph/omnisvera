import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app.companion_promotion import promote_dorn
from app.character_creation import list_sheets
from app.character_play import build_character_definition, load_definition_overrides, get_or_create_state
from app.session_workspace import save_workspace_token


class CompanionPromotionTests(unittest.TestCase):
    def test_same_player_definition_and_state_without_healing_or_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.sqlite'
            token = save_workspace_token(path, token_type='monster', name='Dorn 7', latitude=50, longitude=50,
                current_hp=11, maximum_hp=20, conditions=['danificado'], sheet={'armor_class':16, 'saving_throw':16,
                'movement':'6 m', 'attacks':[{'name':'Punho', 'damage':'1d6+2', 'bonus':'+3'}], 'abilities':['Proteger']})
            note = {'path':'Characters/Individual/Unidade DORN-7.md', 'title':'Dorn 7', 'frontmatter':{}, 'content':''}
            self.assertTrue(promote_dorn(path, token_id=token['id'], note=note)['created'])
            self.assertFalse(promote_dorn(path, token_id=token['id'], note=note)['created'])
            sheet = list_sheets(path)[0]
            definition = build_character_definition(profile_id='dorn7', note=note, sheet=sheet, inventory=[], overrides=load_definition_overrides(path,'dorn7'))
            state = get_or_create_state(path, profile_id='dorn7', sheet=sheet, definition=definition)
            self.assertEqual(state['current_hp'], 11)
            self.assertEqual(state['conditions'], ['danificado'])
            self.assertEqual(definition['attacks'][0]['damage'], '1d6+2')
            self.assertEqual(definition['attacks'][0]['attack_bonus'], 3)
            self.assertEqual(definition['defenses']['armor_class'], 16)
            self.assertIsNone(definition['level'])
            self.assertEqual(definition['session_abilities'][0]['name'], 'Proteger')
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('SELECT token_type,character_id,current_hp FROM session_workspace_tokens').fetchone(), ('character','dorn7',None))
