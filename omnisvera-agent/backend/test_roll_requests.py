from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from app.dice_rolls import (
    RollSpec, complete_roll_request, create_roll, create_roll_request,
    init_dice_rolls, list_roll_requests, list_rolls,
)


class RollRequestReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "rolls.sqlite3"
        init_dice_rolls(self.db)
        self.request, _ = self.request_roll("cf01-request-1")

    def request_roll(self, key):
        return create_roll_request(
            self.db, request_id=key, campaign_id="cf01", character_id="varkh",
            requested_by="master", spec=RollSpec("attribute", "Carisma", "1d20+3", "attribute", "charisma"),
            visibility="owner", target_value=14, target_hidden=True,
        )

    def complete(self, *, actor="varkh", key="cf01-completion-1", request=None):
        return complete_roll_request(
            self.db, request_id=(request or self.request)["id"], completion_request_id=key,
            actor_id=actor, actor_role="gm" if actor == "master" else "player", rng=lambda *_: 15,
        )

    def test_create_replay_keeps_one_request(self):
        replay, created = self.request_roll("cf01-request-1")
        self.assertFalse(created)
        self.assertEqual(replay["id"], self.request["id"])
        self.assertEqual(len(list_roll_requests(self.db)), 1)

    def test_pending_survives_new_connection_and_is_character_filtered(self):
        self.assertEqual(list_roll_requests(self.db, character_id="varkh")[0]["id"], self.request["id"])
        self.assertEqual(list_roll_requests(self.db, character_id="raziel"), [])

    def test_wrong_player_cannot_complete_pending(self):
        with self.assertRaises(PermissionError):
            self.complete(actor="raziel")
        self.assertEqual(list_rolls(self.db), [])

    def test_completion_preserves_modifier_and_provenance(self):
        roll, created = self.complete()
        self.assertTrue(created)
        self.assertEqual((roll["individual_results"], roll["modifier"], roll["total"]), ([15], 3, 18))
        self.assertEqual((roll["source"], roll["source_id"], roll["actor_id"]), ("roll_request", str(self.request["id"]), "varkh"))
        request = list_roll_requests(self.db, include_completed=True)[0]
        self.assertEqual(request["roll_event_id"], roll["id"])
        self.assertEqual(request["completed_by"], "varkh")
        self.assertGreaterEqual(request["completed_at"], request["created_at"])

    def test_lost_response_retry_returns_same_event(self):
        first, _ = self.complete()  # The client loses this response.
        replay, created = self.complete()
        self.assertFalse(created)
        self.assertEqual(first, replay)
        self.assertEqual(len(list_rolls(self.db)), 1)

    def test_wrong_player_cannot_replay_completed_request(self):
        self.complete()
        with self.assertRaises(PermissionError):
            self.complete(actor="raziel")

    def test_different_completion_key_cannot_roll_again(self):
        self.complete()
        with self.assertRaises(ValueError):
            self.complete(key="cf01-another-key")
        self.assertEqual(len(list_rolls(self.db)), 1)

    def test_concurrent_completion_never_creates_two_rolls(self):
        def attempt(_):
            try:
                return self.complete()
            except ValueError as error:
                self.assertIn("processada", str(error))
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(attempt, range(4)))
        self.assertTrue(any(result is not None for result in results))
        self.assertEqual(len(list_rolls(self.db)), 1)
        self.complete()  # A later retry must recover the successful response.

    def test_gm_can_still_complete_request(self):
        roll, _ = self.complete(actor="master")
        self.assertEqual(roll["actor_role"], "gm")

    def test_recovery_path_checks_owner_before_returning_event(self):
        roll, _ = self.complete()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE dice_roll_requests SET status='processing',roll_event_id=NULL,completed_at=NULL")
        with self.assertRaises(PermissionError):
            self.complete(actor="raziel")
        recovered, created = self.complete()
        self.assertFalse(created)
        self.assertEqual(recovered["id"], roll["id"])

    def test_completion_key_cannot_link_an_unrelated_roll(self):
        create_roll(self.db, request_id="cf01-completion-1", campaign_id="cf01", character_id="varkh",
                    actor_id="varkh", actor_role="player", roll_type="free", label="Outra rolagem",
                    formula="1d6", visibility="table")
        with self.assertRaises(ValueError):
            self.complete()
        self.assertEqual(list_roll_requests(self.db)[0]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
