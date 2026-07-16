from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        vault = root / "vault"
        database = root / "companion.sqlite3"
        (vault / "Characters/Individual").mkdir(parents=True)
        npc_path = vault / "Characters/Individual/NPC Técnico.md"
        npc_path.write_text("""---
type: character
role: npc
visibility: Público
spoiler_level: none
gm_secret: false
aliases: [Avaliador]
race: Humano
function: Avaliador do Conclave
faction: Conclave dos Errantes
location: Ambiente de Validação
status: Ativo
thumbnail: zz_media/characters/npc_tecnico.png
description: Um avaliador conhecido.
canon: true
---
# NPC Técnico

Texto que não deve ser copiado para o SQLite.
""", encoding="utf-8")
        before_hash = hashlib.sha256(npc_path.read_bytes()).hexdigest()
        player_path = vault / "Characters/Individual/Vezemir.md"
        player_path.write_text("---\ntype: character\nrole: player\nvisibility: Público\nspoiler_level: none\ngm_secret: false\n---\n# Vezemir\n", encoding="utf-8")

        profiles = {"vezemir": {"token": "npc-player-token", "character_path": "Characters/Individual/Vezemir.md", "character_title": "Vezemir"}}
        os.environ.update({
            "OMNISVERA_VAULT_PATH": str(vault), "OMNISVERA_DB_PATH": str(database),
            "OMNISVERA_MASTER_TOKEN": "npc-master-token", "OMNISVERA_PLAYER_TOKEN": "npc-public-token",
            "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps(profiles), "OMNISVERA_REBUILD_ON_STARTUP": "true",
            "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
        })
        sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "npc-master-token"}
        player = {"X-Omnisvera-Token": "npc-player-token"}
        with TestClient(app) as client:
            blocked = client.post("/gm/npcs", headers=player, json={"request_id": "api-npc-blocked", "name": "Bloqueado"})
            assert blocked.status_code == 401
            imported = client.post("/gm/npcs/import", headers=master, json={"request_id": "api-npc-import-001", "source_path": "Characters/Individual/NPC Técnico.md"})
            assert imported.status_code == 200, imported.text
            npc = imported.json(); npc_id = npc["id"]
            assert npc["source_path"].endswith("NPC Técnico.md") and "Texto que não deve" not in imported.text
            duplicate = client.post("/gm/npcs/import", headers=master, json={"request_id": "api-npc-import-002", "source_path": "NPC Técnico"})
            assert duplicate.status_code == 200 and duplicate.json()["id"] == npc_id

            player_view = client.get(f"/npcs/{npc_id}", headers=player)
            assert player_view.status_code == 200 and "private_description" not in player_view.text
            assert client.get("/npcs?query=Avaliador", headers=player).json()[0]["id"] == npc_id

            relation = client.post(f"/gm/npcs/{npc_id}/relationships", headers=master, json={
                "request_id": "api-npc-relation", "target_type": "character", "target_id": "vezemir", "target_label": "Vezemir",
                "public_label": "Conhecido", "private_label": "Confia com cautela", "trust_value": 2,
                "visible_to_players": True, "reason": "Validação técnica",
            })
            assert relation.status_code == 200
            relation_id = relation.json()["id"]
            player_relation_text = client.get(f"/npcs/{npc_id}", headers=player).text
            assert "Conhecido" in player_relation_text and "Confia com cautela" not in player_relation_text and "trust_value" not in player_relation_text
            changed = client.patch(f"/gm/npc-relationships/{relation_id}", headers=master, json={"expected_version": 1, "fields": {"trust_value": 3}, "reason": "Cumpriu o combinado"})
            assert changed.status_code == 200 and changed.json()["trust_value"] == 3
            stale = client.patch(f"/gm/npc-relationships/{relation_id}", headers=master, json={"expected_version": 1, "fields": {"trust_value": 4}, "reason": "Desatualizado"})
            assert stale.status_code == 409

            public_memory = client.post(f"/gm/npcs/{npc_id}/memories", headers=master, json={"request_id": "api-npc-memory-public", "memory_type": "fact", "title": "Memória pública", "summary": "Um encontro ocorreu.", "confidence": "confirmed", "visibility": "table"})
            secret_memory = client.post(f"/gm/npcs/{npc_id}/memories", headers=master, json={"request_id": "api-npc-memory-secret", "memory_type": "secret", "title": "Memória secreta", "summary": "Segredo técnico.", "confidence": "believed", "visibility": "gm"})
            false_memory = client.post(f"/gm/npcs/{npc_id}/memories", headers=master, json={"request_id": "api-npc-memory-false", "memory_type": "observation", "title": "Crença falsa", "summary": "Crença não canônica.", "confidence": "false_known_by_npc", "visibility": "gm"})
            assert public_memory.status_code == secret_memory.status_code == false_memory.status_code == 200
            filtered = client.get(f"/npcs/{npc_id}", headers=player).text
            assert "Memória pública" in filtered and "Memória secreta" not in filtered and "Crença falsa" not in filtered and "confidence" not in filtered
            contradicted = client.post(f"/gm/npc-memories/{public_memory.json()['id']}/contradict", headers=master, json={"request_id": "api-npc-contradict", "title": "Memória corrigida", "summary": "O encontro ocorreu depois.", "confidence": "confirmed", "visibility": "table", "reason": "Correção"})
            assert contradicted.status_code == 200 and contradicted.json()["contradicts_memory_id"] == public_memory.json()["id"]

            scene = client.post("/gm/scenes", headers=master, json={"request_id": "api-npc-scene-001", "title": "Cena técnica", "location_name": "Ambiente de Validação", "visibility": "table"})
            assert scene.status_code == 200; scene_id = scene.json()["id"]
            participant = client.post(f"/gm/scenes/{scene_id}/participants", headers=master, json={"participant_type": "npc", "npc_name": npc["name"], "npc_source": f"npc:{npc_id}", "public_label": npc["name"], "visible_to_players": True})
            assert participant.status_code == 200
            assert client.post(f"/gm/scenes/{scene_id}/status", headers=master, json={"status": "active"}).status_code == 200
            scene_response = client.get(f"/scenes/{scene_id}", headers=player)
            assert scene_response.status_code == 200, scene_response.text
            scene_view = scene_response.json()
            assert scene_view["participants"][0]["npc"]["id"] == npc_id
            encounter = client.post(f"/gm/npcs/{npc_id}/encounters", headers=master, json={"request_id": "api-npc-encounter", "scene_id": scene_id, "title": "Encontro na cena", "public_summary": "Encontro público.", "private_summary": "Detalhe secreto."})
            encounter_retry = client.post(f"/gm/npcs/{npc_id}/encounters", headers=master, json={"request_id": "api-npc-encounter-retry", "scene_id": scene_id, "title": "Duplicado"})
            assert encounter.status_code == encounter_retry.status_code == 200 and encounter.json()["id"] == encounter_retry.json()["id"]

            contract = client.post("/gm/contracts", headers=master, json={"request_id": "api-npc-contract", "title": "Contrato técnico", "issuer_name": "Conclave", "public_summary": "Resumo", "public_briefing": "Briefing"})
            assert contract.status_code == 200; contract_id = contract.json()["id"]
            assert client.post(f"/gm/contracts/{contract_id}/publish", headers=master, json={"request_id": "api-npc-contract-publish"}).status_code == 200
            linked = client.post(f"/gm/npcs/{npc_id}/contracts", headers=master, json={"request_id": "api-npc-contract-link", "contract_id": contract_id, "role": "Contratante", "visible_to_players": True})
            assert linked.status_code == 200
            assert client.get(f"/contracts/{contract_id}", headers=player).json()["npcs"][0]["npc_id"] == npc_id

            promise = client.post(f"/gm/npcs/{npc_id}/memories", headers=master, json={"request_id": "api-npc-promise", "memory_type": "promise", "title": "Promessa", "summary": "Entregar informação.", "visibility": "table", "responsible_party": npc["name"], "beneficiary": "Vezemir"})
            assert promise.status_code == 200 and promise.json()["obligation_status"] == "active"
            fulfilled = client.patch(f"/gm/npc-memories/{promise.json()['id']}", headers=master, json={"expected_version": 1, "fields": {"obligation_status": "fulfilled", "status": "resolved"}, "reason": "Cumprida"})
            assert fulfilled.status_code == 200 and fulfilled.json()["obligation_status"] == "fulfilled"

            gm_detail = client.get(f"/npcs/{npc_id}", headers=master).json()
            event_id = gm_detail["events"][0]["id"]
            voided = client.post(f"/gm/npc-events/{event_id}/void", headers=master, json={"reason": "Teste de auditoria"})
            assert voided.status_code == 200 and voided.json()["voided"]
            summary = client.get(f"/npcs/{npc_id}/summary", headers=player)
            assert summary.status_code == 200 and summary.json()["canonical"] is False and "Segredo técnico" not in summary.text
            assert hashlib.sha256(npc_path.read_bytes()).hexdigest() == before_hash

    print("NPC_MEMORY_API_PASS")


if __name__ == "__main__":
    main()
