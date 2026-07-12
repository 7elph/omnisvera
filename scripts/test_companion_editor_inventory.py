from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.note_editor import EditConflictError, read_editable_note, save_editable_note  # noqa: E402
from app.player_inventory import list_inventory, upsert_inventory  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        vault = root / "vault"
        vault.mkdir()
        note = vault / "Nota.md"
        note.write_text("---\ntype: lore\n---\n# Nota\n\nTexto.\n", encoding="utf-8")
        opened = read_editable_note(vault, "Nota.md")
        saved = save_editable_note(vault, root / "backups", "Nota.md", opened["content"].replace("Texto.", "Texto novo."), opened["content_hash"])
        assert "Texto novo." in saved["content"]
        assert list((root / "backups").rglob("*.md"))
        try:
            save_editable_note(vault, root / "backups", "Nota.md", saved["content"], opened["content_hash"])
        except EditConflictError:
            pass
        else:
            raise AssertionError("Conflito de edição não detectado")

        database = root / "inventory.sqlite3"
        item = upsert_inventory(database, profile_id="raziel", item_path="Items/Frasco.md", item_title="Frasco", quantity=2, equipped=True, notes="No cinto")
        assert item["equipped"] is True
        assert list_inventory(database, "raziel")[0]["quantity"] == 2
        assert list_inventory(database, "vezemir") == []

    print("companion editor and inventory: PASS")


if __name__ == "__main__":
    main()
