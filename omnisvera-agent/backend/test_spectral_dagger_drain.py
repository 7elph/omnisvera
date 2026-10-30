import json
import sqlite3
from contextlib import closing

from test_hemomante_techniques import TechniqueFixture
from test_combat import SequenceRng
from app.combat import resolve_attack, confirm_attack_resolution


class SpectralDaggerDrainTests(TechniqueFixture):
    def attack(self, slot='melee', d20=15, path='Items/Adagas de Espectro Fantasma.md', explicit=False, boost=0):
        weapon = dict(item_path=path, item_title='Adagas de Espectro Fantasma',
            quantity=1, equipped=True, damage_formula='1d4', equipment_slot='', effect_rules=[])
        definition = dict(attacks=[dict(id=slot, name=slot, attack_bonus=3,
            damage='1d4', weapon_item_path=path)], active_effects=[], item_effects={})
        record, _ = resolve_attack(self.db, request_id='spectral-001', actor_character_id='raziel',
            actor_name='Raziel', requested_by_id='raziel', requested_by_role='player',
            definition=definition, inventory=[weapon], attack_id=slot,
            weapon_item_path=path if explicit else None,
            target=dict(type='token', id=self.wounded['id'], name='Lobo', armor_class=10, current_hp=6),
            blood_boost=boost,roll_mode='physical', physical_d20=d20, rng=SequenceRng(*([4]*(boost+1))))
        return record

    def confirm(self, record):
        return confirm_attack_resolution(self.db, resolution_id=record['resolution_id'],
            requested_by_id='raziel', requested_by_role='player')

    def test_optional_boost_costs_on_confirmation_and_heals_only_actual_damage(self):
        preview=self.attack(boost=2)
        self.assertEqual(12,preview['damage_total'])
        self.assertEqual(2,preview['breakdown']['resource_cost']['amount'])
        confirmed,_=self.confirm(preview)
        self.assertEqual(6,confirmed['breakdown']['drain_result']['healed'])
        self.assertEqual(6,confirmed['breakdown']['drain_result']['drained'])
        self.confirm(preview)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            self.assertEqual(3,state['resources'][0]['current'])

    def test_boost_on_miss_still_spends_without_healing(self):
        preview=self.attack(d20=2,boost=2);self.assertEqual(0,preview['damage_total'])
        self.confirm(preview)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            self.assertEqual(3,state['resources'][0]['current']);self.assertEqual(10,state['current_hp'])

    def test_melee_heals_only_on_confirmation_and_replay_does_not_duplicate(self):
        record = self.attack()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(10, json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])['current_hp'])
        confirmed, applied = self.confirm(record)
        self.assertTrue(applied)
        self.assertEqual(4, confirmed['breakdown']['drain_result']['healed'])
        self.assertEqual(14, confirmed['breakdown']['drain_result']['hp_after'])
        replay, applied = self.confirm(record)
        self.assertFalse(applied)
        self.assertEqual(confirmed, replay)

    def test_ranged_explicit_weapon_also_heals(self):
        confirmed, _ = self.confirm(self.attack(slot='ranged', explicit=True))
        self.assertEqual(4, confirmed['breakdown']['drain_result']['healed'])

    def test_miss_does_not_heal(self):
        confirmed, _ = self.confirm(self.attack(d20=1))
        self.assertEqual(0, confirmed['breakdown']['drain_result']['healed'])

    def test_overkill_and_maximum_hp_cap_healing(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=2 WHERE id=?', (self.wounded['id'],))
            row = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            row['current_hp'] = 15
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(row),))
        confirmed, _ = self.confirm(self.attack())
        self.assertEqual(2, confirmed['breakdown']['drain_result']['drained'])
        self.assertEqual(1, confirmed['breakdown']['drain_result']['healed'])
        self.assertEqual(16, confirmed['breakdown']['drain_result']['hp_after'])

    def test_other_weapon_does_not_gain_drain_from_display_name(self):
        record = self.attack(path='Items/Adaga.md')
        self.assertFalse(record['breakdown']['life_drain'])
        confirmed, _ = self.confirm(record)
        self.assertNotIn('drain_result', confirmed['breakdown'])

    def test_zero_hp_cannot_revive_and_failed_confirmation_rolls_back_damage(self):
        record = self.attack()
        with closing(sqlite3.connect(self.db)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['current_hp'] = 0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(state),))
        with self.assertRaisesRegex(ValueError, '0 PV'):
            self.confirm(record)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(6, db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?', (self.wounded['id'],)).fetchone()[0])
