from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.npc_memory import (  # noqa: E402
    contradict_memory,
    create_memory,
    create_npc,
    create_relationship,
    get_npc,
    init_npc_memory,
    link_contract,
    list_contract_npcs,
    list_npcs,
    record_encounter,
    structured_summary,
    update_memory,
    update_npc,
    update_npc_state,
    update_relationship,
    void_event,
)


def expect_error(callback, phrase: str = "") -> None:
    try:
        callback()
    except (RuntimeError, ValueError) as error:
        if phrase:
            assert phrase.casefold() in str(error).casefold(), str(error)
    else:
        raise AssertionError("Era esperado um erro")


def main() -> None:
    checks = 0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        database = root / "npc.sqlite3"
        vault_note = root / "NPC Técnico.md"
        vault_note.write_text("---\ntype: character\n---\n# Não modificar\n", encoding="utf-8")
        before_hash = hashlib.sha256(vault_note.read_bytes()).hexdigest()
        init_npc_memory(database)

        npc, created = create_npc(database, request_id="npc-service-001", campaign_id="omnisvera", actor_id="master", fields={
            "source_path": "Characters/Individual/NPC Técnico.md", "name": "NPC Técnico de Validação",
            "class_or_role": "Avaliador do Conclave", "current_location": "Ambiente de Validação",
            "public_description": "Perfil público técnico.", "private_description": "Descrição privada.",
            "public_status": "Disponível", "private_status": "Em observação", "visible_to_players": True,
        })
        assert created and npc["name"] == "NPC Técnico de Validação"; checks += 1
        repeated, created_again = create_npc(database, request_id="npc-service-001", campaign_id="omnisvera", actor_id="master", fields={"name": "Duplicado"})
        assert not created_again and repeated["id"] == npc["id"]; checks += 1
        by_source, source_created = create_npc(database, request_id="npc-service-002", campaign_id="omnisvera", actor_id="master", fields={"source_path": npc["source_path"], "name": "Duplicado por fonte"})
        assert not source_created and by_source["id"] == npc["id"]; checks += 1

        gm = get_npc(database, npc["id"], access_mode="gm")
        player = get_npc(database, npc["id"], access_mode="player")
        assert gm and gm["private_description"] == "Descrição privada."; checks += 1
        assert player and "private_description" not in player and "private_status" not in player; checks += 1
        assert list_npcs(database, campaign_id="omnisvera", access_mode="player", query="Avaliador"); checks += 1
        assert list_npcs(database, campaign_id="omnisvera", access_mode="gm", location="Validação"); checks += 1

        updated = update_npc(database, npc["id"], expected_version=1, fields={"occupation": "Escriba técnico"}, actor_id="master")
        assert updated["version"] == 2; checks += 1
        expect_error(lambda: update_npc(database, npc["id"], expected_version=1, fields={"occupation": "Perdido"}, actor_id="master"), "versão"); checks += 1
        state = update_npc_state(database, npc["id"], expected_version=1, fields={"public_status": "Ativo", "disposition_summary": "Cauteloso"}, actor_id="master")
        assert state["version"] == 2 and state["public_status"] == "Ativo"; checks += 1
        expect_error(lambda: update_npc_state(database, npc["id"], expected_version=1, fields={"public_status": "Perdido"}, actor_id="master"), "versão"); checks += 1

        relation, relation_created = create_relationship(database, npc["id"], request_id="npc-relation-001", actor_id="master", reason="Vezemir cumpriu o contrato", fields={
            "target_type": "character", "target_id": "vezemir", "target_label": "Vezemir", "public_label": "Aliado conhecido",
            "private_label": "Confiança em formação", "trust_value": 1, "fear_value": 0, "respect_value": 2,
            "public_notes": "Trabalharam juntos.", "private_notes": "Avalia a lealdade.", "visible_to_players": True,
        })
        assert relation_created and relation["trust_value"] == 1; checks += 1
        assert not any(item.get("target_id") == str(npc["id"]) for item in (get_npc(database, npc["id"], access_mode="gm") or {})["relationships"]); checks += 1
        player_relation = (get_npc(database, npc["id"], access_mode="player") or {})["relationships"][0]
        assert "trust_value" not in player_relation and "private_label" not in player_relation; checks += 1
        changed = update_relationship(database, relation["id"], expected_version=1, fields={"trust_value": 2}, actor_id="master", reason="Nova ação positiva")
        assert changed["version"] == 2 and changed["trust_value"] == 2; checks += 1
        expect_error(lambda: update_relationship(database, relation["id"], expected_version=1, fields={"trust_value": 9}, actor_id="master", reason="Conflito"), "versão"); checks += 1

        fact, _ = create_memory(database, npc["id"], request_id="npc-memory-fact", actor_id="master", fields={"memory_type": "fact", "title": "Fato técnico", "summary": "Vezemir esteve presente.", "confidence": "confirmed", "visibility": "table", "importance": "high", "character_id": "vezemir"})
        rumor, _ = create_memory(database, npc["id"], request_id="npc-memory-rumor", actor_id="master", fields={"memory_type": "rumor", "title": "Rumor técnico", "summary": "Uma versão não confirmada circula.", "confidence": "suspected", "visibility": "gm"})
        false_belief, _ = create_memory(database, npc["id"], request_id="npc-memory-false", actor_id="master", fields={"memory_type": "observation", "title": "Crença falsa", "summary": "O NPC acredita em algo incorreto.", "confidence": "false_known_by_npc", "visibility": "gm"})
        assert fact["confidence"] == "confirmed" and rumor["memory_type"] == "rumor" and false_belief["confidence"] == "false_known_by_npc"; checks += 1
        player_memories = (get_npc(database, npc["id"], access_mode="player") or {})["memories"]
        assert [item["title"] for item in player_memories] == ["Fato técnico"] and "confidence" not in player_memories[0]; checks += 1
        contradicted = contradict_memory(database, fact["id"], request_id="npc-memory-contradiction", actor_id="master", reason="Correção administrativa", fields={"title": "Fato corrigido", "summary": "A presença ocorreu em outro momento.", "confidence": "confirmed", "visibility": "table"})
        gm_after_contradiction = get_npc(database, npc["id"], access_mode="gm") or {}
        assert contradicted["contradicts_memory_id"] == fact["id"] and any(item["id"] == fact["id"] and item["status"] == "contradicted" for item in gm_after_contradiction["memories"]); checks += 1

        encounter, encounter_created = record_encounter(database, npc["id"], request_id="npc-encounter-001", actor_id="master", fields={"scene_id": 77, "contract_id": 88, "title": "Encontro técnico", "public_summary": "Encontro conhecido.", "private_summary": "Detalhe reservado."})
        encounter_repeat, encounter_created_again = record_encounter(database, npc["id"], request_id="npc-encounter-002", actor_id="master", fields={"scene_id": 77, "title": "Duplicado"})
        assert encounter_created and not encounter_created_again and encounter_repeat["id"] == encounter["id"]; checks += 1
        player_encounter = (get_npc(database, npc["id"], access_mode="player") or {})["encounters"][0]
        assert "private_summary" not in player_encounter and player_encounter["scene_id"] == 77; checks += 1

        link, link_created = link_contract(database, npc["id"], request_id="npc-contract-001", contract_id=88, role="Contratante", visible_to_players=True, actor_id="master")
        assert link_created and link["role"] == "Contratante"; checks += 1
        link_repeat, link_created_again = link_contract(database, npc["id"], request_id="npc-contract-002", contract_id=88, role="Duplicado", visible_to_players=True, actor_id="master")
        assert not link_created_again and link_repeat["id"] == link["id"]; checks += 1
        assert list_contract_npcs(database, 88, access_mode="player")[0]["name"] == npc["name"]; checks += 1

        promise, _ = create_memory(database, npc["id"], request_id="npc-promise-001", actor_id="master", fields={"memory_type": "promise", "title": "Promessa técnica", "summary": "Entregar uma resposta.", "responsible_party": "NPC Técnico", "beneficiary": "Vezemir", "due_text": "Após a validação", "visibility": "table"})
        fulfilled = update_memory(database, promise["id"], expected_version=1, fields={"obligation_status": "fulfilled", "status": "resolved", "fulfilled_at": "2026-07-16T12:00:00+00:00"}, actor_id="master", reason="Promessa cumprida")
        assert fulfilled["obligation_status"] == "fulfilled" and fulfilled["status"] == "resolved"; checks += 1
        debt, _ = create_memory(database, npc["id"], request_id="npc-debt-001", actor_id="master", fields={"memory_type": "debt", "title": "Dívida técnica", "summary": "Uma dívida controlada.", "visibility": "gm"})
        forgiven = update_memory(database, debt["id"], expected_version=1, fields={"obligation_status": "forgiven", "status": "resolved"}, actor_id="master", reason="Dívida perdoada")
        assert forgiven["obligation_status"] == "forgiven"; checks += 1

        summary_player = structured_summary(database, npc["id"], access_mode="player", character_id="vezemir")
        summary_gm = structured_summary(database, npc["id"], access_mode="gm")
        assert summary_player and summary_player["canonical"] is False and all(item.get("visibility") == "table" for item in summary_player["memories"]); checks += 1
        assert summary_gm and any(item["title"] == "Crença falsa" for item in summary_gm["memories"]); checks += 1

        events = gm_after_contradiction["events"]
        assert events and any(event["event_type"] == "memory_contradicted" for event in events); checks += 1
        voided = void_event(database, events[0]["id"], actor_id="master", reason="Anulação técnica")
        assert voided["voided"] and voided["void_reason"] == "Anulação técnica"; checks += 1
        player_events = (get_npc(database, npc["id"], access_mode="player") or {})["events"]
        assert all(event.get("visibility") == "table" and "private_text" not in event for event in player_events); checks += 1

        hidden, _ = create_npc(database, request_id="npc-hidden-001", campaign_id="omnisvera", actor_id="master", fields={"name": "NPC Oculto", "visible_to_players": False})
        assert get_npc(database, hidden["id"], access_mode="player") is None; checks += 1
        assert all(item["id"] != hidden["id"] for item in list_npcs(database, campaign_id="omnisvera", access_mode="player")); checks += 1
        assert hashlib.sha256(vault_note.read_bytes()).hexdigest() == before_hash; checks += 1

    assert checks >= 33, checks
    print(f"NPC_MEMORY_PASS {checks}/33")


if __name__ == "__main__":
    main()
