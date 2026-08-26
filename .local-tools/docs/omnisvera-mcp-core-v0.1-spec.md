# Omnisvera MCP Core v0.1 — Technical Specification

- **Status:** Draft for implementation
- **Architecture:** [ADR-001 — Omnisvera MCP Core](ADR-001-omnisvera-mcp-core.md)
- **Transport:** `stdio` only
- **Primary objective:** introduce a modular Core without breaking current MCP behavior

## 1. Goal

v0.1 creates a correct, testable local Core around `.local-tools/mcp_server.py`. It preserves current client-facing contracts while introducing a central registry, internally injected call context, policy enforcement, source adapters, resilient search, dynamic handoff, provenance-aware operational memory, sanitized audit, read-only Companion state, and future transport independence.

v0.1 is not a remote-access milestone.

## 2. Baseline contract

The existing FastMCP `stdio` server exposes:

```text
get_handoff()
get_migration_status()
semantic_search(query, limit=8)
assistant_status()
create_local_proposal(task, source_files)
audit_changed_notes()
```

Tool names, public arguments, string-compatible outputs, Codex launch flow, proposal safety, Vault audit behavior, and the prohibition on automatic canonical-lore edits remain compatible. Baseline fixtures must capture all six public schemas before migration.

## 3. Non-goals

- Streamable HTTP, OAuth, Cloudflare, or Tailscale
- Collaborator identities or remote scopes
- Companion writes or direct Vault-write tools
- Autonomous queue or old remote MCP migration
- Godot integration
- New vector database or sophisticated SkillBank
- Generalized autonomous agents
- Replacement of Companion or Vault as source of truth

## 4. Target package

```text
.local-tools/
├── mcp_server.py
└── omnisvera_mcp/
    ├── __init__.py
    ├── server.py
    ├── core/
    │   ├── registry.py
    │   ├── context.py
    │   ├── policy.py
    │   ├── provenance.py
    │   ├── audit.py
    │   ├── handoff.py
    │   └── health.py
    ├── adapters/
    │   ├── vault.py
    │   ├── git.py
    │   └── companion.py
    ├── memory/
    │   ├── store.py
    │   └── models.py
    ├── search/
    │   ├── exact.py
    │   ├── lexical.py
    │   ├── semantic.py
    │   └── ranking.py
    ├── tools/
    │   ├── existing.py
    │   └── system.py
    └── resources/
        └── registry.py
```

This is a target organization, not permission to create empty modules. `mcp_server.py` remains the configured entrypoint.

## 5. Invocation and authorization

Public MCP signatures contain only legitimate client-controlled arguments. `CallContext` is absent from schemas and injected by the launcher.

```python
registry.invoke(
    tool_name: str,
    context: CallContext,
    arguments: dict,
)
```

Minimum context fields are actor, client, transport, scopes, request ID, and optional project/task IDs. For trusted v0.1 `stdio`, the launcher supplies Sage/local identity. Client arguments cannot override identity.

Every registered tool/resource executes through:

```python
allow(context, action, resource_metadata) -> decision
```

The initial policy may be small, but the enforcement hook is mandatory and deny-by-default for missing authority.

## 6. Existing-tool compatibility

All six tools preserve name, parameters, compatible return representation, and meaningful behavior. `semantic_search` remains text-compatible; richer internal metadata must not replace the legacy representation. `create_local_proposal` remains grounded in explicit source files and gains no canonical-write authority.

## 7. Adapters

### VaultAdapter

Enumerates and safely reads relevant Vault files, exposes metadata, resolves exact paths/names, supports lexical indexing, identifies changed notes, preserves existing audits, and reports freshness/dirty state. It neither silently edits canon nor requires Ollama for basic retrieval.

### GitAdapter

Exposes branch, HEAD, working-tree status, relevant changed paths, and freshness signals.

### CompanionAdapter

Uses authenticated HTTP API endpoints only. Initial read-only targets are health, app state, and dashboard where the real API supports them. Missing endpoints return typed degradation; they do not justify internal FastAPI imports. Companion offline does not make the Core itself unhealthy.

## 8. Search and incremental freshness

```text
exact + lexical + semantic when usable -> ranking
```

Exact and deterministic lexical retrieval remain available whenever the Vault is readable. Semantic states include healthy, stale, dirty, offline, and unknown; semantic failure never disables other retrieval modes.

At startup and before a search, compare relevant file fingerprints, refresh changed/new/deleted lexical entries, and mark affected semantic records `embedding_dirty`. A live watcher is optional. When embeddings return, process dirty/outdated documents instead of rebuilding everything unless corruption or an explicit rebuild requires it.

Freshness states are `fresh`, `stale`, `dirty`, `unknown`, and `unavailable`. Freshness and confidence are independent.

## 9. Dynamic handoff

`get_handoff()` becomes a generated view over current Git, Vault, Companion, memory/project state, migration evidence, and known limitations. Important sections retain value/summary, source, observation time, confidence, freshness, and limitations. The legacy public tool renders a compatible human-readable result. Optional snapshots never override fresher evidence.

## 10. Memory Store

Technology: SQLite. Core tables:

```text
memory_items
memory_sources
project_states
audit_events
```

`memory_items` supports typed observations, decisions, heuristics, skills, baselines, experiments, preferences, constraints, facts, and handoff snapshots. `memory_sources` records source type/ref/time, relation, and excerpt hash. `project_states` records observed state, source, confidence, and freshness.

The database lives in a documented ignored local path that can later move without changing public contracts. Cut 1 creates no database.

## 11. Resources and namespaces

Initial vocabulary:

```text
sage://
mia://
omnisvera://
projects://
system://
```

Namespaces organize; policy authorizes. v0.1 exposes only useful read-only resources, not placeholders.

## 12. Health and audit

`system.health` reports the independent state of Core, Vault, Git, Companion, lexical index, semantic index, embedding provider, and memory using healthy, degraded, stale, offline, unavailable, or unknown. Exact public naming is confirmed before implementation.

Audit stores allowlisted operational metadata: time, actor, client, transport, action/tool, target ID/category, result, duration, source IDs, argument hash, and request ID. It does not automatically store full notes, credentials, headers, private responses, campaign secrets, full prompts, or raw sensitive payloads.

## 13. Reversible delivery cuts

### Cut 1 — Foundation without behavior change

- Capture baseline schemas/behavior for all six tools.
- Create the minimal package.
- Implement Registry, internal CallContext, and Policy hook.
- Keep `mcp_server.py` as launcher.
- Migrate one deterministic read-only tool.
- Compare old and new behavior.

Constraints: no database, search change, handoff semantic change, Companion dependency, or public schema change. Exit requires equivalent behavior, passing baseline tests, and trivial rollback.

### Cut 2 — Adapters and resilient search

- Migrate all six tools.
- Add VaultAdapter and GitAdapter.
- Add exact and lexical search.
- Make semantic retrieval optional.
- Detect changes at startup/pre-search.
- Track semantic dirty/stale state.

Exit requires all six tools compatible, retrieval without Ollama, changed-note detection, no canonical edits, and rollback without data migration.

### Cut 3 — Operational state

- Add minimal SQLite memory, provenance, project states, and sanitized audit.
- Add read-only CompanionAdapter and system health.
- Replace static current-handoff semantics with HandoffService.
- Add useful read-only resources/namespaces.
- Optionally persist handoff snapshots.

Exit requires documented/ignored DB path, provenance, sanitized audit, graceful Companion degradation, source-aware handoff, no expanded write authority, and non-destructive rollback.

## 14. Test strategy

Contract tests verify all existing tools, public schemas, representative behavior, compatible output, and unchanged write boundaries. Registry tests verify internal context injection, absence from public schemas, identity non-forgeability, and policy-before-handler. Later cuts add search, handoff, audit, and Companion API-boundary tests described by their exit criteria.

## 15. Definition of Done

v0.1 is complete only when:

1. Codex still launches through the current `stdio` configuration.
2. All six tools and public contracts remain compatible.
3. CallContext is internal and policy runs on the invocation path.
4. No canonical Vault note is modified.
5. Exact and lexical retrieval work without Ollama.
6. Semantic retrieval is optional and tracks dirty content incrementally.
7. Health distinguishes component states.
8. Handoff uses current sources and exposes provenance/freshness/limitations.
9. Memory uses the minimal four-table model with provenance.
10. Audit is sanitized.
11. CompanionAdapter is read-only and uses HTTP API boundaries.
12. Existing and new tests pass.
13. Each cut is reversible without destructive migration.
14. No remote feature is required.

## 16. Deferred to v0.2

Streamable HTTP over the same Registry, HTTP authorization, identities/scopes, Cloudflare/Tailscale protection, collaborator access, expanded Companion reads, carefully scoped writes, and retirement of the historical remote integration.

## 17. Implementation rule

```text
existing state -> smallest useful change -> test -> compare -> keep/revert
```
