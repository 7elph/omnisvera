from __future__ import annotations

import asyncio
import secrets
import threading
import time
from dataclasses import dataclass

from fastapi import WebSocket

from .access import AccessContext


@dataclass(frozen=True)
class RealtimeTicket:
    access: AccessContext
    expires_at: float


class SessionRealtime:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._tickets: dict[str, RealtimeTicket] = {}
        self._ticket_lock = threading.Lock()
        self._connection_lock = asyncio.Lock()

    def issue_ticket(self, access: AccessContext) -> str:
        token = secrets.token_urlsafe(32)
        now = time.monotonic()
        with self._ticket_lock:
            self._tickets = {key: value for key, value in self._tickets.items() if value.expires_at > now}
            self._tickets[token] = RealtimeTicket(access=access, expires_at=now + 60)
        return token

    def consume_ticket(self, token: str) -> AccessContext | None:
        with self._ticket_lock:
            ticket = self._tickets.pop(token, None)
        if ticket is None or ticket.expires_at <= time.monotonic():
            return None
        return ticket.access

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._connection_lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._connection_lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        async with self._connection_lock:
            connections = list(self._connections)
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        if stale:
            async with self._connection_lock:
                for websocket in stale:
                    self._connections.discard(websocket)


session_realtime = SessionRealtime()
