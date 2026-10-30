import unittest
from unittest.mock import patch
from dataclasses import replace
from app import main
from app.access import AccessContext
import test_battle_mode as fixture


class ActiveEffectVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.BattleModeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.settings = replace(main.settings, database_path=self.fixture.db,
            player_profiles={'vezemir': {'character_path': 'Vezemir.md'}, 'morthak': {'character_path': 'Morthak.md'}})
        self.card = dict(id='velocidade', name='Velocidade', description='Público', image_path='speed.jpg')

    def view(self, snapshot):
        with patch.object(main, 'settings', self.settings), patch.object(main, '_character_ids', return_value=['vezemir']), \
             patch.object(main, '_session_action_catalog', return_value=[self.card]):
            return main._combat_snapshot_for_access(snapshot, AccessContext(mode='player', profile_id='morthak'))

    def test_public_icons_do_not_disclose_another_players_raw_effect(self):
        effect = dict(id='e1', target_type='character', target_id='vezemir', label='Velocidade',
            source='Velocidade (Vezemir)', duration='rounds', rounds=3, modifiers={'attack_bonus': 2}, private_notes='secret')
        view = self.view(dict(effects=[effect], encounter={}, round=1, version=1))
        self.assertEqual(view['effects'], [])
        self.assertEqual(view['active_effect_icons'][0]['target_id'], 'vezemir')
        self.assertNotIn('private_notes', str(view))
        secret = {**effect, 'target_type': 'token', 'target_id': 'hidden-token'}
        self.assertEqual(self.view(dict(effects=[secret], encounter={}, round=1, version=1))['active_effect_icons'], [])

    def test_real_three_round_expiration_and_manual_removal(self):
        self.fixture.command('apply', target_type='character', target_id='vezemir', label='Velocidade',
            source='Velocidade (Vezemir)', duration='rounds', rounds=3, modifiers={})
        from app.combat_effects import readeffects
        self.assertEqual(len(self.view(readeffects(self.fixture.db))['active_effect_icons']), 1)
        for expected in [2, 1, None]:
            snapshot = self.fixture.command('round')
            icons = self.view(snapshot)['active_effect_icons']
            if expected is None:
                self.assertEqual(icons, [])
            else:
                self.assertEqual(icons[0]['rounds'], expected)
        self.fixture.command('apply', target_type='character', target_id='vezemir', label='Velocidade',
            source='Velocidade (Vezemir)', duration='manual', modifiers={})
        snapshot = readeffects(self.fixture.db)
        snapshot = self.fixture.command('remove', id=snapshot['effects'][0]['id'])
        self.assertEqual(self.view(snapshot)['active_effect_icons'], [])

    def test_map_spell_overlay_excludes_hidden_actors_and_private_effect_fields(self):
        visible=dict(id='reflex',target_type='character',target_id='dorn7',spell='reflexos',
            images_remaining=3,map_id='arena',private_notes='secret')
        hidden={**visible,'id':'hidden','target_type':'token','target_id':'hidden-npc'}
        old_map={**visible,'id':'other','map_id':'other-map'}
        workspace={'map':{'id':'arena'},'tokens':[{'id':'dorn-pin','character_id':'dorn7'}]}
        with patch.object(main,'get_workspace_snapshot',return_value=workspace):
            result=self.view(dict(effects=[visible,hidden,old_map],encounter={},version=1))
        self.assertEqual(['reflex'],[e['id'] for e in result['map_spell_effects']])
        self.assertNotIn('private_notes',str(result))
