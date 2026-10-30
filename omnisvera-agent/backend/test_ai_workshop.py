"""Focused tests for the private AI workshop core (TEMP SQLite only).

No external provider, browser, worker activation, campaign mutation or heavy
suite. Clocks are controlled by passing ``now`` to every state transition.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import ai_workshop as workshop


def _now() -> datetime:
    return datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)


def _output(revision: str = "r1") -> dict:
    return {
        "sources": [{"path": "fixture.txt", "sha256": "a" * 64}],
        "revision": revision,
        "facts": [],
        "suggestions": [],
        "questions": [],
    }


class WorkshopFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "workshop.sqlite3"
        self.campaign = self.root / "campaign.sqlite3"
        workshop.init_workshop(self.db)
        self.now = _now()

    def enqueue(self, *, request_id="req-000001", queue="text", revision="r1",
                purpose="summary", gap=False, priority=100, depends_on=(),
                variant_of=None, payload=None, entity_id="s1", max_attempts=5,
                max_variants=workshop.MAX_VARIANTS):
        return workshop.enqueue_job(
            self.db, queue=queue, entity_type="session", entity_id=entity_id,
            revision=revision, purpose=purpose, request_id=request_id,
            priority=priority, gap=gap, depends_on=depends_on,
            variant_of=variant_of, payload=payload or {"sources": [
                {"path": "fixture.txt", "sha256": "a" * 64, "text": "fonte"},
            ]}, max_attempts=max_attempts, max_variants=max_variants, now=self.now,
        )

    def claim(self, *, worker="w1", queue="text", table="inactive", now=None,
              lease=300):
        return workshop.claim_next_job(
            self.db, queue=queue, worker_id=worker, table_state=table,
            lease_seconds=lease, now=now or self.now,
        )

    def finish(self, job, *, status="awaiting_approval", duration=100):
        return workshop.finish_job(
            self.db, job["id"], worker_id=job["lease_owner"],
            lease_token=job["lease_token"], status=status,
            output=_output(job["revision"]),
            metrics={"provider": "fixture", "model": "fixture", "duration_ms": duration},
            now=self.now + timedelta(seconds=1),
        )


class EnqueueAndPlanTests(WorkshopFixture):
    def test_dedupe_same_entity_revision_purpose_and_new_revision(self):
        first = self.enqueue()
        repeat = workshop.enqueue_job(
            self.db, queue="text", entity_type="session", entity_id="s1",
            revision="r1", purpose="summary", request_id="req-000002",
            payload={"sources": [{"path": "fixture.txt", "sha256": "a" * 64,
                                  "text": "fonte"}]}, now=self.now,
        )
        self.assertTrue(first["created"])
        self.assertEqual(first["job"]["id"], repeat["job"]["id"])
        self.assertFalse(repeat["created"])
        changed = self.enqueue(request_id="req-000003", revision="r2")
        self.assertNotEqual(first["job"]["id"], changed["job"]["id"])

    def test_request_id_conflict_is_rejected(self):
        self.enqueue()
        with self.assertRaises(workshop.WorkshopError) as caught:
            self.enqueue(purpose="other")
        self.assertEqual(caught.exception.code, "request_id_conflict")

    def test_plan_is_deterministic_and_puts_gap_before_variant(self):
        targets = [
            {"queue": "text", "entity_type": "session", "entity_id": "b",
             "revision": "r1", "purpose": "summary", "gap": False,
             "priority": 1, "variant_of": 7},
            {"queue": "text", "entity_type": "session", "entity_id": "a",
             "revision": "r1", "purpose": "summary", "gap": True, "priority": 99},
            {"queue": "text", "entity_type": "session", "entity_id": "a",
             "revision": "r1", "purpose": "summary", "gap": True, "priority": 99},
        ]
        before = self.db.read_bytes()
        first = workshop.plan_jobs(targets)
        second = workshop.plan_jobs(list(reversed(targets)))
        self.assertEqual(first["items"], second["items"])
        self.assertEqual(first["count"], 2)
        self.assertTrue(first["items"][0]["gap"])
        self.assertFalse(first["mutated"])
        self.assertEqual(before, self.db.read_bytes())

    def test_variant_ceiling(self):
        parent = self.enqueue()
        base = {"sources": [{"path": "fixture.txt", "sha256": "a" * 64, "text": "fonte"}]}
        self.enqueue(request_id="req-var-001", variant_of=parent["job"]["id"],
                     gap=False, payload={**base, "attempt": 1})
        self.enqueue(request_id="req-var-002", variant_of=parent["job"]["id"],
                     gap=False, payload={**base, "attempt": 2})
        with self.assertRaises(workshop.WorkshopError) as caught:
            self.enqueue(request_id="req-var-003", variant_of=parent["job"]["id"],
                         payload={**base, "attempt": 3}, max_variants=2)
        self.assertEqual(caught.exception.code, "variant_limit")
        repeat = self.enqueue(request_id="req-var-004", variant_of=parent["job"]["id"],
                              gap=False, payload={**base, "attempt": 1})
        self.assertFalse(repeat["created"])


class DependencyAndLeaseTests(WorkshopFixture):
    def test_dependency_blocks_until_parent_success(self):
        parent = self.enqueue(request_id="req-dep-001", priority=100)
        child = self.enqueue(request_id="req-dep-002", priority=1, purpose="child", depends_on=(parent["job"]["id"],))
        first = self.claim()
        self.assertEqual(first["job"]["id"], parent["job"]["id"])
        self.finish(first["job"])
        second = self.claim()
        self.assertEqual(second["job"]["id"], child["job"]["id"])

    def test_failed_dependency_parks_child(self):
        parent = self.enqueue(request_id="req-dep-010", max_attempts=1)
        child = self.enqueue(request_id="req-dep-011", purpose="child", depends_on=(parent["job"]["id"],))
        claimed = self.claim()["job"]
        workshop.apply_failure(self.db, claimed["id"], worker_id=claimed["lease_owner"],
                               lease_token=claimed["lease_token"], kind="provider_error",
                               now=self.now)
        result = self.claim()
        self.assertIsNone(result["job"])
        stored = workshop.get_job(self.db, child["job"]["id"])
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["blocked_reason"], "dependency_failed")

    def test_concurrent_claim_has_one_winner(self):
        self.enqueue()
        first = self.claim(worker="w1")
        second = self.claim(worker="w2")
        self.assertIsNotNone(first["job"])
        self.assertIsNone(second["job"])

    def test_expired_lease_recovers_without_duplicate_job(self):
        self.enqueue()
        first = self.claim(worker="w1", lease=30)["job"]
        recovered = self.claim(worker="w2", now=self.now + timedelta(seconds=31))["job"]
        self.assertEqual(first["id"], recovered["id"])
        self.assertEqual(recovered["lease_owner"], "w2")
        self.assertEqual(recovered["recoveries"], 1)
        self.assertNotEqual(first["lease_token"], recovered["lease_token"])

    def test_checkout_lock_is_exclusive_and_releasable(self):
        lock = self.root / "worker.lock"
        token = workshop.acquire_checkout_lock(lock, "w1")
        with self.assertRaises(workshop.CheckoutLockBusy):
            workshop.acquire_checkout_lock(lock, "w2")
        workshop.release_checkout_lock(lock, token)
        token2 = workshop.acquire_checkout_lock(lock, "w2")
        self.assertTrue(token2)


class PauseAndRetryTests(WorkshopFixture):
    def test_session_combat_and_unknown_suspend_claims(self):
        self.enqueue()
        for state in ("session", "combat", "unknown"):
            result = self.claim(table=state)
            self.assertIsNone(result["job"])
            self.assertIn(result["reason"], {"table_active", "table_state_unknown"})
        self.assertEqual(workshop.get_job(self.db, 1)["status"], "queued")

    def test_retry_after_is_respected(self):
        self.enqueue()
        job = self.claim()["job"]
        workshop.apply_failure(self.db, job["id"], worker_id=job["lease_owner"],
                               lease_token=job["lease_token"], kind="retry_after",
                               retry_after_seconds=60, now=self.now)
        self.assertIsNone(self.claim(now=self.now + timedelta(seconds=59))["job"])
        self.assertIsNotNone(self.claim(now=self.now + timedelta(seconds=61))["job"])

    def test_quota_reset_blocks_then_releases(self):
        self.enqueue()
        job = self.claim()["job"]
        reset = (self.now + timedelta(minutes=10)).isoformat()
        workshop.apply_failure(self.db, job["id"], worker_id=job["lease_owner"],
                               lease_token=job["lease_token"], kind="quota",
                               reset_at=reset, now=self.now)
        stored = workshop.get_job(self.db, job["id"])
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["blocked_reason"], "quota")
        self.assertIsNone(self.claim(now=self.now + timedelta(minutes=5))["job"])
        self.assertIsNotNone(self.claim(now=self.now + timedelta(minutes=11))["job"])
        providers = workshop.provider_status(self.db)["providers"]
        self.assertEqual(providers[0]["observed_reset_at"], reset)

    def test_auth_failure_is_permanent(self):
        self.enqueue()
        job = self.claim()["job"]
        workshop.apply_failure(self.db, job["id"], worker_id=job["lease_owner"],
                               lease_token=job["lease_token"], kind="auth_permanent",
                               now=self.now)
        self.assertEqual(workshop.get_job(self.db, job["id"])["status"], "failed")
        self.assertIsNone(self.claim(now=self.now + timedelta(days=1))["job"])
        self.assertTrue(workshop.provider_status(self.db)["providers"][0]["auth_failed"])

    def test_attempt_cap_and_exponential_backoff(self):
        self.enqueue(request_id="req-retry-1")
        current = self.now
        for attempt in range(5):
            claimed = self.claim(now=current)["job"]
            self.assertIsNotNone(claimed)
            workshop.apply_failure(self.db, claimed["id"], worker_id=claimed["lease_owner"],
                                   lease_token=claimed["lease_token"], kind="provider_error",
                                   now=current)
            stored = workshop.get_job(self.db, claimed["id"])
            if attempt < 4:
                self.assertEqual(stored["status"], "queued")
                self.assertIsNone(self.claim(now=current + timedelta(seconds=1))["job"])
                current = datetime.fromisoformat(stored["available_at"])
        self.assertEqual(workshop.get_job(self.db, claimed["id"])["status"], "failed")
        self.assertEqual(workshop.get_job(self.db, claimed["id"])["error_code"],
                         "attempts_exhausted")

    def test_ambiguous_timeout_goes_to_review_without_retry(self):
        self.enqueue()
        job = self.claim()["job"]
        workshop.apply_failure(self.db, job["id"], worker_id=job["lease_owner"],
                               lease_token=job["lease_token"], kind="timeout_ambiguous",
                               now=self.now)
        self.assertEqual(workshop.get_job(self.db, job["id"])["status"], "needs_review")
        self.assertIsNone(self.claim(now=self.now + timedelta(days=1))["job"])

    def test_waiting_permission_is_not_auto_approved_or_retried(self):
        self.enqueue(queue="code")
        job = self.claim(queue="code")["job"]
        workshop.apply_failure(self.db, job["id"], worker_id=job["lease_owner"],
                               lease_token=job["lease_token"], kind="waiting_permission",
                               now=self.now)
        stored = workshop.get_job(self.db, job["id"])
        self.assertEqual(stored["status"], "waiting_permission")
        self.assertIsNone(self.claim(queue="code", now=self.now + timedelta(hours=1))["job"])

    def test_config_block_does_not_auto_retry_and_requeue_is_explicit(self):
        class ConfigError(Exception):
            kind = "config"
            message_code = "provider_not_configured"

        def broken(_job):
            raise ConfigError()

        broken.uses_external_budget = False
        self.enqueue()
        blocked = workshop.tick(self.db, {"text": broken}, min_free_ram_mb=0,
                                now=self.now)
        self.assertEqual(blocked["status"], "blocked")
        later = workshop.tick(self.db, {"text": broken}, min_free_ram_mb=0,
                              now=self.now + timedelta(days=3))
        self.assertEqual(later["status"], "idle")
        with self.assertRaises(workshop.WorkshopError) as caught:
            workshop.requeue_job(self.db, blocked["job"]["id"])
        self.assertEqual(caught.exception.code, "confirmation_required")
        requeued = workshop.requeue_job(self.db, blocked["job"]["id"], confirm=True,
                                        now=self.now + timedelta(days=3))
        self.assertEqual(requeued["status"], "queued")
        finished = workshop.tick(self.db, {"text": _draft_adapter()}, min_free_ram_mb=0,
                                 now=self.now + timedelta(days=3))
        self.assertEqual(finished["status"], "completed")

    def test_ram_admission_blocks_low_or_unknown_memory(self):
        self.enqueue()
        low = workshop.tick(self.db, {"text": _draft_adapter()}, min_free_ram_mb=512,
                            ram_available_mb=100, now=self.now)
        self.assertEqual(low["status"], "paused")
        self.assertEqual(low["reason"], "insufficient_memory")
        unknown = workshop.tick(self.db, {"text": _draft_adapter()}, min_free_ram_mb=512,
                                ram_available_mb=None, now=self.now)
        self.assertEqual(unknown["reason"], "memory_unknown")
        allowed = workshop.tick(self.db, {"text": _draft_adapter()}, min_free_ram_mb=512,
                                ram_available_mb=2048, now=self.now)
        self.assertEqual(allowed["status"], "completed")


def _draft_adapter():
    def adapter(job):
        return {"status": "awaiting_approval",
                "output": _output(job["revision"]),
                "metrics": {"provider": "fixture", "model": "fixture",
                            "duration_ms": 7}}
    adapter.uses_external_budget = False
    return adapter


class TableStateTests(WorkshopFixture):
    def _campaign(self, *, session_active=0, encounter=None, old_pending=0,
                  with_clock=True):
        with closing(sqlite3.connect(self.campaign)) as connection, connection:
            connection.execute("CREATE TABLE game_sessions(id INTEGER PRIMARY KEY, status TEXT)")
            connection.execute("CREATE TABLE combat_attack_resolutions(id INTEGER PRIMARY KEY, status TEXT)")
            if session_active:
                connection.execute("INSERT INTO game_sessions VALUES(1,'active')")
            for index in range(old_pending):
                connection.execute("INSERT INTO combat_attack_resolutions VALUES(?, 'pending')",
                                   (index + 1,))
            if with_clock:
                connection.execute("CREATE TABLE combat_effect_clock(id INTEGER PRIMARY KEY, encounter_json TEXT)")
                connection.execute("INSERT INTO combat_effect_clock VALUES(1,?)",
                                   (json.dumps(encounter or {}),))

    def test_old_pending_receipts_and_residual_battle_mode_are_inactive(self):
        self._campaign(encounter={"active": False, "battle_mode": True}, old_pending=67)
        self.assertEqual(workshop.read_table_state(self.campaign), "inactive")

    def test_active_encounter_pauses_even_without_battle_mode(self):
        self._campaign(encounter={"active": True})
        self.assertEqual(workshop.read_table_state(self.campaign), "combat")

    def test_active_session_is_session_when_no_encounter(self):
        self._campaign(session_active=1, encounter={"active": False, "battle_mode": True})
        self.assertEqual(workshop.read_table_state(self.campaign), "session")

    def test_invalid_encounter_structure_is_unknown(self):
        with closing(sqlite3.connect(self.campaign)) as connection, connection:
            connection.execute("CREATE TABLE game_sessions(id INTEGER PRIMARY KEY, status TEXT)")
            connection.execute("CREATE TABLE combat_effect_clock(id INTEGER PRIMARY KEY, encounter_json TEXT)")
            connection.execute("INSERT INTO combat_effect_clock VALUES(1,'not-json')")
        self.assertEqual(workshop.read_table_state(self.campaign), "unknown")

    def test_missing_authoritative_table_is_unknown(self):
        with closing(sqlite3.connect(self.campaign)) as connection, connection:
            connection.execute("CREATE TABLE unrelated(id INTEGER)")
        self.assertEqual(workshop.read_table_state(self.campaign), "unknown")


class MetricsSecretsAndSafetyTests(WorkshopFixture):
    def test_metrics_average_p50_p95_and_sample_size(self):
        for index, duration in enumerate((100, 200, 300, 400)):
            self.enqueue(request_id=f"req-metric-{index}", purpose=f"m{index}")
            job = self.claim()["job"]
            self.finish(job, duration=duration)
        measured = workshop.stats(self.db, queue="text")
        self.assertEqual(measured["samples"], 4)
        self.assertEqual(measured["average_ms"], 250)
        self.assertEqual(measured["p50_ms"], 300)
        self.assertEqual(measured["p95_ms"], 400)
        self.assertEqual(measured["successes"], 4)

    def test_payload_and_output_do_not_store_secrets(self):
        secret = "super-secret-value-123456"
        previous = os.environ.get("AI_WORKSHOP_TEST_TOKEN")
        os.environ["AI_WORKSHOP_TEST_TOKEN"] = secret
        try:
            self.enqueue(payload={"sources": [], "note": f"token={secret}"})
            stored = workshop.get_job(self.db, 1)
            self.assertNotIn(secret, json.dumps(stored["payload_json"]))
            job = self.claim()["job"]
            output = _output(job["revision"])
            output["suggestions"] = [f"leaked {secret}"]
            finished = workshop.finish_job(
                self.db, job["id"], worker_id=job["lease_owner"],
                lease_token=job["lease_token"], status="awaiting_approval",
                output=output, now=self.now,
            )
            self.assertNotIn(secret, json.dumps(finished["output_json"]))
        finally:
            if previous is None:
                os.environ.pop("AI_WORKSHOP_TEST_TOKEN", None)
            else:
                os.environ["AI_WORKSHOP_TEST_TOKEN"] = previous

    def test_output_contract_is_required(self):
        self.enqueue()
        job = self.claim()["job"]
        with self.assertRaises(workshop.WorkshopError) as caught:
            workshop.finish_job(self.db, job["id"], worker_id=job["lease_owner"],
                                lease_token=job["lease_token"],
                                status="awaiting_approval", output={"draft": "x"},
                                now=self.now)
        self.assertEqual(caught.exception.code, "output_missing_contract")
        self.assertEqual(workshop.get_job(self.db, job["id"])["status"], "running")

    def test_tick_is_draft_only_and_does_not_touch_campaign(self):
        with closing(sqlite3.connect(self.campaign)) as connection, connection:
            connection.execute("CREATE TABLE scene_lab_proposals(id INTEGER PRIMARY KEY)")
        self.enqueue()
        result = workshop.tick(self.db, {"text": _draft_adapter()}, min_free_ram_mb=0,
                               now=self.now)
        self.assertEqual(result["job"]["status"], "awaiting_approval")
        with closing(sqlite3.connect(self.campaign)) as connection:
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM scene_lab_proposals").fetchone()[0], 0)

    def test_read_only_status_does_not_create_missing_database(self):
        missing = self.root / "missing.sqlite3"
        result = workshop.status(missing)
        self.assertFalse(result["initialized"])
        self.assertFalse(missing.exists())

    def test_relative_database_path_is_resolved_on_read(self):
        previous = os.getcwd()
        os.chdir(self.root)
        try:
            result = workshop.status(Path("workshop.sqlite3"))
        finally:
            os.chdir(previous)
        self.assertTrue(result["initialized"])


if __name__ == "__main__":
    unittest.main()
