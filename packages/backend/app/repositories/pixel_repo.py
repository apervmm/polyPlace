from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.action import Action
from app.db.models.pixel import Pixel


async def get_all_pixels(session: AsyncSession) -> list[Pixel]:
    result = await session.execute(select(Pixel))
    return list(result.scalars().all())


async def upsert_pixel(session: AsyncSession, x: int, y: int, color: str, userid: str | None) -> Pixel:
    # stmt = (
    #     pg_insert(Pixel)
    #     .values(x=x, y=y, color=color, userid=userid)
    #     .on_conflict_do_update(
    #         index_elements=["x", "y"],
    #         set_={"color": color, "userid": userid, "updated_at": Pixel.updated_at.default_factory if False else None},
    #     )
    #     .returning(Pixel)
    # )

    stmt = (
        pg_insert(Pixel)
        .values(x=x, y=y, color=color, userid=userid)
        .on_conflict_do_update(
            index_elements=["x", "y"],
            set_={"color": color, "userid": userid},
        )
        .returning(Pixel)
    )
    result = await session.execute(stmt)
    pixel = result.scalar_one()

    session.add(Action(x=x, y=y, color=color, userid=userid))
    await session.commit()
    return pixel