from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.player_actions import (  # noqa: E402
    create_player_action,
    list_player_actions,
    update_player_action,
)
from app.vault_index import rebuild_index  # noqa: E402
from app.vault_reader import VaultNote  # noqa: E402


def main() -> None:
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        database = Path(temp) / "companion.sqlite3"
        created = create_player_action(
            database,
            character_path="Characters/Individual/Vezemir.md",
            character_title="Vezemir",
            action_type="investigate",
            target_path="CAMPANHA/Rumors/Teste.md",
            target_title="Rumor de teste",
            intent="Examinar os rastros sem tocar na evidência.",
        )
        assert created["status"] == "submitted"
        assert len(list_player_actions(database)) == 1

        rebuild_index(
            database,
            [
                VaultNote(
                    path="Public.md",
                    title="Public",
                    aliases=[],
                    type="lore",
                    visibility="Público",
                    tags=["lore"],
                    content="Conteúdo público.",
                    frontmatter={"visibility": "Público"},
                    updated_at="2026-07-12T12:00:00+00:00",
                )
            ],
        )
        assert len(list_player_actions(database)) == 1

        answered = update_player_action(
            database,
            created["id"],
            status="answered",
            gm_response="Você encontra marcas recentes ao lado da estrada.",
        )
        assert answered is not None
        assert answered["status"] == "answered"
        assert answered["gm_response"].startswith("Você encontra")

        try:
            update_player_action(database, created["id"], status="invalid", gm_response=None)
        except ValueError:
            pass
        else:
            raise AssertionError("Estado inválido deveria ser rejeitado")

    print("companion player actions: PASS")


if __name__ == "__main__":
    main()
