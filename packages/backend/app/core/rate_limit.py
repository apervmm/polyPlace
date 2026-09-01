from app.core.redis import redis_client


PLACEMENT_COOLDOWN_SEC = 5


async def is_rate_limited(user_id: str) -> bool:
    key = f"polyplace:cooldown:{user_id}"
    was_set = await redis_client.set(key, 1, nx=True, ex=PLACEMENT_COOLDOWN_SEC)
    return was_set is None