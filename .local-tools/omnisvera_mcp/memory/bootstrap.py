from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .store import MemoryStore


CORE_COMMIT = "6100a105a14f4e5c0d8c5bb45930b22d3b4f3309"
BRIDGE_COMMIT = "055e7818255c3d91ad46093b16daa0ba843a2732"
FOUNDATION_COMMIT = "45324b650348f085ef63a3989c3295697568c92c"


def source(
    source_type: str,
    source_ref: str,
    source_timestamp: str,
    relation: str,
) -> dict[str, Any]:
    return {
        "source_type": source_type,
        "source_ref": source_ref,
        "source_timestamp": source_timestamp,
        "relation": relation,
        "excerpt_hash": None,
        "created_at": source_timestamp,
    }


MEMORY_SEED_V0_1: tuple[dict[str, Any], ...] = (
    {
        "id": "D-001",
        "namespace": "omnisvera",
        "type": "decision",
        "title": "Omnisvera MCP Core v0.1 congelado",
        "content": "O Omnisvera MCP Core v0.1 foi concluído e congelado no commit 6100a10.",
        "status": "accepted",
        "confidence": 1.0,
        "owner": "omnisvera",
        "classification": "internal",
        "created_at": "2026-08-26T23:18:15-03:00",
        "updated_at": "2026-08-26T23:18:15-03:00",
        "metadata": {"version": "v0.1", "commit": CORE_COMMIT},
        "sources": [
            source("commit", f"commit:{CORE_COMMIT}", "2026-08-26T23:18:15-03:00", "establishes"),
            source("document", "doc:.local-tools/docs/omnisvera-mcp-core-v0.1-spec.md", "2026-08-26T23:18:15-03:00", "specifies"),
        ],
    },
    {
        "id": "D-002",
        "namespace": "mia",
        "type": "decision",
        "title": "MIA Bridge PoC somente leitura",
        "content": "O MIA Bridge PoC expõe apenas capacidades de leitura pelo túnel seguro.",
        "status": "accepted",
        "confidence": 1.0,
        "owner": "omnisvera",
        "classification": "internal",
        "created_at": "2026-08-27T02:22:39-03:00",
        "updated_at": "2026-08-27T02:22:39-03:00",
        "metadata": {"phase": "proof-of-connection", "commit": BRIDGE_COMMIT},
        "sources": [
            source("commit", f"commit:{BRIDGE_COMMIT}", "2026-08-27T02:22:39-03:00", "establishes"),
            source("document", "doc:.local-tools/docs/mia-bridge-poc.md", "2026-08-27T02:22:39-03:00", "specifies"),
        ],
    },
    {
        "id": "C-001",
        "namespace": "omnisvera",
        "type": "constraint",
        "title": "Vault é a fonte de verdade do canon",
        "content": "O Vault permanece como fonte de verdade de lore, canon e relações da wiki.",
        "status": "accepted",
        "confidence": 1.0,
        "owner": "omnisvera",
        "classification": "internal",
        "created_at": "2026-08-26T20:01:44-03:00",
        "updated_at": "2026-08-26T20:01:44-03:00",
        "metadata": {"domain": "canon"},
        "sources": [
            source("commit", f"commit:{FOUNDATION_COMMIT}", "2026-08-26T20:01:44-03:00", "establishes"),
            source("document", "doc:.local-tools/docs/ADR-001-omnisvera-mcp-core.md", "2026-08-26T20:01:44-03:00", "specifies"),
        ],
    },
    {
        "id": "H-001",
        "namespace": "sage",
        "type": "heuristic",
        "title": "Infraestrutura evolui em cortes pequenos",
        "content": "Mudanças de infraestrutura devem ser pequenas, reversíveis e testadas antes do próximo corte.",
        "status": "accepted",
        "confidence": 0.95,
        "owner": "sage",
        "classification": "internal",
        "created_at": "2026-08-26T20:01:44-03:00",
        "updated_at": "2026-08-26T20:01:44-03:00",
        "metadata": {"scope": "infrastructure"},
        "sources": [
            source("commit", f"commit:{FOUNDATION_COMMIT}", "2026-08-26T20:01:44-03:00", "demonstrates"),
            source("document", "doc:.local-tools/docs/omnisvera-mcp-core-v0.1-spec.md", "2026-08-26T20:01:44-03:00", "specifies"),
        ],
    },
)


def apply_bootstrap(store: MemoryStore) -> dict[str, int]:
    return store.apply_seed([dict(item) for item in MEMORY_SEED_V0_1])


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    store = MemoryStore(root / ".assistant-runtime" / "omnisvera-mcp" / "memory.db")
    result = apply_bootstrap(store)
    print(json.dumps({**result, "counts": store.stats()["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
