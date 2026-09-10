"""Smoke test: Football Real Data Provider against TheSportsDB live API."""
import sys
import time
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

# Load football adapter
import types as _mt
_world_mod = _mt.ModuleType("world")
_world_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "world.py")
sys.modules["world"] = _world_mod
_world_src = (LOCAL_TOOLS / "omnisvera_mcp" / "world.py").read_text(encoding="utf-8")
exec(compile(_world_src, _world_mod.__file__, "exec"), _world_mod.__dict__)

_football_mod = _mt.ModuleType("omnisvera_mcp.adapters.football")
_football_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "adapters" / "football.py")
_football_mod.__package__ = "omnisvera_mcp.adapters"
sys.modules["omnisvera_mcp.adapters.football"] = _football_mod
sys.modules["football"] = _football_mod
_football_src = (LOCAL_TOOLS / "omnisvera_mcp" / "adapters" / "football.py").read_text(encoding="utf-8")
_football_src = _football_src.replace("from ..world import", "from world import")
exec(compile(_football_src, _football_mod.__file__, "exec"), _football_mod.__dict__)

HttpFootballDataProvider = _football_mod.HttpFootballDataProvider
FootballWorldAdapter = _football_mod.FootballWorldAdapter


def main():
    print("=" * 60)
    print("SMOKE TEST: Football Real Data Provider")
    print("=" * 60)

    # Premier League team IDs (TheSportsDB)
    PL_TEAMS = {
        "133604": "Arsenal",
        "133616": "Manchester United",
        "133610": "Liverpool",
        "133612": "Manchester City",
        "133608": "Chelsea",
    }

    print(f"\nProvider: HttpFootballDataProvider")
    print(f"Source: TheSportsDB (free API, no key)")
    print(f"Teams: {len(PL_TEAMS)} Premier League clubs")

    provider = HttpFootballDataProvider(team_ids=list(PL_TEAMS.keys()))
    adapter = FootballWorldAdapter(provider=provider)

    # 1. Describe
    print(f"\n--- world.describe('football') ---")
    desc = adapter.describe()
    print(f"  world_id: {desc.world_id}")
    print(f"  world_type: {desc.world_type}")
    print(f"  adapter_id: {desc.adapter_id}")
    print(f"  capabilities: {desc.capabilities}")
    print(f"  schemas: {desc.schemas}")
    print(f"  provider: {desc.metadata.get('provider')}")
    print(f"  provider_state: {desc.metadata.get('provider_state')}")

    # 2. Health
    print(f"\n--- health ---")
    health = adapter.health()
    for k, v in health.items():
        print(f"  {k}: {v}")

    # 3. Observe
    print(f"\n--- world.observe('football') ---")
    start = time.time()
    obs = adapter.observe()
    elapsed = time.time() - start

    print(f"  observed_at: {obs.observed_at}")
    print(f"  schema: {obs.schema}")
    print(f"  world_id: {obs.world_id}")
    print(f"  matches: {len(obs.state.get('matches', []))}")
    print(f"  provider_state: {obs.provenance.get('provider_state')}")
    print(f"  freshness_seconds: {obs.provenance.get('freshness_seconds')}")
    print(f"  fetch_time: {elapsed:.2f}s")

    # 4. Show matches
    matches = obs.state.get("matches", [])
    if matches:
        print(f"\n--- matches (first 5) ---")
        for m in matches[:5]:
            status_icon = {"scheduled": "[ ]", "completed": "[x]", "live": "[*]"}.get(m["status"], "[?]")
            score = ""
            if m["status"] == "completed":
                score = f" {m.get('home_score', '?')}-{m.get('away_score', '?')}"
            print(f"  {status_icon} {m['home']['name']} vs {m['away']['name']}{score}")
            print(f"       {m['competition']} | {m['match_date'][:10]} | {m.get('venue', 'N/A')}")
    else:
        print("\n  No matches found.")

    # 5. Provider status after fetch
    print(f"\n--- provider status after fetch ---")
    final_status = provider.status
    print(f"  state: {final_status.state}")
    print(f"  message: {final_status.message}")
    print(f"  last_success: {final_status.last_success}")
    print(f"  consecutive_failures: {final_status.consecutive_failures}")

    print(f"\n{'=' * 60}")
    print("SMOKE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
