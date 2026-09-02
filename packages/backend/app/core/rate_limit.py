from app.core.redis import redis_client


USER_COOLDOWN_SEC = 5
IP_COOLDOWN_SEC = 3


async def _check_cooldown(key: str, ttl_seconds: int) -> bool:
    """Returns True if the key is still cooling down (i.e. rate-limited)."""
    was_set = await redis_client.set(key, "1", nx=True, ex=ttl_seconds)
    return was_set is None


# async def is_rate_limited(user_id: str) -> bool:
#     key = f"polyplace:cooldown:{user_id}"
#     was_set = await redis_client.set(key, 1, nx=True, ex=PLACEMENT_COOLDOWN_SEC)
#     return was_set is None


async def is_user_rate_limited(user_id: str) -> bool:
    key = f"polyplace:cooldown:{user_id}"
    return await _check_cooldown(key, USER_COOLDOWN_SEC)


async def is_ip_rate_limited(ip: str) -> bool:
    key = f"polyplace:cooldown:{ip}"
    return await _check_cooldown(ip, IP_COOLDOWN_SEC)