"""Contracts enrich effective approved abilities, never grant them on reads."""
from unittest import TestCase

from app.action_library import native_action_contract
from app.approved_spell_pack import dorn_abilities
from app.character_creation import list_sheets
from app.character_play import build_character_definition, load_definition_overrides


class ContractSheetProjectionTests(TestCase):
    def setUp(self):
        import test_dorn_spells as fixtures
        self.fixture = fixtures.DornSpellTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def build(self, approved=False):
        overrides = load_definition_overrides(self.fixture.db, 'dorn7')
        if approved:
            overrides['approved_session_abilities'] = dorn_abilities()
        return build_character_definition(profile_id='dorn7', note=self.fixture.base.note,
            sheet=next(s for s in list_sheets(self.fixture.db) if s['profile_id']=='dorn7'),
            inventory=[], overrides=overrides)

    def test_reflexos_effective_card_uses_same_backend_contract(self):
        definition = self.build(approved=True)
        ability = next(a for a in definition['session_abilities'] if a['id']=='reflexos')
        self.assertEqual(native_action_contract('technique:dorn7:reflexos', definition['level']),
                         ability.get('action_contract'))

    def test_metadata_does_not_grant_reflexos_to_unconfigured_sheet(self):
        self.assertNotIn('reflexos', [a['id'] for a in self.build()['session_abilities']])

    def test_approved_pack_cards_share_native_contracts_without_granting(self):
        definition = self.build(approved=True)
        for identity in ('forca-arcana', 'teia', 'dissipar-magia'):
            with self.subTest(identity=identity):
                ability = next(a for a in definition['session_abilities'] if a['id']==identity)
                self.assertEqual(native_action_contract('technique:dorn7:'+identity, definition['level']),
                                 ability.get('action_contract'))
                self.assertNotIn(identity, [a['id'] for a in self.build()['session_abilities']])


class VezemirContractProjectionTests(TestCase):
    def test_buff_cards_resolve_metadata_using_effective_level(self):
        import test_vezemir_techniques as fixtures
        fixture = fixtures.VezemirTechniquesTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        response = fixture.client.get('/characters/vezemir')
        self.assertEqual(200, response.status_code)
        definition = response.json()['definition']
        for identity in ('forca-arcana', 'velocidade'):
            with self.subTest(identity=identity):
                ability = next(a for a in definition['session_abilities'] if a['id']==identity)
                self.assertEqual(native_action_contract('technique:vezemir:'+identity, definition['level']),
                                 ability.get('action_contract'))


class MorthakContractProjectionTests(TestCase):
    def test_approved_high_spells_project_metadata_without_granting_on_reads(self):
        import copy
        import sqlite3
        from contextlib import closing
        import test_morthak_sheet as fixtures
        from app.action_library import describe_action
        from app.level_advancement import NECROMANCER_ABILITIES_5
        fixture = fixtures.MorthakSheetTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        overrides = load_definition_overrides(fixture.db, 'morthak')
        sheet = next(s for s in list_sheets(fixture.db) if s['profile_id'] == 'morthak')
        def build(values):
            return build_character_definition(profile_id='morthak', note={'title':'Morthak'},
                                              sheet=sheet, inventory=[], overrides=values)
        before = build(overrides)
        approved = copy.deepcopy(overrides)
        approved['approved_session_abilities'] = NECROMANCER_ABILITIES_5
        after = build(approved)
        for identity in ('clonagem', 'magia-da-morte'):
            with self.subTest(identity=identity):
                self.assertNotIn(identity, [a['id'] for a in before['session_abilities']])
                ability = next(a for a in after['session_abilities'] if a['id'] == identity)
                ref = 'technique:morthak:' + identity
                self.assertEqual(native_action_contract(ref, 5), ability['action_contract'])
                description = describe_action(fixture.db, ref)
                self.assertEqual(ability['action_contract'], description['contract'])
                self.assertEqual(2, len(description['costs']))
                self.assertFalse(description['executable'])
        self.assertEqual(overrides, load_definition_overrides(fixture.db, 'morthak'))
        with closing(sqlite3.connect(fixture.db)) as db:
            self.assertEqual(0, db.execute('SELECT COUNT(*) FROM combat_effect_commands').fetchone()[0])
