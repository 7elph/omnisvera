# ADR-001 — Omnisvera MCP Core

- **Status:** Accepted
- **Date:** 2026-08-26
- **Scope:** Omnisvera local tooling and future shared MCP integration

## Context

Omnisvera currently has MCP capabilities split across multiple integrations. The active local vault MCP is implemented in `.local-tools/mcp_server.py` using FastMCP over `stdio`. It exposes six tools:

- `get_handoff`
- `get_migration_status`
- `semantic_search`
- `assistant_status`
- `create_local_proposal`
- `audit_changed_notes`

The local MCP is useful for continuity, audit, and vault access, but tool registration is centralized in one launcher module, handoff is a static file, semantic search fails when its semantic stack is unavailable, provenance-aware operational memory does not exist, Companion state is external, and authorization is not a first-class internal concern. A historical remote MCP integration must not become a second product implementation.

## Decision

Adopt **Omnisvera MCP Core** as the official MCP architecture.

Omnisvera MCP Core is the local integration, memory, provenance, and governance layer that provides a consistent MCP interface over Vault, Git, Companion, and operational memory while preserving each system as the source of truth for its own domain.

The existing `.local-tools/mcp_server.py` evolves incrementally into a thin launcher. The first implementation remains local and `stdio`-only. The Core unifies interface and governance, not underlying stores.

## Source-of-truth boundaries

| Domain | Source of truth |
|---|---|
| Lore, canon, and wiki relationships | Vault |
| Source code and repository state | Git/repository |
| Companion runtime state and sessions | Companion API |
| Sage/MIA operational memory | MCP Core memory store |
| Search indexes | Derived state |
| Handoff | Generated view |
| Audit history | MCP Core audit log |

The Core may cache, index, summarize, or reference source data, but must not silently become the canonical owner of another system's data.

## Frozen principles

```text
unified interface != unified database
namespace != authorization
remote transport != identity
memory != truth
semantic search != search
handoff != source of truth
internal context != client-controlled argument
audit != indiscriminate content copy
```

## Call context and policy

Every internal invocation follows the conceptual contract:

```python
registry.invoke(tool_name, context, arguments)
```

`CallContext` contains transport-injected identity such as actor, client, transport, scopes, request/correlation ID, and optional project/task handles. It is never exposed as a public MCP tool argument. For v0.1, the trusted local `stdio` launcher injects Sage/local identity. Every registered tool and resource still passes through a policy decision point so stricter identities can be introduced without changing handlers.

## Namespaces

Resources may be organized under:

- `sage://`
- `mia://`
- `omnisvera://`
- `projects://`
- `system://`

Namespaces express organization and semantic ownership, never authority. Policy evaluates the explicit owner, audiences, classification, and required scopes of protected resources and returned memory items. Player, collaborator, GM, infrastructure, and private-memory access are not a linear clearance hierarchy.

## Compatibility and search

The six existing tool names, public argument schemas, and text-compatible outputs are preserved during v0.1. In particular, `semantic_search(query, limit=8)` must not silently become JSON-only.

Search degrades gracefully:

```text
exact + lexical + optional semantic -> ranking
```

Exact and lexical retrieval work without Ollama. On startup and before search, the Core detects changed files incrementally, refreshes metadata/lexical state, and marks affected semantic documents dirty. A live watcher is optional.

## Companion boundary

`CompanionAdapter` uses authenticated Companion HTTP APIs and never imports FastAPI internals for convenience. v0.1 access is read-only. This preserves Companion authorization, validation, ledger and idempotency rules, process boundaries, and deployment independence.

## Handoff, memory, provenance, and audit

`get_handoff` evolves into a generated view over currently accessible Git, Vault, Companion, and operational-memory evidence. Important sections preserve source, observation time, confidence, freshness, and limitations. Optional snapshots are historical evidence, not current truth.

The initial SQLite store has four conceptual tables:

- `memory_items`
- `memory_sources`
- `project_states`
- `audit_events`

Memory preserves source references so the system can answer why it believes something. Audit is operational evidence, not a content archive. It may store identity, action, target identifiers, result, duration, source IDs, request ID, argument fingerprints, and allowlisted metadata. Tokens, full notes, full private responses, GM secrets, full prompts, and raw sensitive payloads are omitted or redacted.

## Transport strategy

v0.1 is `stdio`-only. Future Streamable HTTP uses the same Registry and handlers. Remote authorization, Cloudflare/Tailscale, collaborators, Godot, queues, direct Vault writes, and Companion writes are deferred. No parallel MCP implementation is created.

## Migration

Migration is incremental and reversible:

1. preserve and baseline existing contracts;
2. introduce Registry, CallContext, and Policy behind the current launcher;
3. migrate tools one at a time;
4. add adapters and resilient search;
5. add operational memory, audit, health, and dynamic handoff;
6. add remote transport only in a later version.

No lore or canonical Vault content is modified by this migration.

## Consequences

Benefits include one logical MCP product, preservation of local workflows, explicit provenance/freshness, search without mandatory Ollama, future transport independence, independently deployable Companion, and scoped future collaborator access.

Costs include additional internal abstractions, regression tests for existing contracts, first-class policy/provenance work, and dependence of the dynamic handoff on upstream freshness.

## Out of scope for ADR-001 implementation phase

- Streamable HTTP and remote authorization
- Cloudflare Access and Tailscale
- Collaborator access and remote scopes
- Godot integration
- Autonomous queues
- Direct Vault or Companion writes
- Sophisticated SkillBank behavior
