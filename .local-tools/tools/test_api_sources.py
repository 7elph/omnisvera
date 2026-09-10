"""Quick probe of available free football APIs."""
import requests
import json

def test_thesportsdb():
    """TheSportsDB free API - no key needed."""
    print("=== TheSportsDB ===")
    try:
        # Next events for Arsenal (id=133604)
        r = requests.get("https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=133604", timeout=10)
        data = r.json()
        events = data.get("events", []) or []
        print(f"  Status: {r.status_code}")
        print(f"  Upcoming Arsenal events: {len(events)}")
        if events:
            e = events[0]
            print(f"  First: {e.get('strEvent')} on {e.get('dateEvent')}")
            print(f"  League: {e.get('strLeague')}")
            print(f"  Venue: {e.get('strVenue')}")
            print(f"  Fields: {list(e.keys())[:15]}")
        return True
    except Exception as ex:
        print(f"  Error: {ex}")
        return False

def test_football_data_org():
    """football-data.org free tier - no API key for basic access."""
    print("\n=== football-data.org ===")
    try:
        # Free tier: Premier League (PL), no auth needed for some endpoints
        r = requests.get(
            "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED",
            headers={"X-Auth-Token": ""},
            timeout=10,
        )
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            matches = data.get("matches", [])
            print(f"  Scheduled PL matches: {len(matches)}")
            if matches:
                m = matches[0]
                print(f"  First: {m.get('homeTeam',{}).get('name')} vs {m.get('awayTeam',{}).get('name')}")
        elif r.status_code == 401:
            print("  Needs API key (free tier available)")
        return True
    except Exception as ex:
        print(f"  Error: {ex}")
        return False

if __name__ == "__main__":
    test_thesportsdb()
    test_football_data_org()
