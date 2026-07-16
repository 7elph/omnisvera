from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.character_play import init_character_play  # noqa: E402
from app.contract_play import (  # noqa: E402
    accept_contract,
    add_assignment,
    approve_reward,
    apply_reputation,
    create_contract,
    create_objective,
    create_reward,
    deliver_reward,
    get_contract,
    link_scene,
    list_contracts,
    list_events,
    list_reputation,
    revert_reputation,
    set_objective_status,
    transition_contract,
    update_contract,
    void_contract_event,
)
from app.player_inventory import init_player_inventory  # noqa: E402
from app.scene_play import change_scene_status, create_scene  # noqa: E402


def expect_error(callback, message: str = "") -> None:
    try:
        callback()
    except (PermissionError, RuntimeError, ValueError) as error:
        if message:
            assert message.casefold() in str(error).casefold(), str(error)
    else:
        raise AssertionError("Era esperado um erro")


def seed_character_state(database: Path, profile_id: str, coins: int = 0) -> None:
    init_character_play(database)
    init_player_inventory(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,'2026-01-01T00:00:00+00:00')",
            (profile_id, json.dumps({"coins": coins, "conditions": [], "resources": []}, ensure_ascii=False)),
        )


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        database = Path(directory) / "contracts.sqlite3"
        seed_character_state(database, "vezemir", coins=3)
        seed_character_state(database, "varkh", coins=0)

        contract, created = create_contract(
            database,
            request_id="contract-svc-0001",
            campaign_id="omnisvera",
            actor_id="master",
            fields={
                "title": "Contrato Técnico de Validação",
                "contract_type": "investigação",
                "issuer_name": "Administração do Conclave",
                "location_name": "Ambiente de Validação",
                "public_summary": "Validar fluxo de contratos.",
                "public_briefing": "Briefing público de validação.",
                "private_briefing": "Segredo de validação.",
                "risk_label": "Técnico",
                "deadline_text": "Durante a validação.",
            },
        )
        assert created and contract["status"] == "draft"
        assert list_contracts(database, access_mode="player", profile_id="vezemir") == []
        assert get_contract(database, contract["id"], access_mode="player", profile_id="vezemir") is None
        same_contract, created_again = create_contract(database, request_id="contract-svc-0001", campaign_id="omnisvera", actor_id="master", fields={})
        assert not created_again and same_contract["id"] == contract["id"]

        updated = update_contract(database, contract["id"], expected_version=contract["version"], fields={"risk_label": "Técnico controlado"}, actor_id="master")
        assert updated["version"] == contract["version"] + 1
        expect_error(lambda: update_contract(database, contract["id"], expected_version=contract["version"], fields={"risk_label": "Perdido"}, actor_id="master"), "vers")

        secret_objective, _ = create_objective(
            database,
            contract["id"],
            request_id="objective-secret-1",
            actor_id="master",
            fields={
                "title": "Objetivo secreto",
                "public_description": "Descrição pública que não deve aparecer ainda.",
                "private_description": "Detalhe secreto do Mestre.",
                "status": "hidden",
                "revealed_to_players": False,
            },
        )
        public_objective, _ = create_objective(
            database,
            contract["id"],
            request_id="objective-public-1",
            actor_id="master",
            fields={
                "title": "Validar o fluxo de contratos",
                "public_description": "Concluir a validação técnica.",
                "status": "available",
                "progress_current": 0,
                "progress_target": 1,
                "revealed_to_players": True,
            },
        )

        published = transition_contract(database, contract["id"], status="published", actor_id="master", actor_role="gm", request_id="publish-svc-001")
        assert published["status"] == "published" and published["published_at"]
        player_contract = get_contract(database, contract["id"], access_mode="player", profile_id="vezemir")
        assert player_contract is not None
        player_text = json.dumps(player_contract, ensure_ascii=False)
        assert "Segredo de validação" not in player_text and "Detalhe secreto" not in player_text
        assert [item["title"] for item in player_contract["objectives"]] == ["Validar o fluxo de contratos"]
        gm_contract = get_contract(database, contract["id"], access_mode="gm", profile_id=None)
        assert gm_contract and "Segredo de validação" in gm_contract["private_briefing"] and len(gm_contract["objectives"]) == 2
        expect_error(lambda: transition_contract(database, contract["id"], status="active", actor_id="master", actor_role="gm", request_id="bad-transition"), "Trans")

        assignment = add_assignment(database, contract["id"], request_id="assign-svc-001", character_id="vezemir", assigned_by="master", public_role="Responsável")
        assert assignment["character_id"] == "vezemir"
        same_assignment = add_assignment(database, contract["id"], request_id="assign-svc-001", character_id="vezemir", assigned_by="master", public_role="Responsável")
        assert same_assignment["id"] == assignment["id"]
        expect_error(lambda: add_assignment(database, contract["id"], request_id="assign-svc-002", character_id="vezemir", assigned_by="master"), "atribu")

        accepted = accept_contract(database, contract["id"], request_id="accept-svc-001", actor_id="master", actor_role="gm")
        assert accepted["status"] == "accepted"
        accepted_retry = accept_contract(database, contract["id"], request_id="accept-svc-001", actor_id="master", actor_role="gm")
        assert accepted_retry["status"] == "accepted"
        active = transition_contract(database, contract["id"], status="active", actor_id="master", actor_role="gm", request_id="start-svc-001")
        assert active["status"] == "active" and active["started_at"]

        revealed = set_objective_status(database, secret_objective["id"], status="available", request_id="reveal-secret-1", actor_id="master")
        assert revealed["revealed_to_players"]
        completed_objective = set_objective_status(database, public_objective["id"], status="completed", request_id="complete-objective-1", actor_id="master")
        assert completed_objective["status"] == "completed"
        completed_retry = set_objective_status(database, public_objective["id"], status="completed", request_id="complete-objective-1", actor_id="master")
        assert completed_retry["status"] == "completed"
        expect_error(lambda: set_objective_status(database, public_objective["id"], status="completed", request_id="complete-objective-2", actor_id="master"), "encerrado")

        scene, _ = create_scene(
            database,
            request_id="contract-scene-001",
            campaign_id="omnisvera",
            title="Cena técnica vinculada",
            location_name="Ambiente de Validação",
            public_description="Cena pública.",
            objective="Validar vínculo",
            visibility="table",
            created_by="master",
        )
        change_scene_status(database, scene["id"], "active")
        linked, linked_created = link_scene(database, contract["id"], request_id="link-scene-001", scene_id=scene["id"], objective_id=secret_objective["id"], link_type="investigation", created_by="master")
        assert linked_created and linked["scene_id"] == scene["id"]
        expect_error(lambda: link_scene(database, contract["id"], request_id="link-scene-002", scene_id=scene["id"], objective_id=secret_objective["id"], link_type="investigation", created_by="master"), "vinculada")
        with_scene = get_contract(database, contract["id"], access_mode="gm", profile_id=None)
        assert with_scene and with_scene["scene_links"][0]["scene_title"] == "Cena técnica vinculada"

        private_reward, _ = create_reward(database, contract["id"], request_id="reward-private-1", actor_id="master", fields={"reward_type": "information", "label": "Informação secreta", "visibility": "gm"})
        assert private_reward["visibility"] == "gm"
        public_before_reward = get_contract(database, contract["id"], access_mode="player", profile_id="vezemir")
        assert public_before_reward and "Informação secreta" not in json.dumps(public_before_reward, ensure_ascii=False)

        completed = transition_contract(database, contract["id"], status="completed", actor_id="master", actor_role="gm", request_id="complete-svc-001")
        assert completed["status"] == "completed"
        assert get_contract(database, contract["id"], access_mode="player", profile_id="vezemir")["status"] == "completed"

        currency_reward, _ = create_reward(database, contract["id"], request_id="reward-currency-1", actor_id="master", fields={"reward_type": "currency", "label": "Moeda genérica", "quantity": 2, "currency_type": "moeda", "visibility": "table"})
        approved_currency = approve_reward(database, currency_reward["id"], request_id="approve-currency-1", actor_id="master")
        assert approved_currency["status"] == "approved"
        delivered_currency = deliver_reward(database, currency_reward["id"], request_id="deliver-currency-1", actor_id="master", character_ids=["vezemir"])
        assert delivered_currency["character_event_ids"]
        delivered_currency_retry = deliver_reward(database, currency_reward["id"], request_id="deliver-currency-1", actor_id="master", character_ids=["vezemir"])
        assert delivered_currency_retry["character_event_ids"] == delivered_currency["character_event_ids"]
        expect_error(lambda: deliver_reward(database, currency_reward["id"], request_id="deliver-currency-2", actor_id="master", character_ids=["vezemir"]), "entregue")

        item_reward, _ = create_reward(database, contract["id"], request_id="reward-item-1", actor_id="master", fields={"reward_type": "item", "label": "Item técnico", "quantity": 1, "item_source": "Items/Item Técnico.md", "item_name": "Item Técnico", "visibility": "table"})
        approve_reward(database, item_reward["id"], request_id="approve-item-1", actor_id="master")
        delivered_item = deliver_reward(database, item_reward["id"], request_id="deliver-item-1", actor_id="master", character_ids=["vezemir"])
        assert delivered_item["character_event_ids"]

        reputation_reward, _ = create_reward(database, contract["id"], request_id="reward-rep-1", actor_id="master", fields={"reward_type": "reputation", "label": "Renome técnico", "reputation_faction": "Conclave dos Errantes", "reputation_amount": 2, "visibility": "table"})
        approve_reward(database, reputation_reward["id"], request_id="approve-rep-1", actor_id="master")
        delivered_rep = deliver_reward(database, reputation_reward["id"], request_id="deliver-rep-1", actor_id="master", character_ids=[])
        assert delivered_rep["reputation_entries"][0]["resulting_value"] == 2
        direct_rep = apply_reputation(database, request_id="direct-rep-001", campaign_id="omnisvera", faction_name="Conclave dos Errantes", delta=-1, reason="Correção técnica", actor_id="master", actor_role="gm", contract_id=contract["id"])
        assert direct_rep["resulting_value"] == 1
        reverted = revert_reputation(database, direct_rep["id"], actor_id="master")
        assert reverted["reverted"]
        ledger = list_reputation(database, party_id="group")
        assert len(ledger) >= 2

        events = list_events(database, contract["id"], access_mode="gm", profile_id=None)
        assert any(event["event_type"] == "reward_delivered" for event in events)
        player_events = list_events(database, contract["id"], access_mode="player", profile_id="vezemir")
        assert all("private_text" not in event for event in player_events)
        voided = void_contract_event(database, events[0]["id"], actor_id="master", reason="Correção técnica")
        assert voided["voided"]

        with sqlite3.connect(database) as connection:
            state = json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            inventory = connection.execute("SELECT quantity FROM player_inventory WHERE profile_id='vezemir' AND item_path='Items/Item Técnico.md'").fetchone()
            character_events = connection.execute("SELECT COUNT(*) FROM character_events WHERE character_id='vezemir'").fetchone()[0]
        assert state["coins"] == 5
        assert inventory and inventory[0] == 1
        assert character_events >= 2

    print("CONTRACT_PLAY_SERVICE_PASS")


if __name__ == "__main__":
    main()
