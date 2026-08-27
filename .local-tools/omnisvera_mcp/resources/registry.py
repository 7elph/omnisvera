from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from ..core.audit import AuditSink, NullAuditSink, arguments_fingerprint
from ..core.context import CallContext
from ..core.policy import PolicyEngine


@dataclass(frozen=True, slots=True)
class RegisteredResource:
    uri: str
    handler: Callable[[CallContext], Any]
    required_scopes: frozenset[str]


class ResourceRegistry:
    def __init__(self, policy: PolicyEngine | None = None, audit: AuditSink | None = None) -> None:
        self.policy = policy or PolicyEngine()
        self.audit = audit or NullAuditSink()
        self.resources: dict[str, RegisteredResource] = {}

    def register(self, resource: RegisteredResource) -> None:
        if resource.uri in self.resources:
            raise ValueError(f"Resource already registered: {resource.uri}")
        self.resources[resource.uri] = resource

    def read(self, uri: str, context: CallContext) -> Any:
        resource = self.resources[uri]
        started = perf_counter()
        result = "denied"
        try:
            self.policy.require(context, required_scopes=resource.required_scopes)
            result = "running"
            value = resource.handler(context)
            result = "success"
            return value
        except Exception:
            if result == "running":
                result = "error"
            raise
        finally:
            self.audit.record({
                "timestamp": datetime.now(timezone.utc).isoformat(), "actor": context.actor,
                "client": context.client, "transport": context.transport, "action": "read",
                "target": uri, "result": result,
                "duration_ms": round((perf_counter() - started) * 1000, 3),
                "arguments_hash": arguments_fingerprint({}), "request_id": context.request_id,
                "metadata": {"resource": uri},
            })
