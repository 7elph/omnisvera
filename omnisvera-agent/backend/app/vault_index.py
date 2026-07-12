from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .access import AccessMode, is_player_safe_row, normalize_text, sanitize_player_note, sanitize_player_summary
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
        conn.executemany(
            """
            INSERT INTO notes (
                path, title, aliases, type, visibility, tags, content, frontmatter, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                title = excluded.title,
                aliases = excluded.aliases,
                type = excluded.type,
                visibility = excluded.visibility,
                tags = excluded.tags,
                content = excluded.content,
                frontmatter = excluded.frontmatter,
                updated_at = excluded.updated_at
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
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS current_note_paths (path TEXT PRIMARY KEY)")
        conn.execute("DELETE FROM current_note_paths")
        conn.executemany(
            "INSERT INTO current_note_paths(path) VALUES (?)",
            [(note.path,) for note in notes],
        )
        conn.execute("DELETE FROM notes WHERE path NOT IN (SELECT path FROM current_note_paths)")
    return len(notes)


def _json_dict(value: str) -> dict[str, Any]:
    try:
        data = json.loads(value or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def row_to_note(row: sqlite3.Row, include_content: bool = False) -> dict[str, Any]:
    frontmatter = _json_dict(row["frontmatter"])
    if str(row["type"] or "").strip().lower() == "character":
        status = _first_string(
            frontmatter.get("status"),
            frontmatter.get("campaign_status"),
            frontmatter.get("NoteStatus"),
        )
    else:
        status = _first_string(
            frontmatter.get("quest_status"),
            frontmatter.get("campaign_status"),
            frontmatter.get("handout_status"),
            frontmatter.get("status"),
            frontmatter.get("NoteStatus"),
        )
    data: dict[str, Any] = {
        "id": row["id"],
        "path": row["path"],
        "title": row["title"],
        "aliases": json.loads(row["aliases"] or "[]"),
        "type": row["type"],
        "visibility": row["visibility"],
        "tags": json.loads(row["tags"] or "[]"),
        "cover": _first_string(frontmatter.get("cover"), frontmatter.get("thumbnail"), frontmatter.get("portrait")),
        "thumbnail": _first_string(frontmatter.get("thumbnail"), frontmatter.get("portrait"), frontmatter.get("cover")),
        "status": status,
        "description": _first_string(frontmatter.get("description"), frontmatter.get("info"), frontmatter.get("summary")),
        "updated_at": row["updated_at"],
    }
    if include_content:
        data["content"] = row["content"]
        data["frontmatter"] = frontmatter
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
    notes = [row_to_note(row) for row in filtered[:limit]]
    return [sanitize_player_summary(note) for note in notes] if access_mode == "player" else notes


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
    by_id = {
        row["id"]: (
            sanitize_player_summary(row_to_note(row))
            if access_mode == "player"
            else row_to_note(row)
        )
        for row in rows
        if _row_allowed(row, access_mode)
    }
    return [by_id[note_id] for note_id in note_ids if note_id in by_id]


def all_notes_for_search(database_path: Path) -> list[sqlite3.Row]:
    init_db(database_path)
    with connect(database_path) as conn:
        return conn.execute("SELECT * FROM notes").fetchall()


def index_signature(database_path: Path) -> tuple[int, str | None]:
    init_db(database_path)
    with connect(database_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS count, MAX(updated_at) AS latest FROM notes").fetchone()
    return int(row["count"] or 0), row["latest"]


def _normalize_lookup(value: str) -> str:
    clean = (
        value.strip()
        .replace("\\", "/")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("´", "'")
        .split("#", 1)[0]
    )
    if clean.lower().endswith(".md"):
        clean = clean[:-3]
    clean = normalize_text(clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip().strip("/")


def _lookup_variants(value: str) -> set[str]:
    base = _normalize_lookup(value)
    if not base:
        return set()

    variants = {base}
    if "/" in base:
        variants.add(base.split("/")[-1])

    expanded: set[str] = set()
    for item in variants:
        expanded.add(item)
        expanded.add(re.sub(r"^(o|a|os|as|um|uma)\s+", "", item).strip())
        expanded.add(re.sub(r"[-_]+", " ", item).strip())
        expanded.add(re.sub(r"['’´`]+", "", item).strip())
        expanded.add(re.sub(r"[^a-z0-9/]+", "", item).strip())

    return {item for item in expanded if item}


def _candidate_lookup_variants(value: str) -> set[str]:
    variants = _lookup_variants(value)
    token_variants: set[str] = set()
    for item in list(variants):
        # Let wikilinks such as [[Varkh]] resolve to notes titled/stemmed
        # "Varkh Nimalis" without turning one-letter/common words into matches.
        for token in re.split(r"[^a-z0-9]+", item):
            if len(token) >= 4:
                token_variants.add(token)
    return variants | token_variants


def resolve_note(database_path: Path, target: str, access_mode: AccessMode = "gm") -> dict[str, Any] | None:
    wanted_variants = _lookup_variants(target.split("|", 1)[0])
    if not wanted_variants:
        return None

    init_db(database_path)
    with connect(database_path) as conn:
        rows = conn.execute("SELECT * FROM notes").fetchall()

    matches: list[sqlite3.Row] = []
    for row in rows:
        if not _row_allowed(row, access_mode):
            continue

        path = row["path"]
        title = row["title"]
        stem = Path(row["path"]).stem
        aliases = json.loads(row["aliases"] or "[]")
        candidates: set[str] = set()
        for value in [path, title, stem, *aliases]:
            candidates.update(_candidate_lookup_variants(str(value)))

        if wanted_variants & candidates:
            matches.append(row)

    if not matches:
        return None

    def rank(row: sqlite3.Row) -> tuple[int, str]:
        path = row["path"]
        note_type = _normalize_lookup(row["type"] or "")
        title_lookup = _normalize_lookup(row["title"])
        stem_lookup = _normalize_lookup(Path(path).stem)
        title_variants = _lookup_variants(row["title"])
        stem_variants = _lookup_variants(Path(path).stem)
        path_variants = _lookup_variants(path)
        score = 0
        if not path.startswith(("Workflow/", "Templates/", "omnisvera-agent/")):
            score += 120
        else:
            score -= 80
        if note_type in {"character", "location", "territory", "faction", "item", "race", "class", "quest", "rumor", "story"}:
            score += 50
        if wanted_variants & title_variants:
            score += 30
        if wanted_variants & stem_variants:
            score += 25
        if any(title_lookup == wanted or title_lookup.startswith(f"{wanted} ") for wanted in wanted_variants):
            score += 80
        if any(stem_lookup == wanted or stem_lookup.startswith(f"{wanted} ") for wanted in wanted_variants):
            score += 80
        if note_type == "character" and any(
            re.search(rf"(^|[^a-z0-9]){re.escape(wanted)}([^a-z0-9]|$)", title_lookup)
            or re.search(rf"(^|[^a-z0-9]){re.escape(wanted)}([^a-z0-9]|$)", stem_lookup)
            for wanted in wanted_variants
        ):
            score += 35
        if wanted_variants & path_variants:
            score += 10
        return (score, path)

    matches.sort(key=rank, reverse=True)
    note = row_to_note(matches[0])
    return sanitize_player_summary(note) if access_mode == "player" else note
