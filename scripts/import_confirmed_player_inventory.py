from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.config import get_settings  # noqa: E402
from app.player_inventory import upsert_inventory  # noqa: E402
from app.vault_reader import read_markdown_note  # noqa: E402


CONFIRMED = {
    "vezemir": [
        ("Items/Grisalma.md", 1, True, "Arma principal"),
        ("Items/Muralha de Dorn.md", 1, True, "Escudo principal"),
        ("Items/O Medalhão.md", 1, True, "Item pessoal"),
    ],
    "varkh": [
        ("Items/01 Armas/Espada curta.md", 1, True, None),
        ("Items/01 Armas/Adaga.md", 2, True, None),
        ("Items/01 Armas/Arco curto.md", 1, False, None),
        ("Items/Máscara de Médico da Peste de Varkh.md", 1, True, "Equipamento pessoal"),
    ],
    "raziel": [
        ("Items/Adagas de Espectro Fantasma.md", 2, True, "Par de adagas; regra base de Adaga"),
        ("Items/Manto Primordial do Ancião.md", 1, True, "Mecanicamente, manto comum"),
    ],
    "morthak": [],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa apenas posses confirmadas nas fichas dos jogadores.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    planned = []
    for profile_id, entries in CONFIRMED.items():
        for relative, quantity, equipped, notes in entries:
            path = settings.vault_path / relative
            if not path.exists():
                raise SystemExit(f"MISSING: {relative}")
            note = read_markdown_note(path, settings.vault_path)
            if note.type != "item":
                raise SystemExit(f"NOT_ITEM: {relative}")
            planned.append((profile_id, note, quantity, equipped, notes))
    for profile_id, note, quantity, equipped, notes in planned:
        prefix = "APPLY" if args.apply else "DRY-RUN"
        print(f"{prefix}: {profile_id} <- {note.title} x{quantity}{' [equipado]' if equipped else ''}")
        if args.apply:
            upsert_inventory(
                settings.database_path,
                profile_id=profile_id,
                item_path=note.path,
                item_title=note.title,
                quantity=quantity,
                equipped=equipped,
                notes=notes,
            )
    print(f"TOTAL={len(planned)}")


if __name__ == "__main__":
    main()
