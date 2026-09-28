import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin.common import Page
from app.core.db import get_db
from app.core.deps import require_admin, require_editor
from app.core.errors import bad_request, conflict, not_found
from app.models import AIGeneration, Language, Report, SearchLog, User, Word
from app.models.enums import ReportStatus, UserPlan, UserRole
from app.services import languages as languages_service

router = APIRouter()


# ---------- dashboard ----------


class MissingWord(BaseModel):
    normalized: str
    query: str
    language_code: str | None
    count: int
    last_searched_at: datetime


async def _missing(session: AsyncSession, days: int, lang: str | None, limit: int) -> list[MissingWord]:
    exists = select(Word.id).where(Word.normalized == SearchLog.normalized).exists()
    stmt = (
        select(
            SearchLog.normalized,
            func.max(SearchLog.query),
            func.max(SearchLog.language_code),
            func.count(),
            func.max(SearchLog.created_at),
        )
        .where(
            SearchLog.found.is_(False),
            SearchLog.intent != "list_new_terms",
            SearchLog.created_at >= datetime.now(UTC) - timedelta(days=days),
            ~exists,
        )
        .group_by(SearchLog.normalized)
        .order_by(func.count().desc(), func.max(SearchLog.created_at).desc())
        .limit(limit)
    )
    if lang:
        stmt = stmt.where(SearchLog.language_code == lang)
    return [
        MissingWord(normalized=n, query=q, language_code=lc, count=c, last_searched_at=t)
        for n, q, lc, c, t in (await session.execute(stmt)).all()
    ]


@router.get("/stats")
async def stats(_: User = Depends(require_editor), session: AsyncSession = Depends(get_db)):
    day_ago = datetime.now(UTC) - timedelta(days=1)
    week_ago = datetime.now(UTC) - timedelta(days=7)
    by_status = dict((await session.execute(select(Word.status, func.count()).group_by(Word.status))).all())
    by_language = dict(
        (await session.execute(select(Word.language_code, func.count()).group_by(Word.language_code))).all()
    )
    searches = dict(
        (
            await session.execute(
                select(SearchLog.found, func.count())
                .where(SearchLog.created_at >= day_ago)
                .group_by(SearchLog.found)
            )
        ).all()
    )
    ai = (
        await session.execute(
            select(func.count(), func.coalesce(func.sum(AIGeneration.cost_usd), 0)).where(
                AIGeneration.created_at >= week_ago
            )
        )
    ).one()
    total_searches = sum(searches.values())
    return {
        "words": {"total": sum(by_status.values()), "by_status": by_status, "by_language": by_language},
        "users": await session.scalar(select(func.count()).select_from(User)),
        "searches_24h": total_searches,
        "not_found_24h": searches.get(False, 0),
        "not_found_rate": round(searches.get(False, 0) / total_searches, 3) if total_searches else 0.0,
        "open_reports": await session.scalar(
            select(func.count()).select_from(Report).where(Report.status == ReportStatus.OPEN)
        ),
        "ai_calls_7d": ai[0],
        "ai_cost_7d": float(ai[1]),
        "top_missing": [m.model_dump(mode="json") for m in await _missing(session, 30, None, 10)],
    }


@router.get("/missing-words", response_model=list[MissingWord])
async def missing_words(
    days: int = Query(default=30, ge=1, le=365),
    lang: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    _: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    return await _missing(session, days, lang, limit)


# ---------- reports ----------


class ReportRow(BaseModel):
    id: int
    word_id: int
    word_lemma: str
    word_language: str
    word_slug: str
    sense_id: int | None
    reason: str
    comment: str | None
    status: str
    user_email: str | None
    created_at: datetime
    resolved_at: datetime | None


class ReportUpdate(BaseModel):
    status: ReportStatus


@router.get("/reports", response_model=Page[ReportRow])
async def list_reports(
    status: ReportStatus | None = ReportStatus.OPEN,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    base = (
        select(Report, Word, User.email)
        .join(Word, Word.id == Report.word_id)
        .outerjoin(User, User.id == Report.user_id)
    )
    if status:
        base = base.where(Report.status == status)
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.execute(
        base.order_by(Report.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    items = [
        ReportRow(
            id=r.id,
            word_id=w.id,
            word_lemma=w.lemma,
            word_language=w.language_code,
            word_slug=w.normalized,
            sense_id=r.sense_id,
            reason=r.reason,
            comment=r.comment,
            status=r.status,
            user_email=email,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
        )  # fmt: skip
        for r, w, email in rows.all()
    ]
    return Page(items=items, total=total or 0, page=page, size=size)


@router.patch("/reports/{report_id}")
async def update_report(
    report_id: int,
    data: ReportUpdate,
    user: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    report = await session.get(Report, report_id)
    if report is None:
        raise not_found("Report topilmadi")
    report.status = data.status
    if data.status == ReportStatus.OPEN:
        report.resolved_by, report.resolved_at = None, None
    else:
        report.resolved_by, report.resolved_at = user.id, datetime.now(UTC)
    await session.commit()
    return {"id": report.id, "status": report.status}


# ---------- users (admin) ----------


class UserRow(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    plan: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserPatch(BaseModel):
    role: UserRole | None = None
    plan: UserPlan | None = None
    is_active: bool | None = None


@router.get("/users", response_model=Page[UserRow])
async def list_users(
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q.strip().lower()}%"))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    users = await session.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size))
    items = [
        UserRow(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            plan=u.plan,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
        )  # fmt: skip
        for u in users.all()
    ]
    return Page(items=items, total=total or 0, page=page, size=size)


@router.patch("/users/{user_id}", response_model=UserRow)
async def update_user(
    user_id: uuid.UUID,
    data: UserPatch,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    user = await session.get(User, user_id)
    if user is None:
        raise not_found("Foydalanuvchi topilmadi")
    if user.id == admin.id and (data.is_active is False or (data.role and data.role != UserRole.ADMIN)):
        raise bad_request("O‘z hisobingizni bloklay yoki admin rolidan chiqara olmaysiz")
    for field in ("role", "plan", "is_active"):
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return UserRow(
        id=user.id, email=user.email, display_name=user.display_name, role=user.role, plan=user.plan,
        is_active=user.is_active, created_at=user.created_at, last_login_at=user.last_login_at,
    )  # fmt: skip


# ---------- languages (admin) ----------


class LanguageRow(BaseModel):
    code: str = Field(min_length=2, max_length=8, pattern=r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
    name: str = Field(min_length=1, max_length=64)
    native_name: str = Field(min_length=1, max_length=64)
    script: Literal[
        "Latn", "Cyrl", "Arab", "Hans", "Hant", "Jpan", "Kore", "Deva", "Grek", "Hebr", "Geor", "Armn"
    ]
    direction: Literal["ltr", "rtl"] = "ltr"
    flag: str | None = None
    is_active: bool = True
    tts_supported: bool = True
    sort_order: int = 100


class LanguagePatch(BaseModel):
    name: str | None = None
    native_name: str | None = None
    flag: str | None = None
    is_active: bool | None = None
    tts_supported: bool | None = None
    sort_order: int | None = None


def _language_row(lang: Language) -> LanguageRow:
    return LanguageRow(
        code=lang.code, name=lang.name, native_name=lang.native_name, script=lang.script, direction=lang.direction,
        flag=lang.flag, is_active=lang.is_active, tts_supported=lang.tts_supported, sort_order=lang.sort_order,
    )  # fmt: skip


@router.get("/languages", response_model=list[LanguageRow])
async def list_all_languages(_: User = Depends(require_admin), session: AsyncSession = Depends(get_db)):
    rows = await session.scalars(select(Language).order_by(Language.sort_order, Language.code))
    return [_language_row(lang) for lang in rows.all()]


@router.post("/languages", response_model=LanguageRow, status_code=201)
async def create_language(
    data: LanguageRow, _: User = Depends(require_admin), session: AsyncSession = Depends(get_db)
):
    if await session.get(Language, data.code):
        raise conflict("Bu til allaqachon mavjud")
    lang = Language(**data.model_dump())
    session.add(lang)
    await session.commit()
    languages_service.invalidate()
    return _language_row(lang)


@router.patch("/languages/{code}", response_model=LanguageRow)
async def update_language(
    code: str, data: LanguagePatch, _: User = Depends(require_admin), session: AsyncSession = Depends(get_db)
):
    lang = await session.get(Language, code)
    if lang is None:
        raise not_found("Til topilmadi")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lang, field, value)
    await session.commit()
    languages_service.invalidate()
    return _language_row(lang)


# ---------- AI usage ----------


@router.get("/ai-usage")
async def ai_usage(
    days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_editor),
    session: AsyncSession = Depends(get_db),
):
    since = datetime.now(UTC) - timedelta(days=days)
    errors = func.count().filter(AIGeneration.ok.is_(False))
    cols = (
        func.count(),
        errors,
        func.coalesce(func.sum(AIGeneration.tokens_in), 0),
        func.coalesce(func.sum(AIGeneration.tokens_out), 0),
        func.coalesce(func.sum(AIGeneration.cost_usd), Decimal(0)),
    )

    def row(values) -> dict[str, float | int]:
        calls, errs, tin, tout, cost = values
        return {"calls": calls, "errors": errs, "tokens_in": tin, "tokens_out": tout, "cost_usd": float(cost)}

    totals = (await session.execute(select(*cols).where(AIGeneration.created_at >= since))).one()
    by_agent = await session.execute(
        select(AIGeneration.agent, AIGeneration.model, *cols)
        .where(AIGeneration.created_at >= since)
        .group_by(AIGeneration.agent, AIGeneration.model)
        .order_by(func.count().desc())
    )
    day = cast(AIGeneration.created_at, Date)
    by_day = await session.execute(
        select(day, *cols).where(AIGeneration.created_at >= since).group_by(day).order_by(day)
    )
    return {
        "days": days,
        "totals": row(totals),
        "by_agent": [{"agent": a, "model": m, **row(rest)} for a, m, *rest in by_agent.all()],
        "by_day": [{"day": d.isoformat(), **row(rest)} for d, *rest in by_day.all()],
    }
