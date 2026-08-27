# Memory Search / Recall — read-only

Public tools, available through the existing stdio Core and explicit bridge allowlist:

```text
memory.search(query: str, item_type: str | None = None, limit: int = 10)
memory.recent(item_type: str | None = None, limit: int = 10)
```

Both return JSON **text** containing a list of full persisted memory records, in the
same format as `memory.get`/`memory.list`: ID, namespace, type, title, content,
status, confidence, owner, classification, timestamps, metadata and `sources`.
No results means `[]`, not a generated answer. Existing contracts are unchanged.

## Retrieval rules

- Search reads `memory_items` directly: ID, title and content only. It does not
  search the Vault, source documents, source references, or `project_states`.
- Unicode case/accent normalization, word boundaries, a small Portuguese/English
  stop-word list; repeated query terms count once. Negations are retained.
- Partial matches are allowed. Descending rank: exact normalized ID, exact
  normalized title, number of distinct matched terms, terms matched in the title.
  Equal ranks break by ascending stable ID. Repeated words do not boost rank.
- Search ranks the complete type-filtered collection **before** applying limit.
- Recent orders by the actual `updated_at` instant (SQLite `julianday`, including
  timezone offsets), descending, then ascending ID. It does not mean creation
  time or last retrieval time. Invalid stored timestamps sort last.
- Query: 1–1000 characters and at least one non-stop-word token. Limit: integer
  1–100. Invalid input fails explicitly. Type is an exact optional filter;
  whitespace is trimmed, blank means no filter, unknown type returns `[]`.
- No synonyms, stemming, translation, semantic inference, embeddings or Ollama.
  A relevant memory without overlapping words will not be found. Prefer focused
  terms and use `item_type="heuristic"` / `"constraint"` / `"decision"` when known.
- No index or schema migration: new persisted rows are visible on the next call.
  This deliberately scans the small memory collection; it is not a large-scale
  search engine.

Examples against the four bootstrap records:

```text
memory.search("Quais restrições existem para o canon?") -> C-001
memory.search("túnel", item_type="decision") -> D-002
memory.search("mudanças reversíveis", item_type="heuristic") -> H-001
memory.search("6100a10") -> D-001
memory.recent(item_type="decision", limit=1) -> D-002
```

## Authority and side effects

Both tools use Registry → internally injected CallContext → Policy → handler →
sanitized Audit, with the **existing** `memory.read` scope and `memory://items`
resource. No new identity or write scope is granted. Classification/namespace are
returned unchanged; this cut does not introduce per-item ACLs beyond existing
memory read authorization. The bridge remains explicitly allowlisted.

Memory/source/project tables are read-only. The sole expected invocation write
is the existing audit event (identity, tool, result, duration, argument hash),
never the raw query or response. No bootstrap/import runs during retrieval.

No tasks, OpenCode execution integration, memory writes or candidate import are
included. Existing MCP clients need tool rediscovery after the server loads the
updated code; existing long-lived servers do not hot-reload Python modules.

## Validation

```powershell
.\.omnisvera-tools\Scripts\python.exe -m unittest discover -s .local-tools/tests -p 'test_*.py' -v
.\.omnisvera-tools\Scripts\python.exe .local-tools/tests/smoke_memory_recall.py
```

`test_memory_recall.py` uses temporary SQLite fixtures for ranking, validation,
provenance, type/limit behavior, chronological ordering, unchanged data, actual
Registry/Policy/Audit and FastMCP bindings. Existing tests cover prior contracts.

The smoke test launches the actual stdio entrypoint and a temporary HTTP child
on an unused loopback port. It uses the real MCP SDK for initialize/list/call,
checks both identities in operational audit, and compares memory/source/project
rows before and after. It expects the four accepted bootstrap records to exist;
it never inserts them. It does not restart production services or the tunnel.

Validated on 2026-08-27: the 47-test baseline passed before changes; the full
suite passed with 68 tests (21 new). Real cold-start discovered 11 stdio tools
and 7 HTTP tools; both retrieved C-001 and recent decisions D-002/D-001. The
operational data comparison was unchanged with 8 expected audit events.
Python compilation and `git diff --check` passed. Ruff was not installed.
The existing negative remote-write test emits an expected unknown-tool warning;
Git also reports Windows LF/CRLF conversion warnings.
