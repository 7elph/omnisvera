from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import unicodedata


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_srd_monsters.json"
ART_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_srd_monster_art.json"
AI_ART_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_monster_ai_art.json"
ART_MEDIA_ROOT = "zz_media/ui/icons/monsters/illustrated-bestiary"


def _search_key(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()


@lru_cache(maxsize=1)
def load_monster_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    monsters = payload.get("monsters", [])
    if payload.get("count") != 255 or len(monsters) != 255:
        raise RuntimeError("O catálogo local da SRD Old Dragon 2 está incompleto.")
    art_manifest = load_monster_art_manifest()
    collection = art_manifest["collection"]
    mappings = art_manifest["mappings"]
    ai_payload = load_monster_ai_art()
    ai_mappings = ai_payload["mappings"]
    enriched_monsters = []
    for monster in monsters:
        art_id = mappings.get(monster["id"])
        enriched = dict(monster)
        if art_id:
            enriched.update(
                {
                    "image_path": f"{ART_MEDIA_ROOT}/{art_id}.webp",
                    "image_attribution": f"{collection['creator']} · {collection['title']}",
                    "image_license": collection["license"],
                    "image_license_url": collection["license_url"],
                    "image_source_url": collection["source_url"],
                }
            )
        elif monster["id"] in ai_mappings:
            enriched.update(
                {
                    "image_path": ai_mappings[monster["id"]],
                    "image_attribution": ai_payload.get("attributions", {}).get(monster["id"], "Mesa Omnisvera · FLUX"),
                    "image_license": "Uso interno de mesa",
                    "image_license_url": None,
                    "image_source_url": None,
                }
            )
        else:
            enriched.update(
                {
                    "image_path": None,
                    "image_attribution": None,
                    "image_license": None,
                    "image_license_url": None,
                    "image_source_url": None,
                }
            )
        from .monster_encounters import encounter_defaults
        enriched['encounter_defaults'] = encounter_defaults(monster)
        enriched_monsters.append(enriched)
    return {**payload, "monsters": enriched_monsters, "art_collection": collection}


@lru_cache(maxsize=1)
def load_monster_art_manifest() -> dict:
    payload = json.loads(ART_MANIFEST_PATH.read_text(encoding="utf-8"))
    collection = payload.get("collection") or {}
    mappings = payload.get("mappings") or {}
    if payload.get("schema_version") != 1 or not collection.get("creator") or not isinstance(mappings, dict):
        raise RuntimeError("O manifesto de imagens do bestiário é inválido.")
    return payload


def list_monster_catalog(query: str = "", category: str = "") -> dict:
    payload = load_monster_catalog()
    query_key = _search_key(query.strip())
    category_key = _search_key(category.strip())
    monsters = [
        monster
        for monster in payload["monsters"]
        if (not query_key or query_key in _search_key(" ".join((monster["name"], monster.get("category", ""), monster.get("habitat", "")))))
        and (not category_key or category_key == _search_key(monster.get("category", "")))
    ]
    return {
        "catalog": payload["catalog"],
        "art_collection": payload["art_collection"],
        "count": len(monsters),
        "total": payload["count"],
        "image_count": sum(1 for monster in monsters if monster.get("image_path")),
        "monsters": monsters,
    }


def get_catalog_monster(monster_id: str) -> dict | None:
    return next((monster for monster in load_monster_catalog()["monsters"] if monster["id"] == monster_id), None)


def load_monster_ai_art() -> dict:
    if not AI_ART_PATH.exists():
        return {"schema_version": 1,
                "collection": {"id": "mesa-omnisvera-flux", "title": "Mesa Omnisvera (FLUX)",
                               "creator": "Mesa Omnisvera", "license": "Uso interno de mesa"},
                "mappings": {}}
    payload = json.loads(AI_ART_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("mappings"), dict):
        raise RuntimeError("O registro de arte FLUX dos monstros é inválido.")
    return payload


def bind_monster_ai_art(monster_id: str, image_path: str, *, attribution: str | None = None) -> bool:
    """Registra a arte aprovada; nunca sobrescreve um vínculo existente."""
    payload = load_monster_ai_art()
    if get_catalog_monster(monster_id) is None:
        raise ValueError("Monstro desconhecido no bestiário")
    if monster_id in payload["mappings"]:
        return False
    payload["mappings"][monster_id] = image_path
    if attribution:
        payload.setdefault("attributions", {})[monster_id] = attribution
    AI_ART_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    load_monster_catalog.cache_clear()
    return True
