import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.provider import build_provider
from app.core.db import make_engine
from app.core.redis import make_redis
from app.services.generation import run_job
from app.workers.celery_app import celery_app


async def _generate(job_id: str) -> None:
    # Each task runs in its own event loop, so it gets its own engine, Redis client and provider.
    engine = make_engine(null_pool=True)
    redis = make_redis()
    try:
        await run_job(job_id, async_sessionmaker(engine, expire_on_commit=False), redis, build_provider())
    finally:
        await redis.aclose()
        await engine.dispose()


@celery_app.task(name="lexora.generate_word")
def generate_word(job_id: str) -> None:
    asyncio.run(_generate(job_id))
