from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import unicodedata


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_abilities.json"


def _search_key(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()


@lru_cache(maxsize=1)
def load_ability_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    abilities = payload.get("abilities", [])
    if payload.get("schema_version") != 1 or payload.get("count") != len(abilities):
        raise RuntimeError("O catálogo de habilidades está incompleto.")
    return payload


def list_ability_catalog(query: str = "", spec: str = "") -> dict:
    payload = load_ability_catalog()
    query_key = _search_key(query.strip())
    spec_key = _search_key(spec.strip())
    abilities = [
        ability
        for ability in payload["abilities"]
        if (not query_key or query_key in _search_key(f"{ability['title']} {ability.get('spec', '')} {ability.get('description', '')[:500]}"))
        and (not spec_key or spec_key == _search_key(ability.get("spec", "")))
    ]
    return {
        "catalog": payload["catalog"],
        "count": len(abilities),
        "total": payload["count"],
        "abilities": abilities,
    }


def get_catalog_ability(ability_id: str) -> dict | None:
    return next((ability for ability in load_ability_catalog()["abilities"] if ability["id"] == ability_id), None)
