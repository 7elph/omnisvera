"""Explicit GM launch; no action without --start. Never creates another session."""
import argparse
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true", help="Activate the prepared Session 5 and open its first scene")
    args = parser.parse_args()
    credentials = json.loads((ROOT / "backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    with httpx.Client(base_url="http://127.0.0.1:8788", headers={"X-Omnisvera-Token": credentials["master_token"]}, timeout=90, trust_env=False) as client:
        response = client.get("/gm/sessions")
        response.raise_for_status()
        sessions = response.json()
        matches = [s for s in sessions if s.get("request_id") == "sage-session05-20260925-session"]
        if len(matches) != 1:
            raise RuntimeError("Prepared Session 5 not uniquely found")
        session = matches[0]
        if any(s["status"] == "active" and s["id"] != session["id"] for s in sessions):
            raise RuntimeError("Another session is active; finish/pause it explicitly first")
        if session["status"] not in {"planned", "active"}:
            raise RuntimeError("Session already paused/completed; refusing automatic restart")
        scene = client.get("/scenes/5")
        scene.raise_for_status()
        first = scene.json()
        assert first["session_id"] == session["id"] and first["title"] == "O recuo"
        assert first.get("map_id") and all(first["checklist"].values())
        if not args.start:
            print("READY_TO_START=YES; no state changed. Use --start only when the table is ready.")
            return
        if session["status"] == "planned":
            response = client.post(f"/gm/sessions/{session['id']}/status", json={"status": "active"})
            response.raise_for_status()
        response = client.post("/gm/scenes/5/open-on-table", json={"request_id": "sage-session05-20260925-live-opening"})
        response.raise_for_status()
        print("SESSION_05_STARTED; opening published; no rewards granted. Refresh the Companion.")


if __name__ == "__main__":
    main()
