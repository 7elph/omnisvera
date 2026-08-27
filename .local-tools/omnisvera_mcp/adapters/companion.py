from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class CompanionObservation:
    source: str
    status: str
    freshness: str
    observed_at: str
    value: Any = None
    limitation: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "freshness": self.freshness,
            "observed_at": self.observed_at,
            "value": self.value,
            "limitation": self.limitation,
        }


class CompanionAdapter:
    """Authenticated, read-only HTTP boundary for the Companion."""

    def __init__(
        self,
        root: Path,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 1.5,
        opener=None,
    ) -> None:
        self.root = root.resolve()
        self.base_url = (base_url or os.getenv("OMNISVERA_COMPANION_URL") or "http://127.0.0.1:8787").rstrip("/")
        self._token = token
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen

    def _master_token(self) -> str | None:
        if self._token:
            return self._token
        environment = os.getenv("OMNISVERA_MASTER_TOKEN") or os.getenv("OMNISVERA_ACCESS_TOKEN")
        if environment:
            return environment
        path = self.root / "omnisvera-agent" / "backend" / "data" / "access_tokens.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            return payload.get("master_token") or payload.get("gm_token")
        except (OSError, json.JSONDecodeError, TypeError, AttributeError):
            return None

    def _get(self, path: str) -> CompanionObservation:
        observed_at = utc_now()
        token = self._master_token()
        if not token:
            return CompanionObservation(path, "unavailable", "unavailable", observed_at, limitation="master credential unavailable")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Accept": "application/json", "X-Omnisvera-Token": token},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return CompanionObservation(path, "healthy", "fresh", observed_at, payload)
        except urllib.error.HTTPError as error:
            return CompanionObservation(path, "degraded", "unavailable", observed_at, limitation=f"HTTP {error.code}")
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            return CompanionObservation(path, "offline", "unavailable", observed_at, limitation=type(error).__name__)

    def get_health(self) -> CompanionObservation:
        return self._get("/health")

    def get_app_state(self) -> CompanionObservation:
        return self._get("/workspace")

    def get_dashboard(self) -> CompanionObservation:
        observed_at = utc_now()
        sessions = self._get("/gm/sessions")
        scene = self._get("/scenes/active")
        if sessions.status != "healthy" or scene.status != "healthy":
            limitation = "; ".join(filter(None, [sessions.limitation, scene.limitation]))
            status = "offline" if "offline" in {sessions.status, scene.status} else "degraded"
            return CompanionObservation("companion.dashboard", status, "unavailable", observed_at, limitation=limitation)
        return CompanionObservation(
            "companion.dashboard", "healthy", "fresh", observed_at,
            {"sessions": sessions.value, "active_scene": scene.value},
        )
