import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    """Tracks live WebSocket connections for broadcast, replacing the Node
    service's `wsServer.clients` iteration."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload)
        targets = list(self._connections)
        results = await asyncio.gather(
            *(ws.send_text(message) for ws in targets), return_exceptions=True
        )
        for ws, result in zip(targets, results):
            if isinstance(result, Exception):
                self._connections.discard(ws)
