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
        for folder in ("Characters/Individual", "Classes", "Races", "Items"):
            (vault / folder).mkdir(parents=True, exist_ok=True)
        (vault / "Characters/Individual/Vezemir.md").write_text(character_note("Vezemir", 12), encoding="utf-8")
        (vault / "Characters/Individual/Varkh.md").write_text(character_note("Varkh", 9), encoding="utf-8")
        (vault / "Classes/Guerreiro.md").write_text("---\ntype: class\nvisibility: Jogadores\n---\n# Guerreiro\n", encoding="utf-8")
        (vault / "Races/Humano.md").write_text("---\ntype: race\nvisibility: Jogadores\n---\n# Humano\n", encoding="utf-8")
        (vault / "Items/Item Técnico.md").write_text("---\ntype: item\nvisibility: Jogadores\n---\n# Item Técnico\n", encoding="utf-8")

        profiles = {
            "vezemir": {"token": "player-vezemir-contract", "character_path": "Characters/Individual/Vezemir.md", "character_title": "Vezemir"},
            "varkh": {"token": "player-varkh-contract", "character_path": "Characters/Individual/Varkh.md", "character_title": "Varkh"},
        }
        os.environ.update({
            "OMNISVERA_VAULT_PATH": str(vault),
            "OMNISVERA_DB_PATH": str(database),
            "OMNISVERA_MASTER_TOKEN": "master-contract",
            "OMNISVERA_PLAYER_TOKEN": "public-contract",
            "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps(profiles),
            "OMNISVERA_REBUILD_ON_STARTUP": "true",
            "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
        })

        import sys
        sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "master-contract"}
        vezemir = {"X-Omnisvera-Token": "player-vezemir-contract"}
        varkh = {"X-Omnisvera-Token": "player-varkh-contract"}

        with TestClient(app) as client:
            assert client.get("/characters/vezemir", headers=master).status_code == 200
            assert client.post("/gm/contracts", headers=vezemir, json={"request_id": "blocked-contract", "title": "Bloqueado"}).status_code == 401

            created = client.post("/gm/contracts", headers=master, json={
                "request_id": "api-contract-001",
                "title": "Contrato Técnico de Validação",
                "contract_type": "investigação",
                "issuer_name": "Administração do Conclave",
                "location_name": "Ambiente de Validação",
                "public_summary": "Validar o fluxo de contratos.",
                "public_briefing": "Briefing público do contrato.",
                "private_briefing": "Segredo privado do Mestre.",
                "risk_label": "Técnico",
            })
            assert created.status_code == 200, created.text
            contract_id = created.json()["id"]
            assert client.get("/contracts", headers=vezemir).json() == []
            assert client.get(f"/contracts/{contract_id}", headers=vezemir).status_code == 404

            secret = client.post(f"/gm/contracts/{contract_id}/objectives", headers=master, json={
                "request_id": "api-objective-secret",
                "title": "Objetivo secreto",
                "public_description": "Não deve aparecer ainda.",
                "private_description": "Conteúdo secreto.",
                "status": "hidden",
                "revealed_to_players": False,
            })
            public = client.post(f"/gm/contracts/{contract_id}/objectives", headers=master, json={
                "request_id": "api-objective-public",
                "title": "Validar fluxo público",
                "public_description": "Objetivo público.",
                "status": "available",
                "revealed_to_players": True,
            })
            assert secret.status_code == 200 and public.status_code == 200
            secret_id = secret.json()["id"]
            public_id = public.json()["id"]

            published = client.post(f"/gm/contracts/{contract_id}/publish", headers=master, json={"request_id": "api-publish-001"})
            assert published.status_code == 200 and published.json()["status"] == "published"
            player_view = client.get(f"/contracts/{contract_id}", headers=vezemir)
            assert player_view.status_code == 200, player_view.text
            player_text = player_view.text
            assert "Segredo privado" not in player_text and "Conteúdo secreto" not in player_text and "Objetivo secreto" not in player_text
            assert [item["title"] for item in player_view.json()["objectives"]] == ["Validar fluxo público"]
            gm_text = client.get(f"/contracts/{contract_id}", headers=master).text
            assert "Segredo privado do Mestre" in gm_text and "Objetivo secreto" in gm_text

            wrong_owner = client.post(f"/contracts/{contract_id}/accept", headers=varkh, json={"request_id": "api-wrong-accept", "character_id": "vezemir"})
            assert wrong_owner.status_code == 403
            accepted = client.post(f"/contracts/{contract_id}/accept", headers=vezemir, json={"request_id": "api-accept-001"})
            assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"
            accepted_retry = client.post(f"/contracts/{contract_id}/accept", headers=vezemir, json={"request_id": "api-accept-001"})
            assert accepted_retry.status_code == 200 and len(accepted_retry.json()["assignments"]) == 1
            duplicate_assignment = client.post(f"/gm/contracts/{contract_id}/assignments", headers=master, json={"request_id": "api-assign-dup1", "character_id": "vezemir"})
            assert duplicate_assignment.status_code == 400

            started = client.post(f"/gm/contracts/{contract_id}/start", headers=master, json={"request_id": "api-start-001"})
            assert started.status_code == 200 and started.json()["status"] == "active"
            bad_transition = client.post(f"/gm/contracts/{contract_id}/publish", headers=master, json={"request_id": "api-bad-transition"})
            assert bad_transition.status_code == 400

            revealed = client.post(f"/gm/contract-objectives/{secret_id}/status", headers=master, json={"request_id": "api-reveal-secret", "status": "available"})
            assert revealed.status_code == 200 and revealed.json()["revealed_to_players"]
            completed_objective = client.post(f"/gm/contract-objectives/{public_id}/status", headers=master, json={"request_id": "api-complete-objective", "status": "completed"})
            assert completed_objective.status_code == 200
            completed_objective_retry = client.post(f"/gm/contract-objectives/{public_id}/status", headers=master, json={"request_id": "api-complete-objective", "status": "completed"})
            assert completed_objective_retry.status_code == 200
            completed_objective_duplicate = client.post(f"/gm/contract-objectives/{public_id}/status", headers=master, json={"request_id": "api-complete-dup2", "status": "completed"})
            assert completed_objective_duplicate.status_code == 400

            scene = client.post("/gm/scenes", headers=master, json={
                "request_id": "api-contract-scene",
                "title": "Cena técnica do contrato",
                "location_name": "Ambiente de Validação",
                "public_description": "Cena de vínculo.",
                "objective": "Validar integração",
                "visibility": "table",
            })
            assert scene.status_code == 200, scene.text
            scene_id = scene.json()["id"]
            linked = client.post(f"/gm/contracts/{contract_id}/scene-links", headers=master, json={"request_id": "api-link-scene", "scene_id": scene_id, "objective_id": secret_id, "link_type": "investigation"})
            assert linked.status_code == 200
            duplicate_link = client.post(f"/gm/contracts/{contract_id}/scene-links", headers=master, json={"request_id": "api-link-scene2", "scene_id": scene_id, "objective_id": secret_id, "link_type": "investigation"})
            assert duplicate_link.status_code == 400
            assert client.post(f"/gm/scenes/{scene_id}/status", headers=master, json={"status": "active"}).status_code == 200
            scene_view = client.get(f"/scenes/{scene_id}", headers=vezemir)
            assert scene_view.status_code == 200 and scene_view.json()["contract_links"][0]["contract_id"] == contract_id
            closed_scene = client.post(f"/gm/scenes/{scene_id}/status", headers=master, json={"status": "resolved", "summary": "Cena técnica encerrada."})
            assert closed_scene.status_code == 200
            contract_events = client.get(f"/contracts/{contract_id}/events", headers=master).json()
            assert any(event["event_type"] == "linked_scene_closed" for event in contract_events)

            private_reward = client.post(f"/gm/contracts/{contract_id}/rewards", headers=master, json={"request_id": "api-private-reward", "reward_type": "information", "label": "Segredo recompensado", "visibility": "gm"})
            assert private_reward.status_code == 200
            assert "Segredo recompensado" not in client.get(f"/contracts/{contract_id}", headers=vezemir).text

            completed = client.post(f"/gm/contracts/{contract_id}/complete", headers=master, json={"request_id": "api-complete-contract"})
            assert completed.status_code == 200 and completed.json()["status"] == "completed"

            currency_reward = client.post(f"/gm/contracts/{contract_id}/rewards", headers=master, json={"request_id": "api-currency-reward", "reward_type": "currency", "label": "Moeda genérica", "quantity": 2, "currency_type": "moeda", "visibility": "table"})
            assert currency_reward.status_code == 200
            currency_id = currency_reward.json()["id"]
            assert client.post(f"/gm/contract-rewards/{currency_id}/approve", headers=master, json={"request_id": "api-approve-currency"}).status_code == 200
            blocked_delivery = client.post(f"/gm/contract-rewards/{currency_id}/deliver", headers=vezemir, json={"request_id": "api-block-deliver", "character_ids": ["vezemir"]})
            assert blocked_delivery.status_code == 401
            delivered = client.post(f"/gm/contract-rewards/{currency_id}/deliver", headers=master, json={"request_id": "api-deliver-currency", "character_ids": ["vezemir"]})
            assert delivered.status_code == 200, delivered.text
            delivered_retry = client.post(f"/gm/contract-rewards/{currency_id}/deliver", headers=master, json={"request_id": "api-deliver-currency", "character_ids": ["vezemir"]})
            assert delivered_retry.status_code == 200 and delivered_retry.json()["character_event_ids"] == delivered.json()["character_event_ids"]

            item_reward = client.post(f"/gm/contracts/{contract_id}/rewards", headers=master, json={"request_id": "api-item-reward", "reward_type": "item", "label": "Item Técnico", "quantity": 1, "item_source": "Items/Item Técnico.md", "item_name": "Item Técnico", "visibility": "table"}).json()
            assert client.post(f"/gm/contract-rewards/{item_reward['id']}/approve", headers=master, json={"request_id": "api-approve-item"}).status_code == 200
            assert client.post(f"/gm/contract-rewards/{item_reward['id']}/deliver", headers=master, json={"request_id": "api-deliver-item", "character_ids": ["vezemir"]}).status_code == 200

            rep_reward = client.post(f"/gm/contracts/{contract_id}/rewards", headers=master, json={"request_id": "api-rep-reward", "reward_type": "reputation", "label": "Renome técnico", "reputation_faction": "Conclave dos Errantes", "reputation_amount": 2, "visibility": "table"}).json()
            assert client.post(f"/gm/contract-rewards/{rep_reward['id']}/approve", headers=master, json={"request_id": "api-approve-rep"}).status_code == 200
            delivered_rep = client.post(f"/gm/contract-rewards/{rep_reward['id']}/deliver", headers=master, json={"request_id": "api-deliver-rep", "character_ids": []})
            assert delivered_rep.status_code == 200 and delivered_rep.json()["reputation_entries"][0]["resulting_value"] == 2
            ledger = client.get("/reputation?party_id=group", headers=master).json()
            assert ledger and ledger[0]["faction_name"] == "Conclave dos Errantes"
            reverted = client.post(f"/gm/reputation/{ledger[0]['id']}/revert", headers=master)
            assert reverted.status_code == 200 and reverted.json()["reverted"]

            character_events = client.get("/characters/vezemir/events", headers=master)
            assert character_events.status_code == 200
            event_types = {event["event_type"] for event in character_events.json()}
            assert {"change_coins", "grant_item"} <= event_types
            player_history = client.get(f"/contracts/{contract_id}/events", headers=vezemir).json()
            assert all("private_text" not in event for event in player_history)
            assert client.get(f"/contracts/{contract_id}", headers=vezemir).json()["status"] == "completed"

    print("CONTRACT_PLAY_API_PASS")


if __name__ == "__main__":
    main()
