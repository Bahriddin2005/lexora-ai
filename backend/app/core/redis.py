from redis.asyncio import Redis

from app.core.config import settings

_client: Redis | None = None


def make_redis() -> Redis:
    if settings.redis_url == "memory://":
        from fakeredis.aioredis import FakeRedis

        return FakeRedis(decode_responses=True)
    return Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = make_redis()
    return _client
