"""Loopback-only CF-01 rehearsal with explicit delay and sanitized timing logs.

Uses the existing temporary-copy fixture. Never imports operational credentials.
Example: python scripts/cf01_network_rehearsal.py --database <temp>/cf01.sqlite3 --port 8872 --delay-ms 3500
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone

from cf01_probe import BACKEND, checked_database, configure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, default=8872)
    parser.add_argument("--delay-ms", type=int, default=3500)
    args = parser.parse_args()
    database = checked_database(args.database)
    if not database.is_file() or not 0 <= args.delay_ms <= 10000:
        parser.error("Use an existing temporary fixture and delay from 0 to 10000 ms")
    configure(database)
    sys.path.insert(0, str(BACKEND))
    from app.main import app
    import uvicorn

    @app.middleware("http")
    async def rehearsal_latency(request, call_next):
        path = request.url.path
        if not (path == "/rolls" or path.startswith("/roll-requests")):
            return await call_next(request)
        received = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()
        await asyncio.sleep(args.delay_ms / 1000)
        response = await call_next(request)
        print(json.dumps({"received_at": received, "method": request.method,
                          "endpoint": path, "delay_ms": args.delay_ms,
                          "response_at": datetime.now(timezone.utc).isoformat(),
                          "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                          "status": response.status_code}), flush=True)
        return response

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
