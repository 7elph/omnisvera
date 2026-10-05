"""Three-player combat rehearsal. Requires cf01_probe serve and an OS-temp DB.

Uses existing copied character definitions, never grants weapons or abilities.
All mutations go to the isolated fixture with public rehearsal credentials.
"""
from __future__ import annotations

import json
import sys
import uuid

import httpx

from cf01_probe import TOKENS, checked_database


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: combat_party_probe.py <temporary-database> <port>")
    database = checked_database(sys.argv[1])
    if not database.is_file():
        raise SystemExit("prepare the disposable fixture first")
    base = f"http://127.0.0.1:{int(sys.argv[2])}"
    prefix = "party-" + uuid.uuid4().hex
    clients = {role: httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS[role]},
                                  timeout=30, trust_env=False)
               for role in ("gm", "vezemir", "raziel", "morthak")}
    def require(response):
        response.raise_for_status()
        return response.json()
    gm = clients["gm"]
    def state():
        return require(gm.get("/combat/effects"))
    def command(action, payload=None):
        return require(gm.post("/gm/combat/effects", json={
            "request_id": prefix + "-" + uuid.uuid4().hex,
            "expected_version": state()["version"], "action": action, "payload": payload or {}}))
    def hp(token_id):
        return next(t["current_hp"] for t in require(gm.get("/workspace"))["tokens"] if t["id"] == token_id)
    try:
        if state().get("encounter", {}).get("active"):
            command("end")
        require(gm.patch("/gm/workspace/table-mode", json={"table_mode": "physical"}))
        workspace = require(gm.get("/workspace"))
        monster = require(gm.post("/gm/workspace/tokens", json={
            "token_type": "monster", "name": "Alvo descartável do ensaio", "visible_to_players": True,
            "latitude": 50, "longitude": 50, "current_hp": 200, "maximum_hp": 200,
            "map_id": (workspace.get("map") or {}).get("id") or "default",
            "sheet": {"armor_class": 1, "attacks": [{"name": "Ferrão", "bonus": "+4", "damage": "1d8 + Veneno"}]}}))
        actors = ["vezemir", "raziel", "morthak"]
        command("start", {"title": "Ensaio dos três personagens", "participants": [
            {"target_type": "character", "target_id": actor, "name": actor, "initiative": 20-i}
            for i, actor in enumerate(actors)] + [
            {"target_type": "token", "target_id": monster["id"], "name": monster["name"], "initiative": 1}]})
        results = []
        for actor in actors:
            client = clients[actor]
            definition = require(client.get(f"/characters/{actor}"))["definition"]
            attack_id = "ranged" if actor == "raziel" else "melee"
            attack = next(a for a in definition["attacks"] if a["id"] == attack_id)
            assert attack.get("weapon_item_path") and attack.get("damage"), f"{actor}: weapon/damage unavailable"
            count = max(1, int(attack.get("attack_count") or 1))
            current = state()["encounter"]
            assert current["participants"][current["turn_index"]]["target_id"] == actor
            body = {"request_id": prefix + "-" + actor, "attack_id": attack_id,
                    "target_type": "token", "target_id": monster["id"], "roll_mode": "physical",
                    "attack_count": count, "d20s": [20] * count}
            before = hp(monster["id"])
            resolution = require(client.post(f"/characters/{actor}/attacks/resolve", json=body))
            assert hp(monster["id"]) == before, "preview must not change HP"
            assert require(client.post(f"/characters/{actor}/attacks/resolve", json=body))["resolution_id"] == resolution["resolution_id"]
            endpoint = f"/combat/attacks/{resolution['resolution_id']}/confirm"
            confirmed = require(client.post(endpoint))
            after = hp(monster["id"])
            assert after == max(0, before - resolution["damage_total"])
            assert after < before, f"{actor}: expected confirmed hit"
            # A newly connected client retries the same confirmation, not a new attack.
            with httpx.Client(base_url=base, headers={"X-Omnisvera-Token": TOKENS[actor]}, trust_env=False, timeout=30) as reconnected:
                assert require(reconnected.post(endpoint))["hp_after"] == confirmed["hp_after"]
                assert hp(monster["id"]) == after
                assert require(reconnected.get("/combat/effects"))["encounter"]["active"]
            events = require(gm.get("/workspace/ledger"))
            assert len([e for e in events if e["source_type"] == "combat_action"
                        and e["source_id"] == resolution["resolution_id"]]) == 1
            turn = {"request_id": prefix + "-turn-" + actor, "expected_version": state()["version"],
                    "action": "next_turn", "payload": {}}
            other = clients[actors[(actors.index(actor)+1) % len(actors)]]
            assert other.post("/combat/next-turn", json={**turn, "request_id": turn["request_id"] + "-forged"}).status_code == 403
            advanced = require(client.post("/combat/next-turn", json=turn))
            assert require(client.post("/combat/next-turn", json=turn)) == advanced
            results.append({"actor": actor, "attack": attack_id, "damage_formula": attack["damage"],
                            "hp_before": before, "hp_after": after, "reconnect_retry": "PASS"})
        current = state()["encounter"]
        assert current["participants"][current["turn_index"]]["target_id"] == monster["id"]
        # Monster uses its persisted attack, no formula or damage supplied by the client.
        require(gm.patch("/gm/workspace/table-mode", json={"table_mode": "digital"}))
        result = require(gm.post(f"/gm/combat/tokens/{monster['id']}/attacks/resolve", json={
            "request_id": prefix + "-monster", "attack_id": "0", "target_type": "character",
            "target_id": "vezemir", "roll_mode": "digital"}))
        confirmed = require(gm.post(f"/combat/attacks/{result['resolution_id']}/confirm"))
        assert require(gm.post(f"/combat/attacks/{result['resolution_id']}/confirm"))["hp_after"] == confirmed["hp_after"]
        advanced = command("next_turn")
        assert advanced["encounter"]["turn_index"] == 0
        assert not command("end")["encounter"]["active"]
        print(json.dumps({"status": "PASS", "transport": "loopback HTTP, not visual/multi-network",
                          "players": results, "gm_digital_attack": result["result"],
                          "gm_formula_input": False, "encounter_ended": True,
                          "limitations": ["manual spell effects not exercised", "no independent mobile clients"]}, ensure_ascii=False, indent=2))
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    main()
