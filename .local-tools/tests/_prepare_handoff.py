import sys, hashlib, csv, json
from pathlib import Path
from datetime import datetime

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))
if str(LOCAL_TOOLS.parent) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS.parent))

from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.experience.updater import ExperienceUpdaterRegistry
from omnisvera_mcp.experience.football_elo import FootballEloUpdater

main_db = Path(r"C:\Users\delib\Desktop\OMNISVERA\.assistant-runtime\omnisvera-mcp\memory.db")
mem = MemoryStore(main_db)
latest = mem.experience_latest('football','football.elo','v1')
print(f"existing latest: {latest['state_version'] if latest else None} hash {latest['learned_state_hash'][:8] if latest else 'none'} obs {latest['observations_used'] if latest else 'none'}")

if latest is None or latest['observations_used'] < 1000:
    print("Creating real Experience from EPL train (3040 matches) for handoff...")
    # Load dataset
    data_root = Path(r"C:\Users\delib\Desktop\OMNISVERA\.local-tools\tools\pl_data")
    rows=[]
    for fname in [f"EPL_{y}.csv" for y in ["1415","1516","1617","1718","1819","1920","2021","2122","2223","2324"]]:
        with open(data_root/fname, newline="", encoding="utf-8") as csvfile:
            import csv
            reader=csv.DictReader(csvfile)
            for r in reader:
                dt_str=(r["Date"] or "").strip()
                if not dt_str: continue
                try: dt=datetime.strptime(dt_str, "%d/%m/%y")
                except: dt=datetime.strptime(dt_str, "%d/%m/%Y")
                outcome=1 if r["FTR"]=="H" else 0
                rows.append({"date":dt.strftime("%Y-%m-%d"), "home":r["HomeTeam"],"away":r["AwayTeam"],"outcome":outcome})
    # dedup and sort
    seen=set(); dedup=[]
    for r in rows:
        k=(r["date"],r["home"],r["away"])
        if k not in seen:
            seen.add(k)
            dedup.append(r)
    dedup.sort(key=lambda x: x["date"])
    train=[r for r in dedup if r["date"] < "2022-07-01"]
    print(f"train {len(train)} from {train[0]['date']} to {train[-1]['date']}")
    all_teams=sorted(set(r["home"] for r in dedup) | set(r["away"] for r in dedup))
    def _expected(h,a,adv=50): return 1.0/(1.0+10**(-((h+adv)-a)/400.0))
    ratings={t:1500 for t in all_teams}
    for m in train:
        exp_p=_expected(ratings[m["home"]], ratings[m["away"]])
        delta=20*(m["outcome"]-exp_p)
        ratings[m["home"]]=round(ratings[m["home"]]+delta,4)
        ratings[m["away"]]=round(ratings[m["away"]]-delta,4)
    init_state={"team_ratings": ratings, "home_advantage":50, "k_factor":20}
    # Create or update experience
    # If no latest, create v1; if exists but small, create new version?
    if latest is None:
        exp = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state=init_state, observations_used=len(train))
        print(f"Created v1 {exp['experience_id'][:8]} hash {exp['learned_state_hash'][:8]} obs {exp['observations_used']}")
    else:
        # Create new version from existing, to simulate continued training? For handoff, we want a real state, we can just create a new version with updated ratings
        # Use experience_create to create next version
        exp = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state=init_state, observations_used=len(train))
        print(f"Created new version v{exp['state_version']} {exp['experience_id'][:8]} hash {exp['learned_state_hash'][:8]}")

latest2 = mem.experience_latest('football','football.elo','v1')
print(f"FINAL latest: v{latest2['state_version']} {latest2['experience_id']} hash {latest2['learned_state_hash']} obs {latest2['observations_used']} perf {latest2['performance']}")
print(f"Source Experience for handoff: experience_id={latest2['experience_id']} state_version={latest2['state_version']} hash={latest2['learned_state_hash']}")

# Also ensure world and manifest are correct
from omnisvera_mcp.world import WorldRegistry
from omnisvera_mcp.adapters.football import FootballWorldAdapter, HttpFootballDataProvider
worlds=WorldRegistry()
try:
    worlds.register(FootballWorldAdapter(provider=HttpFootballDataProvider(team_ids=["133604"])))
    print("world football registered")
except Exception as e:
    print(f"world reg failed {e}")
