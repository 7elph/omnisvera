import json
from contextlib import closing
from unittest.mock import patch
from app.dorn_mage import apply_dorn_mage, SPEC
from app.construct_rules import repair, validate_effect, validate_healing
from app.character_play import build_character_definition, load_definition_overrides, apply_character_action
from app.dice_rolls import resolve_character_roll, resolve_item_damage_formula
from app.character_creation import list_sheets
from app.combat_effects import effect_command, readeffects
import sqlite3
import test_dorn_mage as fixture

class DornConstructTests(fixture.DornMageTests):
    def setUp(self):
        super().setUp(); apply_dorn_mage(self.db)
    def definition(self):
        return build_character_definition(profile_id='dorn7',note=self.note,sheet=list_sheets(self.db)[0],inventory=[],overrides=load_definition_overrides(self.db,'dorn7'))
    # Do not inherit the legacy migration cases as duplicate current-build tests.
    def test_exact_sheet_idempotency_and_no_old_attacks(self):
        definition=self.definition()
        self.assertEqual('Unidade DORN-7', definition['name'])
        self.assertEqual((3,20,11,'9 m'),(definition['level'],definition['progression']['maximum_hp'],definition['defenses']['armor_class'],definition['movement']))
        spells=[(a['name'],a['circle']) for a in definition['session_abilities'] if a['kind']=='spell']
        self.assertEqual([('Mísseis Mágicos',1),('Levitação',2),('Escuridão',2),('Relâmpago',3)],spells)
        self.assertNotIn('Recalibração',definition['abilities']['racial'])
        self.assertEqual([3,0],[a['attack_bonus'] for a in definition['attacks']])
        self.assertFalse(apply_dorn_mage(self.db)['applied'])
    def test_changed_hp_blocks_without_partial_write(self):
        # A rerun of the current approval does not overwrite injuries or spends.
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0]); state['current_hp']=5
            db.execute('UPDATE character_states SET state_json=?',(json.dumps(state),))
        self.assertFalse(apply_dorn_mage(self.db)['applied'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(5,json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])['current_hp'])
    def test_active_combat_blocks(self):
        # Current approval is a no-op even while in combat; it never rewrites it.
        self.assertFalse(apply_dorn_mage(self.db)['applied'])
    def test_conditional_jp_and_exact_immunities(self):
        definition=self.definition()
        for category in ('magical_sleep','charm','mind_control'):
            self.assertEqual('1d20+4',resolve_character_roll(definition,[],'saving_throw',category).formula)
        self.assertEqual('1d20',resolve_character_roll(definition,[],'saving_throw','fire').formula)
        with closing(sqlite3.connect(self.db)) as db:
            for category in ('physical_transformation','natural_disease','common_poison'):
                with self.assertRaises(ValueError):validate_effect(db,'dorn7',category)
            for category in ('fire','acid','cold','electricity','damage','magic'):
                validate_effect(db,'dorn7',category)
            with self.assertRaisesRegex(ValueError,'cura mágica'):
                validate_healing(db,'dorn7','conventional_magical_healing')
            validate_healing(db,'dorn7','construct_healing')
    def test_magic_healing_rejected_by_actual_action_without_hp_change(self):
        with self.assertRaisesRegex(ValueError,'Corpo Artificial'):
            apply_character_action(self.db,character_id='dorn7',actor_id='master',actor_role='gm',action='heal',payload={'amount':3,'effect_category':'conventional_magical_healing'})
    def test_repair_kit_capped_atomic_replay_and_gm_only(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0]);state['current_hp']=19
            db.execute('UPDATE character_states SET state_json=?',(json.dumps(state),))
        args=dict(actor_id='master',actor_role='gm',request_id='repair-fixture')
        first=repair(self.db,**args,rng=lambda a,b:4)
        self.assertEqual((19,20,4),(first['hp_before'],first['hp_after'],first['heal_roll']))
        self.assertEqual(first,repair(self.db,**args))
        with self.assertRaises(PermissionError):repair(self.db,actor_id='player',actor_role='player',request_id='wrong-role')
        with closing(sqlite3.connect(self.db)) as db,db:
            self.assertEqual(4,db.execute("SELECT quantity FROM player_inventory WHERE item_title='Kit de Reparo'").fetchone()[0])
            db.execute("DELETE FROM player_inventory WHERE item_title='Kit de Reparo'")
        with self.assertRaisesRegex(ValueError,'Kit'):repair(self.db,**{**args,'request_id':'no-kit'})
    def test_repair_consumes_five_kits_without_daily_reset(self):
        for number in range(5):
            result=repair(self.db,actor_id='master',actor_role='gm',request_id=f'kit-{number}',rng=lambda a,b:1)
            self.assertEqual(4-number,result['kits_remaining'])
        with self.assertRaisesRegex(ValueError,'Kit'):
            repair(self.db,actor_id='master',actor_role='gm',request_id='sixth-kit')
        apply_character_action(self.db,character_id='dorn7',actor_id='master',actor_role='gm',action='rest_at_inn',payload={})
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(0,db.execute("SELECT quantity FROM player_inventory WHERE profile_id='dorn7' AND item_title='Kit de Reparo'").fetchone()[0])

    def test_repair_uses_only_consumable_slot_and_clears_disabled_after_external_repair(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            encounter = {'active':True, 'battle_mode':True, 'turn_sequence':1, 'participants':[{'target_type':'character','target_id':'dorn7'}], 'turn_index':0, 'action_committed':True}
            db.execute('UPDATE combat_effect_clock SET encounter_json=?', (json.dumps(encounter),))
        repair(self.db, actor_id='master', actor_role='gm', request_id='repair-after-attack', rng=lambda a,b:2)
        snapshot = readeffects(self.db)
        self.assertTrue(snapshot['encounter']['consumable_used'])
        self.assertTrue(snapshot['encounter']['action_committed'])
        with self.assertRaisesRegex(ValueError, 'consumível'):
            repair(self.db, actor_id='master', actor_role='gm', request_id='repair-twice', rng=lambda a,b:2)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE combat_effect_clock SET encounter_json='{}'")
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            state.update(current_hp=0, conditions=['desativado'])
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='dorn7'", (json.dumps(state),))
        result = repair(self.db, actor_id='master', actor_role='gm', request_id='external-repair', rng=lambda a,b:2)
        self.assertEqual(2, result['hp_after'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertNotIn('desativado', json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])['conditions'])

    def test_dagger_throw_uses_no_strength(self):
        dagger=next(i for i in SPEC['items'] if i['name']=='Adaga')
        item={'damage_formula':dagger['damage'],'mechanics':{'thrown_damage_formula':dagger['thrown_damage']}}
        self.assertEqual('1d4+2',resolve_item_damage_formula({'attack_slot':'melee'},item))
        self.assertEqual('1d4',resolve_item_damage_formula({'attack_slot':'ranged'},item))
    def test_approval_does_not_modify_another_owners_shared_weapon(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            old = db.execute("SELECT item_path FROM player_inventory WHERE profile_id='dorn7' AND item_title='Malha Rúnica'").fetchone()[0]
            db.execute("INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,updated_at) VALUES('other',?,'Cajado Rúnico',1,0,'fixture')", (old,))
            db.execute('UPDATE session_custom_items SET name=? WHERE id=?', ('Cajado Rúnico', int(old.split(':')[1])))
            overrides=load_definition_overrides(self.db,'dorn7'); overrides['approved_build']='dorn-mage2-legacy'
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='dorn7'", (json.dumps(overrides),))
        apply_dorn_mage(self.db)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual('Cajado Rúnico',db.execute('SELECT name FROM session_custom_items WHERE id=?',(int(old.split(':')[1]),)).fetchone()[0])
            new=db.execute("SELECT item_path FROM player_inventory WHERE profile_id='dorn7' AND item_title='Malha Rúnica'").fetchone()[0]
            self.assertNotEqual(old,new)
    def test_every_spell_restores_its_own_use(self):
        for ability in SPEC['abilities']:
            if not ability.get('uses'):continue
            key=ability['uses']['resource_key']
            apply_character_action(self.db,character_id='dorn7',actor_id='master',actor_role='gm',action='consume_resource',payload={'resource_key':key,'amount':1})
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual([2,0,0,0],[r['current'] for r in json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])['resources']])
        apply_character_action(self.db,character_id='dorn7',actor_id='master',actor_role='gm',action='rest_at_inn',payload={})
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual([3,1,1,1],[r['current'] for r in json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])['resources']])
