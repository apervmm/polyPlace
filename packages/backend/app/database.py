# app/database.py
import asyncpg
from app.config import settings

pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    """Called once at app startup — opens the connection pool."""
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        ssl="require",
        min_size=1,
        max_size=10,
    )


async def disconnect_db() -> None:
    """Called once at app shutdown — closes all pooled connections cleanly."""
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    """Used by service-layer functions to grab the pool for queries."""
    if pool is None:
        raise RuntimeError("Database pool not initialized — did the app forget to call connect_db()?")
    return pool