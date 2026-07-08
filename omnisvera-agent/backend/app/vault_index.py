from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .access import AccessMode, is_player_safe_row, sanitize_player_note
from .vault_reader import VaultNote


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(database_path: Path) -> None:
    with connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                aliases TEXT NOT NULL,
                type TEXT,
                visibility TEXT,
                tags TEXT NOT NULL,
                content TEXT NOT NULL,
                frontmatter TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_path ON notes(path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(type)")


def rebuild_index(database_path: Path, notes: list[VaultNote]) -> int:
    init_db(database_path)
    with connect(database_path) as conn:
        conn.execute("DELETE FROM notes")
        conn.executemany(
            """
            INSERT INTO notes (
                path, title, aliases, type, visibility, tags, content, frontmatter, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    note.path,
                    note.title,
                    json.dumps(note.aliases, ensure_ascii=False),
                    note.type,
                    note.visibility,
                    json.dumps(note.tags, ensure_ascii=False),
                    note.content,
                    json.dumps(note.frontmatter, ensure_ascii=False, default=str),
                    note.updated_at,
                )
                for note in notes
            ],
        )
    return len(notes)


def row_to_note(row: sqlite3.Row, include_content: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": row["id"],
        "path": row["path"],
        "title": row["title"],
        "aliases": json.loads(row["aliases"] or "[]"),
        "type": row["type"],
        "visibility": row["visibility"],
        "tags": json.loads(row["tags"] or "[]"),
        "updated_at": row["updated_at"],
    }
    if include_content:
        data["content"] = row["content"]
        data["frontmatter"] = json.loads(row["frontmatter"] or "{}")
    return data


def _row_allowed(row: sqlite3.Row, access_mode: AccessMode = "gm") -> bool:
    return access_mode == "gm" or is_player_safe_row(row)


def list_notes(database_path: Path, limit: int = 500, access_mode: AccessMode = "gm") -> list[dict[str, Any]]:
    init_db(database_path)
    with connect(database_path) as conn:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY title COLLATE NOCASE ASC LIMIT ?",
            (limit if access_mode == "gm" else limit * 4,),
        ).fetchall()
    filtered = [row for row in rows if _row_allowed(row, access_mode)]
    return [row_to_note(row) for row in filtered[:limit]]


def get_note(database_path: Path, note_id: int, access_mode: AccessMode = "gm") -> dict[str, Any] | None:
    init_db(database_path)
    with connect(database_path) as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row or not _row_allowed(row, access_mode):
        return None
    note = row_to_note(row, include_content=True)
    return sanitize_player_note(note) if access_mode == "player" else note


def get_notes_by_ids(
    database_path: Path,
    note_ids: list[int],
    access_mode: AccessMode = "gm",
) -> list[dict[str, Any]]:
    if not note_ids:
        return []
    init_db(database_path)
    placeholders = ",".join("?" for _ in note_ids)
    with connect(database_path) as conn:
        rows = conn.execute(f"SELECT * FROM notes WHERE id IN ({placeholders})", note_ids).fetchall()
    by_id = {row["id"]: row_to_note(row) for row in rows if _row_allowed(row, access_mode)}
    return [by_id[note_id] for note_id in note_ids if note_id in by_id]


def all_notes_for_search(database_path: Path) -> list[sqlite3.Row]:
    init_db(database_path)
    with connect(database_path) as conn:
        return conn.execute("SELECT * FROM notes").fetchall()
