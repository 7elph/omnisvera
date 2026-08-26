from __future__ import annotations

from dataclasses import dataclass

from .context import CallContext


class AuthorizationDenied(PermissionError):
    """Raised before a handler runs when its policy requirements are unmet."""


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    """Small deny-by-default policy hook for the trusted local foundation."""

    def decide(
        self,
        context: CallContext,
        *,
        required_scopes: frozenset[str],
    ) -> PolicyDecision:
        if not context.actor or not context.client or not context.transport:
            return PolicyDecision(False, "invocation identity is incomplete")
        if "*" in context.scopes:
            return PolicyDecision(True, "trusted wildcard scope")
        missing = required_scopes.difference(context.scopes)
        if missing:
            return PolicyDecision(
                False,
                f"missing required scopes: {', '.join(sorted(missing))}",
            )
        return PolicyDecision(True, "required scopes granted")

    def require(
        self,
        context: CallContext,
        *,
        required_scopes: frozenset[str],
    ) -> None:
        decision = self.decide(context, required_scopes=required_scopes)
        if not decision.allowed:
            raise AuthorizationDenied(decision.reason)
