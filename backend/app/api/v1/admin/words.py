from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.admin.common import Page
from app.core.db import get_db
from app.core.deps import client_ip, require_admin, require_editor
from app.core.errors import conflict, not_found
from app.core.redis import get_redis
from app.models import Report, SearchLog, User, Word, WordVersion
from app.models.enums import ContentStatus, EntryType, ReportStatus
from app.schemas.entry import WordEntry, WordEntryIn
from app.services import dictionary, generation, quotas
from app.services.normalization import normalize

router = APIRouter()


class AdminWordRow(BaseModel):
    id: int
    language_code: str
    lemma: str
    slug: str
    entry_type: str
    status: str
    confidence: float | None
    version: int
    pos: list[str]
    source: str | None
    demand: int = 0
    open_reports: int = 0
    created_at: datetime
    updated_at: datetime


class VersionRow(BaseModel):
    version: int
    reason: str | None
    changed_by: str | None
    created_at: datetime


class ReportBrief(BaseModel):
    id: int
    reason: str
    comment: str | None
    status: str
    created_at: datetime


class AdminWordDetail(BaseModel):
    entry: WordEntry
    form: WordEntryIn
    versions: list[VersionRow]
    reports: list[ReportBrief]


class CreateWordIn(BaseModel):
    language_code: str
    lemma: str = Field(min_length=1, max_length=200)
    entry_type: EntryType = EntryType.WORD


class UpdateWordIn(BaseModel):
    entry: WordEntryIn
    reason: str = Field(default="edit", max_length=200)


class GenerateIn(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    lang: str | None = None


def _demand_since() -> datetime:
    return datetime.now(UTC) - timedelta(days=30)


async def _rows(session: AsyncSession, words: list[Word]) -> list[AdminWordRow]:
    if not words:
        return []
    ids = [w.id for w in words]
    keys = [w.normalized for w in words]
    demand_rows = await session.execute(
        select(SearchLog.normalized, SearchLog.result_word_id, func.count())
        .where(
            SearchLog.created_at >= _demand_since(),
            or_(SearchLog.result_word_id.in_(ids), SearchLog.normalized.in_(keys)),
        )
        .group_by(SearchLog.normalized, SearchLog.result_word_id)
    )
    demand: dict[int, int] = dict.fromkeys(ids, 0)
    by_key = {w.normalized: w.id for w in words}
    for key, word_id, count in demand_rows.all():
        target = word_id if word_id in demand else by_key.get(key)
        if target is not None:
            demand[target] += count
    report_rows = await session.execute(
        select(Report.word_id, func.count())
        .where(Report.word_id.in_(ids), Report.status == ReportStatus.OPEN)
        .group_by(Report.word_id)
    )
    reports = dict(report_rows.all())
    rows = []
    for w in words:
        pos = list(dict.fromkeys(s.pos for s in w.senses))
        rows.append(
            AdminWordRow(
                id=w.id, language_code=w.language_code, lemma=w.lemma, slug=w.normalized, entry_type=w.entry_type,
                status=w.status, confidence=w.confidence, version=w.version, pos=pos,
                source=w.source.name if w.source else None, demand=demand.get(w.id, 0),
                open_reports=reports.get(w.id, 0), created_at=w.created_at, updated_at=w.updated_at,
            )
        )  # fmt: skip
    return rows


async def _detail(session: AsyncSession, word: Word) -> AdminWordDetail:
    versions = await session.execute(
        select(WordVersion.version, WordVersion.reason, User.email, WordVersion.created_at)
        .outerjoin(User, User.id == WordVersion.changed_by)
        .where(WordVersion.word_id == word.id)
        .order_by(WordVersion.version.desc())
    )
    reports = await session.scalars(
        select(Report).where(Report.word_id == word.id).order_by(Report.created_at.desc()).limit(50)
    )
    return AdminWordDetail(
        entry=await dictionary.build_entry(session, word),
        form=dictionary.to_entry_in(word),
        versions=[
            VersionRow(version=v, reason=r, changed_by=e, created_at=c) for v, r, e, c in versions.all()
        ],
        reports=[
            ReportBrief(id=r.id, reason=r.reason, comment=r.comment, status=r.status, created_at=r.created_at)
            for r in reports.all()
        ],
    )


async def _load(session: AsyncSession, word_id: int) -> Word:
    word = await dictionary.load_word(session, word_id)
    if word is None:
        raise not_found("So‘z topilmadi")
    return word


@router.get("/words", response_model=Page[AdminWordRow])
async def list_words(
    status: str | None = None,
    lang: str | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Word)
    if status:
        stmt = stmt.where(Word.status == status)
    if lang:
        stmt = stmt.where(Word.language_code == lang)
    if q:
        stmt = stmt.where(Word.normalized.like(f"%{normalize(q, lang)}%"))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    words = await session.scalars(
        stmt.options(selectinload(Word.senses))
        .order_by(Word.updated_at.desc(), Word.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return Page(items=await _rows(session, list(words.all())), total=total or 0, page=page, size=size)


@router.get("/moderation", response_model=Page[AdminWordRow])
async def moderation_queue(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    pending = (ContentStatus.DRAFT.value, ContentStatus.AI_GENERATED.value)
    words = list(
        (
            await session.scalars(
                select(Word).options(selectinload(Word.senses)).where(Word.status.in_(pending))
            )
        ).all()
    )
    rows = await _rows(session, words)
    rows.sort(
        key=lambda r: (-r.open_reports, -r.demand, r.confidence if r.confidence is not None else 1.0, r.id)
    )
    return Page(items=rows[(page - 1) * size : page * size], total=len(rows), page=page, size=size)


@router.post("/words", response_model=AdminWordDetail, status_code=201)
async def create_word(
    data: CreateWordIn, user: User = Depends(require_editor), session: AsyncSession = Depends(get_db)
):
    key = normalize(data.lemma, data.language_code)
    if await session.scalar(
        select(Word.id).where(Word.language_code == data.language_code, Word.normalized == key)
    ):
        raise conflict("Bu so‘z allaqachon mavjud")
    word = await dictionary.create_entry(
        session, data.language_code, WordEntryIn(lemma=data.lemma, entry_type=data.entry_type),
        status=ContentStatus.DRAFT, source_code="editor", reason="admin:create", user_id=user.id,
    )  # fmt: skip
    await session.commit()
    return await _detail(session, await _load(session, word.id))


@router.post("/words/generate", response_model=generation.JobOut)
async def generate_word(
    data: GenerateIn,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_editor),
    redis: Redis = Depends(get_redis),
):
    return await generation.start_job(
        redis, term=data.term, lang_hint=data.lang, domain=None, subject=quotas.subject_for(user, client_ip(request)),
        user_id=user.id, background_tasks=background_tasks,
    )  # fmt: skip


@router.get("/words/{word_id}", response_model=AdminWordDetail)
async def get_word(word_id: int, _: User = Depends(require_editor), session: AsyncSession = Depends(get_db)):
    return await _detail(session, await _load(session, word_id))


@router.put("/words/{word_id}", response_model=AdminWordDetail)
async def update_word(
    word_id: int,
    data: UpdateWordIn,
    user: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    word = await _load(session, word_id)
    try:
        await dictionary.update_entry(
            session, word, data.entry, reason=f"admin:edit {data.reason}".strip(), user_id=user.id,
            source_code="editor",
        )  # fmt: skip
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise conflict("Bu lemma bilan boshqa so‘z mavjud") from exc
    return await _detail(session, await _load(session, word_id))


async def _set_status(
    session: AsyncSession, word_id: int, status: ContentStatus, user: User
) -> AdminWordDetail:
    word = await _load(session, word_id)
    await dictionary.set_status(session, word, status, reason=f"admin:{status.value}", user_id=user.id)
    if status == ContentStatus.PUBLISHED:
        word.confidence = max(word.confidence or 0.0, 0.95)
    await session.commit()
    return await _detail(session, await _load(session, word_id))


@router.post("/words/{word_id}/publish", response_model=AdminWordDetail)
async def publish_word(
    word_id: int, user: User = Depends(require_editor), session: AsyncSession = Depends(get_db)
):
    return await _set_status(session, word_id, ContentStatus.PUBLISHED, user)


@router.post("/words/{word_id}/reject", response_model=AdminWordDetail)
async def reject_word(
    word_id: int, user: User = Depends(require_editor), session: AsyncSession = Depends(get_db)
):
    return await _set_status(session, word_id, ContentStatus.REJECTED, user)


@router.post("/words/{word_id}/regenerate", response_model=generation.JobOut)
async def regenerate_word(
    word_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    word = await _load(session, word_id)
    return await generation.start_job(
        redis, term=word.lemma, lang_hint=word.language_code, domain=None,
        subject=quotas.subject_for(user, client_ip(request)), user_id=user.id,
        background_tasks=background_tasks, regenerate_word_id=word.id,
    )  # fmt: skip


@router.delete("/words/{word_id}", status_code=204)
async def delete_word(
    word_id: int, _: User = Depends(require_admin), session: AsyncSession = Depends(get_db)
):
    await session.execute(delete(Word).where(Word.id == word_id))
    await session.commit()


@router.get("/words/{word_id}/versions/{version}")
async def get_version(
    word_id: int, version: int, _: User = Depends(require_editor), session: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    snap = await session.scalar(
        select(WordVersion.snapshot).where(WordVersion.word_id == word_id, WordVersion.version == version)
    )
    if snap is None:
        raise not_found("Versiya topilmadi")
    return snap
