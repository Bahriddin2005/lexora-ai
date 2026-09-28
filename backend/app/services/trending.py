"""Real-time trending words: hourly Redis sorted sets, summed over the last 24 hours."""

from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

BUCKET_TTL = 48 * 3600
CACHE_TTL = 60


def _bucket(scope: str, at: datetime) -> str:
    return f"trend:{scope}:{at:%Y%m%d%H}"


async def bump(redis: Redis, lang: str, word_id: int) -> None:
    now = datetime.now(UTC)
    async with redis.pipeline(transaction=False) as pipe:
        for scope in (lang, "all"):
            key = _bucket(scope, now)
            pipe.zincrby(key, 1, str(word_id))
            pipe.expire(key, BUCKET_TTL)
        await pipe.execute()


async def top(
    redis: Redis, lang: str | None = None, limit: int = 20, hours: int = 24
) -> list[tuple[int, float]]:
    scope = lang or "all"
    cache_key = f"trend:cache:{scope}:{hours}"
    if not await redis.exists(cache_key):
        now = datetime.now(UTC)
        keys = [_bucket(scope, now - timedelta(hours=h)) for h in range(hours)]
        await redis.zunionstore(cache_key, keys)
        await redis.expire(cache_key, CACHE_TTL)
    rows = await redis.zrevrange(cache_key, 0, limit - 1, withscores=True)
    return [(int(member), float(score)) for member, score in rows]


async def invalidate(redis: Redis) -> None:
    async for key in redis.scan_iter("trend:cache:*"):
        await redis.delete(key)
