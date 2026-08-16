from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.access import AccessContext
from app.character_play import init_character_play
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger, list_session_ledger, session_ledger_version
from app.session_workspace import init_session_workspace, record_workspace_message


class SessionLedgerTests(unittest.TestCase):
    def test_backfill_triggers_and_visibility_share_one_append_only_log(self) -> None:
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "ledger.sqlite3"
            init_character_play(database)
            init_dice_rolls(database)
            init_session_workspace(database)
            init_session_ledger(database)
            record_workspace_message(database, actor_id="master", actor_name="Mestre", actor_role="gm", character_id="sage", text="A sessão começou.")
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute(
                    """INSERT INTO character_events(character_id,actor_id,actor_role,event_type,field,before_json,after_json,reason,created_at)
                       VALUES('vezemir','master','gm','damage','current_hp','10','8','Recebeu dano','2026-08-16T00:00:00+00:00')"""
                )
                connection.execute(
                    """INSERT INTO character_events(character_id,actor_id,actor_role,event_type,field,before_json,after_json,reason,created_at)
                       VALUES('vezemir','master','gm','definition_update','private','null','1','Nota privada','2026-08-16T00:00:01+00:00')"""
                )
                connection.execute(
                    """INSERT INTO dice_roll_events(request_id,campaign_id,character_id,actor_id,actor_role,roll_type,label,formula,dice,modifier,individual_results_json,subtotal,total,target_hidden,visibility,source,created_at)
                       VALUES('roll-1','omnisvera','vezemir','vezemir','player','free','Ataque','1d20','1d20',0,'[17]',17,17,0,'table','free','2026-08-16T00:00:02+00:00')"""
                )
            gm_entries = list_session_ledger(database, AccessContext(mode="gm"))
            player_entries = list_session_ledger(database, AccessContext(mode="player", profile_id="vezemir"))
            self.assertEqual(4, len(gm_entries))
            self.assertEqual(3, len(player_entries))
            self.assertEqual({"message", "state", "roll"}, {item["event_kind"] for item in player_entries})
            self.assertEqual(4, session_ledger_version(database))


if __name__ == "__main__":
    unittest.main()
