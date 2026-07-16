from __future__ import annotations

import tempfile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.scene_play import (  # noqa: E402
    active_scene,
    add_participant,
    cancel_action,
    change_scene_status,
    change_session_status,
    create_element,
    create_scene,
    create_session,
    declare_action,
    get_action,
    link_completed_roll,
    link_roll_request,
    list_scenes,
    list_sessions,
    record_consequence,
    resolve_action,
    scene_view,
    update_element,
    update_participant,
    update_scene,
    void_event,
)


def expect_error(callback, message: str = "") -> None:
    try:
        callback()
    except (PermissionError, RuntimeError, ValueError) as error:
        if message:
            assert message.casefold() in str(error).casefold(), str(error)
    else:
        raise AssertionError("Era esperado um erro")


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        database = Path(directory) / "scene.sqlite3"
        session, created = create_session(
            database,
            request_id="session-service-01",
            campaign_id="omnisvera",
            title="Sessão técnica",
            session_number=1,
            private_notes="Somente Mestre",
            created_by="master",
        )
        assert created and session["status"] == "planned"
        repeated_session, repeated = create_session(
            database,
            request_id="session-service-01",
            campaign_id="omnisvera",
            title="Não duplica",
            created_by="master",
        )
        assert not repeated and repeated_session["id"] == session["id"]
        assert change_session_status(database, session["id"], "active")["started_at"]
        assert len(list_sessions(database)) == 1

        first, created = create_scene(
            database,
            request_id="scene-service-001",
            campaign_id="omnisvera",
            session_id=session["id"],
            title="Primeira cena",
            location_name="Sala técnica",
            public_description="Descrição pública",
            objective="Validar",
            private_notes="Nota secreta",
            visibility="table",
            created_by="master",
        )
        assert created and first["version"] == 1
        updated = update_scene(database, first["id"], expected_version=1, fields={"objective": "Objetivo atualizado"})
        assert updated["version"] == 2
        expect_error(lambda: update_scene(database, first["id"], expected_version=1, fields={"objective": "Perdido"}), "outro dispositivo")
        change_scene_status(database, first["id"], "active")
        assert active_scene(database)["id"] == first["id"]

        second, _ = create_scene(
            database,
            request_id="scene-service-002",
            campaign_id="omnisvera",
            title="Segunda cena",
            location_name="Outra sala",
            created_by="master",
        )
        change_scene_status(database, second["id"], "active")
        assert active_scene(database)["id"] == second["id"]
        assert next(item for item in list_scenes(database) if item["id"] == first["id"])["status"] == "paused"
        change_scene_status(database, second["id"], "paused")
        change_scene_status(database, first["id"], "active")

        participant = add_participant(
            database,
            first["id"],
            participant_type="player_character",
            character_id="vezemir",
            public_label="Vezemir",
            public_status="Ativo",
            private_status="Observado",
        )
        repeated_participant = add_participant(
            database,
            first["id"],
            participant_type="player_character",
            character_id="vezemir",
            public_label="Duplicado",
        )
        assert participant["id"] == repeated_participant["id"]
        update_participant(database, participant["id"], {"public_status": "Ferido"})

        hidden, _ = create_element(
            database,
            first["id"],
            request_id="element-hidden-01",
            element_type="threat",
            title="Ameaça oculta",
            private_description="Perigo técnico",
            status="hidden",
            visibility="gm",
            created_by="master",
        )
        clue, _ = create_element(
            database,
            first["id"],
            request_id="element-clue-001",
            element_type="clue",
            title="Pista técnica",
            public_description="Uma marca de validação.",
            private_description="Detalhe privado.",
            status="hidden",
            visibility="gm",
            created_by="master",
        )
        player_before = scene_view(database, first["id"], access_mode="player", profile_id="vezemir")
        assert not player_before["elements"] and "private_notes" not in player_before
        assert "private_status" not in player_before["participants"][0]
        gm_view = scene_view(database, first["id"], access_mode="gm", profile_id=None)
        assert len(gm_view["elements"]) == 2 and gm_view["private_notes"] == "Nota secreta"
        update_element(database, clue["id"], fields={}, reveal=True)
        player_after = scene_view(database, first["id"], access_mode="player", profile_id="vezemir")
        assert [item["title"] for item in player_after["elements"]] == ["Pista técnica"]
        assert all(item["id"] != hidden["id"] for item in player_after["elements"])

        action, created = declare_action(
            database,
            first["id"],
            request_id="action-service-01",
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            action_type="investigate",
            description="Vezemir examina a pista.",
            target_label="Marca",
        )
        assert created and action["status"] == "declared"
        same, created_again = declare_action(
            database,
            first["id"],
            request_id="action-service-01",
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            action_type="investigate",
            description="Não duplica",
        )
        assert not created_again and same["id"] == action["id"]
        expect_error(
            lambda: declare_action(database, first["id"], request_id="action-wrong-01", character_id="vezemir", actor_id="varkh", actor_role="player", action_type="observe", description="Inválida"),
            "próprio personagem",
        )
        linked = link_roll_request(database, action["id"], 77)
        assert linked["status"] == "awaiting_roll"
        link_completed_roll(database, scene_id=first["id"], action_id=action["id"], roll_id=88, actor_id="vezemir", actor_role="player", public_text="Resultado 15")
        assert get_action(database, action["id"])["resulting_roll_id"] == 88
        resolved = resolve_action(database, action["id"], actor_id="master", resolution="Pista encontrada")
        assert resolved["status"] == "resolved"
        expect_error(lambda: resolve_action(database, action["id"], actor_id="master", resolution="Outra"), "finalizada")

        rejected_action, _ = declare_action(database, first["id"], request_id="action-reject-01", character_id="vezemir", actor_id="vezemir", actor_role="player", action_type="attack", description="Ataca narrativamente")
        assert resolve_action(database, rejected_action["id"], actor_id="master", resolution="Não há alvo", reject=True)["status"] == "rejected"
        cancelable, _ = declare_action(database, first["id"], request_id="action-cancel-01", character_id="vezemir", actor_id="vezemir", actor_role="player", action_type="move", description="Move-se")
        assert cancel_action(database, cancelable["id"], actor_id="vezemir", actor_role="player")["status"] == "cancelled"

        consequence = record_consequence(database, scene_id=first["id"], action_id=action["id"], character_id="vezemir", character_event_id=501, actor_id="master", title="Condição aplicada", public_text="Vezemir foi marcado")
        assert consequence["character_event_id"] == 501
        voided = void_event(database, consequence["id"], actor_id="master", reason="Reversão técnica")
        assert voided["voided"]

        change_scene_status(database, first["id"], "resolved", summary="Fluxo técnico concluído")
        expect_error(lambda: declare_action(database, first["id"], request_id="action-closed-1", character_id="vezemir", actor_id="vezemir", actor_role="player", action_type="observe", description="Tarde demais"), "não está ativa")
        archived = scene_view(database, first["id"], access_mode="player", profile_id="vezemir")
        assert archived["status"] == "resolved" and archived["resolution_summary"] == "Fluxo técnico concluído"
        assert change_session_status(database, session["id"], "completed")["ended_at"]

    print("SCENE_PLAY_SERVICE_PASS")


if __name__ == "__main__":
    main()
