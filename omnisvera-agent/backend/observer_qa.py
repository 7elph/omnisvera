"""Synthetic visual QA only. Always creates its own temporary database."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
from contextlib import closing

from omnisvera_app import MemoryStore, create_app

QA_TOKEN = "synthetic-qa-only-not-an-operational-secret"


def seed(path):
    store = MemoryStore(path)
    now = datetime.now(timezone.utc)
    old = (now-timedelta(days=2)).isoformat()
    for i, status in enumerate(("fresh", "stale", "unknown", "error")):
        store.capture_signal(world_id="football", signal_id="football.match.home_score", entity_ref=f"match:qa-{i}",
            schema="football.v1", value=2 if i!=2 else None, value_type="number", unit="goals", observed_at=old if i else now.isoformat(),
            source={"provider":"Synthetic QA", "url":"https://example.invalid/scores?token=withheld", "authorization":"withheld"} if i!=2 else {},
            metadata={"freshness":status})
    first = store.experience_create(world_id="football", predictor_id="football.qa", predictor_version="fixture",
        predictor_type="test", learned_state_schema="qa.v1", learned_state={"rating":1500})
    snapshot = store.create_snapshot_memory(domain="world.football",subject="Synthetic QA",state={"rating":1500},
        sources=[{"source_type":"fixture", "source_ref":"qa:only", "source_timestamp":now.isoformat(), "relation":"supports"}])
    def prediction(exp, claim):
        return store.create_prediction(domain="world.football",world_id="football", snapshot_memory_id=snapshot,
            claim=claim,probability=.6,horizon=(now+timedelta(days=1)).isoformat(),resolution_rule={},
            predictor_id="football.qa",predictor_version="fixture",experience_id=exp["experience_id"],
            experience_state_version=exp["state_version"],experience_state_hash=exp["learned_state_hash"],
            signals_used=[{"signal_id":"football.match.home_score","entity_ref":"match:qa-0","observed_at":now.isoformat()}])
    resolved_id=prediction(first,"Exemplo sintético · mandante vence")
    resolved=store.resolve_prediction(resolved_id,outcome=1)
    second=store.experience_create(world_id="football",predictor_id="football.qa",predictor_version="fixture",
        predictor_type="test",learned_state_schema="qa.v1",learned_state={"rating":1502},
        source_prediction_ids=[resolved_id],source_outcome_ids=[resolved["resolution"]["id"]])
    open_id=prediction(second,"Exemplo sintético · próxima partida")
    for result in ("success","error"):
        store.record_audit({"timestamp":now.isoformat(),"actor":"qa","client":"qa","transport":"test",
            "action":"world.model","target":"qa","result":result,"duration_ms":42,
            "arguments_hash":"qa","request_id":"qa","metadata":{"secret":"withheld"}})
    return {"open":open_id,"resolved":resolved_id,"first":first,"second":second}


if __name__ == "__main__":
    import uvicorn
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=18911)
    parser.add_argument("--scenario",choices=["populated","empty","unavailable","monitor-error"],default="populated")
    args=parser.parse_args()
    with TemporaryDirectory(prefix="omnisvera-observer-qa-") as folder:
        path=Path(folder)/"qa.db"
        if args.scenario=="empty":
            MemoryStore(path)
        elif args.scenario!="unavailable":
            seed(path)
            if args.scenario=="monitor-error":
                with closing(MemoryStore(path)._connect()) as connection, connection:
                    connection.execute("DROP TABLE audit_events")
        app=create_app(path,QA_TOKEN,dist=Path(__file__).resolve().parents[1]/"frontend"/"dist-omnisvera",
            environment_label="QA SINTÉTICO — não são dados operacionais")
        uvicorn.run(app,host="127.0.0.1",port=args.port,access_log=False)
