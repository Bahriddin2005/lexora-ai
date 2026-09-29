from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import get_redis
from app.models import Translation, Word, WordSense
from app.models.enums import VISIBLE_STATUSES
from app.schemas.entry import WordSummary
from app.services import dictionary, trending, web_dictionary
from app.services.normalization import normalize

router = APIRouter(tags=["discover"])


class OnlineWord(BaseModel):
    language_code: str
    title: str
    description: str | None
    url: str


class DictionaryPage(BaseModel):
    items: list[WordSummary]
    online_items: list[OnlineWord]
    total: int
    page: int
    size: int


@router.get("/dictionary", response_model=DictionaryPage)
async def dictionary_words(
    lang: str | None = None,
    letter: str | None = Query(default=None, min_length=1, max_length=3),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=40, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    filters = [Word.status.in_(VISIBLE_STATUSES)]
    if lang:
        filters.append(Word.language_code == lang)
    if letter:
        filters.append(func.lower(Word.normalized).like(f"{letter.lower()}%"))
    if q and (needle := normalize(q)):
        translated = (
            select(Translation.id)
            .join(WordSense, Translation.sense_id == WordSense.id)
            .where(WordSense.word_id == Word.id, func.lower(Translation.normalized).contains(needle))
            .exists()
        )
        filters.append(or_(func.lower(Word.normalized).contains(needle), translated))

    total = await session.scalar(select(func.count(Word.id)).where(*filters)) or 0
    stmt = (
        select(Word.id)
        .where(*filters)
        .order_by(Word.normalized, Word.language_code, Word.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    ids = list((await session.scalars(stmt)).all())
    online_items: list[OnlineWord] = []
    if q and total == 0:
        online_items = [
            OnlineWord(**item.__dict__)
            for item in await web_dictionary.search(q, preferred_language=lang)
        ]
    return DictionaryPage(
        items=await dictionary.summaries(session, ids),
        online_items=online_items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/trending", response_model=list[WordSummary])
async def get_trending(
    lang: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    rows = await trending.top(redis, lang, limit)
    scores = dict(rows)
    items = await dictionary.summaries(session, [word_id for word_id, _ in rows])
    for item in items:
        item.score = scores.get(item.id)
    return items


@router.get("/new-words", response_model=list[WordSummary])
async def new_words(
    lang: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Word.id).where(Word.status.in_(VISIBLE_STATUSES))
    if lang:
        stmt = stmt.where(Word.language_code == lang)
    stmt = stmt.order_by(Word.created_at.desc(), Word.id.desc()).offset((page - 1) * limit).limit(limit)
    return await dictionary.summaries(session, list((await session.scalars(stmt)).all()))


@router.get("/ai-terms", response_model=list[WordSummary])
async def ai_terms(limit: int = Query(default=20, ge=1, le=100), session: AsyncSession = Depends(get_db)):
    has_ai_sense = select(WordSense.id).where(WordSense.word_id == Word.id, WordSense.domain == "ai").exists()
    stmt = (
        select(Word.id)
        .where(Word.status.in_(VISIBLE_STATUSES), or_(Word.tags.contains(["ai"]), has_ai_sense))
        .order_by(Word.first_seen_at.desc(), Word.id.desc())
        .limit(limit)
    )
    return await dictionary.summaries(session, list((await session.scalars(stmt)).all()))


class SitemapItem(BaseModel):
    language_code: str
    slug: str
    updated_at: datetime


@router.get("/sitemap-words", response_model=list[SitemapItem])
async def sitemap_words(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=5000, ge=1, le=50000),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Word.language_code, Word.normalized, Word.updated_at)
        .where(Word.status.in_(VISIBLE_STATUSES))
        .order_by(Word.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await session.execute(stmt)).all()
    return [SitemapItem(language_code=lang, slug=slug, updated_at=updated) for lang, slug, updated in rows]
