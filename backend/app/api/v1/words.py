from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import require_provider
from app.core.db import SessionLocal, get_db
from app.core.deps import client_ip, get_current_user_optional
from app.core.errors import not_found
from app.core.redis import get_redis
from app.models import User, UserFavorite, Word
from app.schemas.entry import WordEntry
from app.services import dictionary, explain, quotas, search
from app.services.languages import active_languages

router = APIRouter(prefix="/words", tags=["words"])

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


async def _entry_response(session: AsyncSession, word: Word, user: User | None) -> WordEntry:
    is_favorite = False
    if user:
        is_favorite = bool(
            await session.scalar(
                select(UserFavorite.word_id).where(
                    UserFavorite.user_id == user.id, UserFavorite.word_id == word.id
                )
            )
        )
    return await dictionary.build_entry(session, word, is_favorite=is_favorite)


async def _not_found_with_suggestions(session: AsyncSession, term: str, langs: list[str]):
    suggestions = await search.did_you_mean(session, term, langs)
    return not_found(
        "So‘z topilmadi",
        suggestions=[
            {"language_code": s.language_code, "slug": s.slug, "lemma": s.lemma} for s in suggestions
        ],
    )


@router.get("/{lang}/{slug}", response_model=WordEntry)
async def get_word(
    lang: str,
    slug: str,
    session: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    word = await dictionary.find_word(session, lang, slug)
    if word is None:
        raise await _not_found_with_suggestions(session, slug, [lang])
    return await _entry_response(session, word, user)


@router.get("/{term}", response_model=WordEntry, summary="Short alias: GET /api/v1/words/hello")
async def get_word_by_term(
    term: str,
    lang: str | None = None,
    session: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    active = await active_languages(session)
    langs = search.candidate_languages(term, active, lang)
    hits = [h for h in await search.lookup(session, term, langs) if h[1] in ("exact", "form")]
    if not hits:
        raise await _not_found_with_suggestions(session, term, langs)
    word = await dictionary.load_word(session, hits[0][0])
    assert word is not None
    return await _entry_response(session, word, user)


class ExplainIn(BaseModel):
    lang: str = Field(default="uz", max_length=8)
    level: Literal["simple", "detailed"] = "simple"
    question: str | None = Field(default=None, max_length=500)


@router.post("/{lang}/{slug}/explain", summary="AI explanation (Server-Sent Events)")
async def explain_word(
    lang: str,
    slug: str,
    data: ExplainIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    word = await dictionary.find_word(session, lang, slug)
    if word is None:
        raise not_found("So‘z topilmadi")
    provider = require_provider()
    entry = await dictionary.build_entry(session, word)
    question = (data.question or "").strip() or None
    inputs = explain.explain_inputs(entry, data.lang, data.level, question)
    digest = explain.digest_for(provider, inputs)

    cached = await explain.cached_text(session, digest)
    if cached is not None:

        async def replay():
            yield explain.sse({"delta": cached})
            yield explain.sse({"done": True, "cached": True})

        return StreamingResponse(replay(), media_type="text/event-stream", headers=SSE_HEADERS)

    remaining = await quotas.consume(redis, quotas.subject_for(user, client_ip(request)), "ai_explain")
    headers = dict(SSE_HEADERS)
    if remaining is not None:
        headers["X-Quota-Remaining"] = str(remaining)
    stream = explain.stream_explanation(
        SessionLocal, provider, inputs, digest, word.id, user.id if user else None
    )
    return StreamingResponse(stream, media_type="text/event-stream", headers=headers)
