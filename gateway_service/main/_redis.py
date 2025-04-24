from redis.asyncio import Redis

from ._config import config

redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


async def get_redis() -> Redis:
    """
    Get a Redis connection.
    """
    return redis
