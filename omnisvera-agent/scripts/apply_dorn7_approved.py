"""Apply explicitly approved GM ally through existing API, preserving any existing token."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    payload = json.loads((ROOT / "backend/app/data/dorn7_approved.json").read_text(encoding="utf-8"))
    db = ROOT / "backend/data/omnisvera_companion.sqlite3"
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as connection:
        rows = connection.execute("SELECT id,name FROM session_workspace_tokens").fetchall()
        matches = [row for row in rows if row[1].lower().replace("-", "").replace(" ", "") in {"dorn7", "unidadedorn7"}]
        if matches:
            print(json.dumps({"status": "EXISTS_NOT_OVERWRITTEN", "ids": [row[0] for row in matches]}))
            return
        backup = ROOT / ".autonomy/runtime" / ("before-dorn-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".sqlite3")
        with closing(sqlite3.connect(backup)) as target:
            connection.backup(target)
    credentials = json.loads((ROOT / "backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    with httpx.Client(base_url="http://127.0.0.1:8788", headers={"X-Omnisvera-Token": credentials["master_token"]}, timeout=60, trust_env=False) as client:
        response = client.get("/workspace")
        response.raise_for_status()
        workspace = response.json()
        payload["map_id"] = (workspace.get("map") or {}).get("id") or "default"
        payload.update(latitude=55, longitude=55)
        response = client.post("/gm/workspace/tokens", json=payload)
        response.raise_for_status()
        token = response.json()
        assert token["maximum_hp"] == 20 and token["sheet"]["armor_class"] == 16
        assert token["visible_to_players"] is False
        print(json.dumps({"status": "CREATED", "token_id": token["id"], "map_id": token["map_id"], "backup": str(backup)}, ensure_ascii=False))
    with httpx.Client(base_url="http://127.0.0.1:8788", headers={"X-Omnisvera-Token": credentials["player_profiles"]["raziel"]["token"]}, timeout=30, trust_env=False) as player:
        response = player.get("/workspace")
        response.raise_for_status()
        assert all(t["id"] != token["id"] for t in response.json()["tokens"])
        response = player.patch(f"/gm/workspace/tokens/{token['id']}", json={"current_hp": 1})
        assert response.status_code in (401, 403)
        print("PLAYER_VISIBILITY=HIDDEN; PLAYER_EDIT=DENIED")


if __name__ == "__main__":
    main()
