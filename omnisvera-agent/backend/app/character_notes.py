"""Personal sheet notes, separate from combat state, public ledger and Vault."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from pydantic import BaseModel, ConfigDict, Field


class CharacterNotesWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    content: str = Field(max_length=12000)
    version: int = Field(ge=0)


class NotesConflictError(ValueError):
    pass


def _connect(database: Path):
    connection = sqlite3.connect(database, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS character_notes (
        character_id TEXT PRIMARY KEY, content TEXT NOT NULL,
        version INTEGER NOT NULL, updated_at TEXT NOT NULL
    )""")
    return connection


def _read(connection, character_id):
    row = connection.execute("SELECT * FROM character_notes WHERE character_id=?", (character_id,)).fetchone()
    return dict(row) if row else {"character_id": character_id, "content": "", "version": 0, "updated_at": None}


def read_notes(database: Path, character_id: str):
    with closing(_connect(database)) as connection:
        return _read(connection, character_id)


def save_notes(database: Path, character_id: str, request: CharacterNotesWrite):
    with closing(_connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        current = _read(connection, character_id)
        # A lost response can be retried without another write/version increment.
        if current["content"] == request.content:
            return current
        if current["version"] != request.version:
            raise NotesConflictError("As anotações mudaram em outro dispositivo. Copie seu rascunho e recarregue as notas salvas antes de tentar novamente.")
        connection.execute("""INSERT INTO character_notes VALUES(?,?,?,?)
            ON CONFLICT(character_id) DO UPDATE SET content=excluded.content,
            version=excluded.version, updated_at=excluded.updated_at""",
            (character_id, request.content, current["version"] + 1, datetime.now(timezone.utc).isoformat()))
        return _read(connection, character_id)
