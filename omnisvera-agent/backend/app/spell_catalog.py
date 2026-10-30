from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import unicodedata


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_spells.json"


def _search_key(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()


@lru_cache(maxsize=1)
def load_spell_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    spells = payload.get("spells", [])
    if payload.get("schema_version") != 1 or payload.get("count") != len(spells):
        raise RuntimeError("O catálogo de magias está incompleto.")
    return payload


def list_spell_catalog(query: str = "", tradition: str = "", circle: int | None = None) -> dict:
    payload = load_spell_catalog()
    query_key = _search_key(query.strip())
    tradition_key = tradition.strip().casefold()
    spells = [
        spell
        for spell in payload["spells"]
        if (not query_key or query_key in _search_key(f"{spell['name']} {spell.get('school', '')} {spell.get('description', '')[:500]}"))
        and (not tradition_key or tradition_key == str(spell.get("tradition", "")).casefold())
        and (circle is None or circle == spell.get("circle"))
    ]
    from .catalog_spell_contracts import catalogue_automation
    return {
        "catalog": payload["catalog"],
        "count": len(spells),
        "total": payload["count"],
        "spells": [{**spell, 'automation': catalogue_automation(spell)} for spell in spells],
    }


def get_catalog_spell(spell_id: str) -> dict | None:
    return next((spell for spell in load_spell_catalog()["spells"] if spell["id"] == spell_id), None)
