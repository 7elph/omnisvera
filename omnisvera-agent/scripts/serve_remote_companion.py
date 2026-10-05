"""Start existing campaign on loopback with saved credentials; no token regeneration."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def main():
    tokens = json.loads((BACKEND / "data/access_tokens.json").read_text(encoding="utf-8-sig"))
    if not tokens.get("master_token"):
        raise RuntimeError("Existing Master credential required")
    profiles = {key: value for key, value in tokens["player_profiles"].items() if not value.get("gm_controlled")}
    os.environ.update({
        "OMNISVERA_VAULT_PATH": str(ROOT.parent),
        "OMNISVERA_DB_PATH": str(BACKEND / "data/omnisvera_companion.sqlite3"),
        "OMNISVERA_MASTER_TOKEN": tokens["master_token"],
        "OMNISVERA_ACCESS_TOKEN": tokens["master_token"],
        "OMNISVERA_PLAYER_TOKEN": tokens.get("player_token", ""),
        "OMNISVERA_PLAYER_PROFILES_JSON": json.dumps(profiles),
        "OMNISVERA_REBUILD_ON_STARTUP": "false",
        "OMNISVERA_TRAINING_CAPTURE_MODE": "off",
    })
    sys.path.insert(0, str(BACKEND))
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8788)


if __name__ == "__main__":
    main()
