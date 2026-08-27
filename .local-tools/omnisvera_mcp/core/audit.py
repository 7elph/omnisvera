from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Protocol


class AuditSink(Protocol):
    def record(self, event: dict[str, Any]) -> None: ...


class NullAuditSink:
    def record(self, event: dict[str, Any]) -> None:
        return None


def arguments_fingerprint(arguments: Mapping[str, Any]) -> str:
    serialized = json.dumps(arguments, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
