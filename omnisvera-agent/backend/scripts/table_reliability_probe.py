"""Full table reliability rehearsal over real HTTP against a temporary CF fixture.

The server must be started by ``cf01_probe.py serve`` with the same database.
This probe uses only the public loopback fixture tokens and refuses databases
outside the operating-system temporary directory.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from contextlib import closing

import httpx

from cf01_probe import TOKENS, checked_database


def require(response: httpx.Response) -> dict | list:
    response.raise_for_status()
    return response.json()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: table_reliability_probe.py <temporary-database> <port>")
    database = checked_database(sys.argv[1])
    if not database.is_file():
        raise SystemExit("temporary rehearsal database does not exist")
    port = int(sys.argv[2])
    base = f"http://127.0.0.1:{port}"
    run_id = "table-" + uuid.uuid4().hex
    clients = {
        role: httpx.Client(
            base_url=base,
            headers={"X-Omnisvera-Token": token},
            timeout=20,
            trust_env=False,
        )
        for role, token in TOKENS.items()
    }
    gm, vezemir, raziel = (clients[key] for key in ("gm", "vezemir", "raziel"))
    try:
        for role, client in (("gm", gm), ("vezemir", vezemir), ("raziel", raziel)):
            health = require(client.get("/health"))
            expected = "gm" if role == "gm" else "player"
            assert health["access_mode"] == expected

        workspace = require(gm.get("/workspace"))
        map_id = (workspace.get("map") or {}).get("id") or "default"
        require(gm.patch("/gm/workspace/table-mode", json={"table_mode": "physical"}))
        monster = require(gm.post("/gm/workspace/tokens", json={
            "token_type": "monster",
            "name": "Criatura do ensaio",
            "visible_to_players": True,
            "latitude": 50,
            "longitude": 50,
            "current_hp": 1,
            "maximum_hp": 1,
            "sheet": {"armor_class": 1, "treasure": "Q"},
            "map_id": map_id,
        }))

        combat = require(gm.get("/combat/effects"))
        if combat.get("encounter", {}).get("active"):
            combat = require(gm.post("/gm/combat/effects", json={
                "request_id": run_id + "-reset",
                "expected_version": combat["version"],
                "action": "end",
                "payload": {},
            }))
        combat = require(gm.post("/gm/combat/effects", json={
            "request_id": run_id + "-start",
            "expected_version": combat["version"],
            "action": "start",
            "payload": {
                "title": "Ensaio de confiabilidade",
                "map_id": map_id,
                "participants": [
                    {"target_type": "character", "target_id": "vezemir", "initiative": 12},
                    {"target_type": "character", "target_id": "raziel", "initiative": 10},
                    {"target_type": "token", "target_id": monster["id"], "initiative": 8},
                ],
            },
        }))
        assert combat["encounter"]["active"]
        assert [entry["initiative"] for entry in combat["encounter"]["participants"]] == [12, 10, 8]

        combat = require(gm.post("/gm/combat/effects", json={
            "request_id": run_id + "-effect",
            "expected_version": combat["version"],
            "action": "apply",
            "payload": {
                "target_type": "character",
                "target_id": "vezemir",
                "label": "Bênção do ensaio",
                "source": "Mestre",
                "duration": "rounds",
                "rounds": 2,
                "modifiers": {"attack_bonus": 1},
            },
        }))
        assert [effect["label"] for effect in require(vezemir.get("/combat/effects"))["effects"]] == ["Bênção do ensaio"]
        assert require(raziel.get("/combat/effects"))["effects"] == []

        character = require(vezemir.get("/characters/vezemir"))
        attacks = character["definition"].get("attacks") or []
        attack = next((entry for entry in attacks if entry.get("active", True) and (entry.get("damage_formula") or entry.get("damage"))), None)
        assert attack, "Vezemir has no usable attack in the rehearsal fixture"
        attack_count = max(1, int(attack.get("attack_count") or 1))
        attack_body = {
            "request_id": run_id + "-attack",
            "attack_id": attack["id"],
            "target_type": "token",
            "target_id": monster["id"],
            "roll_mode": "physical",
            "attack_count": attack_count,
            "d20s": [20] * attack_count,
        }
        assert raziel.post("/characters/vezemir/attacks/resolve", json={**attack_body, "request_id": run_id + "-forged"}).status_code == 403
        resolution = require(vezemir.post("/characters/vezemir/attacks/resolve", json=attack_body))
        before = next(token for token in require(vezemir.get("/workspace"))["tokens"] if token["id"] == monster["id"])
        assert before["current_hp"] == 1, "attack resolution changed HP before confirmation"
        confirmed = require(vezemir.post(f"/combat/attacks/{resolution['resolution_id']}/confirm"))
        repeated = require(vezemir.post(f"/combat/attacks/{resolution['resolution_id']}/confirm"))
        assert confirmed["hp_before"] == 1 and confirmed["hp_after"] == 0
        assert repeated["hp_after"] == 0

        loot = require(gm.post("/gm/workspace/loot/resolve", json={
            "request_id": run_id + "-loot",
            "token_id": monster["id"],
            "scope": "carried",
            "roll_mode": "digital",
        }))
        assert not any(entry["resolution_id"] == loot["resolution_id"] for entry in require(vezemir.get("/workspace/loot")))
        loot = require(gm.post(f"/gm/workspace/loot/{loot['resolution_id']}/reveal"))
        visible_loot = require(vezemir.get("/workspace/loot"))
        assert any(entry["resolution_id"] == loot["resolution_id"] for entry in visible_loot)
        reward = loot["rewards"][0]
        loot = require(gm.post(f"/gm/workspace/loot/{loot['resolution_id']}/distribute", json={
            "request_id": run_id + "-distribute",
            "allocations": [{"reward_id": reward["id"], "character_id": "vezemir", "quantity": reward["quantity"]}],
        }))
        require(gm.post(f"/gm/workspace/loot/{loot['resolution_id']}/distribute", json={
            "request_id": run_id + "-distribute",
            "allocations": [{"reward_id": reward["id"], "character_id": "vezemir", "quantity": reward["quantity"]}],
        }))
        inventory = require(vezemir.get("/characters/vezemir"))["inventory"]
        assert any(item["item_title"] == reward["name"] and item["quantity"] >= reward["quantity"] for item in inventory)

        combat = require(gm.get("/combat/effects"))
        combat = require(gm.post("/gm/combat/effects", json={
            "request_id": run_id + "-round",
            "expected_version": combat["version"],
            "action": "round",
            "payload": {},
        }))
        assert combat["round"] >= 2
        require(gm.post("/gm/combat/effects", json={
            "request_id": run_id + "-end",
            "expected_version": combat["version"],
            "action": "end",
            "payload": {},
        }))

        ledger = require(gm.get("/workspace/ledger"))
        source_counts = {
            "combat_action": len([entry for entry in ledger if entry["source_type"] == "combat_action" and entry["source_id"] == resolution["resolution_id"]]),
            "loot_reveal": len([entry for entry in ledger if entry["source_type"] == "loot_reveal" and entry["source_id"] == loot["resolution_id"]]),
            "loot_distribution": len([entry for entry in ledger if entry["source_type"] == "loot_distribution" and entry["source_id"] == loot["resolution_id"]]),
        }
        assert source_counts == {"combat_action": 1, "loot_reveal": 1, "loot_distribution": 1}
        with closing(sqlite3.connect(database)) as connection:
            combat_rows = connection.execute(
                "SELECT COUNT(*) FROM session_ledger WHERE source_type='combat_action' AND detail_json LIKE ?",
                (f"%{resolution['resolution_id']}%",),
            ).fetchone()[0]
        assert combat_rows == 1
        print(json.dumps({
            "status": "PASS",
            "transport": "real HTTP",
            "actors": ["master", "vezemir", "raziel"],
            "encounter": "started, advanced and ended",
            "effect_visibility": "owner only",
            "attack": {"strikes": attack_count, "hp": [1, 0], "confirmations": 2, "ledger_rows": combat_rows},
            "loot": {"revealed": True, "distributed": True, "reward": reward["name"], "quantity": reward["quantity"]},
            "ledger_matches": source_counts,
        }, ensure_ascii=False, indent=2))
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    main()
