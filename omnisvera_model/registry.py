from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json, write_json
from .paths import REGISTRY_PATH
from .schema import utc_now

STATUSES = {"experimental", "candidate", "approved", "rejected", "archived"}


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "production_model": None, "models": {}}
    return read_json(path)


def register(model_id: str, metadata: dict[str, Any], path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(path)
    status = str(metadata.get("status") or "experimental")
    if status not in STATUSES:
        raise ValueError("status de modelo inválido")
    registry["models"][model_id] = {**metadata, "status": status, "updated_at": utc_now()}
    write_json(path, registry)
    return registry["models"][model_id]


def promote(model_id: str, gates: dict[str, Any], path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(path)
    if model_id not in registry["models"]:
        raise ValueError("modelo não registrado")
    if registry["models"][model_id].get("status") == "experimental" or registry["models"][model_id].get("experimental_only"):
        raise ValueError("artefato experimental não pode ser promovido")
    required = ("security_100_percent", "no_critical_leaks", "no_invented_sources",
                "regression_30_of_30", "factuality_not_worse", "naturalness_improved", "fallback_ok")
    missing = [key for key in required if gates.get(key) is not True]
    if missing:
        raise ValueError("gates de promoção falharam: " + ", ".join(missing))
    previous = registry.get("production_model")
    registry["models"][model_id]["status"] = "approved"
    registry["models"][model_id]["rollback_target"] = previous
    registry["models"][model_id]["promotion_gates"] = gates
    registry["production_model"] = model_id
    write_json(path, registry)
    return registry["models"][model_id]


def rollback(path: Path = REGISTRY_PATH) -> str | None:
    registry = load_registry(path)
    current = registry.get("production_model")
    if not current:
        return None
    target = registry["models"].get(current, {}).get("rollback_target")
    registry["models"][current]["status"] = "archived"
    registry["production_model"] = target
    write_json(path, registry)
    return target
