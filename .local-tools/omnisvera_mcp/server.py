from __future__ import annotations

import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .adapters.git import GitAdapter
from .adapters.companion import CompanionAdapter
from .adapters.vault import VaultAdapter
from .adapters.football import FootballWorldAdapter, HttpFootballDataProvider
from .adapters.crypto import CryptoWorldAdapter, CoinGeckoProvider
from .core.context import CallContext
from .core.handoff import HandoffService
from .core.health import HealthService
from .core.registry import RegisteredTool, ToolRegistry
from .memory import MemoryStore, SQLiteAuditSink
from .resources import RegisteredResource, ResourceRegistry
from .search.coordinator import SearchCoordinator
from .search.lexical import LexicalIndex
from .search.semantic import OllamaSemanticBackend
from .tools.existing import ExistingToolHandlers
from . import epistemic
from .world import WorldRegistry, WorldModelRegistry, CoreStateVectorBuilder
from .manifest import generate_manifest
from .bootstrap import generate_bootstrap


ContextFactory = Callable[[], CallContext]


from .ops import OPERATIONAL_SIGNAL_IDS as WORLD_CONTEXT_OPERATIONAL


def _build_world_context(
    memory: MemoryStore,
    worlds: WorldRegistry,
    model_builders: WorldModelRegistry,
    *,
    world_id: str,
    lookback_hours: int = 24,
) -> dict:
    """Aggregated read-only view of a world for AI consumption.

    No persistence, no inference without provenance, bounded payload.
    """
    if not world_id:
        raise ValueError("world_id is required")
    if not 1 <= lookback_hours <= 168:
        raise ValueError("lookback_hours must be between 1 and 168")
    # Verify world exists (raises KeyError → caller surfaces as error)
    adapter = worlds.get(world_id)
    descriptor = adapter.describe()
    health: dict = {}
    try:
        health = adapter.health()  # type: ignore
        if not isinstance(health, dict):
            health = {"status": str(health)}
    except Exception:
        health = {"status": "unknown"}

    now_iso = datetime.now(timezone.utc).isoformat()

    # Current domain state (latest per key, domain only)
    current_domain = memory.current_state_for_world(
        world_id, operational_ids=WORLD_CONTEXT_OPERATIONAL, limit=200
    )
    # Operational current (separate)
    with contextlib.closing(memory._connect()) as conn:  # type: ignore
        rows = conn.execute(
            "SELECT id, world_id, signal_id, entity_ref, schema, value_json, value_type, unit, observed_at "
            "FROM signal_observations WHERE world_id=? ORDER BY observed_at DESC LIMIT 200",
            (world_id,),
        ).fetchall()
        operational_current: list[dict] = []
        seen_op: set[tuple[str, str | None]] = set()
        for r in rows:
            sid = r["signal_id"]
            if sid not in WORLD_CONTEXT_OPERATIONAL:
                continue
            key = (sid, r["entity_ref"])
            if key in seen_op:
                continue
            seen_op.add(key)
            operational_current.append({
                "signal_id": sid,
                "entity_ref": r["entity_ref"],
                "value": json.loads(r["value_json"]),
                "value_type": r["value_type"],
                "unit": r["unit"],
                "observed_at": r["observed_at"],
            })

    # Entities: distinct from current domain + open predictions subjects
    entities_set: set[str] = set()
    for s in current_domain:
        if s.get("entity_ref"):
            entities_set.add(s["entity_ref"])  # type: ignore
    # Recent changes (domain only)
    recent_changes = memory.recent_domain_changes(
        world_id, operational_ids=WORLD_CONTEXT_OPERATIONAL,
        lookback_hours=lookback_hours, limit=20,
    )
    # Patterns (domain-derived, bounded)
    try:
        patterns = memory.patterns_for_world(world_id, limit=20)
    except Exception:
        patterns = []
    patterns = patterns[:20]

    # Open predictions for this world
    try:
        open_preds = memory.list_predictions(domain=world_id, status="open", limit=20)
    except Exception:
        open_preds = []
    open_predictions = []
    for p in open_preds[:20]:
        open_predictions.append({
            "prediction_id": p.get("id"),
            "subject_ref": p.get("subject_ref"),
            "claim": p.get("claim"),
            "probability": p.get("probability"),
            "horizon": p.get("horizon"),
            "predictor_id": p.get("predictor_id"),
            "predictor_version": p.get("predictor_version"),
            "created_at": p.get("created_at"),
        })
        if p.get("subject_ref"):
            entities_set.add(p["subject_ref"])  # type: ignore

    # Recent outcomes
    try:
        recent_outcomes = memory.recent_outcomes_for_world(world_id, limit=20)
    except Exception:
        recent_outcomes = []

    # Model — compact summary only
    model_summary: dict | None = None
    if current_domain:
        try:
            # reuse builder helper with domain signals only
            signals_for_model = memory.signals_for_world(world_id, limit=200)
            # filter operational out
            signals_for_model = [s for s in signals_for_model if s.get("signal_id") not in WORLD_CONTEXT_OPERATIONAL]
            patterns_for_model = memory.patterns_for_world(world_id, limit=20)
            builder = model_builders.get("core.state-vector")
            model = builder.build(world_id=world_id, signals=signals_for_model, patterns=patterns_for_model, query={"world_id": world_id})
            md = model.as_dict()
            model_summary = {
                "model_id": md.get("model_id"),
                "created_at": md.get("created_at"),
                "schema": md.get("schema"),
                "builder_id": md.get("builder_id"),
                "builder_version": md.get("builder_version"),
                "signal_count": len(md.get("signal_refs", [])),
                "pattern_count": len(md.get("pattern_refs", [])),
                "entity_count": len(md.get("state", {}).get("entities", [])),
                "limitations": md.get("limitations", [])[:5],
            }
        except Exception:
            model_summary = None

    # Freshness & limitations
    limitations: list[str] = []
    freshness_info: dict[str, object] = {}
    last_run = None
    try:
        last_run = memory.scheduler_freshness_for_world(world_id)
    except Exception:
        pass
    # last observation timestamp
    last_observed: str | None = None
    if current_domain:
        last_observed = max(s.get("observed_at", "") for s in current_domain)
    elif operational_current:
        last_observed = max(s.get("observed_at", "") for s in operational_current)

    # Data age
    data_age_seconds: float | None = None
    if last_observed:
        try:
            lo = last_observed.replace("Z", "+00:00")
            dt = datetime.fromisoformat(lo)
            data_age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
        except Exception:
            pass

    # Distinguish poll time vs informational change time (audit 3)
    last_domain_change_at: str | None = None
    if recent_changes:
        last_domain_change_at = recent_changes[0]["current_observed_at"]
    freshness_info = {
        "last_observation_at": last_observed,
        "last_domain_change_at": last_domain_change_at,
        "data_age_seconds": round(data_age_seconds, 1) if data_age_seconds is not None else None,
        "scheduler_last_run": last_run,
    }

    # World-level limitations
    if health.get("status") not in ("healthy",):
        limitations.append(f"provider status: {health.get('status')} — {health.get('message','')}".strip())
    if last_run is None:
        limitations.append("no scheduler telemetry yet — cannot distinguish 'unchanged' from 'not observed'")
    elif last_run.get("success") == 0:
        limitations.append(f"last scheduler run failed: {last_run.get('error')}")
    if data_age_seconds is not None and data_age_seconds > 7200:
        limitations.append(f"stale: last observation {round(data_age_seconds/3600,1)}h ago")
    if not current_domain:
        limitations.append("no domain signals yet for this world")
    if not open_predictions and not recent_outcomes:
        limitations.append("no predictions/outcomes for this world yet")

    # Known provider caveats (from football adapter status map etc.)
    # Keep generic — adapter limitations are surfaced via health/message above.

    # Active entities list
    active_entities = sorted(entities_set)

    # Provenance
    provenance = {
        "world_id": world_id,
        "generated_at": now_iso,
        "sources": {
            "descriptor": "world.describe",
            "health": "world.health",
            "current_state": "signal_observations (latest per key, domain only)",
            "recent_changes": f"signal_observations diff, lookback_hours={lookback_hours}",
            "patterns": "memory.patterns_for_world",
            "open_predictions": "predictions(status=open, domain=world_id)",
            "recent_outcomes": "predictions JOIN prediction_resolutions",
            "model": "WorldModelRegistry core.state-vector",
            "scheduler": "scheduler_runs",
        },
        "last_observation_at": last_observed,
        "signal_counts": {
            "domain_current": len(current_domain),
            "operational_current": len(operational_current),
            "recent_changes": len(recent_changes),
        },
    }

    return {
        "world": {
            "world_id": descriptor.world_id,
            "world_type": descriptor.world_type,
            "name": descriptor.name,
        },
        "observed_at": now_iso,
        "health": health,
        "current_state": {
            "signals": [
                {
                    "signal_id": s["signal_id"],
                    "entity_ref": s["entity_ref"],
                    "value": s["value"],
                    "value_type": s["value_type"],
                    "unit": s["unit"],
                    "observed_at": s["observed_at"],
                }
                for s in current_domain
            ],
            "entities": active_entities,
        },
        "recent_changes": recent_changes,
        "patterns": patterns,
        "open_predictions": open_predictions,
        "recent_outcomes": recent_outcomes,
        "model": model_summary,
        "operational": {
            "signals": operational_current,
        },
        "freshness": freshness_info,
        "limitations": limitations,
        "provenance": provenance,
    }


def _build_world_model(
    worlds: WorldRegistry,
    model_builders: WorldModelRegistry,
    memory: MemoryStore,
    args: dict,
) -> dict:
    """Build a world model using the WorldModelRegistry and persisted signals."""
    world_id = str(args.get("world_id", ""))
    builder_id = str(args.get("builder_id", "core.state-vector"))
    entity_ref = args.get("entity_ref")
    signal_ids = args.get("signal_ids")
    since = args.get("since")
    until = args.get("until")

    if not world_id:
        raise ValueError("world_id is required")

    # Verify world exists
    worlds.get(world_id)

    # Get builder
    builder = model_builders.get(builder_id)

    # Get signals from memory
    signals = memory.signals_for_world(world_id, limit=500)

    # Filter by entity_ref if specified
    if entity_ref:
        signals = [s for s in signals if s.get("entity_ref") == entity_ref]

    # Filter by signal_ids if specified
    if signal_ids:
        sig_id_set = set(signal_ids)
        signals = [s for s in signals if s.get("signal_id") in sig_id_set]

    # Filter by time range if specified
    if since:
        signals = [s for s in signals if s.get("observed_at", "") >= since]
    if until:
        signals = [s for s in signals if s.get("observed_at", "") <= until]

    # Get patterns
    patterns = memory.patterns_for_world(world_id, limit=500)

    # Build model
    model = builder.build(
        world_id=world_id,
        signals=signals,
        patterns=patterns,
        query=args,
    )
    return model.as_dict()


@dataclass(frozen=True, slots=True)
class ToolBindings:
    get_handoff: Callable[[], str]
    get_migration_status: Callable[[], str]
    semantic_search: Callable[[str, int], str]
    assistant_status: Callable[[], str]
    create_local_proposal: Callable[[str, list[str]], str]
    audit_changed_notes: Callable[[], str]
    system_health: Callable[[], str]
    memory_get: Callable[[str], str]
    memory_list: Callable[[str | None, int], str]
    memory_search: Callable[[str, str | None, int], str]
    memory_recent: Callable[[str | None, int], str]


def register_foundation_tools(
    mcp: FastMCP,
    root: Path,
    *,
    context_factory: ContextFactory | None = None,
) -> tuple[ToolBindings, ToolRegistry, SearchCoordinator]:
    """Register all compatible tools through the Cut 2 Core invocation path."""

    root = root.resolve()
    vault = VaultAdapter(root)
    git = GitAdapter(root)
    lexical = LexicalIndex(
        vault,
        root / ".local-index" / "lexical-v1.json",
        semantic_index_path=root / ".local-index" / "vault.jsonl",
    )
    semantic = OllamaSemanticBackend(root / ".local-index" / "vault.jsonl")
    search = SearchCoordinator(lexical, semantic)
    search.refresh()
    memory = MemoryStore(root / ".assistant-runtime" / "omnisvera-mcp" / "memory.db")
    companion = CompanionAdapter(root)
    health = HealthService(root, vault, git, lexical, semantic, companion, memory)
    handoff = HandoffService(vault, git, companion, memory, health)
    handlers = ExistingToolHandlers(vault, git, search, handoff)
    audit = SQLiteAuditSink(memory)
    registry = ToolRegistry(audit=audit)

    # World registry
    worlds = WorldRegistry()
    model_builders = WorldModelRegistry()
    model_builders.register(CoreStateVectorBuilder())
    
    # Football world — real data from TheSportsDB
    try:
        football_provider = HttpFootballDataProvider(
            team_ids=[
                "133604",  # Arsenal
                "133616",  # Chelsea
                "133608",  # Manchester City
                "133614",  # Liverpool
                "133594",  # Manchester United
            ]
        )
        football_adapter = FootballWorldAdapter(provider=football_provider)
        worlds.register(football_adapter)
    except Exception:
        pass  # Football world not available
    
    # Crypto world — real data from CoinGecko
    try:
        crypto_provider = CoinGeckoProvider(
            coin_ids=["bitcoin", "ethereum", "solana", "binancecoin"]
        )
        crypto_adapter = CryptoWorldAdapter(provider=crypto_provider)
        worlds.register(crypto_adapter)
    except Exception:
        pass  # Crypto world not available

    def read_memory(_context: CallContext, arguments: dict) -> str:
        memory_id = str(arguments.get("memory_id", "")).strip()
        if not memory_id:
            raise ValueError("memory_id is required")
        item = memory.get_memory(memory_id)
        if item is None:
            raise ValueError(f"memory item not found: {memory_id}")
        return json.dumps(item, ensure_ascii=False, indent=2)

    def list_memory(_context: CallContext, arguments: dict) -> str:
        raw_type = arguments.get("item_type")
        item_type = str(raw_type).strip() if raw_type is not None else None
        if item_type == "":
            item_type = None
        limit = int(arguments.get("limit", 20))
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return json.dumps(
            memory.list_memories(item_type=item_type, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    def search_memory(_context: CallContext, arguments: dict) -> str:
        return json.dumps(
            memory.search_memories(
                arguments.get("query"), item_type=arguments.get("item_type"),
                limit=arguments.get("limit", 10),
            ), ensure_ascii=False, indent=2,
        )

    def recent_memory(_context: CallContext, arguments: dict) -> str:
        return json.dumps(
            memory.recall_recent(
                item_type=arguments.get("item_type"), limit=arguments.get("limit", 10),
            ), ensure_ascii=False, indent=2,
        )

    for tool in (
        RegisteredTool(
            "get_handoff",
            handlers.get_handoff,
            "read",
            "omnisvera://handoff",
            frozenset({"vault.handoff.read"}),
        ),
        RegisteredTool(
            "get_migration_status",
            handlers.get_migration_status,
            "read",
            "omnisvera://migration/status",
            frozenset({"vault.migration.read"}),
        ),
        RegisteredTool(
            "semantic_search",
            handlers.semantic_search,
            "search",
            "omnisvera://vault",
            frozenset({"vault.search"}),
        ),
        RegisteredTool(
            "assistant_status",
            handlers.assistant_status,
            "read",
            "projects://current/status",
            frozenset({"project.read"}),
        ),
        RegisteredTool(
            "create_local_proposal",
            handlers.create_local_proposal,
            "propose",
            "omnisvera://proposals",
            frozenset({"vault.propose"}),
        ),
        RegisteredTool(
            "audit_changed_notes",
            handlers.audit_changed_notes,
            "audit",
            "omnisvera://vault/changed",
            frozenset({"vault.audit"}),
        ),
        RegisteredTool(
            "system.health",
            lambda _context, _arguments: json.dumps(health.collect(), ensure_ascii=False, indent=2),
            "health",
            "system://health",
            frozenset({"system.health.read"}),
        ),
        RegisteredTool(
            "memory.get",
            read_memory,
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ),
        RegisteredTool(
            "memory.list",
            list_memory,
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ),
        RegisteredTool(
            "memory.search", search_memory, "read", "memory://items",
            frozenset({"memory.read"}),
        ),
        RegisteredTool(
            "memory.recent", recent_memory, "read", "memory://items",
            frozenset({"memory.read"}),
        ),
        # System tools
        RegisteredTool(
            "system.manifest",
            lambda _ctx, _args: json.dumps(generate_manifest(
                worlds=[d.as_dict() for d in worlds.list()],
                model_builders=model_builders.list(),
                tools=[{"name": t.name, "access_mode": t.action} for t in registry._tools.values()],
            ), ensure_ascii=False, indent=2),
            "read",
            "system://manifest",
            frozenset({"system.health.read"}),
        ),
        RegisteredTool(
            "system.bootstrap",
            lambda _ctx, _args: json.dumps(generate_bootstrap(
                health=health.collect(),
                handoff=handoff.snapshot(),
                worlds=[d.as_dict() for d in worlds.list()],
                memory_stats=memory.stats(),
                manifest_summary=generate_manifest(
                    worlds=[d.as_dict() for d in worlds.list()],
                    model_builders=model_builders.list(),
                    tools=[{"name": t.name, "access_mode": t.action} for t in registry._tools.values()],
                ),
            ), ensure_ascii=False, indent=2),
            "read",
            "system://bootstrap",
            frozenset({"system.health.read"}),
        ),
        # Companion
        RegisteredTool(
            "get_companion_state",
            lambda _ctx, _args: json.dumps(companion.get_dashboard().as_dict(), ensure_ascii=False, indent=2),
            "read",
            "projects://companion/current",
            frozenset({"companion.read"}),
        ),
        # World tools
        RegisteredTool(
            "world.list",
            lambda _ctx, _args: json.dumps([d.as_dict() for d in worlds.list()], ensure_ascii=False, indent=2),
            "read",
            "world://list",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.describe",
            lambda _ctx, args: json.dumps(worlds.get(str(args.get("world_id", ""))).describe().as_dict(), ensure_ascii=False, indent=2),
            "read",
            "world://describe",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.observe",
            lambda _ctx, args: json.dumps(worlds.get(str(args.get("world_id", ""))).observe().as_dict(), ensure_ascii=False, indent=2),
            "read",
            "world://observe",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.signals",
            lambda _ctx, args: json.dumps([s.as_dict() for s in worlds.get(str(args.get("world_id", ""))).signals()], ensure_ascii=False, indent=2),
            "read",
            "world://signals",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.signal_history",
            lambda _ctx, args: json.dumps(memory.signal_history(
                world_id=str(args.get("world_id", "")),
                signal_id=str(args.get("signal_id", "")),
                limit=int(args.get("limit", 50)),
            ), ensure_ascii=False, indent=2),
            "read",
            "world://signals/history",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.signal_changes",
            lambda _ctx, args: json.dumps(memory.signal_changes(
                world_id=str(args.get("world_id", "")),
                signal_id=str(args.get("signal_id", "")),
                limit=int(args.get("limit", 20)),
            ), ensure_ascii=False, indent=2),
            "read",
            "world://signals/changes",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.signal_patterns",
            lambda _ctx, args: json.dumps(memory.signal_patterns(
                world_id=str(args.get("world_id", "")),
                signal_id=str(args.get("signal_id", "")),
                limit=int(args.get("limit", 10)),
            ), ensure_ascii=False, indent=2),
            "read",
            "world://signals/patterns",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.model",
            lambda _ctx, args: json.dumps(_build_world_model(worlds, model_builders, memory, args), ensure_ascii=False, indent=2),
            "read",
            "world://model",
            frozenset({"world.read"}),
        ),
        RegisteredTool(
            "world.capture_signals",
            lambda _ctx, args: json.dumps({"captured": memory.capture_signals(
                signals=args.get("signals", []),
            )}, ensure_ascii=False, indent=2),
            "write",
            "world://signals/capture",
            frozenset({"world.write"}),
        ),
        RegisteredTool(
            "world.context",
            lambda _ctx, args: json.dumps(
                _build_world_context(
                    memory, worlds, model_builders,
                    world_id=str(args.get("world_id", "")),
                    lookback_hours=int(args.get("lookback_hours", 24)) if args.get("lookback_hours") is not None else 24,
                ),
                ensure_ascii=False, indent=2,
            ),
            "read",
            "world://context",
            frozenset({"world.read"}),
        ),
        # Epistemic tools
        RegisteredTool(
            "epistemic.create_snapshot",
            lambda _ctx, args: epistemic.create_snapshot(memory, _ctx, args),
            "write",
            "epistemic://snapshots",
            frozenset({"epistemic.write"}),
        ),
        RegisteredTool(
            "epistemic.snapshot_from_model",
            lambda _ctx, args: epistemic.snapshot_from_model(memory, _ctx, args),
            "write",
            "epistemic://snapshots",
            frozenset({"epistemic.write"}),
        ),
        RegisteredTool(
            "epistemic.validate_candidate",
            lambda _ctx, args: epistemic.validate_candidate(memory, _ctx, args),
            "read",
            "epistemic://predictions",
            frozenset({"epistemic.read"}),
        ),
        RegisteredTool(
            "epistemic.commit_candidate",
            lambda _ctx, args: epistemic.commit_candidate(memory, _ctx, args),
            "write",
            "epistemic://predictions",
            frozenset({"epistemic.write"}),
        ),
        RegisteredTool(
            "epistemic.create_prediction",
            lambda _ctx, args: epistemic.create_prediction(memory, _ctx, args),
            "write",
            "epistemic://predictions",
            frozenset({"epistemic.write"}),
        ),
        RegisteredTool(
            "epistemic.list_predictions",
            lambda _ctx, args: epistemic.list_predictions(memory, _ctx, args),
            "read",
            "epistemic://predictions",
            frozenset({"epistemic.read"}),
        ),
        RegisteredTool(
            "epistemic.get_prediction",
            lambda _ctx, args: epistemic.get_prediction(memory, _ctx, args),
            "read",
            "epistemic://predictions",
            frozenset({"epistemic.read"}),
        ),
        RegisteredTool(
            "epistemic.resolve_prediction",
            lambda _ctx, args: epistemic.resolve_prediction(memory, _ctx, args),
            "write",
            "epistemic://predictions",
            frozenset({"epistemic.write"}),
        ),
        RegisteredTool(
            "epistemic.calibration_summary",
            lambda _ctx, args: epistemic.calibration_summary(memory, _ctx, args),
            "read",
            "epistemic://calibration",
            frozenset({"epistemic.read"}),
        ),
        RegisteredTool(
            "epistemic.resolve_due_predictions",
            lambda _ctx, args: epistemic.resolve_due_predictions(memory, _ctx, args),
            "write",
            "epistemic://predictions",
            frozenset({"epistemic.write"}),
        ),
    ):
        registry.register(tool)
    make_context = context_factory or CallContext.trusted_local_stdio

    @mcp.tool()
    def get_handoff() -> str:
        """Retorna o objetivo, regras e próximo passo compartilhados entre Codex e Ollama."""
        return registry.invoke("get_handoff", make_context(), {})

    @mcp.tool()
    def get_migration_status() -> str:
        """Retorna o registro versionado da migração de Disgraceland para Omnisvera."""
        return registry.invoke("get_migration_status", make_context(), {})

    @mcp.tool()
    def semantic_search(query: str, limit: int = 8) -> str:
        """Pesquisa o índice semântico local e retorna trechos com caminhos de origem."""
        return registry.invoke(
            "semantic_search",
            make_context(),
            {"query": query, "limit": limit},
        )

    @mcp.tool()
    def assistant_status() -> str:
        """Retorna estado Git e handoff atual sem modificar arquivos."""
        return registry.invoke("assistant_status", make_context(), {})

    @mcp.tool()
    def create_local_proposal(task: str, source_files: list[str]) -> str:
        """Gera proposta somente a partir de fontes explícitas, sem editar notas canônicas."""
        return registry.invoke(
            "create_local_proposal",
            make_context(),
            {"task": task, "source_files": source_files},
        )

    @mcp.tool()
    def audit_changed_notes() -> str:
        """Executa auditoria de YAML e wikilinks apenas nas notas modificadas."""
        return registry.invoke("audit_changed_notes", make_context(), {})

    @mcp.tool(name="system.health")
    def system_health() -> str:
        """Retorna saúde, freshness e limitações dos subsistemas do Omnisvera."""
        return registry.invoke("system.health", make_context(), {})

    @mcp.tool(name="memory.get")
    def memory_get(memory_id: str) -> str:
        """Retorna uma memória persistida por ID, incluindo sua proveniência."""

        return registry.invoke("memory.get", make_context(), {"memory_id": memory_id})

    @mcp.tool(name="memory.list")
    def memory_list(item_type: str | None = None, limit: int = 20) -> str:
        """Lista memórias persistidas, opcionalmente filtradas por tipo."""

        return registry.invoke(
            "memory.list",
            make_context(),
            {"item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.search")
    def memory_search(query: str, item_type: str | None = None, limit: int = 10) -> str:
        """Busca lexical em ID, título e conteúdo; retorna memórias com fontes.

        Ignora caixa/acentos, não interpreta sinônimos. Limite: 1–100.
        """
        return registry.invoke(
            "memory.search", make_context(),
            {"query": query, "item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.recent")
    def memory_recent(item_type: str | None = None, limit: int = 10) -> str:
        """Retorna memórias com fontes, por updated_at decrescente e ID. Limite: 1–100."""
        return registry.invoke(
            "memory.recent", make_context(), {"item_type": item_type, "limit": limit},
        )

    resources = ResourceRegistry(audit=audit)
    resources.register(RegisteredResource("system://health", lambda _context: health.collect(), frozenset({"system.health.read"})))
    resources.register(RegisteredResource("omnisvera://handoff", lambda _context: handoff.snapshot(), frozenset({"vault.handoff.read"})))
    resources.register(RegisteredResource("projects://companion/current", lambda _context: companion.get_dashboard().as_dict(), frozenset({"companion.read"})))

    @mcp.resource("system://health", name="Omnisvera system health")
    def system_health_resource() -> str:
        return json.dumps(resources.read("system://health", make_context()), ensure_ascii=False, indent=2)

    @mcp.resource("omnisvera://handoff", name="Dynamic Omnisvera handoff")
    def dynamic_handoff_resource() -> str:
        return json.dumps(resources.read("omnisvera://handoff", make_context()), ensure_ascii=False, indent=2)

    @mcp.resource("projects://companion/current", name="Current Companion project state")
    def companion_state_resource() -> str:
        return json.dumps(resources.read("projects://companion/current", make_context()), ensure_ascii=False, indent=2)

    registry.services = {
        "memory": memory,
        "companion": companion,
        "health": health,
        "handoff": handoff,
        "resources": resources,
        "worlds": worlds,
        "model_builders": model_builders,
    }

    return (
        ToolBindings(
            get_handoff=get_handoff,
            get_migration_status=get_migration_status,
            semantic_search=semantic_search,
            assistant_status=assistant_status,
            create_local_proposal=create_local_proposal,
            audit_changed_notes=audit_changed_notes,
            system_health=system_health,
            memory_get=memory_get,
            memory_list=memory_list,
            memory_search=memory_search,
            memory_recent=memory_recent,
        ),
        registry,
        search,
    )
