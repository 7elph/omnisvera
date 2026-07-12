from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
sys.path.insert(0, str(BACKEND))

from app.player_actions import create_player_action, list_player_actions  # noqa: E402
from app.access import AccessContext  # noqa: E402
from app.main import _personalize_player_question  # noqa: E402
from app.player_discoveries import (  # noqa: E402
    list_discoveries,
    reveal_discovery,
    revoke_discovery,
)


def main() -> None:
    access = AccessContext(
        mode="player",
        profile_id="vezemir",
        character_path="Characters/Individual/Vezemir.md",
        character_title="Vezemir",
    )
    assert _personalize_player_question("Quem sou eu?", access) == "Quem é Vezemir?"
    assert _personalize_player_question("O que existe em Nimalis?", access) == "O que existe em Nimalis?"

    with tempfile.TemporaryDirectory() as temp_dir:
        database = Path(temp_dir) / "profiles.sqlite3"
        create_player_action(
            database,
            character_path="Characters/Individual/Vezemir.md",
            character_title="Vezemir",
            action_type="investigate",
            target_path="Locations/Nimalis.md",
            target_title="Nimalis",
            intent="Examinar os portões.",
        )
        create_player_action(
            database,
            character_path="Characters/Individual/Morthak.md",
            character_title="Morthak",
            action_type="theory",
            target_path="Lore/O Véu Cinzento.md",
            target_title="O Véu Cinzento",
            intent="Comparar os sinais.",
        )
        vezemir_actions = list_player_actions(
            database, character_path="Characters/Individual/Vezemir.md"
        )
        assert len(vezemir_actions) == 1
        assert vezemir_actions[0]["character_title"] == "Vezemir"
        assert len(list_player_actions(database)) == 2

        discovery = reveal_discovery(
            database,
            profile_id="vezemir",
            note_path="Locations/Nimalis.md",
            note_title="Nimalis",
        )
        assert list_discoveries(database, profile_id="vezemir") == [discovery]
        assert list_discoveries(database, profile_id="morthak") == []
        assert revoke_discovery(database, discovery["id"])
        assert list_discoveries(database, profile_id="vezemir") == []

    print("companion player profiles: PASS")


if __name__ == "__main__":
    main()
