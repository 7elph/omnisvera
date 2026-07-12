from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.player_progress import (  # noqa: E402
    add_event,
    list_events,
    list_quests,
    mark_events_read,
    upsert_quest,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        database = Path(temp_dir) / "progress.sqlite3"
        personal = add_event(
            database,
            profile_id="vezemir",
            kind="discovery",
            title="Nova pista",
            message="Um símbolo foi reconhecido.",
            note_path="CAMPANHA/Rumors/Pista.md",
        )
        group = add_event(
            database,
            profile_id="group",
            kind="quest_update",
            title="Missão atualizada",
            message="A estrada foi liberada.",
            note_path="CAMPANHA/Quests/Estrada.md",
        )
        assert len(list_events(database, profile_id="vezemir")) == 2
        assert len(list_events(database, profile_id="morthak")) == 1
        assert mark_events_read(database, profile_id="vezemir", event_ids=[personal["id"], group["id"]]) == 2
        assert all(event["read_at"] for event in list_events(database, profile_id="vezemir"))
        assert list_events(database, profile_id="morthak")[0]["read_at"] is None

        quest = upsert_quest(
            database,
            profile_id="group",
            note_path="CAMPANHA/Quests/Estrada.md",
            note_title="A Estrada",
            status="in_progress",
            progress="Encontrar a caravana.",
        )
        assert list_quests(database, profile_id="vezemir") == [quest]
        assert list_quests(database, profile_id="morthak") == [quest]

    print("companion player progress: PASS")


if __name__ == "__main__":
    main()
