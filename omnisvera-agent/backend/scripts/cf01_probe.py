"""CF-01: real HTTP/browser rehearsal against a TEMPORARY COPY, never live data.

  python scripts/cf01_probe.py prepare --database <temp-dir>/cf01.sqlite3
  python scripts/cf01_probe.py serve --database <same> --port 8871
  python scripts/cf01_probe.py probe --database <same> --port 8871

The public fixture credentials below work only on the loopback rehearsal server.
No operational tokens are loaded. Restart serve after backend changes.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import sys
import tempfile
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
TOKENS = {role: f"cf01-local-{role}" for role in ("gm", "varkh", "raziel", "vezemir", "morthak")}


def checked_database(raw):
    database = Path(raw).resolve()
    # Test tools cannot open an operational database for writing, even by mistake.
    if Path(tempfile.gettempdir()).resolve() not in database.parents:
        raise ValueError("CF-01 database must be under the OS temporary directory")
    return database


def configure(database):
    profiles = {
        "varkh": ("Varkh Nimalis", "Varkh Nimalis"), "raziel": ("Raziel", "Raziel"),
        "vezemir": ("Vezemir", "Vezemir"), "morthak": ("Morthak", "Morthak"),
    }
    os.environ.update({
        "OMNISVERA_DB_PATH": str(database), "OMNISVERA_MASTER_TOKEN": TOKENS["gm"],
        "OMNISVERA_ACCESS_TOKEN": TOKENS["gm"], "OMNISVERA_PLAYER_TOKEN": "cf01-local-generic",
        "OMNISVERA_REBUILD_ON_STARTUP": "false", "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
        "OLLAMA_BASE_URL": "http://127.0.0.1:1",
        "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps({
            key: {"token": TOKENS[key], "character_path": f"Characters/Individual/{filename}.md", "character_title": title}
            for key, (filename, title) in profiles.items()
        }),
    })


def probe(database, port):
    import httpx
    base = f"http://127.0.0.1:{port}"
    prefix = f"cf01-{uuid.uuid4().hex}"
    clients = {role: httpx.Client(base_url=base, headers={"X-Omnisvera-Token": token}, timeout=20, trust_env=False)
               for role, token in TOKENS.items()}
    gm, player, other = (clients[key] for key in ("gm", "varkh", "raziel"))
    marks = {}
    def mark(name): marks[name] = datetime.now(timezone.utc).isoformat()
    try:
        assert httpx.get(base + "/roll-requests", trust_env=False).status_code == 401
        for role in ("gm", "varkh", "raziel"):
            response = clients[role].get("/health")
            response.raise_for_status()
            assert response.json()["access_mode"] == ("gm" if role == "gm" else "player")
        payload = {"request_id": prefix, "character_id": "varkh", "roll_type": "attribute",
                   "source_id": "charisma", "label": prefix, "visibility": "owner", "target_value": 14, "hide_target": True}
        assert other.post("/gm/roll-requests", json=payload).status_code == 401
        response = gm.post("/gm/roll-requests", json=payload)
        response.raise_for_status()
        request = response.json()
        marks["request_created_at"] = request["created_at"]
        assert gm.post("/gm/roll-requests", json=payload).json()["id"] == request["id"]
        assert request["id"] not in [r["id"] for r in other.get("/roll-requests").json()]
        pending = next(r for r in player.get("/roll-requests").json() if r["id"] == request["id"])
        assert pending.get("target_value") is None
        mark("player_api_visible_at")
        with httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS["varkh"]}, trust_env=False) as reconnected:
            assert request["id"] in [r["id"] for r in reconnected.get("/roll-requests").json()]
        key = f"request:{request['id']}:{request['request_id'][-80:]}"
        endpoint = f"/roll-requests/{request['id']}/complete"
        assert other.post(endpoint, json={"request_id": key}).status_code == 403
        mark("player_sent_at")
        # Disconnect immediately after sending: no response is read by the client.
        body = json.dumps({"request_id": key}).encode()
        headers = (f"POST {endpoint} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
                   f"X-Omnisvera-Token: {TOKENS['varkh']}\r\nContent-Type: application/json\r\n"
                   f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode()
        with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
            connection.sendall(headers + body)
            connection.shutdown(socket.SHUT_WR)
        deadline = time.monotonic() + 10
        record = None
        while time.monotonic() < deadline:
            with closing(sqlite3.connect(database)) as connection:
                connection.row_factory = sqlite3.Row
                record = connection.execute("SELECT * FROM dice_roll_requests WHERE id=?", (request["id"],)).fetchone()
            if record["status"] == "completed": break
            time.sleep(.1)
        assert record["status"] == "completed", "Disconnected request did not finish"
        marks["server_completed_at"] = record["completed_at"]
        response = player.post(endpoint, json={"request_id": key})
        response.raise_for_status()
        roll = response.json()
        assert roll["id"] == record["roll_event_id"]
        assert player.post(endpoint, json={"request_id": key}).json()["id"] == roll["id"]
        assert other.post(endpoint, json={"request_id": key}).status_code == 403
        assert player.post(endpoint, json={"request_id": prefix + "-other"}).status_code == 400
        assert request["id"] not in [r["id"] for r in player.get("/roll-requests").json()]
        assert roll["id"] in [r["id"] for r in gm.get("/rolls").json()]
        mark("gm_api_visible_at")
        assert roll["id"] not in [r["id"] for r in other.get("/rolls").json()]
        ledger = gm.get("/workspace/ledger").json()
        events = [e for e in ledger if e["source_type"] == "dice_roll" and e["source_id"] == str(roll["id"])]
        assert len(events) == 1
        assert events[0]["character_id"] == "varkh"
        assert events[0]["detail"]["total"] == roll["total"]
        with closing(sqlite3.connect(database)) as connection:
            assert connection.execute("SELECT COUNT(*) FROM dice_roll_events WHERE source='roll_request' AND source_id=?", (str(request["id"]),)).fetchone()[0] == 1
        print(json.dumps({"status": "PASS", "transport": "real HTTP + disconnected TCP response", "request_id": request["id"],
                          "roll_id": roll["id"], "ledger_events": len(events), "marks": marks}, indent=2))
    finally:
        for client in clients.values(): client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "serve", "probe"))
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, default=8871)
    args = parser.parse_args()
    database = checked_database(args.database)
    if args.action == "prepare":
        if database.exists(): raise ValueError("Refusing to overwrite an existing rehearsal")
        database.parent.mkdir(parents=True, exist_ok=True)
        source = BACKEND / "data" / "omnisvera_companion.sqlite3"
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original, closing(sqlite3.connect(database)) as copy:
            original.backup(copy)
        print(f"Isolated SQLite backup ready: {database}")
        return
    if not database.is_file(): raise ValueError("Run prepare first")
    if args.action == "probe":
        probe(database, args.port)
    else:
        configure(database)
        sys.path.insert(0, str(BACKEND))
        import uvicorn
        uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
