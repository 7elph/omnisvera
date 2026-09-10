"""Probe TheSportsDB endpoints for football data provider."""
import requests
import json

def probe_next_events(team_id, team_name):
    """Get upcoming events for a team."""
    r = requests.get(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={team_id}", timeout=10)
    data = r.json()
    events = data.get("events", []) or []
    print(f"\n--- {team_name} (id={team_id}) - {len(events)} upcoming ---")
    for e in events[:3]:
        print(f"  {e.get('strEvent')} | {e.get('dateEvent')} | {e.get('strLeague')}")
        print(f"    Venue: {e.get('strVenue')}")
        print(f"    Status: {e.get('intHomeScore')} home / {e.get('intAwayScore')} away")
    return events

def probe_last_events(team_id, team_name):
    """Get last events for a team."""
    r = requests.get(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={team_id}", timeout=10)
    data = r.json()
    events = data.get("results", []) or data.get("events", []) or []
    print(f"\n--- {team_name} (id={team_id}) - {len(events)} recent ---")
    for e in events[:3]:
        score = f"{e.get('intHomeScore', '?')}-{e.get('intAwayScore', '?')}"
        print(f"  {e.get('strEvent')} | {e.get('dateEvent')} | Score: {score}")
        print(f"    Venue: {e.get('strVenue')}")
    return events

def probe_event_detail(event_id):
    """Get single event detail."""
    r = requests.get(f"https://www.thesportsdb.com/api/v1/json/3/lookupevent.php?id={event_id}", timeout=10)
    data = r.json()
    event = data.get("events", [{}])[0] if data.get("events") else {}
    print(f"\n--- Event {event_id} ---")
    if event:
        print(f"  {event.get('strEvent')}")
        print(f"  Status: {event.get('strStatus')}")
        print(f"  Home: {event.get('strHomeTeam')} | Away: {event.get('strAwayTeam')}")
        print(f"  Score: {event.get('intHomeScore')} - {event.get('intAwayScore')}")
        print(f"  League: {event.get('strLeague')}")
        print(f"  Venue: {event.get('strVenue')}")
        print(f"  Round: {event.get('intRound')}")
        print(f"  Timestamp: {event.get('strTimestamp')}")
        print(f"  Thumb: {event.get('strThumb')}")
    return event

# Premier League teams
TEAMS = {
    "133604": "Arsenal",
    "133616": "Manchester United",
    "133610": "Liverpool",
    "133612": "Manchester City",
    "133608": "Chelsea",
}

if __name__ == "__main__":
    # Check upcoming for a couple teams
    for tid, tname in list(TEAMS.items())[:2]:
        probe_next_events(tid, tname)
    
    # Check recent for one team
    probe_last_events("133604", "Arsenal")
    
    # Check if we can get event detail
    events = probe_next_events("133604", "Arsenal")
    if events:
        probe_event_detail(events[0].get("idEvent"))
