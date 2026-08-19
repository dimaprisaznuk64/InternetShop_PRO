import json
import logging
from typing import Any, Optional
from functools import wraps
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

redis_client: Optional[aioredis.Redis] = None

DEFAULT_TTL = 300  # 5 minutes


async def get_redis() -> Optional[aioredis.Redis]:
    return redis_client


async def init_redis() -> None:
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await redis_client.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        redis_client = None


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


async def cache_get(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        if data is not None:
            return json.loads(data)
    except Exception as e:
        logger.warning("Cache get error: %s", e)
    return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.warning("Cache set error: %s", e)


async def cache_delete(key: str) -> None:
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning("Cache delete error: %s", e)


async def cache_delete_pattern(pattern: str) -> None:
    if not redis_client:
        return
    try:
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.warning("Cache delete pattern error: %s", e)
