"""Probe TheSportsDB league-level endpoints."""
import requests

def probe_league_next(league_id, league_name):
    """Get next events for a league."""
    r = requests.get(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={league_id}", timeout=10)
    data = r.json()
    events = data.get("events", []) or []
    print(f"\n--- {league_name} (id={league_id}) - {len(events)} upcoming ---")
    for e in events[:5]:
        print(f"  {e.get('strEvent')} | {e.get('dateEvent')} | Status: {e.get('strStatus')}")
    return events

# Premier League: 4328
# La Liga: 4335
# Bundesliga: 4331
# Serie A: 4332
# Ligue 1: 4334
# Champions League: 4480

if __name__ == "__main__":
    probe_league_next(4328, "Premier League")
    probe_league_next(4335, "La Liga")
