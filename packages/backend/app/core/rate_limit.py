from app.core.redis import redis_client
from dataclasses import dataclass


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
    key = f"polyplace:cooldown:user:{user_id}"
    return await _check_cooldown(key, USER_COOLDOWN_SEC)


async def is_ip_rate_limited(ip: str) -> bool:
    if not ip:
        return False
    key = f"polyplace:cooldown:ip:{ip}"
    return await _check_cooldown(ip, IP_COOLDOWN_SEC)



@dataclass
class RateLimiter:
    """A reusable, named rate limitter"""
    name: str             
    window_seconds: int   


    def _key(self, identifier: str) -> str:
        return f"polyplace:ratelimit:{self.name}:{identifier}"

    async def is_limited(self, identifier: str) -> bool:
        """identifier = Whatever you are limiting by"""
        was_set = await redis_client.set(
            self._key(identifier), "1", nx=True, ex=self.window_seconds
        )
        return was_set is None
    
    async def get_ttl(self, identifier: str) -> int:
        """
            Seconds remaining until this identifier is no longer rate-limited
            0, if not limited
        """
        ttl = await redis_client.ttl(self._key(identifier))
        return max(ttl, 0)
    

placement_user_limiter = RateLimiter(name="placement_user", window_seconds=5)
placement_ip_limiter = RateLimiter(name="placement_ip", window_seconds=3)
register_ip_limiter = RateLimiter(name="register_ip", window_seconds=60)