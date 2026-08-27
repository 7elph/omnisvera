from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .context import CallContext
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


class ToolRegistry:
    """Internal invocation path shared by present and future transports."""

    def __init__(self, policy: PolicyEngine | None = None) -> None:
        self._policy = policy or PolicyEngine()
        self._tools: dict[str, RegisteredTool] = {}

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

        self._policy.require(context, required_scopes=tool.required_scopes)
        return tool.handler(context, safe_arguments)

    def get(self, tool_name: str) -> RegisteredTool:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)
