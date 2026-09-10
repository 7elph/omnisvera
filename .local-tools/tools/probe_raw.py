"""Probe TheSportsDB - check raw responses."""
import requests

def probe(url, label):
    try:
        r = requests.get(url, timeout=10)
        print(f"\n--- {label} ---")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"  Body (first 300): {r.text[:300]}")
    except Exception as e:
        print(f"\n--- {label} ---")
        print(f"  Error: {e}")

if __name__ == "__main__":
    # League next events
    probe("https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=4328", "PL league next")
    # Team next events  
    probe("https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=133604", "Arsenal next")
    # All teams in league
    probe("https://www.thesportsdb.com/api/v1/json/3/lookup_all_teams.php?id=4328", "PL all teams")
    # Event by ID
    probe("https://www.thesportsdb.com/api/v1/json/3/lookupevent.php?id=2494017", "Event detail")
