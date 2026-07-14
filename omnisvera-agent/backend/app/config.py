from __future__ import annotations

import os
import json
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
    fast_model: str
    quality_model: str
    candidate_model: str
    production_model: str
    model_mode: str
    production_approved: bool
    embedding_model: str
    response_mode: str
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
    player_profiles: dict[str, dict[str, str]]
    rebuild_on_startup: bool


def _rag_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"lexical", "semantic", "hybrid"}:
        return normalized
    return "hybrid"


def _response_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"fast", "grounded"}:
        return normalized
    return "fast"


def _model_mode(value: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in {"baseline", "candidate", "production"} else "baseline"


def _safe_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)


def _production_is_approved(vault_path: Path, model: str) -> bool:
    path=vault_path / "omnisvera-model" / "artifacts" / "model_registry.json"
    try: registry=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return False
    record=(registry.get("models") or {}).get(model) or {}
    return registry.get("production_model") == model and record.get("status") == "approved"


def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    vault_path = Path(os.getenv("OMNISVERA_VAULT_PATH", str(_default_vault_path()))).resolve()
    database_path = Path(
        os.getenv(
            "OMNISVERA_DB_PATH",
            str(backend_root / "data" / "omnisvera_companion.sqlite3"),
        )
    ).resolve()
    fast_model = os.getenv("OMNISVERA_FAST_MODEL", "qwen2:1.5b")
    quality_model = os.getenv("OMNISVERA_QUALITY_MODEL", "llama-3.2-omnisvera-3b")
    candidate_model = os.getenv("OMNISVERA_CANDIDATE_MODEL", quality_model)
    production_model = os.getenv("OMNISVERA_PRODUCTION_MODEL", quality_model)
    model_mode = _model_mode(os.getenv("OMNISVERA_MODEL_MODE", "baseline"))
    production_approved = _production_is_approved(vault_path, production_model)
    response_mode = _response_mode(os.getenv("OMNISVERA_RESPONSE_MODE", "grounded"))
    selected_model = {
        "baseline": fast_model,
        "candidate": candidate_model,
        "production": production_model if production_approved else fast_model,
    }[model_mode]
    try:
        raw_profiles = json.loads(os.getenv("OMNISVERA_PLAYER_PROFILES_JSON", "{}"))
        player_profiles = raw_profiles if isinstance(raw_profiles, dict) else {}
    except json.JSONDecodeError:
        player_profiles = {}
    return Settings(
        vault_path=vault_path,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=selected_model,
        fast_model=fast_model,
        quality_model=quality_model,
        candidate_model=candidate_model,
        production_model=production_model,
        model_mode=model_mode,
        production_approved=production_approved,
        embedding_model=os.getenv(
            "OMNISVERA_EMBED_MODEL",
            os.getenv("OMNISVERA_EMBEDDING_MODEL", "nomic-embed-text"),
        ),
        response_mode=response_mode,
        database_path=database_path,
        semantic_index_path=Path(
            os.getenv(
                "OMNISVERA_SEMANTIC_INDEX_PATH",
                str(vault_path / ".local-index" / "vault.jsonl"),
            )
        ).resolve(),
        rag_mode=_rag_mode(os.getenv("OMNISVERA_RAG_MODE", "hybrid")),
        rag_context_limit=min(8, _safe_int("OMNISVERA_RAG_CONTEXT_LIMIT", 6)),
        rag_context_chars=min(5200, _safe_int("OMNISVERA_RAG_CONTEXT_CHARS", 3600)),
        auto_refresh_index=os.getenv("OMNISVERA_AUTO_REFRESH_INDEX", "true").lower()
        in {"1", "true", "yes", "sim"},
        auto_refresh_interval_seconds=_safe_int("OMNISVERA_AUTO_REFRESH_INTERVAL_SECONDS", 12),
        access_token=os.getenv("OMNISVERA_ACCESS_TOKEN") or None,
        master_token=os.getenv("OMNISVERA_MASTER_TOKEN") or os.getenv("OMNISVERA_ACCESS_TOKEN") or None,
        player_token=os.getenv("OMNISVERA_PLAYER_TOKEN") or None,
        player_profiles=player_profiles,
        rebuild_on_startup=os.getenv("OMNISVERA_REBUILD_ON_STARTUP", "false").lower()
        in {"1", "true", "yes", "sim"},
    )
