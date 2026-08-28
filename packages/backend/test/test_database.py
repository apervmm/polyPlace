import asyncio
from app.database import connect_db, disconnect_db, get_pool


async def main():
    await connect_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
    await disconnect_db()
    print("Database connection successful — pool created and closed cleanly")


asyncio.run(main())