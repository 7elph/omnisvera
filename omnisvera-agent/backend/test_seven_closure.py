"""Focused regressions from the seven-pendency closure. No live data writes."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from app.spell_engine import derive_spell_mechanic
from app.spell_catalog import get_catalog_spell
from app.item_catalog import get_catalog_item
from app import monster_catalog

class SpellSafetyTests(unittest.TestCase):
    def test_hypnosis_target_count_is_not_damage(self):
        self.assertIsNone(derive_spell_mechanic(get_catalog_spell('arcana-hipnotismo'))['damage'])
    def test_strength_buff_dice_are_not_damage(self):
        self.assertIsNone(derive_spell_mechanic(get_catalog_spell('arcana-forca'))['damage'])
    def test_fear_duration_is_not_damage(self):
        self.assertIsNone(derive_spell_mechanic(get_catalog_spell('arcana-visao-de-cadaver'))['damage'])
    def test_explicit_damage_after_duration_uses_the_damage_dice(self):
        s={'description':'Dura 1d4 rodadas. O alvo sofre 2d6 pontos de dano.','jogada_protecao':'JPD reduz','alcance':'9 metros'}
        self.assertEqual(derive_spell_mechanic(s)['damage'],'2d6')
    def test_reversible_healing_requires_a_chosen_variant(self):
        self.assertIsNone(derive_spell_mechanic(get_catalog_spell('divina-curar-ferimentos-leves-r'))['damage'])

class CatalogDataTests(unittest.TestCase):
    def test_missing_attack_bonus_needs_explicit_source_dice(self):
        from scripts.repair_monster_attack_bonuses import source_attack_bonuses
        html='<span aria-label="Ataque: Soco" data-dice-bar-attack-param="true" data-dice-bar-instruction-param="1d20">Soco</span>'
        self.assertEqual(source_attack_bonuses(html),{'soco':0})
        self.assertEqual(source_attack_bonuses('<span>Soco (1d3)</span>'),{})
        self.assertEqual(source_attack_bonuses(html.replace('1d20','1d6')),{})
    def test_only_explicit_public_flavor_is_imported(self):
        from scripts.enrich_monster_descriptions import public_description
        html='<p>Private rules</p><p class="odo-bk-flavor public">A four-legged iron bull.</p><p class="masked">Hidden prose</p>'
        self.assertEqual(public_description(html),'A four-legged iron bull.')
        self.assertIsNone(public_description('<p class="masked">No public description</p>'))
    def test_reference_paragraphs_cannot_be_sold_as_equipment(self):
        from app.merchant import add_stock
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'referência'):
                add_stock(Path(d)/'unused.sqlite3',merchant_id='any',compendium_item_id='item-magico-categoria-pergaminhos',price_override_po=1)
            self.assertFalse((Path(d)/'unused.sqlite3').exists())
    def test_kit_name_and_weight_are_separate_without_changing_identity(self):
        item=get_catalog_item('kit-basico-arpeu-gancho-triplo-para-escalada-3-kg-5-pp')
        self.assertEqual(item['name'],'Arpéu')
        self.assertEqual(item['peso'],'3 kg')
        self.assertIn('Gancho triplo',item['description'])
    def test_rope_price_matches_explicit_table_source(self):
        item=get_catalog_item('kit-basico-corda-corda-de-15-m-que-suporta-ate-250-kg-de-peso-15-kg-1-p')
        self.assertEqual(item['preco'],'1 PO')
        self.assertEqual(item['preco_po'],1)
        self.assertEqual(item['id'],'kit-basico-corda-corda-de-15-m-que-suporta-ate-250-kg-de-peso-15-kg-1-p')
    def test_generated_art_records_the_real_provider(self):
        with tempfile.TemporaryDirectory() as d,patch.object(monster_catalog,'AI_ART_PATH',Path(d)/'art.json'):
            self.assertTrue(monster_catalog.bind_monster_ai_art('gorgon','companion-assets/bestiary/gorgon-20261026.png',attribution='Mesa Omnisvera - OpenAI imagegen'))
            monster_catalog.load_monster_catalog.cache_clear()
            try:self.assertEqual(monster_catalog.get_catalog_monster('gorgon')['image_attribution'],'Mesa Omnisvera - OpenAI imagegen')
            finally:monster_catalog.load_monster_catalog.cache_clear()

class CustomMonsterCompatibilityTests(unittest.TestCase):
    def test_text_source_cannot_crash_custom_monster_passives(self):
        import sqlite3
        from app.monster_runtime import token_monster,passive_data
        db=sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('CREATE TABLE session_workspace_tokens(id TEXT,name TEXT,sheet_json TEXT,token_type TEXT)')
        for i,source in enumerate(['session7:operator',None,[],17,{'monster_id':'troll'}]):
            db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,?,?)',(str(i),'custom',json.dumps({'source':source}),'monster'))
            if isinstance(source,dict):self.assertEqual(token_monster(db,str(i))[0]['id'],'troll')
            else:
                self.assertEqual(passive_data(db,'token',str(i)),{})
                self.assertEqual(token_monster(db,str(i))[1]['source'],source)

class CodeFallbackTests(unittest.TestCase):
    def test_cloud_failure_is_not_charged_to_opencode(self):
        from app import ai_workshop as workshop
        from app.ai_workshop_adapters import WorkshopAdapterError
        from app.workshop_execution import CodeOllamaAdapter
        def quota(job):raise WorkshopAdapterError('quota')
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'workshop.sqlite3'
            workshop.enqueue_job(db,queue='code',entity_type='module',entity_id='sample',revision='v1',purpose='audit',request_id='cloud-failure-test',payload={'provider':'opencode'})
            result=workshop.tick(db,{'code':CodeOllamaAdapter(quota)},queue='code',worker_id='fixture',ram_available_mb=2048,min_free_ram_mb=1024)
            self.assertEqual(result['status'],'failed')
            providers=workshop.provider_status(db)['providers']
            self.assertEqual([p['provider'] for p in providers],['ollama-code'])
    def test_cloud_route_is_explicit_in_status(self):
        from app.ai_workshop_adapters import code_adapter_status
        with patch('app.workshop_execution.configuration',return_value={'enabled':True,'code':True,'code_provider':'ollama-cloud'}):
            status=code_adapter_status()
        self.assertEqual(status['provider'],'ollama-cloud')
        self.assertEqual(status['cli_launch'],'disabled')
        self.assertFalse(status['executed_suggestions'])
    def test_cloud_code_analysis_stays_text_and_records_its_route(self):
        from app.workshop_execution import CodeOllamaAdapter
        job={'queue':'code','payload_json':{'sources':[]}}
        original={'status':'awaiting_approval','output':{'draft':'Sugestão para revisão'},'metrics':{'provider':'ollama','model':'gpt-oss:120b-cloud'}}
        result=CodeOllamaAdapter(lambda j:original)(job)
        self.assertFalse(result['output']['executed_suggestions'])
        self.assertEqual(result['output']['execution_route'],'ollama_cloud_code_analysis')
        self.assertEqual(result['metrics']['provider'],'ollama')
        self.assertEqual(job['queue'],'code')
