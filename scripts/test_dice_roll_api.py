from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def character_note(name: str, hp: int) -> str:
    return f"""---
type: character
visibility: Público
spoiler_level: none
gm_secret: false
role: player
race: Humano
class: Guerreiro
level: 1
status: Vivo
location: "[[Nimalis]]"
---

# {name}

## O que os jogadores sabem

{name} é um aventureiro conhecido.

## Atributos

| Status | Valor |
|---|---:|
| Força | 16 |
| Destreza | 10 |
| Constituição | 12 |
| Inteligência | 9 |
| Sabedoria | 11 |
| Carisma | 8 |

| Combate e recursos | Valor |
|---|---:|
| Classe de Armadura | 14 |
| Pontos de Vida | {hp} |
| Bônus de Ataque | +4 |
| Movimento | 9 m |
"""


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        vault = root / "vault"
        database = root / "companion.sqlite3"
        (vault / "Characters" / "Individual").mkdir(parents=True)
        (vault / "Items").mkdir(parents=True)
        (vault / "Classes").mkdir(parents=True)
        (vault / "Races").mkdir(parents=True)
        (vault / "Characters" / "Individual" / "Vezemir.md").write_text(character_note("Vezemir", 12), encoding="utf-8")
        (vault / "Characters" / "Individual" / "Varkh.md").write_text(character_note("Varkh", 9), encoding="utf-8")
        (vault / "Items" / "Grisalma.md").write_text(
            "---\ntype: item\nvisibility: Jogadores\nspoiler_level: none\ngm_secret: false\nbase_damage: 2d6\n---\n# Grisalma\n",
            encoding="utf-8",
        )
        for name in ("Guerreiro",):
            (vault / "Classes" / f"{name}.md").write_text(
                "---\ntype: class\nvisibility: Jogadores\n---\n# Guerreiro\n\n| Nível | XP | DV/PV | BA | JP |\n|---:|---:|---:|---:|---:|\n| 1 | 0 | 1 | +1 | 16 |\n",
                encoding="utf-8",
            )
        (vault / "Races" / "Humano.md").write_text(
            "---\ntype: race\nvisibility: Jogadores\n---\n# Humano\n\n| Movimento | 9 m |\n|---|---|\n",
            encoding="utf-8",
        )

        profiles = {
            "vezemir": {"token": "player-vezemir-test", "character_path": "Characters/Individual/Vezemir.md", "character_title": "Vezemir"},
            "varkh": {"token": "player-varkh-test", "character_path": "Characters/Individual/Varkh.md", "character_title": "Varkh"},
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

        sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "master-test"}
        vezemir = {"X-Omnisvera-Token": "player-vezemir-test"}
        varkh = {"X-Omnisvera-Token": "player-varkh-test"}

        with TestClient(app) as client:
            free = client.post(
                "/rolls",
                headers=vezemir,
                json={"request_id": "api-free-roll-01", "formula": "2d6+1", "label": "Teste livre", "visibility": "table"},
            )
            assert free.status_code == 200, free.text
            free_data = free.json()
            assert len(free_data["individual_results"]) == 2
            assert free_data["total"] == sum(free_data["individual_results"]) + 1

            invalid = client.post(
                "/rolls",
                headers=vezemir,
                json={"request_id": "api-invalid-001", "formula": "1d20;eval(1)", "visibility": "table"},
            )
            assert invalid.status_code == 400

            attribute = client.post(
                "/characters/vezemir/rolls",
                headers=vezemir,
                json={"request_id": "api-attribute-01", "roll_type": "attribute", "source_id": "strength", "visibility": "table"},
            )
            assert attribute.status_code == 200, attribute.text
            assert attribute.json()["formula"].startswith("1d20+")
            assert attribute.json()["modifier"] > 0

            duplicate = client.post(
                "/characters/vezemir/rolls",
                headers=vezemir,
                json={"request_id": "api-attribute-01", "roll_type": "attribute", "source_id": "strength", "visibility": "table"},
            )
            assert duplicate.status_code == 200
            assert duplicate.json()["id"] == attribute.json()["id"]
            assert duplicate.json()["total"] == attribute.json()["total"]

            forbidden_character = client.post(
                "/characters/vezemir/rolls",
                headers=varkh,
                json={"request_id": "api-forbidden-01", "roll_type": "attribute", "source_id": "strength", "visibility": "table"},
            )
            assert forbidden_character.status_code == 403

            gm_character = client.post(
                "/characters/vezemir/rolls",
                headers=master,
                json={"request_id": "api-master-roll-1", "roll_type": "attack", "source_id": "melee", "visibility": "table"},
            )
            assert gm_character.status_code == 200, gm_character.text
            assert gm_character.json()["formula"].startswith("1d20+")

            item = client.post("/gm/search", headers=master, json={"query": "Grisalma", "limit": 2}).json()[0]
            granted = client.post(
                "/characters/vezemir/actions",
                headers=master,
                json={"action": "grant_item", "payload": {"note_id": item["id"], "quantity": 1, "equipped": True}},
            )
            assert granted.status_code == 200, granted.text
            damage = client.post(
                "/characters/vezemir/rolls",
                headers=vezemir,
                json={"request_id": "api-damage-roll-1", "roll_type": "damage", "source_id": "Items/Grisalma.md", "visibility": "table"},
            )
            assert damage.status_code == 200, damage.text
            assert damage.json()["formula"] == "2d6"

            unconfigured = client.post(
                "/characters/vezemir/rolls",
                headers=vezemir,
                json={"request_id": "api-ability-none", "roll_type": "ability", "source_id": "Frenesi", "visibility": "table"},
            )
            assert unconfigured.status_code == 400

            secret = client.post(
                "/rolls",
                headers=master,
                json={"request_id": "api-secret-roll-1", "formula": "1d20", "label": "Segredo do Mestre", "visibility": "gm", "target_value": 12, "hide_target": True},
            )
            assert secret.status_code == 200
            player_history = client.get("/rolls?limit=50", headers=vezemir)
            assert player_history.status_code == 200
            assert "Segredo do Mestre" not in player_history.text
            assert all(event["visibility"] != "gm" for event in player_history.json())
            master_history = client.get("/rolls?limit=50", headers=master)
            assert any(event["id"] == secret.json()["id"] for event in master_history.json())

            private_target = client.post(
                "/rolls",
                headers=vezemir,
                json={"request_id": "api-private-target", "formula": "1d20", "visibility": "private", "target_value": 15},
            )
            assert private_target.status_code == 200
            public_target = client.post(
                "/rolls",
                headers=vezemir,
                json={"request_id": "api-public-target1", "formula": "1d20", "visibility": "table", "target_value": 15},
            )
            assert public_target.status_code == 403

            requested = client.post(
                "/gm/roll-requests",
                headers=master,
                json={
                    "request_id": "api-roll-request1",
                    "character_id": "vezemir",
                    "roll_type": "attribute",
                    "source_id": "strength",
                    "visibility": "owner",
                    "target_value": 13,
                    "hide_target": True,
                    "reason": "Teste solicitado pelo Mestre",
                },
            )
            assert requested.status_code == 200, requested.text
            pending = client.get("/roll-requests", headers=vezemir)
            assert pending.status_code == 200 and len(pending.json()) == 1
            assert pending.json()[0]["target_value"] is None
            assert client.get("/roll-requests", headers=varkh).json() == []

            completed = client.post(
                f"/roll-requests/{requested.json()['id']}/complete",
                headers=vezemir,
                json={"request_id": "api-complete-roll1"},
            )
            assert completed.status_code == 200, completed.text
            completed_again = client.post(
                f"/roll-requests/{requested.json()['id']}/complete",
                headers=vezemir,
                json={"request_id": "api-complete-roll1"},
            )
            assert completed_again.status_code == 200
            assert completed_again.json()["id"] == completed.json()["id"]
            double_completion = client.post(
                f"/roll-requests/{requested.json()['id']}/complete",
                headers=vezemir,
                json={"request_id": "api-complete-roll2"},
            )
            assert double_completion.status_code == 400

            player_void = client.post(
                f"/gm/rolls/{attribute.json()['id']}/void",
                headers=vezemir,
                json={"reason": "Não posso"},
            )
            assert player_void.status_code == 401
            voided = client.post(
                f"/gm/rolls/{attribute.json()['id']}/void",
                headers=master,
                json={"reason": "Teste de anulação"},
            )
            assert voided.status_code == 200 and voided.json()["voided"] is True
            assert voided.json()["total"] == attribute.json()["total"]

    print("DICE_ROLL_API_PASS")


if __name__ == "__main__":
    main()
