from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.character_play import init_character_play  # noqa: E402
from app.npc_memory import create_npc, get_npc, init_npc_memory  # noqa: E402
from app.world_travel import (  # noqa: E402
    add_journey_participant,
    advance_journey,
    complete_journey,
    create_journey,
    create_location,
    create_map,
    create_route,
    discover_location,
    get_journey,
    get_location,
    get_map,
    init_world_travel,
    link_journey_scene,
    link_location,
    list_journey_events,
    list_journeys,
    list_locations,
    list_maps,
    list_routes,
    related_locations,
    transition_journey,
    update_location,
    update_location_state,
    update_map,
    void_journey_event,
)


def expect_error(callback, phrase: str = "") -> None:
    try:
        callback()
    except (RuntimeError, ValueError, sqlite3.IntegrityError) as error:
        if phrase:
            assert phrase.casefold() in str(error).casefold(), str(error)
    else:
        raise AssertionError("Era esperado um erro")


def main() -> None:
    checks = 0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        database = root / "world.sqlite3"
        vault_note = root / "MAPA.md"
        vault_note.write_text("---\ntype: map\n---\n# Somente leitura\n", encoding="utf-8")
        before_hash = hashlib.sha256(vault_note.read_bytes()).hexdigest()
        init_character_play(database)
        init_npc_memory(database)
        init_world_travel(database)

        with sqlite3.connect(database) as connection:
            connection.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,'now')", ("vezemir", json.dumps({"current_location": "Origem antiga", "maximum_hp": 10, "current_hp": 10})))

        world_map, created = create_map(database, request_id="map-technical-001", campaign_id="omnisvera", actor_id="master", fields={"title": "Mapa Técnico", "source_path": "MAPA.md", "image_path": "zz_media/maps/mapa.png", "map_type": "world", "coordinate_system": "percentage", "visibility": "table"})
        assert created and world_map["title"] == "Mapa Técnico"; checks += 1
        repeated, again = create_map(database, request_id="map-technical-001", campaign_id="omnisvera", actor_id="master", fields={"title": "Duplicado"})
        assert not again and repeated["id"] == world_map["id"]; checks += 1
        by_source, source_created = create_map(database, request_id="map-technical-002", campaign_id="omnisvera", actor_id="master", fields={"title": "Fonte duplicada", "source_path": "MAPA.md"})
        assert not source_created and by_source["id"] == world_map["id"]; checks += 1
        assert list_maps(database, campaign_id="omnisvera", access_mode="player")[0]["title"] == "Mapa Técnico"; checks += 1
        assert "private_description" not in get_map(database, world_map["id"], access_mode="player"); checks += 1
        updated_map = update_map(database, world_map["id"], expected_version=1, fields={"public_description": "Mapa público"})
        assert updated_map["version"] == 2; checks += 1
        expect_error(lambda: update_map(database, world_map["id"], expected_version=1, fields={"title": "Antigo"}), "versão"); checks += 1

        north, _ = create_location(database, request_id="location-north-001", campaign_id="omnisvera", actor_id="master", fields={"map_id": world_map["id"], "name": "Ponto Norte", "location_type": "landmark", "x": 20, "y": 25, "visibility": "table", "discovered_by_default": True, "public_description": "Visível", "private_description": "Privado"})
        south, _ = create_location(database, request_id="location-south-001", campaign_id="omnisvera", actor_id="master", fields={"map_id": world_map["id"], "name": "Ponto Sul", "location_type": "landmark", "x": 80, "y": 75, "visibility": "gm", "private_description": "Destino oculto"})
        assert north["x"] == 20 and north["state_version"] == 1; checks += 1
        assert get_location(database, north["id"], access_mode="player")["name"] == "Ponto Norte"; checks += 1
        assert get_location(database, south["id"], access_mode="player") is None; checks += 1
        player_north = get_location(database, north["id"], access_mode="player")
        assert "private_description" not in player_north and "private_status" not in player_north; checks += 1
        moved = update_location(database, north["id"], expected_version=1, fields={"x": 22.5, "y": 27.5})
        assert moved["version"] == 2 and moved["x"] == 22.5; checks += 1
        expect_error(lambda: update_location(database, north["id"], expected_version=1, fields={"x": 1}), "versão"); checks += 1
        state = update_location_state(database, north["id"], expected_version=1, fields={"danger_label": "Baixo", "accessible": True})
        assert state["state_version"] == 2 and state["danger_label"] == "Baixo"; checks += 1

        rumor, rumor_created = discover_location(database, south["id"], request_id="discovery-rumor-001", campaign_id="omnisvera", actor_id="master", fields={"discoverer_type": "campaign", "party_id": "group", "knowledge_level": "rumored", "public_name_override": "Lugar ao sul"})
        assert rumor_created and rumor["knowledge_level"] == "rumored"; checks += 1
        rumored = get_location(database, south["id"], access_mode="player")
        assert rumored and rumored["name"] == "Lugar ao sul" and rumored["x"] is None and rumored["y"] is None; checks += 1
        discover_location(database, south["id"], request_id="discovery-full-001", campaign_id="omnisvera", actor_id="master", fields={"discoverer_type": "campaign", "party_id": "group", "knowledge_level": "discovered"})
        discovered = get_location(database, south["id"], access_mode="player")
        assert discovered and discovered["name"] == "Ponto Sul" and discovered["x"] == 80; checks += 1
        discover_location(database, south["id"], request_id="discovery-visited-001", campaign_id="omnisvera", actor_id="master", fields={"discoverer_type": "campaign", "party_id": "group", "knowledge_level": "visited"})
        assert get_location(database, south["id"], access_mode="player")["knowledge_level"] == "visited"; checks += 1

        route, route_created = create_route(database, request_id="route-tech-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": north["id"], "destination_location_id": south["id"], "title": "Caminho Técnico", "route_type": "road", "duration_value": 4, "duration_unit": "etapas", "public": True})
        assert route_created and route["origin_location_id"] == north["id"]; checks += 1
        assert not any(item["origin_location_id"] == south["id"] and item["destination_location_id"] == north["id"] for item in list_routes(database, campaign_id="omnisvera", access_mode="gm")); checks += 1
        assert list_routes(database, campaign_id="omnisvera", access_mode="player")[0]["title"] == "Caminho Técnico"; checks += 1
        hidden_route, _ = create_route(database, request_id="route-hidden-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": south["id"], "destination_location_id": north["id"], "title": "Retorno oculto", "route_type": "trail", "public": False})
        assert all(item["id"] != hidden_route["id"] for item in list_routes(database, campaign_id="omnisvera", access_mode="player")); checks += 1
        expect_error(lambda: create_route(database, request_id="route-invalid-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": north["id"], "destination_location_id": north["id"], "title": "Inválida"}), "diferentes"); checks += 1

        npc, _ = create_npc(database, request_id="npc-world-001", campaign_id="omnisvera", actor_id="master", fields={"name": "NPC Técnico", "current_location": "Ponto Norte", "visible_to_players": True})
        journey, journey_created = create_journey(database, request_id="journey-tech-001", campaign_id="omnisvera", actor_id="master", fields={"route_id": route["id"], "origin_location_id": north["id"], "destination_location_id": south["id"], "title": "Travessia Técnica", "progress_target": 4, "visibility": "table"})
        assert journey_created and journey["status"] == "planned"; checks += 1
        repeat_journey, repeat_created = create_journey(database, request_id="journey-tech-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": north["id"], "destination_location_id": south["id"], "title": "Duplicada"})
        assert not repeat_created and repeat_journey["id"] == journey["id"]; checks += 1
        expect_error(lambda: create_journey(database, request_id="journey-invalid-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": north["id"], "destination_location_id": north["id"], "title": "Inválida"}), "diferentes"); checks += 1
        pc_participant, participant_created = add_journey_participant(database, journey["id"], request_id="journey-pc-001", actor_id="master", fields={"participant_type": "player_character", "character_id": "vezemir", "public_label": "Vezemir"})
        npc_participant, _ = add_journey_participant(database, journey["id"], request_id="journey-npc-001", actor_id="master", fields={"participant_type": "npc", "npc_id": npc["id"], "public_label": "NPC Técnico"})
        assert participant_created and pc_participant["character_id"] == "vezemir" and npc_participant["npc_id"] == npc["id"]; checks += 1
        expect_error(lambda: add_journey_participant(database, journey["id"], request_id="journey-pc-002", actor_id="master", fields={"participant_type": "player_character", "character_id": "vezemir", "public_label": "Duplicado"}), "incluído"); checks += 1
        assert len(get_journey(database, journey["id"], access_mode="player", profile_id="vezemir")["participants"]) == 2; checks += 1

        started = transition_journey(database, journey["id"], request_id="journey-start-001", actor_id="master", action="start", expected_version=1)
        assert started["status"] == "active" and started["version"] == 2; checks += 1
        started_repeat = transition_journey(database, journey["id"], request_id="journey-start-001", actor_id="master", action="start", expected_version=1)
        assert started_repeat["version"] == 2; checks += 1
        advanced = advance_journey(database, journey["id"], request_id="journey-advance-001", actor_id="master", expected_version=2, amount=1)
        assert advanced["progress_current"] == 1 and advanced["version"] == 3; checks += 1
        advanced_repeat = advance_journey(database, journey["id"], request_id="journey-advance-001", actor_id="master", expected_version=2, amount=1)
        assert advanced_repeat["progress_current"] == 1; checks += 1
        paused = transition_journey(database, journey["id"], request_id="journey-pause-001", actor_id="master", action="pause", expected_version=3)
        assert paused["status"] == "paused"; checks += 1
        expect_error(lambda: advance_journey(database, journey["id"], request_id="journey-advance-paused", actor_id="master", expected_version=4, amount=1), "ativa"); checks += 1
        resumed = transition_journey(database, journey["id"], request_id="journey-resume-001", actor_id="master", action="resume", expected_version=4)
        assert resumed["status"] == "active"; checks += 1
        scene_link, scene_created = link_journey_scene(database, journey["id"], request_id="journey-scene-001", actor_id="master", scene_id=77, stage_label="Etapa técnica", progress_value=1)
        assert scene_created and scene_link["scene_id"] == 77; checks += 1
        scene_link_repeat, scene_created_again = link_journey_scene(database, journey["id"], request_id="journey-scene-002", actor_id="master", scene_id=77)
        assert not scene_created_again and scene_link_repeat["id"] == scene_link["id"]; checks += 1

        completed = complete_journey(database, journey["id"], request_id="journey-complete-001", actor_id="master", expected_version=5)
        assert completed["status"] == "completed" and completed["progress_current"] == 4; checks += 1
        completed_repeat = complete_journey(database, journey["id"], request_id="journey-complete-001", actor_id="master", expected_version=5)
        assert completed_repeat["status"] == "completed"; checks += 1
        with sqlite3.connect(database) as connection:
            character_state = json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            assert character_state["current_location_id"] == south["id"] and character_state["location"] == "Ponto Sul"; checks += 1
            assert connection.execute("SELECT COUNT(*) FROM character_events WHERE character_id='vezemir' AND event_type='journey_arrival'").fetchone()[0] == 1; checks += 1
            assert connection.execute("SELECT current_location_id FROM npc_states WHERE npc_id=?", (npc["id"],)).fetchone()[0] == south["id"]; checks += 1
            assert connection.execute("SELECT COUNT(*) FROM npc_events WHERE npc_id=? AND event_type='location_changed'", (npc["id"],)).fetchone()[0] == 1; checks += 1
        assert (get_npc(database, npc["id"], access_mode="gm") or {})["current_location"] == "Ponto Sul"; checks += 1
        assert any(item["event_type"] == "arrival" for item in list_journey_events(database, journey["id"], access_mode="player")); checks += 1
        event = list_journey_events(database, journey["id"], access_mode="gm")[0]
        voided = void_journey_event(database, event["id"], actor_id="master", reason="Correção técnica")
        assert voided["voided"] and voided["void_reason"] == "Correção técnica"; checks += 1

        cancelled, _ = create_journey(database, request_id="journey-cancel-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": south["id"], "destination_location_id": north["id"], "title": "Viagem cancelada", "progress_target": 2})
        add_journey_participant(database, cancelled["id"], request_id="journey-cancel-pc", actor_id="master", fields={"participant_type": "player_character", "character_id": "vezemir", "public_label": "Vezemir"})
        cancelled_result = transition_journey(database, cancelled["id"], request_id="journey-cancel-transition", actor_id="master", action="cancel", expected_version=1, reason="Teste")
        assert cancelled_result["status"] == "cancelled"; checks += 1
        with sqlite3.connect(database) as connection:
            assert json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])["current_location_id"] == south["id"]; checks += 1
        failed, _ = create_journey(database, request_id="journey-fail-001", campaign_id="omnisvera", actor_id="master", fields={"origin_location_id": south["id"], "destination_location_id": north["id"], "title": "Viagem falha"})
        failed = transition_journey(database, failed["id"], request_id="journey-fail-start", actor_id="master", action="start", expected_version=1)
        failed = transition_journey(database, failed["id"], request_id="journey-fail-transition", actor_id="master", action="fail", expected_version=2, reason="Bloqueada")
        assert failed["status"] == "failed"; checks += 1

        scene_location, linked = link_location(database, kind="scene", owner_id=77, location_id=south["id"], request_id="scene-location-001", actor_id="master")
        assert linked and scene_location["location_id"] == south["id"]; checks += 1
        contract_location, linked = link_location(database, kind="contract", owner_id=88, location_id=south["id"], request_id="contract-location-001", actor_id="master", role="destination", public=True)
        assert linked and contract_location["public"]; checks += 1
        assert related_locations(database, kind="scene", owner_id=77, access_mode="player")[0]["location"]["name"] == "Ponto Sul"; checks += 1
        assert related_locations(database, kind="contract", owner_id=88, access_mode="player")[0]["link"]["role"] == "destination"; checks += 1
        assert list_journeys(database, campaign_id="omnisvera", access_mode="player", profile_id="vezemir"); checks += 1
        assert hashlib.sha256(vault_note.read_bytes()).hexdigest() == before_hash; checks += 1

    assert checks >= 54, checks
    print(f"WORLD_TRAVEL_PASS {checks}/54")


if __name__ == "__main__":
    main()
