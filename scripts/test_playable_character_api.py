from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def character_note(name: str, race: str, character_class: str, hp: int, thumbnail: str) -> str:
    return f"""---
type: character
visibility: Público
spoiler_level: none
gm_secret: false
role: player
race: {race}
class: {character_class}
level: 1
status: Vivo
location: \"[[Nimalis]]\"
thumbnail: {thumbnail}
---

# {name}

## O que os jogadores sabem

{name} é um aventureiro conhecido.

## Atributos

| Status | Valor |
|---|---:|
| Força | 13 |
| Destreza | 10 |
| Constituição | 12 |
| Inteligência | 9 |
| Sabedoria | 11 |
| Carisma | 8 |

| Combate e recursos | Valor |
|---|---:|
| Classe de Armadura | 14 |
| Pontos de Vida | {hp} |
| Bônus de Ataque | +1 |
| Movimento | 9 m |

## História

Uma história pública curta.
"""


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        vault = root / "vault"
        database = root / "companion.sqlite3"
        (vault / "Characters" / "Individual").mkdir(parents=True)
        (vault / "Items").mkdir(parents=True)
        (vault / "zz_media" / "thumbnails").mkdir(parents=True)
        (vault / "Characters" / "Individual" / "Vezemir.md").write_text(
            character_note("Vezemir", "Meio-Elfo", "Guerreiro", 12, "zz_media/thumbnails/vezemir.png"),
            encoding="utf-8",
        )
        (vault / "Characters" / "Individual" / "Varkh.md").write_text(
            character_note("Varkh", "Antropo", "Alquimista", 9, "zz_media/thumbnails/inexistente.png"),
            encoding="utf-8",
        )
        (vault / "Items" / "Adaga.md").write_text(
            "---\ntype: item\nvisibility: Jogadores\nspoiler_level: none\ngm_secret: false\n---\n# Adaga\n",
            encoding="utf-8",
        )
        (vault / "zz_media" / "thumbnails" / "vezemir.png").write_bytes(b"test-image")

        profiles = {
            "vezemir": {
                "token": "player-vezemir-test",
                "character_path": "Characters/Individual/Vezemir.md",
                "character_title": "Vezemir",
            },
            "varkh": {
                "token": "player-varkh-test",
                "character_path": "Characters/Individual/Varkh.md",
                "character_title": "Varkh",
            },
        }
        os.environ.update(
            {
                "OMNISVERA_VAULT_PATH": str(vault),
                "OMNISVERA_DB_PATH": str(database),
                "OMNISVERA_MASTER_TOKEN": "master-test",
                "OMNISVERA_PLAYER_TOKEN": "public-test",
                "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps(profiles),
                "OMNISVERA_REBUILD_ON_STARTUP": "true",
                "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
            }
        )

        import sys

        backend = Path(__file__).resolve().parents[1] / "omnisvera-agent" / "backend"
        sys.path.insert(0, str(backend))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "master-test"}
        vezemir = {"X-Omnisvera-Token": "player-vezemir-test"}
        varkh = {"X-Omnisvera-Token": "player-varkh-test"}

        with TestClient(app) as client:
            roster = client.get("/characters", headers=vezemir)
            assert roster.status_code == 200, roster.text
            assert len(roster.json()) == 2

            own = client.get("/characters/vezemir", headers=vezemir)
            assert own.status_code == 200, own.text
            own_data = own.json()
            assert own_data["access_level"] == "owner"
            assert own_data["state"]["current_hp"] == 12
            assert "gm_fields" not in own_data["definition"]

            other = client.get("/characters/varkh", headers=vezemir)
            assert other.status_code == 200, other.text
            other_data = other.json()
            assert other_data["access_level"] == "public"
            assert "state" not in other_data
            assert "attributes" not in other_data["definition"]
            assert other_data["inventory"] == []

            forbidden = client.post(
                "/characters/varkh/actions",
                headers=vezemir,
                json={"action": "damage", "payload": {"amount": 1}},
            )
            assert forbidden.status_code == 403

            damaged = client.post(
                "/characters/vezemir/actions",
                headers=vezemir,
                json={"action": "damage", "payload": {"amount": 3}, "reason": "Teste"},
            )
            assert damaged.status_code == 200, damaged.text
            assert damaged.json()["state"]["current_hp"] == 9

            events = client.get("/characters/vezemir/events", headers=vezemir)
            assert events.status_code == 200
            assert events.json()[0]["event_type"] == "damage"

            definition = client.patch(
                "/gm/characters/vezemir/definition",
                headers=master,
                json={"fields": {"initiative": 1, "gm_fields": {"notes": "Segredo de teste"}}},
            )
            assert definition.status_code == 200, definition.text
            assert definition.json()["definition"]["gm_fields"]["notes"] == "Segredo de teste"

            player_after = client.get("/characters/vezemir", headers=vezemir).json()
            assert "gm_fields" not in player_after["definition"]
            owner_events = client.get("/characters/vezemir/events", headers=vezemir)
            assert owner_events.status_code == 200
            assert all(event["event_type"] != "definition_update" for event in owner_events.json())
            assert "Segredo de teste" not in owner_events.text
            assert "Segredo de teste" not in json.dumps(player_after, ensure_ascii=False)

            base_locked = client.patch(
                "/gm/characters/vezemir/definition",
                headers=varkh,
                json={"fields": {"level": 20}},
            )
            assert base_locked.status_code == 401

            granted = client.post(
                "/characters/vezemir/actions",
                headers=master,
                json={"action": "grant_item", "payload": {"note_id": 3, "quantity": 1}},
            )
            if granted.status_code == 400:
                item = client.post("/gm/search", headers=master, json={"query": "Adaga", "limit": 2}).json()[0]
                granted = client.post(
                    "/characters/vezemir/actions",
                    headers=master,
                    json={"action": "grant_item", "payload": {"note_id": item["id"], "quantity": 1}},
                )
            assert granted.status_code == 200, granted.text
            assert any(item["item_title"] == "Adaga" for item in granted.json()["inventory"])

            event_id = events.json()[0]["id"]
            reverted = client.post(f"/gm/characters/vezemir/events/{event_id}/revert", headers=master)
            assert reverted.status_code == 200, reverted.text
            assert reverted.json()["state"]["current_hp"] == 12

            portrait = client.get("/media/zz_media/thumbnails/vezemir.png", headers=vezemir)
            assert portrait.status_code == 200
            missing = client.get("/media/zz_media/thumbnails/definitely_missing.png", headers=varkh)
            assert missing.status_code == 404

    print("PLAYABLE_CHARACTER_API_PASS")


if __name__ == "__main__":
    main()
