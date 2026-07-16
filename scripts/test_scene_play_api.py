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
        for folder in ("Characters/Individual", "Classes", "Races", "Items"):
            (vault / folder).mkdir(parents=True, exist_ok=True)
        (vault / "Characters/Individual/Vezemir.md").write_text(character_note("Vezemir", 12), encoding="utf-8")
        (vault / "Characters/Individual/Varkh.md").write_text(character_note("Varkh", 9), encoding="utf-8")
        (vault / "Classes/Guerreiro.md").write_text("---\ntype: class\nvisibility: Jogadores\n---\n# Guerreiro\n\n| Nível | XP | DV/PV | BA | JP |\n|---:|---:|---:|---:|---:|\n| 1 | 0 | 1 | +1 | 16 |\n", encoding="utf-8")
        (vault / "Races/Humano.md").write_text("---\ntype: race\nvisibility: Jogadores\n---\n# Humano\n\n| Movimento | 9 m |\n|---|---|\n", encoding="utf-8")
        (vault / "Items/Grisalma.md").write_text("---\ntype: item\nvisibility: Jogadores\nbase_damage: 2d6\n---\n# Grisalma\n", encoding="utf-8")

        profiles = {
            "vezemir": {"token": "player-vezemir-test", "character_path": "Characters/Individual/Vezemir.md", "character_title": "Vezemir"},
            "varkh": {"token": "player-varkh-test", "character_path": "Characters/Individual/Varkh.md", "character_title": "Varkh"},
        }
        os.environ.update({
            "OMNISVERA_VAULT_PATH": str(vault),
            "OMNISVERA_DB_PATH": str(database),
            "OMNISVERA_MASTER_TOKEN": "master-test",
            "OMNISVERA_PLAYER_TOKEN": "public-test",
            "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps(profiles),
            "OMNISVERA_REBUILD_ON_STARTUP": "true",
            "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
        })

        import sys
        sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "master-test"}
        vezemir = {"X-Omnisvera-Token": "player-vezemir-test"}
        varkh = {"X-Omnisvera-Token": "player-varkh-test"}

        with TestClient(app) as client:
            blocked_session = client.post("/gm/sessions", headers=vezemir, json={"request_id": "blocked-session-1", "title": "Proibida"})
            assert blocked_session.status_code == 401

            session = client.post("/gm/sessions", headers=master, json={"request_id": "api-session-0001", "title": "Sessão técnica", "session_number": 1, "private_notes": "Segredo da sessão"})
            assert session.status_code == 200, session.text
            session_id = session.json()["id"]
            assert client.post(f"/gm/sessions/{session_id}/status", headers=master, json={"status": "active"}).status_code == 200

            scene = client.post("/gm/scenes", headers=master, json={
                "request_id": "api-scene-00001", "session_id": session_id, "title": "Teste Técnico de Cena",
                "location_name": "Ambiente de Validação", "public_description": "Uma área neutra de teste.",
                "objective": "Validar o painel de cena", "private_notes": "Nota privada de validação", "visibility": "table",
            })
            assert scene.status_code == 200, scene.text
            scene_id = scene.json()["id"]
            assert client.get(f"/scenes/{scene_id}", headers=vezemir).status_code == 404

            participant = client.post(f"/gm/scenes/{scene_id}/participants", headers=master, json={"participant_type": "player_character", "character_id": "vezemir", "public_label": "Vezemir", "public_status": "Ativo", "private_status": "Monitorado"})
            assert participant.status_code == 200, participant.text

            threat = client.post(f"/gm/scenes/{scene_id}/elements", headers=master, json={"request_id": "api-threat-0001", "element_type": "threat", "title": "Ameaça técnica", "private_description": "Não pode vazar", "status": "hidden", "visibility": "gm"})
            assert threat.status_code == 200, threat.text
            clue = client.post(f"/gm/scenes/{scene_id}/elements", headers=master, json={"request_id": "api-clue-000001", "element_type": "clue", "title": "Pista técnica", "public_description": "Marca visível", "private_description": "Origem secreta", "status": "hidden", "visibility": "gm"})
            clue_id = next(item for item in clue.json()["elements"] if item["title"] == "Pista técnica")["id"]

            activated = client.post(f"/gm/scenes/{scene_id}/status", headers=master, json={"status": "active"})
            assert activated.status_code == 200
            player_view = client.get("/scenes/active", headers=vezemir)
            assert player_view.status_code == 200, player_view.text
            player_text = player_view.text
            assert "Nota privada" not in player_text and "Não pode vazar" not in player_text and "Origem secreta" not in player_text
            assert player_view.json()["participants"][0]["character"]["name"] == "Vezemir"
            assert not player_view.json()["elements"]
            gm_view = client.get(f"/scenes/{scene_id}", headers=master)
            assert "Nota privada de validação" in gm_view.text and "Ameaça técnica" in gm_view.text

            wrong_action = client.post(f"/scenes/{scene_id}/actions", headers=varkh, json={"request_id": "api-action-wrong1", "character_id": "vezemir", "action_type": "observe", "description": "Tenta agir por outro"})
            assert wrong_action.status_code == 403
            action = client.post(f"/scenes/{scene_id}/actions", headers=vezemir, json={"request_id": "api-action-00001", "action_type": "investigate", "description": "Vezemir examina as marcas na porta.", "target_label": "Porta de ferro"})
            assert action.status_code == 200, action.text
            action_id = action.json()["id"]
            repeated = client.post(f"/scenes/{scene_id}/actions", headers=vezemir, json={"request_id": "api-action-00001", "action_type": "investigate", "description": "Não duplica"})
            assert repeated.status_code == 200 and repeated.json()["id"] == action_id

            roll_request = client.post(f"/gm/scenes/actions/{action_id}/request-roll", headers=master, json={"request_id": "api-scene-roll-01", "roll_type": "attribute", "source_id": "strength", "target_value": 10, "hide_target": True, "visibility": "owner", "label": "Examinar a porta"})
            assert roll_request.status_code == 200, roll_request.text
            assert roll_request.json()["scene_id"] == scene_id and roll_request.json()["action_id"] == action_id
            pending = client.get("/roll-requests", headers=vezemir).json()
            assert len(pending) == 1 and pending[0]["target_value"] is None
            completed = client.post(f"/roll-requests/{roll_request.json()['id']}/complete", headers=vezemir, json={"request_id": "api-scene-complete1"})
            assert completed.status_code == 200, completed.text
            assert completed.json()["scene_id"] == scene_id and completed.json()["action_id"] == action_id
            scene_after_roll = client.get(f"/scenes/{scene_id}", headers=vezemir).json()
            assert any(event.get("roll", {}).get("id") == completed.json()["id"] for event in scene_after_roll["events"] if event.get("roll"))

            resolved = client.post(f"/gm/scenes/actions/{action_id}/resolve", headers=master, json={"resolution": "A marca foi examinada."})
            assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"
            resolved_again = client.post(f"/gm/scenes/actions/{action_id}/resolve", headers=master, json={"resolution": "Duplicada"})
            assert resolved_again.status_code == 400

            revealed = client.post(f"/gm/scene-elements/{clue_id}/reveal", headers=master)
            assert revealed.status_code == 200 and revealed.json()["visibility"] == "table"
            revealed_player = client.get(f"/scenes/{scene_id}", headers=vezemir).json()
            assert [item["title"] for item in revealed_player["elements"]] == ["Pista técnica"]

            damage = client.post(f"/gm/scenes/{scene_id}/consequences", headers=master, json={"character_id": "vezemir", "action_id": action_id, "action": "damage", "payload": {"amount": 2}, "title": "Dano técnico", "public_text": "Vezemir sofre 2 de dano", "visibility": "table"})
            assert damage.status_code == 200, damage.text
            assert damage.json()["character_event"]["after"] == 10
            condition = client.post(f"/gm/scenes/{scene_id}/consequences", headers=master, json={"character_id": "vezemir", "action_id": action_id, "action": "add_condition", "payload": {"condition": "Marcado"}, "title": "Condição técnica", "public_text": "Vezemir está marcado"})
            assert condition.status_code == 200, condition.text
            character_event_id = condition.json()["character_event"]["event_id"]
            character = client.get("/characters/vezemir", headers=master).json()
            assert "Marcado" in character["state"]["conditions"]
            reverted = client.post(f"/gm/characters/vezemir/events/{character_event_id}/revert", headers=master)
            assert reverted.status_code == 200 and "Marcado" not in reverted.json()["state"]["conditions"]

            consequence_event_id = damage.json()["scene_event"]["id"]
            voided = client.post(f"/gm/scene-events/{consequence_event_id}/void", headers=master, json={"reason": "Reversão de validação"})
            assert voided.status_code == 200 and voided.json()["voided"]

            closed = client.post(f"/gm/scenes/{scene_id}/status", headers=master, json={"status": "resolved", "summary": "Teste técnico concluído"})
            assert closed.status_code == 200 and closed.json()["status"] == "resolved"
            after_close = client.post(f"/scenes/{scene_id}/actions", headers=vezemir, json={"request_id": "api-action-closed1", "action_type": "observe", "description": "Ação tardia"})
            assert after_close.status_code == 400
            archived = client.get(f"/scenes/{scene_id}", headers=vezemir)
            assert archived.status_code == 200 and archived.json()["resolution_summary"] == "Teste técnico concluído"
            assert client.post(f"/gm/sessions/{session_id}/status", headers=master, json={"status": "completed"}).json()["status"] == "completed"

    print("SCENE_PLAY_API_PASS")


if __name__ == "__main__":
    main()
