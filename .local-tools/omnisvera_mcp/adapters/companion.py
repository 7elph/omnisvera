from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..world import WorldDescriptor, WorldObservation, WorldSignal, utc_now


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
    """Authenticated, read-only HTTP boundary for the Companion.

    Satisfies WorldAdapter protocol — Companion is one world among many.
    """

    WORLD_ID = "companion"
    WORLD_TYPE = "simulation.rpg"
    ADAPTER_ID = "companion.http.v1"

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

    # -- WorldAdapter protocol ------------------------------------------------

    def describe(self) -> WorldDescriptor:
        return WorldDescriptor(
            world_id=self.WORLD_ID,
            world_type=self.WORLD_TYPE,
            name="Omnisvera Companion",
            adapter_id=self.ADAPTER_ID,
            capabilities=["observe", "history", "model"],
            schemas=["companion.session.v1"],
            metadata={"base_url": self.base_url},
        )

    def health(self) -> dict[str, Any]:
        obs = self.get_health()
        return {
            "status": obs.status,
            "freshness": obs.freshness,
            "observed_at": obs.observed_at,
            "limitation": obs.limitation,
        }

    def observe(self, query: dict[str, Any] | None = None) -> WorldObservation:
        from ..companion_session import build_companion_session_model
        model = build_companion_session_model(self)
        return WorldObservation(
            world_id=self.WORLD_ID,
            observed_at=model.observed_at,
            schema=model.schema,
            state=model.as_dict(),
            sources=[{"source_type": "world_observation", "source_ref": "companion:companion.session.v1"}],
            provenance={"adapter": self.ADAPTER_ID, "base_url": self.base_url},
        )

    def signals(self, observation: WorldObservation | None = None) -> list[WorldSignal]:
        """Extract universal signals from Companion state.

        If no observation is provided, observes first.
        Signals are derived deterministically from the observation state.
        """
        if observation is None:
            observation = self.observe()

        state = observation.state
        signals: list[WorldSignal] = []
        observed_at = observation.observed_at

        # companion.session.status — string
        session_status = state.get("session_status")
        if session_status is not None:
            signals.append(WorldSignal(
                signal_id="companion.session.status",
                world_id=self.WORLD_ID,
                schema=observation.schema,
                name="session_status",
                value=session_status,
                value_type="string",
                observed_at=observed_at,
                source={"observation_world_id": observation.world_id, "derivation": "direct"},
                metadata={"field": "session_status"},
            ))

        # companion.session.participant_count — number
        participants = state.get("participants", [])
        if isinstance(participants, list):
            signals.append(WorldSignal(
                signal_id="companion.session.participant_count",
                world_id=self.WORLD_ID,
                schema=observation.schema,
                name="participant_count",
                value=len(participants),
                value_type="number",
                observed_at=observed_at,
                unit="count",
                source={"observation_world_id": observation.world_id, "derivation": "deterministic"},
                metadata={"field": "participants", "derivation": "len(participants)"},
            ))

        # companion.session.active_thread_count — number
        threads = state.get("active_threads", [])
        if isinstance(threads, list):
            signals.append(WorldSignal(
                signal_id="companion.session.active_thread_count",
                world_id=self.WORLD_ID,
                schema=observation.schema,
                name="active_thread_count",
                value=len(threads),
                value_type="number",
                observed_at=observed_at,
                unit="count",
                source={"observation_world_id": observation.world_id, "derivation": "deterministic"},
                metadata={"field": "active_threads", "derivation": "len(active_threads)"},
            ))

        # companion.operational.status — string
        operational = state.get("operational", {})
        if isinstance(operational, dict):
            dashboard_status = operational.get("companion_dashboard_status")
            if dashboard_status is not None:
                signals.append(WorldSignal(
                    signal_id="companion.operational.status",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="operational_status",
                    value=dashboard_status,
                    value_type="string",
                    observed_at=observed_at,
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "operational.companion_dashboard_status"},
                ))

            # companion.operational.ollama_accessible — boolean
            ollama = operational.get("ollama_accessible")
            if ollama is not None:
                signals.append(WorldSignal(
                    signal_id="companion.operational.ollama_accessible",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="ollama_accessible",
                    value=bool(ollama),
                    value_type="boolean",
                    observed_at=observed_at,
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "operational.ollama_accessible"},
                ))

        return signals

    # -- Original API (preserved) --------------------------------------------

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

    def _get(self, path: str, *, timeout: float | None = None) -> CompanionObservation:
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
            with self._opener(request, timeout=self.timeout if timeout is None else timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return CompanionObservation(path, "healthy", "fresh", observed_at, payload)
        except urllib.error.HTTPError as error:
            return CompanionObservation(path, "degraded", "unavailable", observed_at, limitation=f"HTTP {error.code}")
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            return CompanionObservation(path, "offline", "unavailable", observed_at, limitation=type(error).__name__)

    def get_health(self) -> CompanionObservation:
        # /health awaits the optional Ollama probe for up to 1.5 s before
        # returning backend=ok. An equal client deadline mislabels it offline.
        # Leave all state reads on their existing short deadline; do not retry.
        return self._get("/health", timeout=max(self.timeout, 3.0))

    def get_app_state(self) -> CompanionObservation:
        return self._get("/workspace")

    def list_sessions(self) -> CompanionObservation:
        """Fetch all game sessions from the Companion."""
        return self._get("/gm/sessions")

    def get_session(self, session_id: int) -> CompanionObservation:
        """Fetch a single game session by ID."""
        return self._get(f"/gm/sessions/{session_id}")

    def list_scenes(self, campaign_id: str) -> CompanionObservation:
        """Fetch all scenes for a campaign."""
        return self._get(f"/campaigns/{campaign_id}/scenes")

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
