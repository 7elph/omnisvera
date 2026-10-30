import unittest
from contextlib import closing
from app.action_cards import attach_action_cards


class ActionCardTests(unittest.TestCase):
    def setUp(self):
        self.cards = [dict(id='spell', name='Lâmina de Sangue', description='Descrição', image_path='zz_media/new.jpg', resources='private'),
                      dict(id='hidden', name='Segredo', description='private', hidden=True),
                      dict(id='Items/Adagas.md', name='Adagas de Espectro Fantasma', description='Item', image_path='zz_media/adagas.jpg')]

    def entry(self, **kwargs):
        return dict(character_id='raziel', event_kind='action', title='Raziel usou LÂMINA DE SANGUE', **kwargs)

    def test_current_art_canonical_case_and_allowlist(self):
        value = attach_action_cards([self.entry()], lambda _: self.cards)[0]
        self.assertEqual(value['title'], 'Raziel usou Lâmina de Sangue')
        self.assertEqual(set(value['action_cards'][0]), {'id', 'name', 'description', 'image_path'})
        self.assertEqual(value['action_cards'][0]['image_path'], 'zz_media/new.jpg')

    def test_free_chat_state_and_hidden_cards_unchanged(self):
        for kind in ('message', 'state'):
            value = {'event_kind': kind, 'title': 'LÂMINA DE SANGUE', 'character_id': 'raziel'}
            self.assertEqual(attach_action_cards([value], lambda _: self.cards), [value])
        value = {'event_kind': 'action', 'title': 'Segredo', 'character_id': 'raziel'}
        self.assertNotIn('action_cards', attach_action_cards([value], lambda _: self.cards)[0])

    def test_confirmed_attack_equipment_link_without_dumping_inventory(self):
        value = attach_action_cards([self.entry(detail={'breakdown': {'equipment': [{'item_path': 'Items/Adagas.md', 'role': 'weapon'}]}})], lambda _: self.cards)[0]
        self.assertEqual(len(value['action_cards']), 2)

    def test_identity_links_name_absent_from_narrative_and_caches_reads(self):
        calls = []
        result = attach_action_cards([self.entry(detail={'ability_id': 'spell'}), self.entry()], lambda key: calls.append(key) or self.cards)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(result), 2)

    def test_longest_match_does_not_duplicate_short_name(self):
        cards = self.cards + [dict(id='short', name='Sangue', description='short')]
        self.assertEqual(len(attach_action_cards([self.entry()], lambda _: cards)[0]['action_cards']), 1)

    def test_selected_night_animal_uses_its_own_art(self):
        value={'character_id':'raziel','event_kind':'action','title':'Forma da Noite: coruja'}
        card={'id':'forma-da-noite','name':'Forma da Noite','description':'Forma'}
        self.assertTrue(attach_action_cards([value],lambda _: [card])[0]['action_cards'][0]['image_path'].endswith('raziel_coruja_969cca62e9.jpg'))

    def test_inventory_history_can_resolve_the_last_consumed_item_without_readding_it(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        import sqlite3
        from app.player_inventory import init_player_inventory, list_inventory
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'inventory.db'
            init_player_inventory(path)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('raziel','session-item:1','Poção',0,0,'now')")
            self.assertEqual(list_inventory(path,'raziel'),[])
            self.assertEqual(len(list_inventory(path,'raziel',include_empty=True)),1)

    def test_visibility_filters_run_before_cards_are_loaded(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        import sqlite3
        from app.character_play import init_character_play
        from app.dice_rolls import init_dice_rolls
        from app.session_workspace import init_session_workspace
        from app.session_ledger import init_session_ledger, append_session_ledger_event, list_session_ledger
        from app.access import AccessContext
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'ledger.db'
            init_character_play(path);init_dice_rolls(path);init_session_workspace(path);init_session_ledger(path)
            with closing(sqlite3.connect(path)) as db, db:
                for visibility,character in [('table','raziel'),('gm','secret-npc'),('owner','morthak')]:
                    append_session_ledger_event(db,source_type='test',source_id=visibility,event_kind='action',actor_id=character,actor_name=character,actor_role='gm',character_id=character,title='Lâmina de Sangue',detail=None,visibility=visibility,created_at='now')
            calls=[]
            rows=list_session_ledger(path,AccessContext(mode='player',profile_id='vezemir'))
            attach_action_cards(rows,lambda key: calls.append(key) or self.cards)
            self.assertEqual(calls,['raziel'])
