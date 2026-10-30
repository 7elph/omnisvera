"""CLI for the private AI workshop (AI-WORKSHOP-20261020).

Read-only by default: inspect/plan/report/status never create or mutate a DB.
Explicit mutations: enqueue, requeue (confirmed), tick (test), provider set,
worker start/pause/stop.
No publishing, approval, sheet/Vault writes, service installation or push.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import ai_workshop as workshop  # noqa: E402
from app import ai_workshop_adapters as adapters  # noqa: E402


def _default_db() -> Path:
    return Path(os.getenv(
        "OMNISVERA_AI_WORKSHOP_DB",
        str(BACKEND_ROOT.parent / '.autonomy' / 'runtime' / 'ai-workshop.sqlite3'),
    )).resolve()


def _default_campaign_db() -> Path:
    return Path(os.getenv(
        "OMNISVERA_DB_PATH",
        str(BACKEND_ROOT / "data" / "omnisvera_companion.sqlite3"),
    )).resolve()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _load_json(path: str | None) -> object:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_inspect(args: argparse.Namespace) -> int:
    result = workshop.status(args.db, table_state=_table_state(args))
    required = workshop.configured_min_free_ram_mb()
    free = workshop.available_memory_mb()
    result["admission"] = {
        "min_free_ram_mb": required,
        "free_ram_mb": free,
        "ram_ok": None if free is None else free >= required,
    }
    result["code_adapter"] = adapters.code_adapter_status()
    result["latency_source"] = "observed_metrics_only"
    _print(result)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    result = {
        "workshop": workshop.status(args.db),
        "stats": {queue: workshop.stats(args.db, queue=queue) for queue in workshop.QUEUES},
        "providers": workshop.provider_status(args.db)["providers"],
        "recent_jobs": workshop.list_jobs(args.db, limit=args.limit),
        "latency_source": "observed_metrics_only",
        "fixtures_are_not_production_latency": True,
    }
    _print(result)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    raw = _load_json(args.input)
    targets = raw.get("targets") if isinstance(raw, dict) else raw
    if not isinstance(targets, list):
        raise workshop.WorkshopError("plan_must_be_list")
    _print(workshop.plan_jobs(targets, max_variants=args.max_variants))
    return 0


def cmd_plan_sources(args: argparse.Namespace) -> int:
    """Plan from Codex's private metadata index; never reads or copies transcript text."""
    path = Path(args.index).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    sessions = data.get("sessions") if isinstance(data, dict) else None
    if not isinstance(sessions, list) or len(sessions) > 100:
        raise workshop.WorkshopError("invalid_source_index")
    targets = []
    for row in sessions:
        if not isinstance(row, dict) or row.get("status") != "ready":
            continue
        documents = row.get("documents")
        if not isinstance(documents, list) or not documents:
            continue
        sources = []
        for document in documents:
            if not isinstance(document, dict):
                raise workshop.WorkshopError("invalid_source_index")
            sources.append({"path": document.get("path"), "sha256": document.get("sha256")})
        revision = sources[0]["sha256"][:16]
        targets.append({
            "queue": "text",
            "entity_type": "session",
            "entity_id": str(row.get("session_id")),
            "revision": revision,
            "purpose": args.purpose,
            "priority": 10,
            "gap": True,
            "sources": sources,
        })
    _print(workshop.plan_jobs(targets, max_variants=args.max_variants))
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    payload = _load_json(args.payload_json) if args.payload_json else {}
    depends_on = [int(item) for item in (args.depends_on or "").split(",") if item.strip()]
    response = workshop.enqueue_job(
        args.db,
        queue=args.queue,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        revision=args.revision,
        purpose=args.purpose,
        request_id=args.request_id or workshop.new_request_id("enqueue"),
        priority=args.priority,
        gap=args.gap,
        depends_on=depends_on,
        variant_of=args.variant_of,
        payload=payload,
        max_variants=args.max_variants,
    )
    _print(response)
    return 0


def _table_state(args: argparse.Namespace) -> str:
    if getattr(args, "table_state", None):
        return args.table_state
    return workshop.read_table_state(args.campaign_db)


def cmd_tick(args: argparse.Namespace) -> int:
    if args.test:
        selected = adapters.test_adapters()
        if args.queue:
            selected = {args.queue: selected[args.queue]}
        table_state = args.table_state or "inactive"
    else:
        selected = adapters.default_adapters(args.campaign_db)
        table_state = _table_state(args)
    result = workshop.tick(
        args.db, selected, table_state=table_state, worker_id=args.worker_id,
        queue=args.queue, continuous=args.continuous, lease_seconds=args.lease_seconds,
        min_free_ram_mb=args.min_free_ram_mb,
    )
    _print(result)
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    if args.worker_action == "status":
        result = workshop.worker_status(args.db)
        result["code_adapter"] = adapters.code_adapter_status()
        result["free_ram_mb"] = workshop.available_memory_mb()
        from app.workshop_execution import configuration
        result["min_free_ram_mb"] = max(workshop.configured_min_free_ram_mb(), configuration()['min_free_ram_mb'])
        _print(result)
        return 0
    if args.worker_action == "pause":
        _print(workshop.set_worker_state(args.db, "paused", reason=args.reason))
        return 0
    if args.worker_action == "stop":
        _print(workshop.set_worker_state(args.db, "stopped", reason=args.reason or "manual"))
        return 0
    if args.worker_action != "start":
        raise workshop.WorkshopError("invalid_worker_action")
    return _worker_start(args)


def _worker_start(args: argparse.Namespace) -> int:
    from app.workshop_execution import configuration
    config = configuration()
    if not args.test and not config['enabled']:
        raise workshop.WorkshopError('automation_disabled')
    args.min_free_ram_mb = max(1024, args.min_free_ram_mb, config['min_free_ram_mb'])
    args.idle_seconds = max(5, args.idle_seconds, config['idle_seconds'])
    workshop.init_workshop(args.db)
    token = workshop.acquire_checkout_lock(args.lock_file, args.worker_id)
    selected = adapters.test_adapters() if args.test else adapters.default_adapters(args.campaign_db)
    workshop.set_worker_state(args.db, "running", reason="worker start")
    print(json.dumps({
        "worker": "running",
        "worker_id": args.worker_id,
        "adapters": sorted(selected),
        "test": bool(args.test),
        "db": str(args.db),
        "note": "foreground worker; pause/stop from another terminal",
    }, ensure_ascii=False), flush=True)
    final_state = "stopped"
    try:
        while True:
            state = workshop.get_worker_state(args.db)
            if state["state"] != "running":
                final_state = state["state"]
                break
            table_state = "inactive" if args.test else workshop.read_table_state(args.campaign_db)
            result = workshop.tick(
                args.db, selected, table_state=table_state, worker_id=args.worker_id,
                continuous=True, lease_seconds=args.lease_seconds, now=_now(),
                min_free_ram_mb=args.min_free_ram_mb,
            )
            if result.get("status") in {"completed", "failed"}:
                delay = 0.2
            elif result.get("status") == "blocked":
                delay = max(1.0, args.idle_seconds)
            else:
                delay = max(1.0, args.idle_seconds)
            time.sleep(delay)
    except KeyboardInterrupt:
        final_state = "stopped"
        workshop.set_worker_state(args.db, "stopped", reason="keyboard interrupt")
    finally:
        workshop.release_checkout_lock(args.lock_file, token)
        if workshop.get_worker_state(args.db)["state"] == "running":
            workshop.set_worker_state(args.db, final_state, reason="worker exit")
    return 0


def cmd_requeue(args: argparse.Namespace) -> int:
    _print(workshop.requeue_job(args.db, args.job_id, confirm=args.confirm))
    return 0


def cmd_provider(args: argparse.Namespace) -> int:
    if args.provider_action != "set":
        raise workshop.WorkshopError("invalid_provider_action")
    _print(workshop.configure_provider(
        args.db, queue=args.queue, provider=args.provider,
        documented_limit=args.documented_limit,
        configured_limit=args.configured_limit,
        observed_remaining=args.observed_remaining,
        observed_reset_at=args.observed_reset_at,
    ))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Private AI workshop queue (no publishing)")
    parser.add_argument("--db", type=Path, default=_default_db(),
                        help="workshop SQLite path (separate from campaign DB)")
    parser.add_argument("--campaign-db", type=Path, default=_default_campaign_db())
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="read-only workshop state")
    inspect.add_argument("--table-state", choices=sorted(workshop.TABLE_STATES))
    inspect.set_defaults(func=cmd_inspect)

    report = sub.add_parser("report", help="read-only metrics and recent jobs")
    report.add_argument("--limit", type=int, default=20)
    report.set_defaults(func=cmd_report)

    plan = sub.add_parser("plan", help="deterministic plan, no mutation")
    plan.add_argument("--input", required=True, help="JSON list or {'targets': [...]}")
    plan.add_argument("--max-variants", type=int, default=workshop.MAX_VARIANTS)
    plan.set_defaults(func=cmd_plan)

    plan_sources = sub.add_parser("plan-sources", help="plan text jobs from the private metadata index")
    plan_sources.add_argument("--index", default=str(BACKEND_ROOT.parent / ".autonomy" / "runtime"
                                                      / "ai-workshop-source-index.json"))
    plan_sources.add_argument("--purpose", default="session_summary_draft")
    plan_sources.add_argument("--max-variants", type=int, default=workshop.MAX_VARIANTS)
    plan_sources.set_defaults(func=cmd_plan_sources)

    enqueue = sub.add_parser("enqueue", help="explicit job insertion")
    enqueue.add_argument("--queue", required=True, choices=workshop.QUEUES)
    enqueue.add_argument("--entity-type", required=True)
    enqueue.add_argument("--entity-id", required=True)
    enqueue.add_argument("--revision", required=True)
    enqueue.add_argument("--purpose", required=True)
    enqueue.add_argument("--request-id")
    enqueue.add_argument("--priority", type=int, default=100)
    enqueue.add_argument("--gap", action="store_true")
    enqueue.add_argument("--depends-on", default="")
    enqueue.add_argument("--variant-of", type=int)
    enqueue.add_argument("--max-variants", type=int, default=workshop.MAX_VARIANTS)
    enqueue.add_argument("--payload-json")
    enqueue.set_defaults(func=cmd_enqueue)

    tick = sub.add_parser("tick", help="one bounded tick (use --test for local fixtures)")
    tick.add_argument("--test", action="store_true")
    tick.add_argument("--queue", choices=workshop.QUEUES)
    tick.add_argument("--continuous", action="store_true")
    tick.add_argument("--table-state", choices=sorted(workshop.TABLE_STATES))
    tick.add_argument("--worker-id", default="tick")
    tick.add_argument("--lease-seconds", type=int, default=300)
    tick.add_argument("--min-free-ram-mb", type=int,
                      default=workshop.configured_min_free_ram_mb())
    tick.set_defaults(func=cmd_tick)

    worker = sub.add_parser("worker", help="foreground worker control")
    worker.add_argument("worker_action", choices=["start", "pause", "stop", "status"])
    worker.add_argument("--test", action="store_true")
    worker.add_argument("--worker-id", default="ai-workshop-worker")
    worker.add_argument("--reason", default="")
    worker.add_argument("--lock-file", type=Path,
                        default=Path(os.getenv("OMNISVERA_AI_WORKSHOP_LOCK",
                                               str(BACKEND_ROOT / "data" / "ai_workshop.worker.lock"))))
    worker.add_argument("--idle-seconds", type=float, default=5.0)
    worker.add_argument("--lease-seconds", type=int, default=300)
    worker.add_argument("--min-free-ram-mb", type=int,
                        default=workshop.configured_min_free_ram_mb())
    worker.set_defaults(func=cmd_worker)

    requeue = sub.add_parser("requeue", help="explicitly requeue a parked/review job")
    requeue.add_argument("--id", dest="job_id", type=int, required=True)
    requeue.add_argument("--confirm", action="store_true")
    requeue.set_defaults(func=cmd_requeue)

    provider = sub.add_parser("provider", help="documented/configured/observed limits")
    provider.add_argument("provider_action", choices=["set"])
    provider.add_argument("--queue", required=True, choices=workshop.QUEUES)
    provider.add_argument("--provider", required=True)
    provider.add_argument("--documented-limit")
    provider.add_argument("--configured-limit", type=int)
    provider.add_argument("--observed-remaining", type=int)
    provider.add_argument("--observed-reset-at")
    provider.set_defaults(func=cmd_provider)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (workshop.WorkshopError, adapters.WorkshopAdapterError) as error:
        code = getattr(error, "code", None) or getattr(error, "message_code", None) or "error"
        _print({"error": code})
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _print({"error": workshop.scrub_secrets(str(error))[:200]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
