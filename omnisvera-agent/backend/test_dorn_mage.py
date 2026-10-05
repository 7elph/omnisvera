import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.companion_promotion import promote_dorn
from app.dorn_mage import apply_dorn_mage, SPEC
from app.character_creation import list_sheets
from app.character_play import build_character_definition, load_definition_overrides
from app.combat import init_combat, magic_missile_definition
from app.combat_effects import init_effects
from app.player_inventory import init_player_inventory
from app.session_workspace import save_workspace_token


class DornMageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'test.sqlite3'
        token = save_workspace_token(self.db, token_type='monster', name='Dorn 7', latitude=50, longitude=50,
            current_hp=20, maximum_hp=20, sheet={'armor_class':16, 'saving_throw':16,
            'attacks':[{'name':'Punho','damage':'1d6+2','bonus':'+3'}], 'abilities':['Proteger']})
        self.note = {'path':'Characters/Individual/Unidade DORN-7.md', 'title':'Dorn 7', 'frontmatter':{}, 'content':''}
        promote_dorn(self.db, token_id=token['id'], note=self.note)
        init_combat(self.db); init_effects(self.db); init_player_inventory(self.db)

    def test_exact_sheet_idempotency_and_no_old_attacks(self):
        self.assertTrue(apply_dorn_mage(self.db)['applied'])
        self.assertFalse(apply_dorn_mage(self.db)['applied'])
        sheet = list_sheets(self.db)[0]
        definition = build_character_definition(profile_id='dorn7', note=self.note, sheet=sheet,
            inventory=[], overrides=load_definition_overrides(self.db, 'dorn7'))
        self.assertEqual(definition['attributes'], SPEC['sheet']['attributes'])
        self.assertEqual(definition['attribute_modifiers']['constitution'], 3)
        self.assertEqual((definition['level'], definition['class_name']), (2, 'Mago'))
        self.assertEqual(definition['defenses']['armor_class'], 11)
        self.assertEqual(definition['defenses']['saving_throw'], 14)
        self.assertEqual(definition['progression']['experience'], 2500)
        self.assertFalse(any(a['name'] == 'Punho' for a in definition['attacks']))
        self.assertFalse(any(a['name'] == 'Proteger' for a in definition['session_abilities']))
        with closing(sqlite3.connect(self.db)) as db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            self.assertEqual((state['current_hp'],state['maximum_hp']), (13,13))
            self.assertEqual(sum(r['maximum'] for r in state['resources']), 3)
            self.assertEqual(db.execute('SELECT count(*) FROM player_inventory').fetchone()[0],6)
            self.assertEqual(db.execute("SELECT count(*) FROM character_events WHERE event_type='approved_build_reconciliation'").fetchone()[0],1)
        missile = magic_missile_definition(definition, state['resources'])['attacks'][0]
        self.assertEqual(missile['damage'], '1d4+2')
        self.assertEqual(missile['resource_cost']['key'], 'dorn_misseis_magicos')

    def test_changed_hp_blocks_without_partial_write(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states").fetchone()[0])
            state['current_hp'] = 19
            db.execute('UPDATE character_states SET state_json=?', (json.dumps(state),))
        with self.assertRaisesRegex(ValueError, 'Estado de Dorn mudou'):
            apply_dorn_mage(self.db)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM player_inventory').fetchone()[0],0)

    def test_active_combat_blocks(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=?', (json.dumps({'active':True,'participants':[{'target_id':'dorn7'}]}),))
        with self.assertRaisesRegex(ValueError,'combate ativo'):
            apply_dorn_mage(self.db)
