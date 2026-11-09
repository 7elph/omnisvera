"""Terrain edits made by the Master in the 3.0 map editor, shared with every player.

One row per terrain name: the full tile, height and prop lists (the client's base map stays the
reference; this is the edited copy). Versioned so two open editors don't overwrite each other.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

MAX_CELLS = 256 * 256
MAX_PROPS = 4000
PROP_KEYS = {"name", "atlas", "rect", "pivot", "x", "y"}


class TerrainConflict(Exception):
    pass


def _connect(database: Path) -> sqlite3.Connection:
    db = sqlite3.connect(database, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS terrain_edits (name TEXT PRIMARY KEY, body TEXT NOT NULL, "
               "version INTEGER NOT NULL, updated_at TEXT NOT NULL)")
    return db


def get_terrain(database: Path, name: str) -> dict:
    with closing(_connect(database)) as db:
        row = db.execute("SELECT body, version, updated_at FROM terrain_edits WHERE name=?", (name,)).fetchone()
    if not row:
        return {"name": name, "version": 0, "edited": False}
    return {"name": name, "version": row[1], "updated_at": row[2], "edited": True, **json.loads(row[0])}


def terrain_version(database: Path, name: str) -> int:
    with closing(_connect(database)) as db:
        row = db.execute("SELECT version FROM terrain_edits WHERE name=?", (name,)).fetchone()
    return row[0] if row else 0


def _clean(payload: dict) -> dict:
    tiles, heights, props = payload.get("tiles"), payload.get("heights"), payload.get("props")
    if not isinstance(tiles, list) or not isinstance(heights, list) or not isinstance(props, list):
        raise ValueError("tiles, heights e props são obrigatórios")
    if not 0 < len(tiles) <= MAX_CELLS or len(heights) != len(tiles) or len(props) > MAX_PROPS:
        raise ValueError("tamanho de terreno inválido")
    clean_props = []
    for prop in props:
        if not isinstance(prop, dict) or not set(prop) <= PROP_KEYS:
            raise ValueError("objeto de cenário inválido")
        rect, pivot = prop.get("rect"), prop.get("pivot")
        if not (isinstance(rect, list) and len(rect) == 4 and isinstance(pivot, list) and len(pivot) == 2):
            raise ValueError("objeto de cenário inválido")
        atlas = str(prop.get("atlas", ""))
        if not atlas.startswith("res://assets/rom2_local/") or ".." in atlas:
            raise ValueError("imagem de objeto inválida")
        clean_props.append({"name": str(prop.get("name", ""))[:80], "atlas": atlas,
                            "rect": [int(v) for v in rect], "pivot": [float(v) for v in pivot],
                            "x": float(prop["x"]), "y": float(prop["y"])})
    return {"tiles": [int(t) for t in tiles], "heights": [round(float(h), 2) for h in heights], "props": clean_props}


def save_terrain(database: Path, name: str, payload: dict, expected_version: int) -> dict:
    body = _clean(payload)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database)) as db, db:
        row = db.execute("SELECT version FROM terrain_edits WHERE name=?", (name,)).fetchone()
        current = row[0] if row else 0
        if int(expected_version) != current:
            raise TerrainConflict("O terreno foi alterado em outra janela. Recarregue antes de salvar.")
        db.execute("INSERT INTO terrain_edits(name, body, version, updated_at) VALUES(?, ?, ?, ?) "
                   "ON CONFLICT(name) DO UPDATE SET body=excluded.body, version=excluded.version, updated_at=excluded.updated_at",
                   (name, json.dumps(body, separators=(",", ":")), current + 1, now))
    return {"name": name, "version": current + 1, "updated_at": now, "edited": True}


def reset_terrain(database: Path, name: str) -> dict:
    with closing(_connect(database)) as db, db:
        db.execute("DELETE FROM terrain_edits WHERE name=?", (name,))
    return {"name": name, "version": 0, "edited": False}
