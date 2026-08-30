from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.schemas.pixel import PlaceMessage
from app.services.board_service import place_pixel
from app.ws.connection_manager import manager

settings = get_settings()


async def handle_place(session: AsyncSession, data: dict, user_id: str | None) -> None:
    msg = PlaceMessage(**data)

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