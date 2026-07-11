from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_vault_path() -> Path:
    # backend/app/config.py -> backend -> omnisvera-agent -> vault root
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    vault_path: Path
    ollama_base_url: str
    ollama_model: str
    embedding_model: str
    database_path: Path
    semantic_index_path: Path
    rag_mode: str
    rag_context_limit: int
    rag_context_chars: int
    auto_refresh_index: bool
    auto_refresh_interval_seconds: int
    access_token: str | None
    master_token: str | None
    player_token: str | None
    rebuild_on_startup: bool


def _rag_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"lexical", "semantic", "hybrid"}:
        return normalized
    return "hybrid"


def _safe_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)


def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    vault_path = Path(os.getenv("OMNISVERA_VAULT_PATH", str(_default_vault_path()))).resolve()
    database_path = Path(
        os.getenv(
            "OMNISVERA_DB_PATH",
            str(backend_root / "data" / "omnisvera_companion.sqlite3"),
        )
    ).resolve()
    return Settings(
        vault_path=vault_path,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        embedding_model=os.getenv("OMNISVERA_EMBEDDING_MODEL", "nomic-embed-text"),
        database_path=database_path,
        semantic_index_path=Path(
            os.getenv(
                "OMNISVERA_SEMANTIC_INDEX_PATH",
                str(vault_path / ".local-index" / "vault.jsonl"),
            )
        ).resolve(),
        rag_mode=_rag_mode(os.getenv("OMNISVERA_RAG_MODE", "hybrid")),
        rag_context_limit=_safe_int("OMNISVERA_RAG_CONTEXT_LIMIT", 8),
        rag_context_chars=_safe_int("OMNISVERA_RAG_CONTEXT_CHARS", 5200),
        auto_refresh_index=os.getenv("OMNISVERA_AUTO_REFRESH_INDEX", "true").lower()
        in {"1", "true", "yes", "sim"},
        auto_refresh_interval_seconds=_safe_int("OMNISVERA_AUTO_REFRESH_INTERVAL_SECONDS", 12),
        access_token=os.getenv("OMNISVERA_ACCESS_TOKEN") or None,
        master_token=os.getenv("OMNISVERA_MASTER_TOKEN") or os.getenv("OMNISVERA_ACCESS_TOKEN") or None,
        player_token=os.getenv("OMNISVERA_PLAYER_TOKEN") or None,
        rebuild_on_startup=os.getenv("OMNISVERA_REBUILD_ON_STARTUP", "false").lower()
        in {"1", "true", "yes", "sim"},
    )
