import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.player_inventory import init_player_inventory, upsert_inventory, list_inventory, normalize_inventory_item_mechanics, recharge_inventory
from app.vault_index import init_db


class MonsterRustTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'rust.sqlite3'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('CREATE TABLE notes(path TEXT PRIMARY KEY,title TEXT,aliases TEXT,tags TEXT,frontmatter TEXT,content TEXT,updated_at TEXT)')
            db.execute('CREATE TABLE session_workspace_tokens(id TEXT PRIMARY KEY,sheet_json TEXT,character_id TEXT,token_type TEXT)')
            db.execute('CREATE TABLE character_states(profile_id TEXT PRIMARY KEY)')
            db.execute("INSERT INTO character_states VALUES('hero')")
            db.execute('INSERT INTO session_workspace_tokens VALUES(?,?,NULL,?)',('rust',json.dumps({'source':{'monster_id':'monstro-ferrugem'}}),'monster'))
        init_player_inventory(self.path)
        self.rules=[{'id':'enchanted-edge','trigger':'while_equipped','kind':'attack_bonus','value':3,'label':'Encantamento +3'},
                    {'id':'strength-damage','trigger':'while_equipped','kind':'damage_bonus','value':2,'label':'FOR +2'}]
        self.source={'effect_rules':self.rules}
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('INSERT INTO notes(path,title,aliases,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?)',
                       ('Items/Test.md','Test','[]','[]',json.dumps(self.source),'', 'now'))
        self.item=upsert_inventory(self.path,profile_id='hero',item_path='Items/Test.md',item_title='Test',quantity=1,equipped=True,notes=None)

    def selection(self,bonus=3):
        return {'material':'metal','magical':bonus>0,'enchantment_bonus':bonus,'enhancement_rule_ids':['enchanted-edge'] if bonus else []}

    def contact(self,selection=None,die=100):
        from app.monster_rust import preview,contact
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.monster_rust.roll_formula',return_value={'total':die,'individual_results':[die]}):
            result=preview(db,'character','hero',self.item['id'],selection)
            return contact(db,'character','hero',self.item['id'],selection,expected_fingerprint=result['fingerprint'],now='later')

    def test_unknown_material_or_magic_does_not_destroy_anything(self):
        from app.monster_rust import preview
        with closing(sqlite3.connect(self.path)) as db:
            self.assertTrue(preview(db,'character','hero',self.item['id'])['needs_metadata'])
        with self.assertRaisesRegex(ValueError,'metadados'):self.contact()
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_magic_resists_ten_percent_per_bonus(self):
        result=self.contact(self.selection(),die=30)
        self.assertTrue(result['resisted']);self.assertEqual(result['bonus_after'],3)
        result=self.contact(die=31)
        self.assertFalse(result['resisted']);self.assertEqual(result['bonus_after'],2)

    def test_projection_only_reduces_selected_magic_rule_and_is_repeat_safe(self):
        self.contact(self.selection())
        raw=list_inventory(self.path,'hero')[0]
        item=normalize_inventory_item_mechanics({**raw,'effect_rules':self.rules})
        self.assertEqual([r['value'] for r in item['effect_rules']],[2,2])
        again=normalize_inventory_item_mechanics(item)
        self.assertEqual(again['effect_rules'],item['effect_rules'])
        self.assertEqual(self.rules[0]['value'],3)

    def test_attribute_binding_is_rejected_before_roll(self):
        selection=self.selection();selection['enhancement_rule_ids']=['strength-damage']
        with self.assertRaisesRegex(ValueError,'atributo|encantamento'):self.contact(selection)
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_zero_enchantment_survives_then_next_contact_destroys(self):
        self.contact(self.selection())
        self.contact();result=self.contact()
        self.assertEqual(result['bonus_after'],0);self.assertFalse(result['destroyed'])
        self.assertEqual(len(list_inventory(self.path,'hero')),1)
        result=self.contact();self.assertTrue(result['destroyed'])
        raw=list_inventory(self.path,'hero',include_empty=True)[0]
        self.assertEqual(raw['quantity'],0);self.assertFalse(raw['equipped']);self.assertIsNone(raw['equipment_slot'])

    def test_common_stack_loses_only_one_and_is_unequipped(self):
        upsert_inventory(self.path,profile_id='hero',item_path='Items/Test.md',item_title='Test',quantity=4,equipped=True,equipment_slot='Corpo a corpo',notes=None)
        self.contact(self.selection(0))
        row=list_inventory(self.path,'hero')[0]
        self.assertEqual(row['quantity'],3);self.assertFalse(row['equipped'])

    def test_magic_stack_requires_instance_split(self):
        upsert_inventory(self.path,profile_id='hero',item_path='Items/Test.md',item_title='Test',quantity=2,equipped=True,notes=None)
        with self.assertRaisesRegex(ValueError,'unidade'):self.contact(self.selection())

    def test_other_owner_is_rejected(self):
        from app.monster_rust import preview
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaisesRegex(ValueError,'inventário'):preview(db,'character','intruder',self.item['id'],self.selection())

    def test_stale_preview_does_not_apply_twice(self):
        from app.monster_rust import preview,contact
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.monster_rust.roll_formula',return_value={'total':100,'individual_results':[100]}):
            fingerprint=preview(db,'character','hero',self.item['id'],self.selection())['fingerprint']
            contact(db,'character','hero',self.item['id'],self.selection(),expected_fingerprint=fingerprint,now='now')
            with self.assertRaisesRegex(ValueError,'mudou'):contact(db,'character','hero',self.item['id'],self.selection(),expected_fingerprint=fingerprint,now='now')

    def test_source_edit_invalidates_preview_and_does_not_rebind(self):
        self.contact(self.selection())
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE notes SET frontmatter=?',(json.dumps({'effect_rules':[dict(self.rules[0],value=4),self.rules[1]]}),))
        with self.assertRaisesRegex(ValueError,'fonte'):self.contact()

    def test_rest_keeps_permanent_item_corrosion(self):
        self.contact(self.selection());before=list_inventory(self.path,'hero')[0]['_instance_condition']
        recharge_inventory(self.path,'inn_rest','hero')
        self.assertEqual(list_inventory(self.path,'hero')[0]['_instance_condition'],before)

    def test_delete_cleans_instance_extension(self):
        self.contact(self.selection())
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('DELETE FROM player_inventory WHERE id=?',(self.item['id'],))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM inventory_item_conditions').fetchone()[0],0)

    def test_nonmetal_is_immune_with_explicit_metadata(self):
        result=self.contact({'material':'nonmetal','magical':False,'enchantment_bonus':0,'enhancement_rule_ids':[]})
        self.assertTrue(result['unaffected']);self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_nonnumeric_magic_is_not_treated_as_mundane(self):
        with self.assertRaisesRegex(ValueError,'numérico'):self.contact({'material':'metal','magical':True,'enchantment_bonus':0,'enhancement_rule_ids':[]})

    def test_replacement_after_destruction_is_fresh_not_an_already_destroyed_item(self):
        self.contact(self.selection(0))
        upsert_inventory(self.path,profile_id='hero',item_path='Items/Test.md',item_title='Test',quantity=1,equipped=True,notes=None)
        self.assertNotIn('_instance_condition',list_inventory(self.path,'hero')[0])

    def test_new_magic_item_cannot_silently_join_a_corroded_stack(self):
        self.contact(self.selection())
        with self.assertRaisesRegex(ValueError,'mescle'):
            upsert_inventory(self.path,profile_id='hero',item_path='Items/Test.md',item_title='Test',quantity=2,equipped=True,notes=None)
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def record(self):
        return {'target_type':'token','target_id':'rust','actor_character_id':'hero','attack_id':'melee','result':'hit',
                'breakdown':{'attack':{'weapon_item_path':'Items/Test.md'},'strikes':[{'result':'hit','damage_total':0}],
                             'damage_profile':{'kind':'weapon'}}}

    def test_reverse_contact_needs_metadata_without_rolling_another_attack(self):
        from app.monster_rust import reverse_contact
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.monster_rust.roll_formula') as roll:
            result=reverse_contact(db,self.record(),'now')
            self.assertTrue(result[0]['manual']);self.assertEqual(result[0]['inventory_id'],self.item['id'])
            roll.assert_not_called()
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_reverse_melee_contact_reduces_known_metal_enchantment(self):
        from app.monster_rust import reverse_contact
        self.contact(self.selection(),die=1)
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.monster_rust.roll_formula',return_value={'total':100,'individual_results':[100]}) as roll:
            result=reverse_contact(db,self.record(),'now');self.assertEqual(result[0]['bonus_after'],2)
            roll.assert_called_once_with('1d100')

    def test_reverse_hit_on_illusion_and_missed_attack_do_not_touch_weapon(self):
        from app.monster_rust import reverse_contact
        for reflected in [True,False]:
            record=self.record()
            if reflected:record['breakdown']['reflection_result']={'rolls':[{'strike':0,'intercepted':True}]}
            else:record['result']='miss'
            with closing(sqlite3.connect(self.path)) as db,db:
                self.assertEqual(reverse_contact(db,record,'now'),[])

    def test_reverse_ranged_contact_does_not_destroy_the_bow(self):
        from app.monster_rust import reverse_contact
        record=self.record();record['attack_id']='ranged'
        with closing(sqlite3.connect(self.path)) as db,db:
            result=reverse_contact(db,record,'now');self.assertTrue(result[0]['manual'])
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_explicit_nonmetal_magic_without_numeric_enchantment_is_not_destroyed(self):
        self.contact({'material':'nonmetal','magical':True,'enchantment_bonus':0,'enhancement_rule_ids':[]})
        self.assertEqual(list_inventory(self.path,'hero')[0]['quantity'],1)

    def test_combat_fingerprint_changes_on_corrosion_but_not_other_owner_inventory(self):
        from app.inventory_conditions import combat_fingerprint
        with closing(sqlite3.connect(self.path)) as db:
            before=combat_fingerprint(db,'hero','token','rust')
        upsert_inventory(self.path,profile_id='bystander',item_path='Items/Test.md',item_title='Test',quantity=1,equipped=True,notes=None)
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(combat_fingerprint(db,'hero','token','rust'),before)
        self.contact(self.selection())
        with closing(sqlite3.connect(self.path)) as db:self.assertNotEqual(combat_fingerprint(db,'hero','token','rust'),before)

    def test_declared_magical_source_cannot_be_classified_mundane(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE notes SET frontmatter=?',(json.dumps({**self.source,'mechanics':{'magical':True}}),))
        with self.assertRaisesRegex(ValueError,'mágico'):self.contact(self.selection(0))

    def test_explicit_enchantment_value_cannot_be_replaced_with_smaller_number(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE notes SET frontmatter=?',(json.dumps({**self.source,'enchantment_bonus':4}),))
        with self.assertRaisesRegex(ValueError,'diverge'):self.contact(self.selection())
