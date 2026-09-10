import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.character_play import apply_character_action, list_character_events
from app.schemas import CharacterStateResponse
import test_combat as fixture


class CurrencyCounterTests(TestCase):
    def setUp(self):
        self.fixture = fixture.CombatAttackResolutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.db = self.fixture.database

    def save(self, currency="gold", value=10, expected=0, actor="gm", character="vezemir", actor_id=None):
        return apply_character_action(self.db, character_id=character,
            actor_id=actor_id or ("master" if actor == "gm" else character), actor_role=actor,
            action="set_currency", payload={"currency": currency, "value": value, "expected_balance": expected})

    def state(self):
        with closing(sqlite3.connect(self.db)) as db:
            return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])

    def test_four_balances_persist_and_gold_reuses_existing_field(self):
        for currency, field in [("gold", "coins"), ("copper", "copper_coins"), ("silver", "silver_coins"), ("platinum", "platinum_coins")]:
            self.save(currency, 20)
            self.save(currency, 7, 20, actor="player")
            self.assertEqual(7, self.state()[field])
        self.assertEqual(20, self.state()["current_hp"])
        events = list_character_events(self.db, "vezemir")
        self.assertEqual(8, len(events))
        self.assertEqual("set_currency", events[0]["event_type"])
        response = CharacterStateResponse(**self.state(), version=1, updated_at="now")
        self.assertEqual(7, response.platinum_coins)

    def test_player_cannot_increase_or_change_another_character(self):
        with self.assertRaises(PermissionError): self.save(actor="player")
        with self.assertRaises(PermissionError): self.save(actor="player", actor_id="raziel")
        self.save(value=10)
        with self.assertRaises(PermissionError): self.save(value=11, expected=10, actor="player")
        self.save(value=0, expected=10, actor="player")
        self.assertEqual(0, self.state()["coins"])

    def test_invalid_input_and_stale_balance_do_not_modify_state(self):
        for value in [-1, 1.5, True, "5", None, 2147483648]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.save(value=value)
        for currency in ["electrum", {}, None]:
            with self.assertRaises(ValueError): self.save(currency=currency)
        self.save(value=20)
        with self.assertRaises(ValueError): self.save(value=10, expected=0)
        self.assertEqual(20, self.state()["coins"])

    def test_duplicate_concurrent_submission_does_not_spend_twice(self):
        self.save(value=20)
        with ThreadPoolExecutor(2) as pool:
            replies = list(pool.map(lambda _: self.save(value=15, expected=20, actor="player"), range(2)))
        self.assertEqual(15, self.state()["coins"])
        self.assertEqual(1, sum(r["event_id"] is not None for r in replies))
        self.assertEqual(2, len(list_character_events(self.db, "vezemir")))

    def test_existing_gold_and_other_state_survive_rest(self):
        self.save(value=57)
        self.save("silver", 3)
        apply_character_action(self.db, character_id="vezemir", actor_id="master", actor_role="gm", action="rest_at_inn", payload={})
        self.assertEqual(57, self.state()["coins"])
        self.assertEqual(3, self.state()["silver_coins"])

    def test_api_rejects_player_credit_and_other_character(self):
        settings = replace(main.settings, database_path=self.db)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main, "settings", settings), patch.object(main, "_playable_character", return_value={}), closing(TestClient(main.app)) as client:
            body = {"action": "set_currency", "payload": {"currency": "gold", "value": 100, "expected_balance": 0}}
            self.assertEqual(403, client.post("/characters/vezemir/actions", json=body).status_code)
            self.assertEqual(403, client.post("/characters/raziel/actions", json=body).status_code)
