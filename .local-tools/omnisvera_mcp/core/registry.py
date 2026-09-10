from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from .context import CallContext
from .audit import AuditSink, NullAuditSink, arguments_fingerprint
from .policy import PolicyEngine


ToolHandler = Callable[[CallContext, Mapping[str, Any]], Any]

IDENTITY_ARGUMENTS = frozenset(
    {"actor", "client", "transport", "scopes", "request_id", "project_id", "task_id"}
)


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    name: str
    handler: ToolHandler
    action: str
    resource: str
    required_scopes: frozenset[str]
    description: str | None = None


class ToolRegistry:
    """Internal invocation path shared by present and future transports."""

    def __init__(self, policy: PolicyEngine | None = None, audit: AuditSink | None = None) -> None:
        self._policy = policy or PolicyEngine()
        self._audit = audit or NullAuditSink()
        self._tools: dict[str, RegisteredTool] = {}
        self.services: dict[str, Any] = {}

    def register(self, tool: RegisteredTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def invoke(
        self,
        tool_name: str,
        context: CallContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> Any:
        try:
            tool = self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

        safe_arguments = dict(arguments or {})
        forged_fields = IDENTITY_ARGUMENTS.intersection(safe_arguments)
        if forged_fields:
            fields = ", ".join(sorted(forged_fields))
            raise ValueError(f"Identity fields are transport-controlled: {fields}")

        started = perf_counter()
        result = "denied"
        try:
            self._policy.require(context, required_scopes=tool.required_scopes)
            result = "running"
            value = tool.handler(context, safe_arguments)
            result = "success"
            return value
        except Exception:
            if result == "running":
                result = "error"
            raise
        finally:
            self._audit.record({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor,
                "client": context.client,
                "transport": context.transport,
                "action": tool.action,
                "target": tool.resource,
                "result": result,
                "duration_ms": round((perf_counter() - started) * 1000, 3),
                "arguments_hash": arguments_fingerprint(safe_arguments),
                "request_id": context.request_id,
                "metadata": {"tool": tool.name},
            })

    def get(self, tool_name: str) -> RegisteredTool:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)
