import json

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import agents
from app.ai.provider import AIError, get_provider
from app.core.config import settings
from app.core.db import get_db
from app.core.deps import client_ip, get_current_user_optional
from app.core.errors import AppError, not_found
from app.core.redis import get_redis
from app.models import User
from app.schemas.entry import WordSummary
from app.services import dictionary, generation, quotas, search, trending
from app.services.intent import Intent, needs_llm, parse_intent_rules
from app.services.languages import active_languages
from app.services.normalization import normalize

router = APIRouter(tags=["search"])


class SuggestionOut(BaseModel):
    language_code: str
    lemma: str
    slug: str
    score: float


class SearchResponse(BaseModel):
    query: str
    intent: Intent
    results: list[WordSummary]
    did_you_mean: list[SuggestionOut] = Field(default_factory=list)
    job: generation.JobOut | None = None
    notice: str | None = None
    ai_available: bool


@router.get("/search", response_model=SearchResponse)
async def search_words(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(min_length=1, max_length=300),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    force_ai: bool = False,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    ip = client_ip(request)
    await quotas.rate_limit(redis, f"search:{ip}", settings.search_rate_limit_per_minute)
    active = await active_languages(session)
    codes = {lang.code for lang in active}
    source = from_ if from_ in codes else None
    target = to if to in codes else None
    provider = get_provider()
    explain_lang = user.ui_language if user else "uz"

    intent, is_nl = parse_intent_rules(q)
    if provider and needs_llm(intent, is_nl):
        try:
            intent = Intent(**(await agents.parse_intent(session, provider, q)).model_dump())
        except AIError:
            pass

    if intent.type == "list_new_terms":
        ids = await search.list_new_terms(session, intent.domain, intent.year, source)
        results = await dictionary.summaries(
            session, ids, target, explain_lang, matches=dict.fromkeys(ids, "list")
        )
        await search.log_search(
            session, query=q, normalized=normalize(q), language_code=source, target_language=target,
            intent=intent.type, found=bool(results), result_word_id=None, user_id=user.id if user else None,
        )  # fmt: skip
        await session.commit()
        return SearchResponse(query=q, intent=intent, results=results, ai_available=provider is not None)

    term = intent.term or q
    source = source or (intent.source_lang if intent.source_lang in codes else None)
    target = target or (intent.target_lang if intent.target_lang in codes else None)
    langs = search.candidate_languages(term, active, source)
    hits = await search.lookup(session, term, langs)
    results = await dictionary.summaries(
        session, [h[0] for h in hits], target, explain_lang, matches=dict(hits)
    )

    did_you_mean: list[SuggestionOut] = []
    job = None
    notice = None
    if not results:
        did_you_mean = [SuggestionOut(**s.__dict__) for s in await search.did_you_mean(session, term, langs)]
        if search.looks_like_word(term):
            if provider is None:
                notice = "ai_unavailable"
            elif force_ai or not did_you_mean or did_you_mean[0].score < 0.5:
                try:
                    job = await generation.start_job(
                        redis,
                        term=term,
                        lang_hint=source,
                        domain=intent.domain,
                        subject=quotas.subject_for(user, ip),
                        user_id=user.id if user else None,
                        background_tasks=background_tasks,
                    )
                except AppError as exc:
                    notice = exc.code

    top = results[0] if results else None
    if top and top.match in ("exact", "form"):
        await trending.bump(redis, top.language_code, top.id)
    await search.log_search(
        session,
        query=q,
        normalized=normalize(term, langs[0] if len(langs) == 1 else None),
        language_code=top.language_code if top else source,
        target_language=target,
        intent=intent.type,
        found=bool(results),
        result_word_id=top.id if top else None,
        user_id=user.id if user else None,
    )
    await session.commit()
    return SearchResponse(
        query=q,
        intent=intent,
        results=results,
        did_you_mean=did_you_mean,
        job=job,
        notice=notice,
        ai_available=provider is not None,
    )


@router.get("/search/suggest", response_model=list[WordSummary])
async def suggest(
    q: str = Query(min_length=1, max_length=100),
    lang: str | None = None,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if len(normalize(q)) < 2:
        return []
    active = await active_languages(session)
    langs = search.candidate_languages(q, active, lang)
    cache_key = f"sug:{','.join(langs)}:{normalize(q)}"
    cached = await redis.get(cache_key)
    if cached:
        return [WordSummary.model_validate(item) for item in json.loads(cached)]
    ids = await search.prefix_suggest(session, q, langs)
    items = await dictionary.summaries(session, ids)
    await redis.set(cache_key, json.dumps([i.model_dump(mode="json") for i in items]), ex=3600)
    return items


@router.get("/jobs/{job_id}", response_model=generation.JobOut)
async def get_job(job_id: str, redis: Redis = Depends(get_redis)):
    job = await generation.get_job(redis, job_id)
    if job is None:
        raise not_found("Vazifa topilmadi")
    return job
