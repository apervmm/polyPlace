import logging

import asyncpg

logger = logging.getLogger(__name__)


async def init_pool(dsn: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10, ssl="require")
    async with pool.acquire() as conn:
        now = await conn.fetchval("SELECT now()")
        logger.info("Connected to DB: %s", now)
    return pool


async def get_state(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT DISTINCT ON (x, y)
            x, y, color, timestamp, userid
        FROM actions
        ORDER BY x, y, timestamp DESC
        """
    )


async def insert_action(
    pool: asyncpg.Pool, x: int, y: int, color: str, user_id: str
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO actions (x, y, color, userid)
        VALUES ($1, $2, $3, $4)
        RETURNING x, y, color, userid, timestamp
        """,
        x,
        y,
        color,
        user_id,
    )
