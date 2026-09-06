import redis.asyncio as redis

from app.core.config import get_settings


settings = get_settings()

redis_client: redis.Redis = redis.from_url(
    settings.redis_url, 
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
    decode_responses=True
)