import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from .auth import decode_user_id
from .config import Settings
from .db import get_state, init_pool, insert_action
from .rate_limit import CooldownTracker
from .schemas import ErrorMessage, InitMessage, PlaceRequest, Pixel, UpdateMessage
from .ws_manager import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    app.state.pool = await init_pool(settings.database_url)
    app.state.manager = ConnectionManager()
    app.state.cooldown = CooldownTracker(settings.place_cooldown_seconds)
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_root() -> PlainTextResponse:
    return PlainTextResponse("OK", status_code=200)


@app.get("/health")
async def health_check() -> JSONResponse:
    try:
        await app.state.pool.fetchval("SELECT 1")
    except Exception as err:  # noqa: BLE001 - report any DB failure as degraded
        return JSONResponse({"status": "degraded", "detail": str(err)}, status_code=503)
    return JSONResponse({"status": "ok"}, status_code=200)


async def _handle_place(
    websocket: WebSocket, data: dict, user_id: str | None
) -> None:
    manager: ConnectionManager = app.state.manager
    cooldown: CooldownTracker = app.state.cooldown
    pool = app.state.pool

    if user_id is None:
        error = ErrorMessage(
            code="unauthenticated",
            message="You must be logged in to place a pixel.",
        )
        await websocket.send_text(error.model_dump_json())
        return

    remaining = cooldown.check(user_id)
    if remaining is not None:
        error = ErrorMessage(
            code="rate_limited",
            message="Placing too fast. Try again shortly.",
            retryAfterSeconds=remaining,
        )
        await websocket.send_text(error.model_dump_json())
        return

    try:
        place = PlaceRequest(**data)
    except ValidationError as err:
        logger.info("Invalid place message: %s", err)
        return

    row = await insert_action(pool, place.x, place.y, place.color, user_id)
    event = UpdateMessage(
        x=row["x"],
        y=row["y"],
        color=row["color"],
        userId=row["userid"],
        timestamp=row["timestamp"],
    )
    await manager.broadcast(json.loads(event.model_dump_json()))


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    settings: Settings = app.state.settings
    manager: ConnectionManager = app.state.manager
    pool = app.state.pool

    token = websocket.query_params.get("token")
    user_id = decode_user_id(token, settings)

    await manager.connect(websocket)
    logger.info("New client %s", f"userId={user_id}" if user_id else "(guest)")

    try:
        rows = await get_state(pool)
        pixels = [
            Pixel(x=r["x"], y=r["y"], color=r["color"], timestamp=r["timestamp"], userid=r["userid"])
            for r in rows
        ]
        init_message = InitMessage(pixels=pixels, userId=user_id)
        await websocket.send_text(init_message.model_dump_json())

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as err:
                logger.info("Error parsing message: %s", err)
                continue

            if isinstance(data, dict) and data.get("type") == "place":
                await _handle_place(websocket, data, user_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
        logger.info("Client with userId=%s disconnected", user_id)
