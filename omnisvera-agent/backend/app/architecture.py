"""Validated, read-only access to the code component index.

The component map is documentation of code ownership, not campaign data. It is
validated once per process so a malformed or incomplete map cannot be presented
as an authoritative architecture contract.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COMPONENT_MAP_PATH = ROOT / "docs" / "AI_COMPONENT_MAP.json"

_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "WEBSOCKET"}
_REQUIRED_COMPONENT_FIELDS = {
    "id", "backend", "frontend", "storage", "routes", "contracts",
    "scope_rule", "extension",
}


class ArchitectureContractError(ValueError):
    """The component map does not satisfy the runtime contract."""


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArchitectureContractError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ArchitectureContractError(f"{field} must be a non-empty list")
    result = []
    for index, item in enumerate(value):
        result.append(_require_string(item, f"{field}[{index}]"))
    return result


def _validate_component(component: Any, index: int) -> dict[str, Any]:
    if not isinstance(component, dict):
        raise ArchitectureContractError(f"components[{index}] must be an object")
    missing = _REQUIRED_COMPONENT_FIELDS - set(component)
    if missing:
        raise ArchitectureContractError(
            f"components[{index}] missing fields: {', '.join(sorted(missing))}"
        )
    component_id = _require_string(component["id"], f"components[{index}].id")
    backend = _require_string_list(component["backend"], f"{component_id}.backend")
    frontend = _require_string_list(component["frontend"], f"{component_id}.frontend")
    storage = _require_string_list(component["storage"], f"{component_id}.storage")
    contracts = _require_string_list(component["contracts"], f"{component_id}.contracts")
    scope_rule = _require_string(component["scope_rule"], f"{component_id}.scope_rule")
    extension = _require_string(component["extension"], f"{component_id}.extension")
    routes = component["routes"]
    if not isinstance(routes, list) or not routes:
        raise ArchitectureContractError(f"{component_id}.routes must be a non-empty list")
    normalized_routes = []
    for route_index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise ArchitectureContractError(f"{component_id}.routes[{route_index}] must be an object")
        method = _require_string(route.get("method"), f"{component_id}.routes[{route_index}].method").upper()
        path = _require_string(route.get("path"), f"{component_id}.routes[{route_index}].path")
        if method not in _METHODS:
            raise ArchitectureContractError(f"{component_id}.routes[{route_index}] unsupported method {method}")
        if not path.startswith("/"):
            raise ArchitectureContractError(f"{component_id}.routes[{route_index}] path must start with /")
        normalized_routes.append({"method": method, "path": path})
    return {
        "id": component_id,
        "backend": backend,
        "frontend": frontend,
        "storage": storage,
        "routes": normalized_routes,
        "contracts": contracts,
        "scope_rule": scope_rule,
        "extension": extension,
    }


@lru_cache(maxsize=1)
def _load_component_map(path_value: str) -> dict[str, Any]:
    path = Path(path_value)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ArchitectureContractError(f"component map not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ArchitectureContractError(f"component map is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ArchitectureContractError("component map root must be an object")
    if raw.get("schema_version") != 1:
        raise ArchitectureContractError("unsupported component map schema_version")
    if raw.get("kind") != "code_component_index":
        raise ArchitectureContractError("component map kind must be code_component_index")
    if raw.get("campaign_data") is not False:
        raise ArchitectureContractError("component map must not contain campaign_data")
    scope = _require_string(raw.get("scope"), "scope")
    approval_policy = _require_string(raw.get("approval_policy"), "approval_policy")
    components = raw.get("components")
    if not isinstance(components, list) or not components:
        raise ArchitectureContractError("components must be a non-empty list")
    normalized = [_validate_component(component, index) for index, component in enumerate(components)]
    ids = [component["id"] for component in normalized]
    if len(ids) != len(set(ids)):
        raise ArchitectureContractError("component ids must be unique")
    return {
        "schema_version": 1,
        "kind": "code_component_index",
        "campaign_data": False,
        "scope": scope,
        "approval_policy": approval_policy,
        "components": normalized,
    }


def load_component_map(path: Path | None = None) -> dict[str, Any]:
    """Return a defensive copy of the validated component map."""
    return deepcopy(_load_component_map(str(path or COMPONENT_MAP_PATH)))


def list_components() -> list[dict[str, Any]]:
    return deepcopy(load_component_map()["components"])


def get_component(component_id: str) -> dict[str, Any] | None:
    for component in list_components():
        if component["id"] == component_id:
            return component
    return None


def route_ownership() -> list[dict[str, Any]]:
    owners: dict[tuple[str, str], set[str]] = {}
    for component in list_components():
        for route in component["routes"]:
            owners.setdefault((route["method"], route["path"]), set()).add(component["id"])
    return [
        {"method": method, "path": path, "component_ids": sorted(component_ids)}
        for (method, path), component_ids in sorted(owners.items())
    ]
