"""Measure only the loopback rehearsal with fixed non-production credentials."""
from time import perf_counter
from uuid import uuid4
import json
import httpx

with httpx.Client(base_url="http://127.0.0.1:8873", trust_env=False, timeout=20) as client:
    gm = {"X-Omnisvera-Token": "cf01-local-gm"}
    player = {"X-Omnisvera-Token": "cf01-local-varkh"}
    timings = []
    def call(label, method, path, headers, **kwargs):
        start = perf_counter()
        response = client.request(method, path, headers=headers, **kwargs)
        response.raise_for_status()
        timings.append({"operation": label, "ms": round((perf_counter() - start) * 1000, 1)})
        return response.json()
    for _ in range(5):
        key = "latency-" + uuid4().hex
        call("free_roll", "POST", "/rolls", player,
             json={"request_id": key, "formula": "1d20", "visibility": "private"})
        request = call("request_create", "POST", "/gm/roll-requests", gm,
             json={"request_id": key + "-request", "character_id": "varkh", "roll_type": "attribute",
                   "source_id": "charisma", "visibility": "owner"})
        call("player_pending", "GET", "/roll-requests", player)
        call("complete", "POST", f"/roll-requests/{request['id']}/complete", player,
             json={"request_id": key + "-complete"})
        call("gm_history", "GET", "/rolls", gm)
    print(json.dumps(timings, indent=2))
