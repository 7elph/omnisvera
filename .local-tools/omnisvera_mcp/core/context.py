from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class CallContext:
    """Trusted invocation identity injected by the active transport."""

    actor: str
    client: str
    transport: str
    scopes: frozenset[str]
    request_id: str
    project_id: str | None = None
    task_id: str | None = None

    @classmethod
    def trusted_local_stdio(cls, *, client: str = "codex") -> "CallContext":
        return cls(
            actor="sage",
            client=client,
            transport="stdio",
            scopes=frozenset({"*"}),
            request_id=uuid4().hex,
        )
