"""Explicit operator conversion: retain credentials in backup, disable player login."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def main():
    backup = ROOT / ".autonomy/runtime" / ("before-npc-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.mkdir(parents=True, exist_ok=False)
    source = ROOT / "backend/data/access_tokens.json"
    tokens = json.loads(source.read_text(encoding="utf-8-sig"))
    profile = tokens["player_profiles"]["varkh"]
    if not profile.get("character_path"):
        raise ValueError("Varkh source missing; refusing conversion")
    shutil.copy2(source, backup / "access_tokens.json")
    db = ROOT / "backend/data/omnisvera_companion.sqlite3"
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as original, closing(sqlite3.connect(backup / db.name)) as copy:
        original.backup(copy)
    profile["gm_controlled"] = True
    source.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recovery backup: {backup}")
    print("Varkh player credential retained but disabled in launchers; sheet/inventory/history untouched.")


if __name__ == "__main__":
    main()
