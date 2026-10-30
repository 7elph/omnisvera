from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.cf01_probe import BACKEND
from scripts.fixture_media import copy_fixture_media


class FixtureMediaTests(unittest.TestCase):
    def test_only_stocked_catalog_icons_are_copied_without_reading_note_content(self):
        expected='zz_media/ui/icons/items/espada-longa.png'
        self.image(expected);self.image('zz_media/ui/icons/items/espada-curta.png')
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('CREATE TABLE merchant_stock(compendium_item_id TEXT)')
            db.execute("INSERT INTO merchant_stock VALUES('arma-corpo-espada-longa')")
            db.execute('CREATE TABLE notes(content TEXT)')
            db.execute("INSERT INTO notes VALUES('private-image.png')")
        before=self.database.read_bytes();result=self.run_copy()
        self.assertIn(expected,result['copied'])
        self.assertNotIn('zz_media/ui/icons/items/espada-curta.png',result['copied'])
        self.assertEqual(before,self.database.read_bytes())

    def test_dorn_projected_spells_and_dagger_fallback_are_copied_without_applying_build(self):
        from app.character_play import SESSION_ABILITY_CATALOG_PATH
        images = json.loads((SESSION_ABILITY_CATALOG_PATH.parent / 'spell_images.json').read_text(encoding='utf8'))
        lightning = images['relampago']
        dagger = 'zz_media/ui/icons/items/adaga.png'
        for name in (lightning, dagger):
            self.image(name)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('CREATE TABLE character_sheets(profile_id TEXT)')
            connection.execute("INSERT INTO character_sheets VALUES('dorn7')")
        before = self.database.read_bytes()
        with patch('app.dorn_mage.apply_dorn_mage', side_effect=AssertionError('must not apply build')), patch(
                'app.approved_spell_pack.apply_approved_spell_pack', side_effect=AssertionError('must not grant spells')):
            result = self.run_copy()
        self.assertIn(lightning, result['copied'])
        self.assertIn(dagger, result['copied'])
        self.assertEqual(before, self.database.read_bytes())

    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = self.root / "source"
        self.target = self.root / "fixture.vault"
        self.source.mkdir()
        self.database = self.root / "fixture.sqlite3"
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript("""
                CREATE TABLE session_workspace_maps(image_path TEXT);
                CREATE TABLE session_workspace_tokens(image_path TEXT, sheet_json TEXT);
                CREATE TABLE player_inventory(image_path TEXT, notes TEXT);
                CREATE TABLE character_definition_overrides(data_json TEXT);
                CREATE TABLE unrelated_private_notes(data_json TEXT);
            """)

    def image(self, relative: str, content: bytes = b"fake-png") -> Path:
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def reference(self, relative: str) -> None:
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO session_workspace_maps VALUES(?)", (relative,))

    def run_copy(self, **limits) -> dict:
        return copy_fixture_media(self.database, self.source, self.target, **limits)

    def test_copies_only_referenced_images_preserving_paths_source_and_database(self) -> None:
        source = self.image("zz_media/maps/arena.png")
        self.image("zz_media/unreferenced.png")
        self.reference("zz_media/maps/arena.png")
        self.reference("zz_media/maps/arena.png")
        before_db, before_source = self.database.read_bytes(), source.read_bytes()
        result = self.run_copy()
        self.assertEqual(result, {"copied": ["zz_media/maps/arena.png"], "missing": [], "skipped": [], "bytes": 8})
        self.assertEqual((self.target / "zz_media/maps/arena.png").read_bytes(), before_source)
        self.assertFalse((self.target / "zz_media/unreferenced.png").exists())
        self.assertEqual(self.database.read_bytes(), before_db)
        self.assertEqual(source.read_bytes(), before_source)

    def test_known_dto_json_and_inventory_images_without_notes_or_arbitrary_json(self) -> None:
        allowed = ["zz_media/portrait.webp", "zz_media/item.jpg", "zz_media/token.gif"]
        for path in allowed + ["zz_media/private.png", "zz_media/note.png"]:
            self.image(path)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO character_definition_overrides VALUES(?)", (
                json.dumps({"portrait": allowed[0], "equipment": [{"image_path": allowed[1]}],
                            "notes": {"image_path": "zz_media/note.png"}}),))
            connection.execute("INSERT INTO session_workspace_tokens VALUES(?, ?)",
                               (allowed[2], "invalid-json"))
            connection.execute("INSERT INTO player_inventory VALUES(?, ?)",
                               (allowed[1], "zz_media/note.png"))
            connection.execute("INSERT INTO unrelated_private_notes VALUES(?)", (
                json.dumps({"image_path": "zz_media/private.png"}),))
        result = self.run_copy()
        self.assertEqual(set(result["copied"]), set(allowed))
        self.assertFalse((self.target / "zz_media/note.png").exists())
        self.assertFalse((self.target / "zz_media/private.png").exists())

    def test_effective_catalog_icons_of_present_actors_are_copied_without_notes(self):
        icon='zz_media/ui/icons/mark.png';self.image(icon)
        self.image('zz_media/private-note.png')
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('CREATE TABLE character_sheets(profile_id TEXT)')
            db.executemany('INSERT INTO character_sheets VALUES(?)',[('raziel',),('unrelated',)])
        with patch('app.character_play.load_session_abilities',return_value=[{'id':'marca-rubra','image_path':icon,'description':{'image_path':'zz_media/private-note.png'}}]) as catalog:
            before=self.database.read_bytes();result=self.run_copy()
        self.assertEqual([icon],result['copied'])
        catalog.assert_called_once_with('raziel')
        self.assertEqual(before,self.database.read_bytes())
        self.assertFalse((self.target/'zz_media/private-note.png').exists())

    def test_inventory_note_media_is_copied_for_audited_actors_only(self) -> None:
        for name in ('grisalma.png', 'private.png', 'unrelated.png'):
            self.image('zz_media/items/' + name)
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript('CREATE TABLE notes(path TEXT,frontmatter TEXT,content TEXT);'
                             'DROP TABLE player_inventory;'
                             'CREATE TABLE player_inventory(profile_id TEXT,item_path TEXT);')
            db.execute('INSERT INTO notes VALUES(?,?,?)', ('Items/Grisalma.md', json.dumps({
                'thumbnail': 'zz_media/items/grisalma.png',
                'cover': 'zz_media/items/grisalma.png',
                'gm_notes': {'cover': 'zz_media/items/private.png'}}), 'zz_media/items/private.png'))
            db.execute('INSERT INTO notes VALUES(?,?,?)', ('Items/Other.md', json.dumps({
                'cover': 'zz_media/items/unrelated.png'}), ''))
            db.execute('INSERT INTO player_inventory VALUES(?,?)', ('vezemir', 'Items/Grisalma.md'))
            db.execute('INSERT INTO player_inventory VALUES(?,?)', ('stranger', 'Items/Other.md'))
        before = self.database.read_bytes()
        result = self.run_copy()
        self.assertEqual({'zz_media/items/grisalma.png'}, set(result['copied']))
        self.assertEqual(before, self.database.read_bytes())
        self.assertFalse((self.target / 'zz_media/items/private.png').exists())
        self.assertFalse((self.target / 'zz_media/items/unrelated.png').exists())

    def test_bounded_packaged_fallbacks_and_dorn_protocol_cards_are_copied(self) -> None:
        packaged = ['zz_media/ui/icons/items/armadura-de-couro.png',
                    'zz_media/ui/icons/items/dados.jpg',
                    'zz_media/ui/icons/items/inventario.jpg',
                    'zz_media/ui/icons/uploads/protocolo_guarda_e51a549b42.jpg',
                    'zz_media/ui/icons/uploads/protocolo_vanguarda_2c8a61c1c8.jpg']
        for path in packaged + ['zz_media/ui/icons/items/not-audited.png',
                                'zz_media/ui/icons/uploads/not-packaged.jpg']:
            self.image(path)
        result = self.run_copy()
        self.assertEqual(set(packaged), set(result['copied']))
        self.assertFalse((self.target / 'zz_media/ui/icons/items/not-audited.png').exists())
        self.assertFalse((self.target / 'zz_media/ui/icons/uploads/not-packaged.jpg').exists())

    def test_three_packaged_night_form_images_are_copied_without_other_uploads(self):
        forms=['zz_media/ui/icons/uploads/raziel_coruja_969cca62e9.jpg',
               'zz_media/ui/icons/uploads/raziel_morcego_82a3c8733e.jpg',
               'zz_media/ui/icons/uploads/raziel_corvo_ae9c2df01e.jpg']
        for relative in forms+['zz_media/ui/icons/uploads/unrelated.jpg']:
            self.image(relative)
        before=self.database.read_bytes()
        self.assertEqual(set(forms),set(self.run_copy()['copied']))
        self.assertEqual(before,self.database.read_bytes())
        self.assertFalse((self.target/'zz_media/ui/icons/uploads/unrelated.jpg').exists())

    def test_missing_images_are_reported_without_success(self) -> None:
        self.reference("zz_media/maps/missing.jpeg")
        result = self.run_copy()
        self.assertEqual(result["missing"], ["zz_media/maps/missing.jpeg"])
        self.assertEqual(result["copied"], [])
        self.assertEqual(result["bytes"], 0)

    def test_scene_covers_and_npc_portraits_are_included_without_private_text(self):
        images=['zz_media/scenes/office.png','zz_media/npcs/merchant.png']
        for relative in images+['zz_media/private.png']:self.image(relative)
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('CREATE TABLE scenes(image_path TEXT,private_notes TEXT)')
            db.execute('CREATE TABLE npc_definitions(portrait_path TEXT,private_description TEXT)')
            db.execute('INSERT INTO scenes VALUES(?,?)',(images[0],'zz_media/private.png'))
            db.execute('INSERT INTO npc_definitions VALUES(?,?)',(images[1],'zz_media/private.png'))
        before=self.database.read_bytes()
        self.assertEqual(set(images),set(self.run_copy()['copied']))
        self.assertEqual(before,self.database.read_bytes())
        self.assertFalse((self.target/'zz_media/private.png').exists())

    def test_actor_portraits_use_only_linked_note_media_not_note_text_or_other_notes(self):
        for name in ('face.png','full.png','private.png','unrelated.png'):
            self.image('zz_media/'+name)
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript('CREATE TABLE character_sheets(profile_id TEXT,character_path TEXT); CREATE TABLE notes(path TEXT,frontmatter TEXT,content TEXT);')
            db.execute('INSERT INTO character_sheets VALUES(?,?)',('morthak','Characters/Morthak.md'))
            db.execute('INSERT INTO notes VALUES(?,?,?)',('Characters/Morthak.md',json.dumps({
                'thumbnail':'zz_media/face.png','cover':'zz_media/full.png',
                'gm_notes':{'portrait':'zz_media/private.png'}}),'zz_media/private.png'))
            db.execute('INSERT INTO notes VALUES(?,?,?)',('Other.md',json.dumps({'cover':'zz_media/unrelated.png'}),''))
        before=self.database.read_bytes()
        result=self.run_copy()
        self.assertEqual({'zz_media/face.png','zz_media/full.png'},set(result['copied']))
        self.assertEqual(before,self.database.read_bytes())

    def test_traversal_absolute_urls_non_media_and_non_images_are_skipped(self) -> None:
        bad = ["zz_media/../secret.png", "zz_media/maps/../../secret.png",
               "zz_media/%2e%2e/secret.png", "zz_media/secret.png:stream", "C:/private.png",
               "/zz_media/private.png", "https://example.com/image.png", "notes/private.png",
               "zz_media/tokens.json", "zz_media/private.svg.exe", "zz_media//x.png"]
        for value in bad:
            self.reference(value)
        result = self.run_copy()
        self.assertEqual(result["copied"], [])
        self.assertEqual(len(result["skipped"]), len(bad))

    def test_target_must_not_equal_or_be_inside_source_and_must_be_temporary(self) -> None:
        for target in (self.source, self.source / "nested", BACKEND / "data/unsafe-fixture"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                copy_fixture_media(self.database, self.source, target)

    def test_database_must_be_existing_temporary_and_is_not_created(self) -> None:
        with self.assertRaises(ValueError):
            copy_fixture_media(BACKEND / "data/operational.sqlite3", self.source, self.target)
        missing = self.root / "missing.sqlite3"
        with self.assertRaises(FileNotFoundError):
            copy_fixture_media(missing, self.source, self.target)
        self.assertFalse(missing.exists())

    def test_existing_target_is_not_overwritten(self) -> None:
        self.image("zz_media/existing.png", b"source")
        self.reference("zz_media/existing.png")
        target = self.target / "zz_media/existing.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"keep-this")
        result = self.run_copy()
        self.assertEqual(target.read_bytes(), b"keep-this")
        self.assertEqual(result["copied"], [])
        self.assertEqual(result["skipped"][0]["reason"], "exists")

    def test_file_and_byte_caps_are_reported(self) -> None:
        for path in ("zz_media/a.png", "zz_media/b.png"):
            self.image(path, b"1234")
            self.reference(path)
        result = self.run_copy(max_files=1, max_bytes=6)
        self.assertEqual(result["copied"], ["zz_media/a.png"])
        self.assertEqual(result["bytes"], 4)
        self.assertEqual(result["skipped"][0]["reason"], "file_limit")
        other = self.root / "bytes.vault"
        result = copy_fixture_media(self.database, self.source, other, max_bytes=3)
        self.assertEqual(result["copied"], [])
        self.assertEqual(result["bytes"], 0)
        self.assertEqual({item["reason"] for item in result["skipped"]}, {"byte_limit"})

    def test_empty_or_missing_schema_columns_are_supported(self) -> None:
        empty = self.root / "empty.sqlite3"
        with closing(sqlite3.connect(empty)) as connection, connection:
            connection.execute("CREATE TABLE session_workspace_tokens(id TEXT)")
        result = copy_fixture_media(empty, self.source, self.target)
        self.assertEqual(result, {"copied": [], "missing": [], "skipped": [], "bytes": 0})

    def test_symlinked_source_or_target_outside_media_is_rejected(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.png").write_bytes(b"secret")
        link = self.source / "zz_media"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create symlinks: {error}")
        self.reference("zz_media/secret.png")
        result = self.run_copy()
        self.assertEqual(result["copied"], [])
        self.assertEqual(result["skipped"][0]["reason"], "unsafe_path")
        link.unlink()
        self.image("zz_media/secret.png")
        self.target.mkdir(exist_ok=True)
        (self.target / "zz_media").symlink_to(outside, target_is_directory=True)
        result = self.run_copy()
        self.assertEqual(result["copied"], [])
        self.assertEqual((outside / "secret.png").read_bytes(), b"secret")
        self.assertEqual(result["skipped"][0]["reason"], "unsafe_path")

    def test_symlink_component_is_rejected_without_host_symlink_privileges(self) -> None:
        self.image("zz_media/image.png")
        self.reference("zz_media/image.png")
        for unsafe_component in (self.source / "zz_media", self.target / "zz_media"):
            with self.subTest(component=unsafe_component), patch.object(
                    Path, "is_symlink", autospec=True,
                    side_effect=lambda path: path == unsafe_component):
                result = self.run_copy()
            self.assertEqual(result["copied"], [])
            self.assertEqual(result["skipped"][0]["reason"], "unsafe_path")


if __name__ == "__main__":
    unittest.main()
