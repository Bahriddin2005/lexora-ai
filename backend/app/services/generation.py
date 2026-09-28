"""AI word generation jobs: Redis-backed job state, EntryAgent → VerificationAgent → publish rule."""

import logging
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai import agents
from app.ai.provider import AIError, LLMProvider, get_provider
from app.ai.schemas import Verification
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.redis import get_redis
from app.models import Word, WordForm
from app.models.enums import VISIBLE_STATUSES, ContentStatus
from app.services import dictionary, quotas
from app.services.languages import active_languages
from app.services.normalization import normalize

logger = logging.getLogger("lexora.generation")

JOB_TTL = 24 * 3600
LOCK_TTL = 300
_STATUS_FOR_WORD = {
    ContentStatus.AI_GENERATED: "done",
    ContentStatus.PUBLISHED: "done",
    ContentStatus.DRAFT: "draft",
    ContentStatus.REJECTED: "rejected",
}


class JobWord(BaseModel):
    language_code: str
    slug: str


class JobOut(BaseModel):
    id: str
    status: str  # queued | running | done | draft | rejected | not_a_word | failed
    term: str | None = None
    word: JobWord | None = None
    message: str | None = None
    suggestions: list[str] = Field(default_factory=list)


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


async def get_job(redis: Redis, job_id: str) -> JobOut | None:
    data = await redis.hgetall(_job_key(job_id))
    if not data:
        return None
    word = JobWord(language_code=data["word_lang"], slug=data["word_slug"]) if data.get("word_slug") else None
    suggestions = [s for s in (data.get("suggestions") or "").split("|") if s]
    return JobOut(
        id=job_id,
        status=data["status"],
        term=data.get("term"),
        word=word,
        message=data.get("message") or None,
        suggestions=suggestions,
    )


async def _set_job(redis: Redis, job_id: str, **fields: Any) -> None:
    mapping = {
        k: ("|".join(v) if isinstance(v, list) else ("" if v is None else str(v))) for k, v in fields.items()
    }
    await redis.hset(_job_key(job_id), mapping=mapping)


def decide_status(v: Verification) -> ContentStatus:
    if v.verdict == "reject" or v.confidence < settings.ai_reject_threshold:
        return ContentStatus.REJECTED
    if v.verdict == "review" or v.confidence < settings.ai_publish_threshold:
        return ContentStatus.DRAFT
    return ContentStatus.AI_GENERATED


async def start_job(
    redis: Redis,
    *,
    term: str,
    lang_hint: str | None,
    domain: str | None,
    subject: quotas.Subject,
    user_id: uuid.UUID | None,
    background_tasks: BackgroundTasks | None,
    regenerate_word_id: int | None = None,
) -> JobOut:
    lock_key = f"gen:lock:{lang_hint or 'auto'}:{normalize(term, lang_hint)}:{regenerate_word_id or ''}"
    existing_id = await redis.get(lock_key)
    if existing_id:
        existing = await get_job(redis, existing_id)
        if existing and existing.status in ("queued", "running"):
            return existing
    await quotas.consume(redis, subject, "ai_generate")
    job_id = uuid.uuid4().hex
    await _set_job(
        redis,
        job_id,
        status="queued",
        term=term,
        lang_hint=lang_hint,
        domain=domain,
        user_id=user_id,
        regenerate_word_id=regenerate_word_id,
        lock_key=lock_key,
    )
    await redis.expire(_job_key(job_id), JOB_TTL)
    await redis.set(lock_key, job_id, ex=LOCK_TTL)
    dispatch(job_id, background_tasks)
    return JobOut(id=job_id, status="queued", term=term)


def dispatch(job_id: str, background_tasks: BackgroundTasks | None) -> None:
    if settings.tasks_mode == "celery":
        from app.workers.tasks import generate_word

        generate_word.delay(job_id)
    elif background_tasks is not None:
        background_tasks.add_task(run_job, job_id, SessionLocal, get_redis())
    else:
        raise RuntimeError("inline job dispatch needs BackgroundTasks")


async def run_job(
    job_id: str,
    session_factory: Callable[[], Any] | async_sessionmaker,
    redis: Redis,
    provider: LLMProvider | None = None,
) -> None:
    data = await redis.hgetall(_job_key(job_id))
    if not data:
        return
    await _set_job(redis, job_id, status="running")
    try:
        provider = provider or get_provider()
        if provider is None:
            await _set_job(redis, job_id, status="failed", message="ai_unavailable")
            return
        async with session_factory() as session:
            result = await generate_and_store(
                session,
                provider,
                term=data["term"],
                lang_hint=data.get("lang_hint") or None,
                domain=data.get("domain") or None,
                user_id=uuid.UUID(data["user_id"]) if data.get("user_id") else None,
                regenerate_word_id=int(data["regenerate_word_id"])
                if data.get("regenerate_word_id")
                else None,
            )
            await session.commit()
        await _set_job(redis, job_id, **result)
    except AIError as exc:
        logger.warning("generation job %s failed: %s", job_id, exc)
        await _set_job(redis, job_id, status="failed", message="ai_error")
    except Exception:
        logger.exception("generation job %s crashed", job_id)
        await _set_job(redis, job_id, status="failed", message="internal_error")
    finally:
        if data.get("lock_key"):
            await redis.delete(data["lock_key"])


async def _find_existing(session: AsyncSession, keys: dict[str, str]) -> Word | None:
    conds = [(Word.language_code == lang) & (Word.normalized == key) for lang, key in keys.items()]
    word = await session.scalar(select(Word).where(or_(*conds)).limit(1))
    if word:
        return word
    form_conds = [(Word.language_code == lang) & (WordForm.normalized == key) for lang, key in keys.items()]
    return await session.scalar(
        select(Word).join(WordForm, WordForm.word_id == Word.id).where(or_(*form_conds)).limit(1)
    )


def _existing_result(word: Word) -> dict[str, Any]:
    visible = word.status in VISIBLE_STATUSES
    return {
        "status": _STATUS_FOR_WORD.get(ContentStatus(word.status), "done"),
        "word_lang": word.language_code if visible else "",
        "word_slug": word.normalized if visible else "",
    }


async def generate_and_store(
    session: AsyncSession,
    provider: LLMProvider,
    *,
    term: str,
    lang_hint: str | None,
    domain: str | None = None,
    user_id: uuid.UUID | None = None,
    regenerate_word_id: int | None = None,
) -> dict[str, Any]:
    languages = [lang.code for lang in await active_languages(session)]

    if regenerate_word_id is None:
        hint_langs = [lang_hint] if lang_hint in languages else languages
        existing = await _find_existing(session, {lang: normalize(term, lang) for lang in hint_langs})
        if existing:
            return _existing_result(existing)

    entry = await agents.generate_entry(
        session,
        provider,
        term=term,
        lang_hint=lang_hint,
        languages=languages,
        domain_hint=domain,
        use_cache=regenerate_word_id is None,
        user_id=user_id,
    )
    if not entry.is_valid_word or not entry.senses:
        return {"status": "not_a_word", "suggestions": entry.suggestions[:5]}

    lang = entry.language if entry.language in languages else (lang_hint or "en")
    entry_in = entry.to_entry_in(set(languages))
    if regenerate_word_id is None:
        existing = await _find_existing(session, {lang: normalize(entry_in.lemma, lang)})
        if existing:
            return _existing_result(existing)

    verification = await agents.verify_entry(session, provider, entry)
    status = decide_status(verification)
    message = "; ".join(verification.issues[:3]) or None

    if regenerate_word_id is not None:
        word = await dictionary.load_word(session, regenerate_word_id)
        if word is None:
            return {"status": "failed", "message": "word_not_found"}
        word = await dictionary.update_entry(
            session, word, entry_in, reason="ai:regenerate", user_id=user_id, status=status,
            source_code="gemini", confidence=verification.confidence,
        )  # fmt: skip
    else:
        word = await dictionary.create_entry(
            session, lang, entry_in, status=status, source_code="gemini", confidence=verification.confidence,
            reason="ai:generate", user_id=user_id, example_source="ai",
        )  # fmt: skip
    visible = word.status in VISIBLE_STATUSES
    return {
        "status": _STATUS_FOR_WORD[ContentStatus(word.status)],
        "word_lang": word.language_code if visible or regenerate_word_id else "",
        "word_slug": word.normalized if visible or regenerate_word_id else "",
        "message": message,
    }
