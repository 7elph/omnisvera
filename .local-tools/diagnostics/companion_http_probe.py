"""Read-only phase timings; never print credentials, response bodies or headers."""
from __future__ import annotations

import http.client
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from omnisvera_mcp.adapters.companion import CompanionAdapter


def run():
    adapter = CompanionAdapter(Path(__file__).resolve().parents[2])
    target = urlsplit(adapter.base_url)
    token = adapter._master_token()
    if not token:
        raise RuntimeError("Companion credential unavailable")
    observations = []
    for path in ("/health", "/workspace", "/gm/sessions", "/scenes/active"):
        for timeout in (adapter.timeout, 5.0):
            start = time.perf_counter()
            row = {"started_at": datetime.now(timezone.utc).isoformat(),
                   "endpoint": path, "host": target.hostname, "port": target.port,
                   "timeout_s": timeout, "retry": False, "connect_ms": None,
                   "headers_ms": None, "first_body_byte_ms": None}
            cls = http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection
            connection = cls(target.hostname, target.port, timeout=timeout)
            phase = "connect"
            try:
                connection.connect()
                row["connect_ms"] = round((time.perf_counter() - start) * 1000, 2)
                phase = "response_headers"
                connection.request("GET", target.path.rstrip("/") + path,
                                   headers={"Accept": "application/json", "X-Omnisvera-Token": token})
                response = connection.getresponse()
                row["headers_ms"] = round((time.perf_counter() - start) * 1000, 2)
                row["status"] = response.status
                phase = "response_body"
                first = response.read(1)
                row["first_body_byte_ms"] = round((time.perf_counter() - start) * 1000, 2)
                row["bytes"] = len(first) + len(response.read())
            except (OSError, TimeoutError, http.client.HTTPException) as error:
                row.update(error=type(error).__name__, failed_phase=phase)
            finally:
                connection.close()
                row["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
                observations.append(row)
    print(json.dumps(observations, indent=2))


if __name__ == "__main__":
    run()
