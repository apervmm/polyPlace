from fastapi import WebSocket
import asyncio
import json

from app.core.redis import redis_client


CHANNEL = "polyplace:updates"


class ConnectionManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._listener_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def publish(self, message: dict) -> None:
       await redis_client.publish(CHANNEL, json.dumps(message))

    async def _broadcast_local(self, message: dict) -> None:
        dead = []
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    async def broadcast(self, message: dict) -> None:
        """ Broacast Locally """
        dead = []
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    async def start_listener(self) -> None:
        """Run once per instance at startup — subscribes to the shared channel
        and re-broadcasts anything published (by any instance) to local clients."""
        pubsub = redis_client.pubsub()

        await pubsub.subscribe(CHANNEL)

        async def _listen():
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                await self.broadcast(data)
        self._listener_task = asyncio.create_task(_listen())

    async def stop_listener(self) -> None:
        """Stop the listener task and unsubscribe from the channel."""
        if self._listener_task:
            self._listener_task.cancel()
            # try:
            #     await self._listener_task
            # except asyncio.CancelledError:
            #     pass
            # self._listener_task = None


manager = ConnectionManager()