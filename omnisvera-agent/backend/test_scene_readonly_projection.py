from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

class SceneReadOnlyProjectionTests(TestCase):
    def test_roster_can_load_without_reconciling_each_sheet(self):
        from app import main
        access=main.AccessContext(mode='gm')
        with patch.object(main,'_character_ids',return_value=['morthak']), \
             patch.object(main,'_character_summary',side_effect=lambda value:value), \
             patch.object(main,'_playable_character',return_value={'id':'morthak'}) as view:
            main.playable_characters(access,read_only=True)
        view.assert_called_once_with('morthak',main.AccessContext(mode='gm'),read_only=True)

    def test_scene_inspection_never_reconciles_character_state(self):
        from app import main
        access=SimpleNamespace(mode='gm',profile_id='master')
        with patch.object(main,'scene_view',return_value={'participants':[{'character_id':'morthak'}]}), \
             patch.object(main,'scene_contract_links',return_value=[]), \
             patch.object(main,'_character_summary',side_effect=lambda value:value), \
             patch.object(main,'_playable_character',return_value={'id':'morthak'}) as view:
            main._scene_payload(23,access)
        view.assert_called_once_with('morthak',access,read_only=True)
