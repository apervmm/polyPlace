from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.schemas.pixel import PlaceMessage
from app.services.board_service import place_pixel
from app.ws.connection_manager import manager
from fastapi import WebSocket
from pydantic import ValidationError

settings = get_settings()



async def handle_place(session: AsyncSession, data: dict, user_id: str | None, websocket: WebSocket) -> None:
    if user_id is None:
        await websocket.send_json({
            "type": "error",
            "message": "You must be logged in to place a pixel",
        })
        return
    

    # msg = PlaceMessage(**data)

    try:
        msg = PlaceMessage(**data)
    except ValidationError:
        await websocket.send_json({"type": "error", "message": "Invalid pixel data"})
        return

    if not (0 <= msg.x < settings.board_width and 0 <= msg.y < settings.board_height):
        return  # dropping out-of-bound placements

    pixel = await place_pixel(session, msg.x, msg.y, msg.color, user_id)

    await manager.broadcast({
        "type": "update",
        "x": pixel.x,
        "y": pixel.y,
        "color": pixel.color,
        "userId": user_id,
        "timestamp": pixel.updated_at.isoformat(),
    })