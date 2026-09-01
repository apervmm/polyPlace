import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import pixel_repo
from app.schemas.pixel import PixelOut
from app.core.redis import redis_client

BOARD_CACHE_KEY = "polyplace:board"


async def get_board_state(session: AsyncSession) -> list[PixelOut]:
    cached = await redis_client.get(BOARD_CACHE_KEY)

    if cached is not None:
        return [PixelOut(**p) for p in json.loads(cached)]
    
    pixels = await pixel_repo.get_all_pixels(session)

    result = [PixelOut.model_validate(p) for p in pixels]

    await redis_client.set(
        BOARD_CACHE_KEY,
        json.dumps([p.model_dump() for p in result]),
    )
 
    return result


async def place_pixel(session: AsyncSession, x: int, y: int, color: str, userid: str | None):
    pixel = await pixel_repo.upsert_pixel(session, x, y, color, userid)
    await _update_cache(x, y, color)
    return pixel


async def _update_cache(x: int, y: int, color: str) -> None:
    """
        Patchning a single pixel into a cached board, since recaching the whole board on a pixel placement is expensive
    """
    cached = await redis_client.get(BOARD_CACHE_KEY)

    if cached is None:
        return
    
    pixels = json.loads(cached)

    for p in pixels:
        if p["x"] == x and p["y"] == y:
            p["color"] = color
            break
    else:
        pixels.append({"x": x, "y": y, "color": color})
    
    await redis_client.set(
        BOARD_CACHE_KEY,
        json.dumps(pixels)
    )