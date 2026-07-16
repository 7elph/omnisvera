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
        root = Path(directory); vault = root / "vault"; database = root / "companion.sqlite3"
        (vault / "Characters/Individual").mkdir(parents=True); (vault / "Locations").mkdir(parents=True); (vault / "zz_media/maps").mkdir(parents=True)
        map_note = vault / "MAPA TÉCNICO.md"
        map_note.write_text("""---
type: map
visibility: Jogadores
cover: zz_media/maps/technical.png
width: 1000
height: 800
---
# Mapa Técnico
```leaflet
image: zz_media/maps/technical.png
bounds: [[0,0],[100,100]]
lat: 50
long: 50
```
""", encoding="utf-8")
        location_note = vault / "Locations/Ponto Técnico.md"
        location_note.write_text("""---
type: location
visibility: Jogadores
location_type: landmark
territory: Ambiente de Validação
cover: zz_media/maps/technical.png
description: Local técnico público.
---
# Ponto Técnico
""", encoding="utf-8")
        character_note = vault / "Characters/Individual/Vezemir.md"
        character_note.write_text("""---
type: character
role: player
visibility: Jogadores
race: Meio-Elfo
class: Guerreiro
level: 1
current_hp: 8
maximum_hp: 8
location: Ponto Técnico Norte
---
# Vezemir
""", encoding="utf-8")
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (map_note, location_note, character_note)}

        os.environ.update({
            "OMNISVERA_VAULT_PATH": str(vault), "OMNISVERA_DB_PATH": str(database),
            "OMNISVERA_MASTER_TOKEN": "world-master-token", "OMNISVERA_PLAYER_TOKEN": "world-public-token",
            "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps({"vezemir": {"token": "world-player-token", "character_path": "Characters/Individual/Vezemir.md", "character_title": "Vezemir"}}),
            "OMNISVERA_REBUILD_ON_STARTUP": "true", "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
        })
        sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))
        from fastapi.testclient import TestClient  # noqa: E402
        from app.main import app  # noqa: E402

        master = {"X-Omnisvera-Token": "world-master-token"}; player = {"X-Omnisvera-Token": "world-player-token"}
        with TestClient(app) as client:
            assert client.post("/gm/world/maps", headers=player, json={"request_id": "blocked-map-001", "title": "Bloqueado"}).status_code == 401
            preview = client.post("/gm/world/maps/import-preview", headers=master, json={"request_id": "preview-map-001", "source_path": "MAPA TÉCNICO.md"})
            assert preview.status_code == 200 and preview.json()["adapter"] == "obsidian_leaflet_image_v1"
            assert client.post("/gm/world/maps/import", headers=master, json={"request_id": "import-map-no-confirm", "source_path": "MAPA TÉCNICO.md"}).status_code == 400
            imported = client.post("/gm/world/maps/import", headers=master, json={"request_id": "import-map-confirm", "source_path": "MAPA TÉCNICO.md", "confirm": True})
            assert imported.status_code == 200, imported.text
            world_map = imported.json(); map_id = world_map["id"]
            assert client.get("/world/maps", headers=player).json()[0]["id"] == map_id
            duplicate = client.post("/gm/world/maps/import", headers=master, json={"request_id": "import-map-duplicate", "source_path": "MAPA TÉCNICO.md", "confirm": True})
            assert duplicate.status_code == 200 and duplicate.json()["id"] == map_id

            north = client.post("/gm/world/locations", headers=master, json={"request_id": "api-location-north", "map_id": map_id, "name": "Ponto Norte", "location_type": "landmark", "x": 20, "y": 20, "visibility": "table", "discovered_by_default": True})
            assert north.status_code == 200, north.text
            south = client.post("/gm/world/locations/import?map_id=%s" % map_id, headers=master, json={"request_id": "api-location-south", "source_path": "Locations/Ponto Técnico.md", "confirm": True, "visibility": "gm"})
            assert south.status_code == 200, south.text
            north_id = north.json()["id"]; south_id = south.json()["id"]
            assert client.get(f"/world/locations/{south_id}", headers=player).status_code == 404
            rumor = client.post(f"/gm/world/locations/{south_id}/discoveries", headers=master, json={"request_id": "api-discovery-rumor", "discoverer_type": "campaign", "knowledge_level": "rumored", "public_name_override": "Um ponto ao sul"})
            assert rumor.status_code == 200
            rumored = client.get(f"/world/locations/{south_id}", headers=player).json()
            assert rumored["name"] == "Um ponto ao sul" and rumored["x"] is None and rumored["y"] is None
            assert client.post(f"/gm/world/locations/{south_id}/discoveries", headers=master, json={"request_id": "api-discovery-full", "discoverer_type": "campaign", "knowledge_level": "discovered"}).status_code == 200
            assert client.get(f"/world/locations/{south_id}", headers=player).json()["name"] == "Ponto Técnico"
            stale = client.patch(f"/gm/world/locations/{north_id}", headers=master, json={"expected_version": 99, "fields": {"x": 30}})
            assert stale.status_code == 409

            route = client.post("/gm/world/routes", headers=master, json={"request_id": "api-route-001", "origin_location_id": north_id, "destination_location_id": south_id, "title": "Caminho Técnico", "route_type": "road", "duration_value": 3, "duration_unit": "etapas", "public": True})
            assert route.status_code == 200 and route.json()["origin_location_id"] == north_id
            assert len(client.get("/world/routes", headers=player).json()) == 1
            hidden_route = client.post("/gm/world/routes", headers=master, json={"request_id": "api-route-hidden", "origin_location_id": south_id, "destination_location_id": north_id, "title": "Volta secreta", "route_type": "trail", "public": False})
            assert hidden_route.status_code == 200 and len(client.get("/world/routes", headers=player).json()) == 1

            assert client.get("/characters/vezemir", headers=master).status_code == 200
            journey = client.post("/gm/world/journeys", headers=master, json={"request_id": "api-journey-001", "route_id": route.json()["id"], "origin_location_id": north_id, "destination_location_id": south_id, "title": "Travessia API", "progress_target": 2, "visibility": "table"})
            assert journey.status_code == 200, journey.text
            journey_id = journey.json()["id"]
            participant = client.post(f"/gm/world/journeys/{journey_id}/participants", headers=master, json={"request_id": "api-journey-pc", "participant_type": "player_character", "character_id": "vezemir", "public_label": "Vezemir"})
            assert participant.status_code == 200
            assert client.post(f"/gm/world/journeys/{journey_id}/participants", headers=master, json={"request_id": "api-journey-pc-duplicate", "participant_type": "player_character", "character_id": "vezemir", "public_label": "Vezemir"}).status_code == 400
            started = client.post(f"/gm/world/journeys/{journey_id}/transition/start", headers=master, json={"request_id": "api-journey-start", "expected_version": 1})
            assert started.status_code == 200 and started.json()["status"] == "active"
            advanced = client.post(f"/gm/world/journeys/{journey_id}/advance", headers=master, json={"request_id": "api-journey-advance", "expected_version": 2, "amount": 1})
            assert advanced.status_code == 200 and advanced.json()["progress_current"] == 1
            repeated = client.post(f"/gm/world/journeys/{journey_id}/advance", headers=master, json={"request_id": "api-journey-advance", "expected_version": 2, "amount": 1})
            assert repeated.status_code == 200 and repeated.json()["progress_current"] == 1
            paused = client.post(f"/gm/world/journeys/{journey_id}/transition/pause", headers=master, json={"request_id": "api-journey-pause", "expected_version": 3})
            assert paused.status_code == 200 and paused.json()["status"] == "paused"
            assert client.post(f"/gm/world/journeys/{journey_id}/advance", headers=master, json={"request_id": "api-journey-paused-advance", "expected_version": 4, "amount": 1}).status_code == 400
            resumed = client.post(f"/gm/world/journeys/{journey_id}/transition/resume", headers=master, json={"request_id": "api-journey-resume", "expected_version": 4})
            assert resumed.status_code == 200 and resumed.json()["status"] == "active"
            scene = client.post("/gm/scenes", headers=master, json={"request_id": "api-world-scene", "title": "Cena de viagem", "location_name": "Estrada", "visibility": "table"})
            assert scene.status_code == 200
            linked_scene = client.post(f"/gm/world/journeys/{journey_id}/scenes", headers=master, json={"request_id": "api-world-scene-link", "scene_id": scene.json()["id"], "stage_label": "Etapa 1", "progress_value": 1})
            assert linked_scene.status_code == 200
            hidden_scene = client.post("/gm/scenes", headers=master, json={"request_id": "api-world-hidden-scene", "title": "Cena oculta", "location_name": "Desconhecido", "visibility": "gm"})
            assert hidden_scene.status_code == 200
            assert client.post(f"/gm/world/journeys/{journey_id}/scenes", headers=master, json={"request_id": "api-world-hidden-link", "scene_id": hidden_scene.json()["id"]}).status_code == 200
            scene_location = client.post(f"/gm/world/scenes/{scene.json()['id']}/location", headers=master, json={"request_id": "api-scene-location", "location_id": south_id})
            assert scene_location.status_code == 200 and client.get(f"/scenes/{scene.json()['id']}/locations", headers=player).status_code == 200
            completed = client.post(f"/gm/world/journeys/{journey_id}/transition/complete", headers=master, json={"request_id": "api-journey-complete", "expected_version": 5})
            assert completed.status_code == 200, completed.text
            assert completed.json()["status"] == "completed"
            character_response = client.get("/characters/vezemir", headers=master)
            assert character_response.status_code == 200, character_response.text
            character = character_response.json()
            assert character["state"]["location"] == "Ponto Técnico"
            player_journey = client.get(f"/world/journeys/{journey_id}", headers=player)
            assert player_journey.status_code == 200 and any(item["event_type"] == "arrival" for item in player_journey.json()["events"])
            player_payload = player_journey.json()
            assert all(link["scene_id"] != hidden_scene.json()["id"] for link in player_payload["scene_links"])
            assert all("before_json" not in event and "after_json" not in event for event in player_payload["events"])

            cancel = client.post("/gm/world/journeys", headers=master, json={"request_id": "api-journey-cancel", "origin_location_id": south_id, "destination_location_id": north_id, "title": "Cancelada", "progress_target": 1})
            cancelled = client.post(f"/gm/world/journeys/{cancel.json()['id']}/transition/cancel", headers=master, json={"request_id": "api-cancel-transition", "expected_version": 1, "reason": "Teste"})
            assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
            assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in before.items())

    print("WORLD_TRAVEL_API_PASS")


if __name__ == "__main__":
    main()
