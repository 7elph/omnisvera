import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import magic_field_items as items


class FieldItemTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'items.sqlite'
        from app.character_creation import init_character_creation
        from app.character_play import init_character_play
        from app.scene_play import init_scene_play
        from app.combat_effects import init_effects
        from app.dice_rolls import init_dice_rolls
        from app.player_inventory import init_player_inventory, upsert_inventory
        from app.session_ledger import init_session_ledger
        from app.session_workspace import init_session_workspace
        from app.spatial_grid import init_spatial
        for init in (init_character_creation, init_character_play, init_dice_rolls, init_effects, init_player_inventory,
                     init_session_workspace, init_scene_play, init_session_ledger, init_spatial):
            init(self.path)
        self.owner = SimpleNamespace(mode='player', profile_id='tester')
        self.gm = SimpleNamespace(mode='gm', profile_id='master')
        self.other = SimpleNamespace(mode='player', profile_id='recipient')
        for owner, item in [('tester', items.CRYSTAL), ('tester', items.GLASSES),
                            ('tester', items.CUP), ('recipient', items.CUP)]:
            upsert_inventory(self.path, profile_id=owner, item_path='compendium:' + item,
                             item_title=item, quantity=1, equipped=False, notes=None)
        sheet = {'character_class': {'class_name': 'Mago'},
                 'languages': {'spoken_languages': 'Comum\nÉlfico', 'written_languages': 'Comum'}}
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""INSERT INTO character_sheets
                (profile_id,character_path,character_title,data_json,updated_at)
                VALUES ('tester','test','Tester',?,'now')""", (json.dumps(sheet),))

    def command(self, key, operation, value=None, *, access=None, request=None):
        return items.execute(self.path, access or self.owner, 'tester', 'compendium:' + key,
                             operation, value or {}, request or ('test:' + operation))

    def test_vision_private_and_retry_does_not_spend_twice(self):
        self.command(items.CRYSTAL, 'set_vision', {
            'subject': 'Portão', 'text': 'Verdade', 'false_text': 'Ilusão', 'chaotic': True,
        }, access=self.gm)
        self.assertNotIn('Verdade', json.dumps(items.inspect(self.path, self.owner, 'tester', 'compendium:' + items.CRYSTAL)))
        from app.player_inventory import list_inventory
        self.assertNotIn('Ilusão', json.dumps(list_inventory(self.path, 'tester'), ensure_ascii=False))
        with patch.object(items, 'roll_formula', return_value={'total': 20}) as roll:
            a = self.command(items.CRYSTAL, 'observe')
            self.assertEqual(a, self.command(items.CRYSTAL, 'observe'))
            roll.assert_called_once()
        self.assertEqual((a['message'], a['remaining']), ('Ilusão', 2))
        self.assertNotIn('false', a)
        with self.assertRaisesRegex(ValueError, 'observação ativa'):
            self.command(items.CRYSTAL, 'observe', request='test:early-observe')
        with self.assertRaises(PermissionError):
            self.command(items.CRYSTAL, 'observe', access=self.other)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT visibility FROM session_ledger').fetchone()[0], 'owner')
        from app.combat_effects import effect_snapshot
        from app.dorn_spells import elapse
        with closing(items.connect(self.path)) as db, db:
            elapse(db, effect_snapshot(db), 599, [], '2026-11-04T01:00:00+00:00')
            self.assertTrue(items._observation(db, 'tester'))
            elapse(db, effect_snapshot(db), 1, [], '2026-11-04T01:00:00+00:00')
            self.assertFalse(items._observation(db, 'tester'))
        with patch.object(items, 'roll_formula', return_value={'total': 31}):
            b = self.command(items.CRYSTAL, 'observe', request='test:second-observe')
        self.assertEqual((b['message'], b['remaining']), ('Verdade', 1))

    def test_crystal_has_fixed_catalog_variants(self):
        from app.item_catalog import get_catalog_item, item_offer_readiness
        from app.player_inventory import upsert_inventory
        key = items.CRYSTAL + '-ordeira'
        upsert_inventory(self.path, profile_id='tester', item_path='compendium:' + key,
                         item_title='Bola de Cristal Ordeira', quantity=1, equipped=False, notes=None)
        self.command(key, 'set_vision', {'subject': 'Portão', 'text': 'Verdade', 'chaotic': True}, access=self.gm)
        with patch.object(items, 'roll_formula') as roll:
            self.assertEqual(self.command(key, 'observe')['message'], 'Verdade')
            roll.assert_not_called()
        for variant in items.CRYSTAL_VARIANTS:
            self.assertEqual(item_offer_readiness(get_catalog_item(variant))['effect_status'], 'native_field_interaction')

    def test_glasses_require_document_under_page_limit_and_keep_content_private(self):
        self.command(items.GLASSES, 'set_document', {'title': 'Crônica', 'text': 'Texto reservado', 'pages': 101}, access=self.gm)
        with self.assertRaisesRegex(ValueError, '100'):
            self.command(items.GLASSES, 'read_document')
        self.command(items.GLASSES, 'set_document', {'title': 'Crônica', 'text': 'Texto reservado', 'pages': 100},
                     access=self.gm, request='test:second-document')
        self.assertNotIn('Texto reservado', json.dumps(items.inspect(self.path, self.owner, 'tester', 'compendium:' + items.GLASSES)))
        self.assertEqual(self.command(items.GLASSES, 'read_document')['message'], 'Texto reservado')

    def test_message_requires_actual_pair_and_current_range(self):
        with closing(sqlite3.connect(self.path)) as db:
            target = db.execute("SELECT id FROM player_inventory WHERE profile_id='recipient'").fetchone()[0]
        self.command(items.CUP, 'bind', {'inventory_id': target}, access=self.gm)
        self.command(items.CUP, 'listen')
        items.execute(self.path, self.other, 'recipient', 'compendium:' + items.CUP,
                      'listen', {}, 'test:other-listen')
        with self.assertRaises(ValueError):
            self.command(items.CUP, 'message', {'text': 'Segredo'})
        with patch.object(items, 'cup_distance', return_value=15.01):
            with self.assertRaisesRegex(ValueError, '15'):
                self.command(items.CUP, 'message', {'text': 'Segredo'})
        with patch.object(items, 'cup_distance', return_value=15):
            self.command(items.CUP, 'message', {'text': 'Segredo'})
            self.command(items.CUP, 'message', {'text': 'Segredo'})
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT character_id,visibility FROM session_ledger WHERE event_kind='message' ORDER BY id").fetchall(),
                             [('tester','owner'), ('recipient','owner')])

    def test_book_updates_native_sheet_once(self):
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.path, profile_id='tester', item_path='compendium:' + items.BOOK,
                         item_title='Livro', quantity=1, equipped=False, notes=None)
        self.command(items.BOOK, 'set_languages', {'languages': ['Comum', 'Anão']}, access=self.gm)
        a = self.command(items.BOOK, 'read_languages')
        self.assertEqual(a, self.command(items.BOOK, 'read_languages'))
        with closing(sqlite3.connect(self.path)) as db:
            result = json.loads(db.execute('SELECT data_json FROM character_sheets').fetchone()[0])
        self.assertEqual(result['languages'], {'spoken_languages': 'Anão', 'written_languages': ''})

    def test_boots_prevent_new_tracks_only_while_equipped(self):
        from app.player_inventory import upsert_inventory
        token = {'character_id': 'tester', 'id': 'test-pin'}
        upsert_inventory(self.path, profile_id='tester', item_path='compendium:' + items.BOOTS,
                         item_title='Botas', quantity=1, equipped=True, equipment_slot='Pés', notes=None)
        with closing(sqlite3.connect(self.path)) as db, db:
            items.record_tracks(db, token, 'map-test', [[1, 1], [1, 2]], 'first-move', 'now')
            db.execute("UPDATE player_inventory SET equipped=0 WHERE item_title='Botas'")
            items.record_tracks(db, token, 'map-test', [[1, 2], [1, 3]], 'second-move', 'now')
        with self.assertRaises(PermissionError):
            items.tracks(self.path, self.owner, 'map-test')
        self.assertEqual(items.tracks(self.path, self.gm, 'map-test')['tracks'],
                         [{'map_id': 'map-test', 'token_id': 'test-pin', 'cells': [[1, 2], [1, 3]], 'created_at': 'now'}])


class FieldItemCombatTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)

    def test_drink_projects_native_attack_and_confirm_can_break_once(self):
        from app.player_inventory import upsert_inventory
        from test_item_specials import ItemSpecialApiTests
        path = 'compendium:' + items.VESSEL
        upsert_inventory(self.db, profile_id='vezemir', item_path=path,
                         item_title='Vaso', quantity=1, equipped=False, notes=None)
        route = '/characters/vezemir/inventory/field-item'
        def use(operation):
            response = self.client.post(route, json={'item_path': path, 'operation': operation,
                                                     'request_id': 'vessel-test-' + operation})
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()
        def sheet():
            return self.client.get('/characters/vezemir').json()
        original = sheet()['state']['current_hp']
        self.assertEqual(use('drink'), use('drink'))
        attack = next(a for a in sheet()['definition']['attacks'] if a['id'] == items.NAILS)
        self.assertEqual(attack['damage'], '1d4')
        target = ItemSpecialApiTests.target(self)
        payload = {**ItemSpecialApiTests.request(self, target, 'vessel-test-attack'), 'attack_id': items.NAILS}
        resolution = self.client.post('/characters/vezemir/attacks/resolve', json=payload)
        self.assertEqual(resolution.status_code, 200, resolution.text)
        confirm = '/combat/attacks/' + resolution.json()['resolution_id'] + '/confirm'
        with patch.object(items, 'roll_formula', return_value={'total': 1}) as roll:
            first = self.client.post(confirm)
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json(), self.client.post(confirm).json())
            roll.assert_called_once_with('1d4')
        self.assertEqual(sheet()['state']['current_hp'], original - 1)
        use('clip')
        self.assertFalse(any(a['id'] == items.NAILS for a in sheet()['definition']['attacks']))
