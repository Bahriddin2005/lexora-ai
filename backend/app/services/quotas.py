"""Daily quotas (AI, translation, TTS) and per-minute rate limits, stored in Redis."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app.core.config import QUOTAS
from app.core.errors import AppError
from app.models import User


@dataclass(frozen=True)
class Subject:
    plan: str  # anon | free | pro
    key: str
    unlimited: bool = False


def subject_for(user: User | None, ip: str) -> Subject:
    if user is None:
        return Subject(plan="anon", key=f"ip:{ip}")
    return Subject(plan=user.plan, key=f"u:{user.id}", unlimited=user.is_staff)


def _seconds_to_midnight() -> int:
    now = datetime.now(UTC)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


def _key(kind: str, subject: Subject) -> str:
    return f"q:{kind}:{subject.key}:{datetime.now(UTC):%Y%m%d}"


def limit_for(subject: Subject, kind: str) -> int:
    return QUOTAS.get(subject.plan, QUOTAS["anon"]).get(kind, 0)


async def consume(redis: Redis, subject: Subject, kind: str, amount: int = 1) -> int | None:
    """Consume `amount` units. Returns remaining units (None if unlimited); raises 429 when exhausted."""
    if subject.unlimited:
        return None
    limit = limit_for(subject, kind)
    key = _key(kind, subject)
    used = await redis.incrby(key, amount)
    if used == amount:
        await redis.expire(key, 2 * 24 * 3600)
    if used > limit:
        await redis.decrby(key, amount)
        raise AppError(
            429,
            "quota_exceeded",
            "Bugungi limit tugadi. Ertaga qayta urinib ko‘ring yoki Pro tarifga o‘ting.",
            {"kind": kind, "limit": limit, "reset_in": _seconds_to_midnight()},
        )
    return limit - used


async def refund(redis: Redis, subject: Subject, kind: str, amount: int = 1) -> None:
    if not subject.unlimited:
        await redis.decrby(_key(kind, subject), amount)


async def usage(redis: Redis, subject: Subject) -> dict[str, dict[str, int | None]]:
    kinds = QUOTAS["anon"].keys()
    result: dict[str, dict[str, int | None]] = {}
    for kind in kinds:
        used = int(await redis.get(_key(kind, subject)) or 0)
        result[kind] = {"used": used, "limit": None if subject.unlimited else limit_for(subject, kind)}
    return result


async def rate_limit(redis: Redis, bucket: str, limit: int, window_seconds: int = 60) -> None:
    window = int(datetime.now(UTC).timestamp()) // window_seconds
    key = f"rl:{bucket}:{window}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds * 2)
    if count > limit:
        raise AppError(429, "rate_limited", "Juda ko‘p so‘rov. Birozdan so‘ng qayta urinib ko‘ring.")
