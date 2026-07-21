from wrapt import lru_cache
import redis.asyncio as redis
from app.core.config import get_settings


@lru_cache
def get_redis_pool():
    settings = get_settings()
    return redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        max_connections=20,
        decode_responses=True
    )
    
@lru_cache
def get_redis_client():
    return redis.Redis(connection_pool=get_redis_pool())