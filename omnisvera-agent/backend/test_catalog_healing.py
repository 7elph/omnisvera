"""Reviewed catalogue family: disposable SQLite, real HP/turn/receipt engines."""
from contextlib import closing
import json
import sqlite3
from unittest import TestCase
from unittest.mock import patch
import test_spell_engine as baseline
from app.spell_engine import cast_spell, derive_spell_mechanic
from app.spell_catalog import get_catalog_spell, list_spell_catalog


class CatalogHealingTests(TestCase):
    setUp = baseline.SpellEngineTests.setUp
    hp = baseline.SpellEngineTests.hp

    def living(self, **extra):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",
                       (json.dumps({'level': 5, 'race': 'Meio-Elfo', **extra}),))
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(current_hp=12, maximum_hp=30, temporary_hp=5)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'", (json.dumps(state),))

    def cast(self, spell='divina-curar-ferimentos-leves-r', **extra):
        return cast_spell(self.db, spell_id=spell, caster_type='token', caster_id='gob1',
                          targets=[{'type': 'character', 'id': 'vezemir'}], request_id='catalog-heal', **extra)

    def test_three_reviewed_formulas_heal_instead_of_damage(self):
        self.living()
        for suffix, formula in [('leves', '1d8'), ('graves', '2d8+1'), ('criticos', '3d8+3')]:
            spell = 'divina-curar-ferimentos-' + suffix + '-r'
            with self.subTest(spell=spell), patch('app.spell_engine.roll_formula', return_value={'total': 4}) as roll:
                self.living()
                result = cast_spell(
                    self.db, spell_id=spell, caster_type='token', caster_id='gob1',
                    targets=[{'type': 'character', 'id': 'vezemir'}], request_id='heal-' + suffix)
                self.assertEqual(16, self.hp())
                self.assertEqual(formula, roll.call_args.args[0])
                self.assertEqual(4, result['results'][0]['healing_applied'])
                self.assertEqual(0, result['results'][0]['damage_dealt'])

    def test_healing_clamps_to_maximum_and_keeps_temporary_hp(self):
        self.living()
        with patch('app.spell_engine.roll_formula', return_value={'total': 50}):
            result = self.cast()
        self.assertEqual(30, self.hp())
        self.assertEqual(18, result['results'][0]['healing_applied'])
        with closing(sqlite3.connect(self.db)) as db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(5, state['temporary_hp'])

    def test_retry_recovers_original_heal_once_without_new_roll(self):
        self.living()
        with patch('app.spell_engine.roll_formula', return_value={'total': 4}) as roll:
            a = self.cast(); b = self.cast()
        self.assertEqual(a, b); self.assertEqual(16, self.hp()); self.assertEqual(1, roll.call_count)

    def test_ineligible_character_does_not_roll_or_change_state(self):
        for change in ({'race':'Vampiro'}, {'race':'Morto-Vivo Esqueleto'}, {'construct_traits':True},
                       {'incorporeal':True}, {'extraplanar':True}, {'race':''}):
            with self.subTest(change=change):
                self.living(**change)
                with patch('app.spell_engine.roll_formula', side_effect=AssertionError('must not roll')):
                    with self.assertRaises(ValueError): self.cast()
                self.assertEqual(12, self.hp())

    def test_no_damage_or_range_override_can_convert_the_heal_or_teleport_it(self):
        self.living()
        for change in ({'damage_override':'1d20'}, {'save_override':'JPD'}, {'range_m':99}, {'range_cells':20}):
            with self.subTest(change=change), self.assertRaises(ValueError): self.cast(**change)
        self.assertEqual(12, self.hp())

    def test_single_target_only_and_physical_mode_needs_no_save_die(self):
        self.living()
        with self.assertRaises(ValueError):
            cast_spell(self.db, spell_id='divina-curar-ferimentos-leves-r',caster_type='token',caster_id='gob1',
                       targets=[{'type':'character','id':'vezemir'},{'type':'token','id':'gob1'}],request_id='heal-area')
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):
            self.cast(roll_mode='physical')
        self.assertEqual(16,self.hp())

    def test_receipt_failure_rolls_back_healing(self):
        self.living()
        with patch('app.spell_engine.roll_formula',return_value={'total':4}), patch(
                'app.spell_engine.save_receipt',side_effect=sqlite3.OperationalError('receipt unavailable')):
            with self.assertRaises(sqlite3.OperationalError):self.cast()
        self.assertEqual(12,self.hp())

    def test_changed_source_is_not_automatically_executed(self):
        self.living()
        original=get_catalog_spell('divina-curar-ferimentos-leves-r')
        with patch('app.spell_engine.get_catalog_spell',return_value={**original,'description':original['description']+' Nova regra.'}):
            with self.assertRaisesRegex(ValueError,'fonte|revis'):
                self.cast()
        self.assertEqual(12,self.hp())

    def test_catalog_exposes_effect_support_without_calling_every_spell_automated(self):
        catalog=list_spell_catalog()
        healing=next(s for s in catalog['spells'] if s['id']=='divina-curar-ferimentos-graves-r')
        self.assertEqual('healing_hp',healing['automation']['family'])
        self.assertEqual('normal',healing['automation']['mode'])
        empty=next(s for s in catalog['spells'] if not s.get('description'))
        self.assertEqual('blocked',empty['automation']['status'])
        complete=next(s for s in catalog['spells'] if s['id']=='divina-cura-completa-r')
        self.assertNotEqual('effect_automated',complete['automation']['status'])

    def test_mechanic_exposes_heal_without_inventing_reverse_damage(self):
        mechanic=derive_spell_mechanic(get_catalog_spell('divina-curar-ferimentos-criticos-r'))
        self.assertEqual('3d8+3',mechanic['healing'])
        self.assertIsNone(mechanic['damage'])

    def test_unidentified_description_preserves_legacy_parser_behavior(self):
        mechanic=derive_spell_mechanic({'name':'Explosão de teste','description':'Dura 1d4 turnos; causa 2d6 de dano.'})
        self.assertEqual('2d6',mechanic['damage']);self.assertIsNone(mechanic['healing'])

    def test_healing_eligibility_uses_race_and_traits_not_a_character_name(self):
        self.living()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO character_states(profile_id,state_json,updated_at) SELECT 'morthak',state_json,updated_at FROM character_states WHERE profile_id='vezemir'")
            db.execute("INSERT INTO character_sheets(profile_id,character_path,character_title,data_json,updated_at) SELECT 'morthak','human-fixture','Morthak humano de ensaio',data_json,updated_at FROM character_sheets WHERE profile_id='vezemir'")
            db.execute("INSERT INTO character_definition_overrides VALUES('morthak',?, 'now')",(json.dumps({'level':5,'race':'Humano'}),))
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):
            result=cast_spell(self.db,spell_id='divina-curar-ferimentos-leves-r',caster_type='token',caster_id='gob1',
                targets=[{'type':'character','id':'morthak'}],request_id='human-race-fixture')
        self.assertEqual(16,result['results'][0]['hp']['after'])

    def test_catalogued_living_token_heals_but_construct_or_undead_never_roll(self):
        for source, valid in [('goblin',True),('golem-de-ferro',False),('esqueleto',False),('efreeti',False),('elemental-do-fogo',False)]:
            with self.subTest(source=source):
                with closing(sqlite3.connect(self.db)) as db,db:
                    db.execute("UPDATE session_workspace_tokens SET sheet_json=?,current_hp=4 WHERE id='gob1'",
                               (json.dumps({'source':{'monster_id':source},'spellcaster_level':1}),))
                call=lambda:cast_spell(self.db,spell_id='divina-curar-ferimentos-leves-r',caster_type='token',caster_id='gob1',
                    targets=[{'type':'token','id':'gob1'}],request_id='heal-token-'+source)
                if valid:
                    with patch('app.spell_engine.roll_formula',return_value={'total':4}):result=call()
                    self.assertEqual(8,result['results'][0]['hp']['after'])
                else:
                    with patch('app.spell_engine.roll_formula',side_effect=AssertionError('must not roll')):
                        with self.assertRaises(ValueError):call()

    def test_combat_healing_spends_existing_action_once_and_rollback_preserves_it(self):
        import test_generic_spell_retry as retry
        self.living();retry.GenericSpellRetryTests.battle(self)
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):
            self.cast();self.cast()
            with self.assertRaises(ValueError):
                cast_spell(self.db,spell_id='divina-curar-ferimentos-graves-r',caster_type='token',caster_id='gob1',
                    targets=[{'type':'character','id':'vezemir'}],request_id='second-heal')
        self.assertEqual(1,retry.GenericSpellRetryTests.attacks_used(self));self.assertEqual(16,self.hp())

    def test_grid_touch_rejects_distant_or_missing_target_position(self):
        from app.spatial_grid import init_spatial
        self.living();init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,created_at,updated_at) VALUES('default','T','x','now','now')")
            db.execute("UPDATE session_workspace_tokens SET map_id='default' WHERE id='gob1'")
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,character_id,current_hp,maximum_hp,created_at,updated_at) VALUES('pc','character','default','V','vezemir',12,30,'now','now')")
            db.execute("INSERT INTO session_workspace_map_grids(map_id,grid_type,cols,rows,cell_size_m,origin_x,origin_y,distance_rule,version) VALUES('default','square',20,20,1.5,0,0,'chebyshev',1)")
            db.execute("INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h,version) VALUES('default','gob1',5,5,1,1,1)")
            db.execute("INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h,version) VALUES('default','pc',8,5,1,1,1)")
        with self.assertRaisesRegex(ValueError,'alcance'):self.cast()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("DELETE FROM session_workspace_entity_positions WHERE token_id='pc'")
        with self.assertRaisesRegex(ValueError,'grid'):self.cast()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h,version) VALUES('default','pc',6,5,1,1,1)")
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):result=self.cast()
        self.assertTrue(result['results'][0]['range']['checked']);self.assertEqual(16,self.hp())


import test_generic_spell_retry_api as api_baseline


class CatalogHealingApiTests(TestCase):
    setUp = baseline.SpellEngineTests.setUp
    client = api_baseline.GenericSpellRetryApiTests.client
    hp = baseline.SpellEngineTests.hp
    living = CatalogHealingTests.living

    def test_http_heal_replay_and_unauthorized_request(self):
        self.living();client=self.client()
        body={'request_id':'http-heal','caster_type':'token','caster_id':'gob1','targets':[{'type':'character','id':'vezemir'}]}
        route='/gm/compendium/spells/divina-curar-ferimentos-graves-r/cast'
        with patch('app.spell_engine.roll_formula',return_value={'total':8}) as roll:
            a=client.post(route,json=body,headers={'X-Test-Role':'gm'})
            b=client.post(route,json=body,headers={'X-Test-Role':'gm'})
        self.assertEqual(200,a.status_code,a.text);self.assertEqual(a.json(),b.json())
        self.assertEqual(20,self.hp());self.assertEqual(1,roll.call_count)
        self.assertEqual(403,client.post(route,json=body).status_code)

    def test_http_catalog_metadata_and_source_gap_block(self):
        client=self.client();catalog=client.get('/gm/compendium/spells',headers={'X-Test-Role':'gm'})
        self.assertEqual(200,catalog.status_code)
        broken=next(s for s in catalog.json()['spells'] if s['automation']['status']=='blocked')
        response=client.post('/gm/compendium/spells/'+broken['id']+'/cast',headers={'X-Test-Role':'gm'},json={
            'request_id':'blocked-source','caster_type':'token','caster_id':'gob1','targets':[{'type':'character','id':'vezemir'}]})
        self.assertEqual(400,response.status_code);self.assertEqual(30,self.hp())
