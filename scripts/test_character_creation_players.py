from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "omnisvera-agent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.character_creation import get_or_create_sheet, update_sheet_step  # noqa: E402
from app.vault_reader import read_markdown_note  # noqa: E402


PLAYERS = {
    "vezemir": ("Vezemir.md", "Meio-Elfo.md", "Guerreiro.md"),
    "varkh": ("Varkh Nimalis.md", "Kenku.md", "Alquimista.md"),
    "raziel": ("Raziel.md", "Vampiro.md", "Hemomante.md"),
    "morthak": ("Morthak.md", "Morto-Vivo Esqueleto.md", "Mago.md"),
}


def as_note(path: Path) -> dict:
    return vars(read_markdown_note(path, ROOT))


def step(sheet: dict, key: str) -> dict:
    return next(item for item in sheet["steps"] if item["key"] == key)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "characters.sqlite3"
        for profile_id, (character_file, race_file, class_file) in PLAYERS.items():
            character = as_note(ROOT / "Characters" / "Individual" / character_file)
            race = as_note(ROOT / "Races" / race_file)
            character_class = as_note(ROOT / "Classes" / class_file)
            sheet = get_or_create_sheet(
                database,
                profile_id=profile_id,
                character_path=character["path"],
                character_title=character["title"],
                note=character,
                race_note=race,
                class_note=character_class,
            )

            race_step = step(sheet, "race")
            class_step = step(sheet, "character_class")
            assert race_step["guide"]["instruction"]
            assert class_step["guide"]["instruction"]
            assert race_step["guide"]["sources"][0]["title"] == race["title"]
            assert class_step["guide"]["sources"][0]["title"] == character_class["title"]
            assert class_step["guide"]["sources"][0]["level_one"], profile_id
            assert step(sheet, "attacks")["guide"]["checklist"]
            assert step(sheet, "equipment")["guide"]["checklist"]
            assert step(sheet, "armor")["guide"]["checklist"]

        # A field explicitly touched by a player must not be repopulated from
        # the Vault when references are refreshed.
        updated = update_sheet_step(
            database,
            profile_id="vezemir",
            step_key="race",
            fields={"movement": None},
        )
        assert updated is not None
        character = as_note(ROOT / "Characters" / "Individual" / "Vezemir.md")
        refreshed = get_or_create_sheet(
            database,
            profile_id="vezemir",
            character_path=character["path"],
            character_title=character["title"],
            note=character,
            race_note=as_note(ROOT / "Races" / "Meio-Elfo.md"),
            class_note=as_note(ROOT / "Classes" / "Guerreiro.md"),
        )
        assert step(refreshed, "race")["fields"]["movement"] is None

    print("CHARACTER_CREATION_PLAYERS_PASS: 4/4")


if __name__ == "__main__":
    main()
