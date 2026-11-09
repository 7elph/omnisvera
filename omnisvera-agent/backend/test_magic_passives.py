"""Reviewed passive families on synthetic native sheets, rolls and commerce."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

PARENT='item-magico-braceletes-de-armadura'
COLLAR='item-magico-colar-do-comerciante'
HELM='item-magico-elmo-da-visao-da-verdade'
RING='item-magico-anel-da-conviccao'
NOW='2026-11-01T23:00:00+00:00'


class MagicPassiveTests(unittest.TestCase):
    def setUp(self):
        from test_magic_equipment import MagicEquipmentApiTests
        MagicEquipmentApiTests.setUp(self)

    def seed(self,identity,slot='Acessório',quantity=1):
        from app.player_inventory import upsert_inventory
        return upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+identity,
            item_title=identity,quantity=quantity,equipped=True,equipment_slot=slot,notes=None)

    def character(self):
        response=self.client.get('/characters/vezemir?read_only=true')
        self.assertEqual(response.status_code,200,response.text);return response.json()

    def test_bracers_have_four_concrete_priced_variants_and_reference_parent(self):
        from app.item_catalog import get_catalog_item,is_catalog_reference
        self.assertTrue(is_catalog_reference(get_catalog_item(PARENT)))
        for n in range(1,5):
            item=get_catalog_item(PARENT+'-'+str(n))
            self.assertIsNotNone(item)
            self.assertEqual(item['preco_po'],1000*n)
            self.assertEqual(item['source_parent_id'],PARENT)
            self.assertEqual(item['effect_rules'][0]['value'],n)

    def test_each_bracer_variant_applies_exact_bonus(self):
        before=self.character()['definition']['defenses']['armor_class']
        for n in range(1,5):
            with closing(sqlite3.connect(self.db)) as db,db:
                db.execute('UPDATE player_inventory SET equipped=0')
            self.seed(PARENT+'-'+str(n))
            self.assertEqual(self.character()['definition']['defenses']['armor_class'],before+n)

    def test_bracer_family_uses_highest_without_suppressing_other_armor_bonuses(self):
        self.seed('item-magico-manto-da-confusao')
        baseline=self.character()['definition']['defenses']['armor_class']
        self.seed(PARENT+'-1');self.seed(PARENT+'-4')
        self.assertEqual(self.character()['definition']['defenses']['armor_class'],baseline+4)

    def test_template_cannot_be_equipped_without_selecting_variant(self):
        self.seed(PARENT)
        r=self.client.post('/characters/vezemir/actions',json={'action':'equip_item','payload':{
            'item_path':'compendium:'+PARENT,'equipment_slot':'Acessório'},'request_id':'template-cannot-equip'})
        self.assertEqual(r.status_code,400,r.text)

    def test_merchant_collar_changes_charisma_check_not_score_attack_or_save(self):
        from app.dice_rolls import resolve_character_roll
        before=self.character();self.seed(COLLAR);after=self.character()
        self.assertEqual(after['definition']['attributes'],before['definition']['attributes'])
        self.assertEqual(after['definition']['attacks'],before['definition']['attacks'])
        self.assertEqual(after['definition']['defenses'],before['definition']['defenses'])
        old=resolve_character_roll(before['definition'],before['inventory'],'attribute','charisma')
        new=resolve_character_roll(after['definition'],after['inventory'],'attribute','charisma')
        from app.dice_rolls import parse_formula
        self.assertEqual(parse_formula(new.formula).modifier,parse_formula(old.formula).modifier+3)

    def test_helm_sees_through_reflexos_without_consuming_images_or_rolling(self):
        from app.dorn_spell_pack import redirect_hits
        self.seed(HELM,'Cabeça')
        effect={'spell':'reflexos','images_remaining':3,'intercept_chance_percent':90}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',('fixture-images','character','dorn7',json.dumps(effect)))
            with patch('app.dorn_spell_pack.roll_formula',side_effect=AssertionError('truth sight must not roll')):
                damage,result=redirect_hits(db,'character','dorn7',[{'result':'hit','damage_total':7}],NOW,observer_id='vezemir')
            self.assertEqual(damage,7);self.assertTrue(result['true_sight'])
            self.assertEqual(json.loads(db.execute("SELECT data_json FROM combat_effects WHERE id='fixture-images'").fetchone()[0])['images_remaining'],3)

    def test_mental_ward_spends_one_lifetime_gem_without_changing_hp(self):
        self.seed(RING)
        from app.magic_passives import block_mental
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            r=block_mental(db,{'type':'character','id':'vezemir'},'fear',NOW)
            self.assertEqual(r['remaining'],5)
            self.assertEqual(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0],5)

    def test_six_gems_exhaust_without_destroying_ring_or_recharging_on_rest(self):
        self.seed(RING)
        from app.magic_passives import block_mental
        from app.player_inventory import recharge_inventory
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            for n in range(5,-1,-1):self.assertEqual(block_mental(db,{'type':'character','id':'vezemir'},'fear',NOW)['remaining'],n)
            self.assertIsNone(block_mental(db,{'type':'character','id':'vezemir'},'fear',NOW))
        recharge_inventory(self.db,'inn_rest','vezemir')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(tuple(db.execute('SELECT quantity,equipped,charges_current,recharge FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()),(1,1,0,'none'))

    def test_ring_only_handles_typed_mental_attacks_and_individual_equipped_copies(self):
        self.seed(RING,quantity=2)
        from app.magic_passives import block_mental
        with closing(sqlite3.connect(self.db)) as db,db:
            db.row_factory=sqlite3.Row
            victim={'type':'character','id':'vezemir'}
            self.assertIsNone(block_mental(db,victim,'fear',NOW))
            db.execute('UPDATE player_inventory SET quantity=1,equipped=0 WHERE item_path=?',('compendium:'+RING,))
            self.assertIsNone(block_mental(db,victim,'fear',NOW))
            db.execute('UPDATE player_inventory SET equipped=1 WHERE item_path=?',('compendium:'+RING,))
            for kind in [None,'poison','petrified','paralyzed','physical']:
                self.assertIsNone(block_mental(db,victim,kind,NOW))
            self.assertIsNone(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0])

    def test_legacy_wrong_recharge_never_refills_lifetime_items(self):
        from app.player_inventory import recharge_inventory
        self.seed(RING);self.seed('item-magico-broche-escudo')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE player_inventory SET charges_current=2,charges_max=6,recharge=? WHERE item_path IN (?,?)',
                ('inn_rest','compendium:'+RING,'compendium:item-magico-broche-escudo'))
        recharge_inventory(self.db,'inn_rest','vezemir')
        response=self.client.post('/characters/vezemir/actions',json={'action':'rest_at_inn','payload':{},'request_id':'lifetime-rest-check'})
        self.assertEqual(response.status_code,200,response.text)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertTrue(all(r[0]==2 for r in db.execute('SELECT charges_current FROM player_inventory WHERE item_path IN (?,?)',('compendium:'+RING,'compendium:item-magico-broche-escudo'))))

    def test_passive_read_only_projection_and_manifest_never_emit_use_command(self):
        self.seed(RING);self.seed(HELM,'Cabeça')
        before=self.character();again=self.character()
        item=next(i for i in again['inventory'] if i['item_path']=='compendium:'+RING)
        self.assertEqual((item['charges_current'],item['charges_max'],item['recharge']),(6,6,'none'))
        self.assertEqual(before['state'],again['state'])
        from app.native_action_manifest import sheet_action_manifest
        manifest=sheet_action_manifest('vezemir',again['definition'],again['state'],again['inventory'])
        entries=[e for e in manifest if e.get('binding')=='equipped_native_passive']
        self.assertEqual(len(entries),2);self.assertTrue(all(e['execution'] is None for e in entries))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIsNone(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0])


class PassiveCommerceTests(unittest.TestCase):
    def setUp(self):
        from test_map_commerce import MapCommerceTests
        MapCommerceTests.setUp(self)

    def test_collar_and_attribute_items_share_native_haggle_math_and_retry(self):
        from app import map_commerce as shop
        from app.merchant import haggle
        from app.player_inventory import upsert_inventory
        from app.character_play import attribute_modifier
        base=haggle(self.db,character_id='vezemir',base_price_po=10,roll_mode='physical',d20=10)
        with closing(sqlite3.connect(self.db)) as db:
            original=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
        for key in [COLLAR,'item-magico-colar-do-menestrel']:
            upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+key,item_title=key,quantity=1,equipped=True,equipment_slot='Acessório',notes=None)
        enhanced=haggle(self.db,character_id='vezemir',base_price_po=10,roll_mode='physical',d20=10)
        score=original['attributes']['charisma']
        expected=attribute_modifier(score+2)+3
        self.assertEqual(enhanced['modifier'],expected)
        with patch('app.map_commerce.roll_formula',return_value={'total':10}) as rng:
            q=shop.quote(self.db,self.mid,self.owner,request_id='native-collar-bargain',character_id='vezemir',kind='buy',target_id=self.line['id'],quantity=1,negotiate=True)
            retry=shop.quote(self.db,self.mid,self.owner,request_id='native-collar-bargain',character_id='vezemir',kind='buy',target_id=self.line['id'],quantity=1,negotiate=True)
            self.assertEqual(q,retry);rng.assert_called_once()
        self.assertEqual(q['bargain']['modifier'],expected)
        self.assertEqual(q['bargain']['total'],10+expected)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0]),original)


class NativeTrueSightTests(unittest.TestCase):
    def _insert_character(self,*args):
        from test_combat import CombatAttackResolutionTests
        return CombatAttackResolutionTests._insert_character(self,*args)

    def setUp(self):
        from test_combat import CombatAttackResolutionTests
        CombatAttackResolutionTests.setUp(self)
        self.addCleanup(CombatAttackResolutionTests.tearDown,self)
        from app.player_inventory import upsert_inventory
        for owner,item,slot in [('vezemir',HELM,'Cabeça'),('raziel','item-magico-manto-da-confusao','Acessório')]:
            upsert_inventory(self.database,profile_id=owner,item_path='compendium:'+item,item_title=item,quantity=1,equipped=True,equipment_slot=slot,notes=None)

    def attack(self,key='native-sight'):
        from test_combat import CombatAttackResolutionTests,SequenceRng
        return CombatAttackResolutionTests._resolve(self,target={'type':'character','id':'raziel','name':'Raziel','armor_class':18,'current_hp':14},request_id=key,rng=SequenceRng(3))

    def test_native_preview_ignores_only_cloak_illusion_ac_not_base_armor(self):
        r=self.attack()
        self.assertEqual(r['target_ac'],16)
        self.assertEqual(r['breakdown']['illusion_ac_ignored'],2)
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute("UPDATE player_inventory SET equipped=0 WHERE profile_id='vezemir'")
        ordinary=self.attack('native-sight-off')
        self.assertEqual(ordinary['target_ac'],18)

    def test_removing_helm_invalidates_pending_preview_without_hp_loss(self):
        r=self.attack()
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute("UPDATE player_inventory SET equipped=0 WHERE profile_id='vezemir'")
        from app.combat import confirm_attack_resolution
        with self.assertRaisesRegex(ValueError,'Equipamento mudou'):
            confirm_attack_resolution(self.database,resolution_id=r['resolution_id'],requested_by_id='vezemir',requested_by_role='player')

    def test_native_confirmation_bypasses_reflexos_and_preserves_its_images(self):
        from app.combat_effects import init_effects
        from app.combat import confirm_attack_resolution
        from app.necromancer_spells import add_effect
        init_effects(self.database)
        with closing(sqlite3.connect(self.database)) as db,db:
            effect=add_effect(db,{'type':'character','id':'raziel'},'Reflexos','Ensaio',NOW,spell='reflexos',images_remaining=3,intercept_chance_percent=90)
        resolution=self.attack('native-sight-confirm')
        self.assertGreater(resolution['damage_total'],0)
        with patch('app.dorn_spell_pack.roll_formula',side_effect=AssertionError('helm bypasses image chance')):
            applied,changed=confirm_attack_resolution(self.database,resolution_id=resolution['resolution_id'],requested_by_id='vezemir',requested_by_role='player')
        self.assertTrue(changed)
        self.assertEqual(applied['damage_total'],resolution['damage_total'])
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(json.loads(db.execute('SELECT data_json FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0])['images_remaining'],3)


class NativeFearWardTests(unittest.TestCase):
    def setUp(self):
        from test_morthak_sheet import MorthakSheetTests
        MorthakSheetTests.setUp(self)
        self.addCleanup(MorthakSheetTests.tearDown,self)
        from app import main
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES('Characters/Individual/Vezemir.md','Vezemir','[]','character','[]','{}','# Vezemir','fixture')")
            db.execute('INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)',('vezemir','Characters/Individual/Vezemir.md','Vezemir','approved',json.dumps({'attributes':{'wisdom':10},'character_class':{'level':1,'saving_throw':14,'hit_points':20}}),'fixture'))
            db.execute('INSERT INTO character_states VALUES(?,?,1,?)',('vezemir',json.dumps({'current_hp':20,'maximum_hp':20,'temporary_hp':0,'resources':[],'conditions':[]}),'fixture'))
        from app.player_inventory import upsert_inventory
        upsert_inventory(self.db,profile_id='vezemir',item_path='compendium:'+RING,item_title='Anel da convicção',quantity=1,equipped=True,equipment_slot='Acessório',notes=None)

    def cast(self,key='fear-ward-native'):
        return self.client.post('/characters/morthak/techniques/aterrorizar',json={'request_id':key,
            'targets':[{'type':'character','id':'vezemir','distance_meters':1}],'position_confirmed':True})

    def test_native_fear_is_negated_before_save_and_cached_with_caster_cost(self):
        with patch('app.necromancer_spells.save_difficult',side_effect=AssertionError('ward replaces JP')):
            r=self.cast();self.assertEqual(r.status_code,200,r.text)
            retry=self.cast();self.assertEqual(retry.status_code,200,retry.text)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0],5)
            self.assertEqual(db.execute("SELECT count(*) FROM combat_effects WHERE active=1 AND target_id='vezemir'").fetchone()[0],0)
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            self.assertEqual(next(r['current'] for r in state['resources'] if r['key']=='aterrorrizar'),0)

    def test_failed_caster_ledger_rolls_back_gem_and_resource(self):
        with patch('app.combat_effects.append_session_ledger_event',side_effect=RuntimeError('isolated failure')):
            with self.assertRaises(RuntimeError):self.cast('fear-ward-rollback')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIsNone(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0])

    def test_actual_sheet_level_takes_precedence_over_declared_low_dv(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            data['character_class']['level']=5
            db.execute("UPDATE character_sheets SET data_json=? WHERE profile_id='vezemir'",(json.dumps(data),))
            db.execute("INSERT INTO character_definition_overrides VALUES('vezemir','{}','fixture')")
        response=self.client.post('/characters/morthak/techniques/aterrorizar',json={'request_id':'actual-dv-authority',
            'targets':[{'type':'character','id':'vezemir','distance_meters':1,'dv':1}],'position_confirmed':True})
        self.assertEqual(response.status_code,200,response.text)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIsNone(db.execute('SELECT charges_current FROM player_inventory WHERE item_path=?',('compendium:'+RING,)).fetchone()[0])
            self.assertEqual(db.execute("SELECT count(*) FROM combat_effects WHERE active=1 AND target_id='vezemir'").fetchone()[0],0)

    def test_legacy_numeric_levels_and_invalid_values_are_distinguished(self):
        from app.necromancer_spells import victim_hit_dice
        with closing(sqlite3.connect(self.db)) as db,db:
            for value,expected in [('5',5),('5.0',5),(True,None),('?',None),(1.5,None),(0,None),('Infinity',None)]:
                with self.subTest(value=value):
                    db.execute("INSERT OR REPLACE INTO character_definition_overrides VALUES('vezemir',?,'fixture')",(json.dumps({'level':value}),))
                    self.assertEqual(victim_hit_dice(db,{'type':'character','id':'vezemir'}),expected)


if __name__=='__main__':unittest.main()
