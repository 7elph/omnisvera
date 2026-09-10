from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import unicodedata


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_srd_monsters.json"
ART_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_srd_monster_art.json"
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
    enriched_monsters = []
    for monster in monsters:
        art_id = mappings.get(monster["id"])
        enriched = dict(monster)
        enriched.update(
            {
                "image_path": f"{ART_MEDIA_ROOT}/{art_id}.webp" if art_id else None,
                "image_attribution": f"{collection['creator']} · {collection['title']}" if art_id else None,
                "image_license": collection["license"] if art_id else None,
                "image_license_url": collection["license_url"] if art_id else None,
                "image_source_url": collection["source_url"] if art_id else None,
            }
        )
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
