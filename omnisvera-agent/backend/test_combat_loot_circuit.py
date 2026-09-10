from unittest import TestCase
import test_combat as combat_fixture
from app.access import AccessContext
from app.combat import confirm_attack_resolution
from app.loot import init_loot, resolve_token_loot, reveal_loot, distribute_loot, list_loot
from app.player_inventory import init_player_inventory, list_inventory
from app.session_workspace import save_workspace_token, list_workspace_tokens
from app.session_ledger import list_session_ledger


class CombatLootCircuitTests(TestCase):
    def test_attack_death_loot_reveal_distribution_and_retries(self):
        fixture = combat_fixture.CombatAttackResolutionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        db = fixture.database
        init_player_inventory(db)
        init_loot(db)
        token = save_workspace_token(db, token_type="monster", name="Orc", latitude=50, longitude=50,
            current_hp=8, maximum_hp=8, sheet={"armor_class": 14, "treasure": "Q"})
        resolution = fixture._resolve(
            target={"type": "token", "id": token["id"], "name": "Orc", "armor_class": 14, "current_hp": 8},
            request_id="circuit-attack-01", rng=combat_fixture.SequenceRng(6))
        self.assertEqual(8, list_workspace_tokens(db)[0]["current_hp"])
        confirmed, applied = confirm_attack_resolution(db, resolution_id=resolution["resolution_id"],
            requested_by_id="vezemir", requested_by_role="player")
        self.assertTrue(applied)
        self.assertEqual((8, 0), (confirmed["hp_before"], confirmed["hp_after"]))
        self.assertFalse(confirm_attack_resolution(db, resolution_id=resolution["resolution_id"],
            requested_by_id="vezemir", requested_by_role="player")[1])
        loot, created = resolve_token_loot(db, request_id="circuit-loot", token_id=token["id"],
            scope="carried", roll_mode="digital", rng=combat_fixture.SequenceRng(1, 1, 1))
        self.assertTrue(created)
        self.assertEqual([], list_loot(db, AccessContext(mode="player", profile_id="vezemir")))
        reveal_loot(db, loot["resolution_id"])
        self.assertFalse(reveal_loot(db, loot["resolution_id"])[1])
        allocation = [{"reward_id": loot["rewards"][0]["id"], "character_id": "vezemir", "quantity": 3}]
        self.assertTrue(distribute_loot(db, resolution_id=loot["resolution_id"],
            request_id="circuit-distribute", allocations=allocation)[1])
        self.assertFalse(distribute_loot(db, resolution_id=loot["resolution_id"],
            request_id="circuit-distribute", allocations=allocation)[1])
        self.assertEqual(3, list_inventory(db, "vezemir")[0]["quantity"])
        ledger = list_session_ledger(db, AccessContext(mode="gm"))
        for source in ("combat_action", "loot_reveal", "loot_distribution"):
            self.assertEqual(1, len([event for event in ledger if event["source_type"] == source]))
