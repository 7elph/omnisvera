from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .config import get_settings

# Status
AssetStatus = Literal["missing", "queued", "generating", "ready", "awaiting_approval", "approved", "failed", "ignored"]
MAX_CONCURRENT_GENERATIONS = 1

# Style presets versioned
STYLE_PRESETS = {
    "omnisvera.scene.v1": "dark medieval high fantasy, grounded painterly realism, professional RPG illustration, dramatic cinematic lighting, coherent material detail, serious worldbuilding tone, no text, no logo, no watermark, widescreen environment, cinematic composition",
    "omnisvera.session.v1": "dark medieval high fantasy, grounded painterly realism, professional RPG illustration, dramatic cinematic lighting, coherent material detail, serious worldbuilding tone, no text, no logo, no watermark, widescreen environment, cinematic composition",
    "omnisvera.item.v1": "dark medieval high fantasy, grounded painterly realism, professional RPG illustration, dramatic cinematic lighting, coherent material detail, serious worldbuilding tone, no text, no logo, no watermark, single object centered, clearly readable at small size, detailed fantasy item illustration, restrained background",
    "omnisvera.potion.v1": "dark medieval high fantasy, grounded painterly realism, professional RPG illustration, dramatic cinematic lighting, coherent material detail, serious worldbuilding tone, no text, no logo, no watermark, single object centered, clearly readable at small size, detailed fantasy item illustration, restrained background, clearly identifiable potion, readable silhouette",
}

ELIGIBLE_ASSET_TYPES = {
    "scene_cover",
    "session_cover",
    "item_art",
    "potion_hp",
    "potion_mp",
}

# Mapping for eligible special items (by name slug)
ELIGIBLE_SPECIAL_ITEMS = {"anel-runico", "anel-rúnico", "moeda-misteriosa", "escama-draconica", "escama-dracônica"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_asset_generation(database_path: Path | None = None) -> None:
    db = database_path or get_settings().database_path
    with closing(_connect(db)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_generation_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                style_version TEXT NOT NULL,
                status TEXT NOT NULL,
                prompt TEXT,
                image_path TEXT,
                error TEXT,
                source_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(entity_type, entity_id, style_version, source_hash)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_jobs_status ON asset_generation_jobs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_jobs_entity ON asset_generation_jobs(entity_type, entity_id)")
        if 'context_json' not in {row[1] for row in conn.execute('PRAGMA table_info(asset_generation_jobs)')}:
            conn.execute("ALTER TABLE asset_generation_jobs ADD COLUMN context_json TEXT")
        conn.commit()

def _source_hash(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

def _is_manual_asset(path: str | None) -> bool:
    # Manual assets are those not in generated prefix and already exist
    if not path:
        return False
    # If path exists and does not contain generated marker, consider manual
    # For now, any existing non-empty path is manual and should not be overwritten
    return True

def list_jobs(database_path: Path | None = None, status: str | None = None) -> list[dict[str, Any]]:
    db = database_path or get_settings().database_path
    init_asset_generation(db)
    with closing(_connect(db)) as conn:
        if status:
            cur = conn.execute("SELECT * FROM asset_generation_jobs WHERE status=? ORDER BY updated_at DESC", (status,))
        else:
            cur = conn.execute("SELECT * FROM asset_generation_jobs ORDER BY updated_at DESC")
        return [dict(row) for row in cur.fetchall()]

def get_job(job_id: int, database_path: Path | None = None) -> dict[str, Any] | None:
    db = database_path or get_settings().database_path
    with closing(_connect(db)) as conn:
        cur = conn.execute("SELECT * FROM asset_generation_jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def scan_eligible_gaps(database_path: Path | None = None) -> list[dict[str, Any]]:
    db = database_path or get_settings().database_path
    init_asset_generation(db)
    gaps: list[dict[str, Any]] = []
    with closing(_connect(db)) as conn:
        # scenes missing image
        for row in conn.execute("SELECT id, title, location_name, public_description, objective FROM scenes WHERE image_path IS NULL OR image_path=''"):
            data = {"title": row["title"], "location_name": row["location_name"], "public_description": row["public_description"], "objective": row["objective"]}
            gaps.append({"entity_type": "scene", "entity_id": str(row["id"]), "asset_type": "scene_cover", "style_version": "omnisvera.scene.v1", "source_data": data, "source_hash": _source_hash(data), "display_name": row["title"] or f"Scene {row['id']}"})
        # game_sessions missing image
        for row in conn.execute("SELECT id, title, public_summary FROM game_sessions WHERE image_path IS NULL OR image_path=''"):
            data = {"title": row["title"], "public_summary": row["public_summary"]}
            gaps.append({"entity_type": "game_session", "entity_id": str(row["id"]), "asset_type": "session_cover", "style_version": "omnisvera.session.v1", "source_data": data, "source_hash": _source_hash(data), "display_name": row["title"] or f"Session {row['id']}"})
        # special items missing
        for row in conn.execute("SELECT id, name, item_type, description FROM session_custom_items WHERE image_path IS NULL OR image_path=''"):
            slug = row["name"].lower().replace(" ", "-").strip()
            # Normalize
            import unicodedata
            slug_norm = "".join(c for c in unicodedata.normalize("NFD", slug) if unicodedata.category(c) != "Mn")
            if slug_norm in ELIGIBLE_SPECIAL_ITEMS or slug in ELIGIBLE_SPECIAL_ITEMS:
                data = {"name": row["name"], "item_type": row["item_type"], "description": row["description"]}
                gaps.append({"entity_type": "session_custom_item", "entity_id": str(row["id"]), "asset_type": "item_art", "style_version": "omnisvera.item.v1", "source_data": data, "source_hash": _source_hash(data), "display_name": row["name"]})
        # HP/MP potion icons - check if files exist, if not, create gap
        # These are not DB entities but UI icons expected at zz_media/ui/icons/items/pocao_hp.png etc
        # We treat as synthetic entities
        from pathlib import Path as _P
        vault = get_settings().vault_path
        for potion_type, display in [("potion_hp", "Poção HP"), ("potion_mp", "Poção MP")]:
            # Check if icon exists in painted or items
            candidates = [
                vault / f"zz_media/ui/icons/items/{potion_type}.png",
                vault / f"zz_media/ui/icons/painted/{potion_type}.png",
                vault / f"zz_media/ui/icons/items/pocao_{'hp' if potion_type=='potion_hp' else 'mp'}.png",
            ]
            exists = any(p.exists() for p in candidates)
            if not exists:
                data = {"potion_type": potion_type}
                gaps.append({"entity_type": "ui_icon", "entity_id": potion_type, "asset_type": potion_type, "style_version": "omnisvera.potion.v1", "source_data": data, "source_hash": _source_hash(data), "display_name": display})
    return gaps

def queue_missing_assets(database_path: Path | None = None) -> list[dict[str, Any]]:
    db = database_path or get_settings().database_path
    init_asset_generation(db)
    gaps = scan_eligible_gaps(db)
    queued: list[dict[str, Any]] = []
    with closing(_connect(db)) as conn:
        for gap in gaps:
            # Check if already has job with same source_hash and status not failed/ignored (dedup)
            cur = conn.execute("SELECT * FROM asset_generation_jobs WHERE entity_type=? AND entity_id=? AND style_version=? AND source_hash=?",
                               (gap["entity_type"], gap["entity_id"], gap["style_version"], gap["source_hash"]))
            existing = cur.fetchone()
            if existing:
                # If already ready/queued/generating, skip
                if existing["status"] in ("queued", "generating", "ready", "awaiting_approval", "approved"):
                    continue
                # If failed/ignored/missing, allow requeue by updating
                if existing["status"] in ("failed", "ignored", "missing"):
                    conn.execute("UPDATE asset_generation_jobs SET status='queued', updated_at=?, error=NULL WHERE id=?",
                                 (_now(), existing["id"]))
                    conn.commit()
                    queued.append(dict(existing))
                    continue
            # Check concurrent limit not needed here, just queue as missing->queued
            # Insert as queued, but first check if manual asset exists (should not queue if image_path already exists for that entity - but scan already filtered missing)
            try:
                conn.execute("INSERT INTO asset_generation_jobs (entity_type, entity_id, asset_type, style_version, status, source_hash, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                             (gap["entity_type"], gap["entity_id"], gap["asset_type"], gap["style_version"], "queued", gap["source_hash"], _now(), _now()))
                conn.commit()
                cur = conn.execute("SELECT * FROM asset_generation_jobs WHERE entity_type=? AND entity_id=? AND style_version=? AND source_hash=?",
                                   (gap["entity_type"], gap["entity_id"], gap["style_version"], gap["source_hash"]))
                row = cur.fetchone()
                if row:
                    queued.append(dict(row))
            except sqlite3.IntegrityError:
                # Duplicate due to race, skip
                pass
    return queued

def update_job_status(job_id: int, status: AssetStatus, error: str | None = None, image_path: str | None = None, database_path: Path | None = None) -> None:
    db = database_path or get_settings().database_path
    with closing(_connect(db)) as conn:
        fields = ["status=?", "updated_at=?"]
        params: list[Any] = [status, _now()]
        fields.append("error=?")
        params.append(error)
        if image_path is not None:
            fields.append("image_path=?")
            params.append(image_path)
        params.append(job_id)
        conn.execute(f"UPDATE asset_generation_jobs SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()

def bind_asset_to_entity(job: dict[str, Any], image_path: str, database_path: Path | None = None) -> None:
    db = database_path or get_settings().database_path
    entity_type = job["entity_type"]
    entity_id = job["entity_id"]
    # Protection: do not overwrite if entity already has image_path
    with closing(_connect(db)) as conn:
        if entity_type == "scene":
            cur = conn.execute("SELECT image_path FROM scenes WHERE id=?", (int(entity_id),))
            row = cur.fetchone()
            if row and row["image_path"]:
                return
            conn.execute("UPDATE scenes SET image_path=? WHERE id=?", (image_path, int(entity_id)))
        elif entity_type == "game_session":
            cur = conn.execute("SELECT image_path FROM game_sessions WHERE id=?", (int(entity_id),))
            row = cur.fetchone()
            if row and row["image_path"]:
                return
            conn.execute("UPDATE game_sessions SET image_path=? WHERE id=?", (image_path, int(entity_id)))
        elif entity_type == "session_custom_item":
            cur = conn.execute("SELECT image_path FROM session_custom_items WHERE id=?", (int(entity_id),))
            row = cur.fetchone()
            if row and row["image_path"]:
                return
            conn.execute("UPDATE session_custom_items SET image_path=? WHERE id=?", (image_path, int(entity_id)))
        elif entity_type == "ui_icon":
            # For potions, image_path is the file to create, no DB binding
            pass
        conn.commit()
