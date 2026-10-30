from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.access import AccessContext
from app.character_play import init_character_play
from app.dice_rolls import complete_roll_request, init_dice_rolls
from app.loot import (
    _expand_digital_rewards,
    LootConflictError,
    distribute_loot,
    init_loot,
    list_loot,
    parse_treasure_code,
    finalize_requested_loot,
    resolve_requested_token_loot,
    resolve_token_loot,
    reveal_loot,
)
from app.player_inventory import init_player_inventory, list_inventory
from app.session_ledger import init_session_ledger, list_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token


class SequenceRng:
    def __init__(self, *values: int):
        self.values = iter(values)

    def __call__(self, minimum: int, maximum: int) -> int:
        value = next(self.values)
        if not minimum <= value <= maximum:
            raise AssertionError(f"{value} fora de {minimum}..{maximum}")
        return value


class LootResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.database = Path(self.temporary.name) / "loot.sqlite3"
        init_character_play(self.database)
        init_dice_rolls(self.database)
        init_player_inventory(self.database)
        init_session_workspace(self.database)
        init_session_ledger(self.database)
        init_loot(self.database)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("vezemir", json.dumps({"current_hp": 20, "maximum_hp": 20}), "2026-01-01T00:00:00+00:00"),
            )
        self.token = save_workspace_token(
            self.database, token_type="monster", name="Orc", latitude=50, longitude=50,
            current_hp=0, maximum_hp=8, sheet={"treasure": "Q (G)", "armor_class": 14},
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_parser_distinguishes_carried_lair_combinations_and_multiplier(self) -> None:
        self.assertEqual(
            [
                {"code": "V", "scope": "carried", "multiplier": 3},
                {"code": "B", "scope": "lair", "multiplier": 1},
                {"code": "C", "scope": "lair", "multiplier": 1},
            ],
            parse_treasure_code("V×3 ( B+C )"),
        )
        self.assertEqual(
            [{"code": "U", "scope": "lair", "multiplier": 1}],
            parse_treasure_code("- ( U )"),
        )

    def test_nonmagical_subtables_resolve_equipment_valuable_and_gem(self) -> None:
        rewards, rolls = _expand_digital_rewards(
            [
                {"id": "r1", "kind": "equipment", "name": "Equipamento", "quantity": 1},
                {"id": "r2", "kind": "valuable", "name": "Objeto", "quantity": 1},
                {"id": "r3", "kind": "gem", "name": "Gema", "quantity": 1},
            ],
            [],
            SequenceRng(3, 3, 3, 4, 1, 1, 6, 6, 3, 4, 6, 6, 3, 1),
        )
        self.assertEqual(["Tochas (1d4)", "Estatueta em Bronze", "Joia"], [item["name"] for item in rewards])
        self.assertIn("700 PO", rewards[1]["gm_notes"])
        self.assertIn("500 PO", rewards[2]["gm_notes"])
        self.assertEqual(8, len(rolls))

    def test_digital_draft_does_not_reveal_then_reveal_is_idempotent(self) -> None:
        resolution, created = resolve_token_loot(
            self.database, request_id="loot-resolve-orc-1", token_id=self.token["id"],
            scope="carried", roll_mode="digital", rng=SequenceRng(2, 3, 4),
        )
        self.assertTrue(created)
        self.assertEqual("draft", resolution["status"])
        self.assertEqual(9, resolution["rewards"][0]["quantity"])
        self.assertEqual([], list_loot(self.database, AccessContext(mode="player", profile_id="vezemir")))

        revealed, first = reveal_loot(self.database, resolution["resolution_id"])
        repeated, second = reveal_loot(self.database, resolution["resolution_id"])
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual("revealed", repeated["status"])
        player_loot = list_loot(self.database, AccessContext(mode="player", profile_id="vezemir"))
        self.assertEqual(1, len(player_loot))
        self.assertEqual([], player_loot[0]["rolls"])
        entries = [entry for entry in list_session_ledger(self.database, AccessContext(mode="gm")) if entry["source_type"] == "loot_reveal"]
        self.assertEqual(1, len(entries))
        self.assertEqual(revealed["reveal_ledger_id"], entries[0]["id"])

    def test_distribution_grants_once_and_reuses_result_on_retry(self) -> None:
        resolution, _ = resolve_token_loot(
            self.database, request_id="loot-resolve-orc-2", token_id=self.token["id"],
            scope="carried", roll_mode="digital", rng=SequenceRng(1, 1, 1),
        )
        reveal_loot(self.database, resolution["resolution_id"])
        allocation = [{"reward_id": resolution["rewards"][0]["id"], "character_id": "vezemir", "quantity": 3}]
        distributed, first = distribute_loot(
            self.database, resolution_id=resolution["resolution_id"], request_id="loot-distribute-orc-2", allocations=allocation,
        )
        repeated, second = distribute_loot(
            self.database, resolution_id=resolution["resolution_id"], request_id="loot-distribute-orc-2", allocations=allocation,
        )
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual("distributed", repeated["status"])
        self.assertEqual([], list_inventory(self.database, "vezemir"))
        with closing(sqlite3.connect(self.database)) as db:
            state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['silver_coins'], 3)
            self.assertEqual(db.execute("SELECT version FROM character_states WHERE profile_id='vezemir'").fetchone()[0], 2)
        entries = [entry for entry in list_session_ledger(self.database, AccessContext(mode="gm")) if entry["source_type"] == "loot_distribution"]
        self.assertEqual(1, len(entries))
        self.assertEqual(distributed["distribution_ledger_id"], entries[0]["id"])

    def test_all_coin_denominations_credit_wallet_but_relic_stays_inventory(self):
        from app.loot import update_loot_rewards
        resolution, _ = resolve_token_loot(self.database, request_id='all-coins-loot',
            token_id=self.token['id'], scope='carried', roll_mode='digital', rng=SequenceRng(1,1,1))
        rewards = [dict(id=kind, kind=kind, name=kind, quantity=2) for kind in ['pc','pp','po','pl']]
        rewards += [dict(id='cache', kind='currency', name='Peças de ouro', quantity=20),
                    dict(id='relic', kind='item', name='Moeda Misteriosa', quantity=1)]
        update_loot_rewards(self.database, resolution['resolution_id'], rewards)
        reveal_loot(self.database, resolution['resolution_id'])
        allocations = [dict(reward_id=r['id'],character_id='vezemir',quantity=r['quantity']) for r in rewards]
        for key in ['all-coins-dist', 'all-coins-retry']:
            distribute_loot(self.database, resolution_id=resolution['resolution_id'], request_id=key, allocations=allocations)
        with closing(sqlite3.connect(self.database)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
        self.assertEqual([state[k] for k in ['copper_coins','silver_coins','coins','platinum_coins']], [2,2,22,2])
        self.assertEqual([i['item_title'] for i in list_inventory(self.database,'vezemir')], ['Moeda Misteriosa'])

    def test_legacy_coin_recovery_requires_evidence_preserves_other_state_and_retries(self):
        from app.currency_recovery import recover_coin_loot
        from app.player_inventory import upsert_inventory
        from app.session_ledger import append_session_ledger_event
        with closing(sqlite3.connect(self.database)) as db, db:
            cursor=db.execute("INSERT INTO session_custom_items(name,item_type,effects_json,usable,created_at,updated_at) VALUES('Peças de ouro','currency','[]',0,'now','now')")
            iid=cursor.lastrowid
        path=f'session-item:{iid}'
        upsert_inventory(self.database,profile_id='vezemir',item_path=path,item_title='Peças de ouro',quantity=20,equipped=False,notes='Saques antigos')
        kwargs=dict(profile_id='vezemir',item_path=path,quantity=20,expected_purse=dict(coins=0,silver_coins=0,copper_coins=0,platinum_coins=0))
        with self.assertRaises(ValueError):recover_coin_loot(self.database,**kwargs)
        with closing(sqlite3.connect(self.database)) as db, db:
            append_session_ledger_event(db,source_type='loot_distribution',source_id='old-loot',event_kind='treasure',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,title='Saques antigos',detail=dict(created_item_ids={'gold':iid},allocations=[dict(reward_id='gold',character_id='vezemir',quantity=20)]),visibility='table',created_at='now')
        with self.assertRaises(ValueError):recover_coin_loot(self.database,**{**kwargs,'expected_purse':dict(coins=1)})
        with self.assertRaises(ValueError):recover_coin_loot(self.database,**kwargs,restored_purse=dict(coins=99,silver_coins=0,copper_coins=0,platinum_coins=0))
        result=recover_coin_loot(self.database,**kwargs)
        self.assertEqual(result['after']['coins'],20)
        self.assertTrue(recover_coin_loot(self.database,**kwargs)['replayed'])
        self.assertEqual([], list_inventory(self.database,'vezemir'))
        with closing(sqlite3.connect(self.database)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_hp'],20)
            self.assertEqual(state['coins'],20)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='currency_recovery'").fetchone()[0],1)

    def test_lair_is_generated_once_and_living_token_is_rejected(self) -> None:
        lair, created = resolve_token_loot(
            self.database, request_id="loot-lair-cave-1", token_id=self.token["id"], scope="lair",
            lair_id="caverna-orcs", roll_mode="quick",
        )
        repeated, created_again = resolve_token_loot(
            self.database, request_id="loot-lair-cave-2", token_id=self.token["id"], scope="lair",
            lair_id="caverna-orcs", roll_mode="quick",
        )
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(lair["resolution_id"], repeated["resolution_id"])

        living = save_workspace_token(
            self.database, token_type="monster", name="Orc vivo", latitude=40, longitude=40,
            current_hp=1, maximum_hp=8, sheet={"treasure": "Q"},
        )
        with self.assertRaises(LootConflictError):
            resolve_token_loot(
                self.database, request_id="loot-living-orc", token_id=living["id"], scope="carried", roll_mode="quick",
            )

    def test_requested_roll_becomes_loot_only_after_player_completes_it(self) -> None:
        resolution, created = resolve_requested_token_loot(
            self.database, request_id="loot-requested-orc", token_id=self.token["id"],
            scope="carried", roller_character_id="vezemir",
        )
        self.assertTrue(created)
        self.assertEqual("requested", resolution["roll_mode"])
        self.assertEqual([], resolution["rewards"])
        self.assertEqual(1, len(resolution["pending_requests"]))
        with self.assertRaises(LootConflictError):
            finalize_requested_loot(self.database, resolution["resolution_id"])
        with self.assertRaises(LootConflictError):
            reveal_loot(self.database, resolution["resolution_id"])

        request = resolution["pending_requests"][0]
        complete_roll_request(
            self.database, request_id=request["roll_request_id"], completion_request_id="loot-player-roll-1",
            actor_id="vezemir", actor_role="player", rng=SequenceRng(2, 3, 4),
        )
        finalized, first = finalize_requested_loot(self.database, resolution["resolution_id"])
        repeated, second = finalize_requested_loot(self.database, resolution["resolution_id"])
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(9, finalized["rewards"][0]["quantity"])
        self.assertEqual(finalized["rewards"], repeated["rewards"])


if __name__ == "__main__":
    unittest.main()
