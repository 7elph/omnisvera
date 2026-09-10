from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.campaign_seed import seed_companion_contracts
from app.contract_play import list_contracts
from app.scene_play import create_session


class CampaignSeedTests(unittest.TestCase):
    def test_seed_is_idempotent_and_preserves_master_privacy(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "campaign-seed.sqlite3"
            session, _created = create_session(
                database,
                request_id="historical-session-004-v1",
                campaign_id="omnisvera",
                title="Os Avistamentos São Reais",
                session_number=4,
                private_notes=None,
                created_by="historical-import",
            )
            self.assertEqual({"created": 2, "unchanged": 0}, seed_companion_contracts(database))
            self.assertEqual({"created": 0, "unchanged": 2}, seed_companion_contracts(database))

            master = list_contracts(database, access_mode="gm")
            player = list_contracts(database, access_mode="player")
            self.assertEqual(2, len(master))
            self.assertEqual(2, len(player))
            dragon = next(item for item in master if "Dragões" in item["title"])
            medicine = next(item for item in player if "Remédios" in item["title"])
            self.assertEqual("completed", dragon["status"])
            self.assertEqual("published", medicine["status"])
            self.assertEqual(int(session["id"]), dragon["session_id"])
            self.assertNotIn("private_briefing", medicine)


if __name__ == "__main__":
    unittest.main()
