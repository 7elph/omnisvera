"""Bounded real Ollama tool-use rehearsal; disposable CF server only, no browser claim."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import time
import uuid

import httpx
from cf01_probe import checked_database, TOKENS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    db = checked_database(args.database)
    output = checked_database(args.output)
    if not db.is_file():
        raise ValueError("Missing disposable database")
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as connection:
        if not connection.execute("SELECT name FROM sqlite_master WHERE name='dice_roll_requests'").fetchone():
            raise ValueError("Fixture not initialized")
    prefix = "cloud-qa-" + uuid.uuid4().hex
    report = {"run_id": prefix, "requested_model": "gpt-oss:120b-cloud", "transport": "HTTP tools, NOT browser/UI", "players": []}
    base = f"http://127.0.0.1:{args.port}"
    tools = [
        {"type": "function", "function": {"name": "pending_rolls", "description": "List my pending test requests", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
        {"type": "function", "function": {"name": "complete_roll", "description": "Complete my request; retrying the same ID must not roll again", "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "reconnect", "description": "Reconnect my player client, then inspect my pending requests", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    ]
    with httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS["gm"]}, timeout=20, trust_env=False) as gm, httpx.Client(timeout=60, trust_env=False) as ollama:
        gm.get("/health").raise_for_status()
        requests = {}
        for role in ("vezemir", "raziel", "morthak"):
            r = gm.post("/gm/roll-requests", json={"request_id": f"{prefix}-{role}", "character_id": role, "roll_type": "attribute", "source_id": "strength", "label": prefix, "visibility": "owner", "target_value": 10, "hide_target": True})
            r.raise_for_status()
            requests[role] = r.json()
        try:
            for role, request in requests.items():
                result = {"player": role, "events": [], "result": "INCONCLUSIVE"}
                report["players"].append(result)
                player = httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS[role]}, timeout=20, trust_env=False)
                allowed = request["id"]
                roll_ids = []
                reconnected = False
                messages = [{"role": "user", "content": "You are a player in a disposable RPG test. Discover your pending test, complete it, reconnect, retry that same completion to test idempotency, then check pending requests. Use the provided tools. Do not invent results. Finish with a concise report. Your identity is fixed by the server."}]
                try:
                    for step in range(8):
                        start = time.monotonic()
                        response = ollama.post("http://127.0.0.1:11434/api/chat", json={"model": report["requested_model"], "messages": messages, "tools": tools, "stream": False})
                        response.raise_for_status()
                        payload = response.json()
                        report["returned_model"] = payload.get("model")
                        message = payload["message"]
                        messages.append(message)
                        calls = message.get("tool_calls") or []
                        if not calls:
                            result["model_report"] = message.get("content", "")
                            break
                        for call in calls:
                            name = call["function"]["name"]
                            arguments = call["function"].get("arguments") or {}
                            if isinstance(arguments, str):
                                arguments = json.loads(arguments)
                            if name in ("pending_rolls", "reconnect") and not arguments:
                                if name == "reconnect":
                                    player.close()
                                    player = httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS[role]}, timeout=20, trust_env=False)
                                    reconnected = True
                                r = player.get("/roll-requests")
                                r.raise_for_status()
                                rows = r.json()
                                assert not any(row["id"] in [v["id"] for k, v in requests.items() if k != role] for row in rows), "Other player's request leaked"
                                own = [row for row in rows if row["id"] == allowed]
                                assert all(row.get("target_value") is None for row in own), "Hidden target leaked"
                                answer = [{"id": row["id"], "status": row["status"], "test": "Strength check"} for row in own]
                            elif name == "complete_roll" and set(arguments) == {"id"} and type(arguments["id"]) is int and arguments["id"] == allowed:
                                key = f"request:{allowed}:{request['request_id'][-80:]}"
                                r = player.post(f"/roll-requests/{allowed}/complete", json={"request_id": key})
                                r.raise_for_status()
                                record = r.json()
                                roll_ids.append(record["id"])
                                answer = {"roll_id": record["id"], "total": record["total"]}
                            else:
                                answer = {"error": "Not permitted by this player's bounded test tools"}
                            result["events"].append({"tool": name, "arguments": arguments, "result": answer, "elapsed_s": round(time.monotonic() - start, 3)})
                            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(answer)})
                    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as connection:
                        persisted = connection.execute("SELECT COUNT(*) FROM dice_roll_events WHERE source='roll_request' AND source_id=?", (str(allowed),)).fetchone()[0]
                    other = next(v["id"] for k, v in requests.items() if k != role)
                    forbidden = player.post(f"/roll-requests/{other}/complete", json={"request_id": prefix + "-forbidden"}).status_code
                    result["supervisor_checks"] = {"persisted_roll_count": persisted, "other_player_completion_status": forbidden, "reconnected": reconnected, "completion_attempts": len(roll_ids), "same_roll_on_retry": len(roll_ids) >= 2 and len(set(roll_ids)) == 1}
                    result["result"] = "PASS" if persisted == 1 and forbidden == 403 and reconnected and len(roll_ids) >= 2 and len(set(roll_ids)) == 1 else "INCONCLUSIVE"
                except Exception as error:
                    result["result"] = "FAIL"
                    result["error"] = f"{type(error).__name__}: {error}"
                finally:
                    player.close()
                    print(json.dumps({"player": role, "result": result["result"]}), flush=True)
        finally:
            report["result"] = "PASS" if len(report["players"]) == 3 and all(p["result"] == "PASS" for p in report["players"]) else "INCONCLUSIVE"
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Report: {output}", flush=True)


if __name__ == "__main__":
    main()
