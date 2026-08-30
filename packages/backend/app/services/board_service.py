from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import pixel_repo
from app.schemas.pixel import PixelOut


async def get_board_state(session: AsyncSession) -> list[PixelOut]:
    pixels = await pixel_repo.get_all_pixels(session)
    return [PixelOut.model_validate(p) for p in pixels]


async def place_pixel(session: AsyncSession, x: int, y: int, color: str, userid: str | None):
    return await pixel_repo.upsert_pixel(session, x, y, color, userid)