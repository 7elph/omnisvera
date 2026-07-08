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
    database_path: Path
    access_token: str | None
    rebuild_on_startup: bool


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
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
        database_path=database_path,
        access_token=os.getenv("OMNISVERA_ACCESS_TOKEN") or None,
        rebuild_on_startup=os.getenv("OMNISVERA_REBUILD_ON_STARTUP", "false").lower()
        in {"1", "true", "yes", "sim"},
    )
