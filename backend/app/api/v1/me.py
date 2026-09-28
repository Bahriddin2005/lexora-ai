from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import client_ip, get_current_user, get_current_user_optional
from app.core.errors import not_found
from app.core.redis import get_redis
from app.models import User, UserFavorite, Word
from app.models.enums import VISIBLE_STATUSES
from app.schemas.entry import WordSummary
from app.services import dictionary, quotas

router = APIRouter(prefix="/me", tags=["me"])


class FavoriteIn(BaseModel):
    word_id: int


@router.get("/favorites", response_model=list[WordSummary])
async def list_favorites(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    rows = (
        await session.execute(
            select(UserFavorite.word_id, UserFavorite.created_at)
            .where(UserFavorite.user_id == user.id)
            .order_by(UserFavorite.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).all()
    saved = dict(rows)
    items = await dictionary.summaries(
        session, [word_id for word_id, _ in rows], explain_lang=user.ui_language
    )
    for item in items:
        item.saved_at = saved[item.id]
    return items


@router.post("/favorites", status_code=201)
async def add_favorite(
    data: FavoriteIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    exists = await session.scalar(
        select(Word.id).where(Word.id == data.word_id, Word.status.in_(VISIBLE_STATUSES))
    )
    if not exists:
        raise not_found("So‘z topilmadi")
    await session.execute(
        insert(UserFavorite).values(user_id=user.id, word_id=data.word_id).on_conflict_do_nothing()
    )
    await session.commit()
    return {"word_id": data.word_id, "is_favorite": True}


@router.delete("/favorites/{word_id}", status_code=204)
async def remove_favorite(
    word_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    await session.execute(
        delete(UserFavorite).where(UserFavorite.user_id == user.id, UserFavorite.word_id == word_id)
    )
    await session.commit()


@router.get("/quota")
async def my_quota(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    redis: Redis = Depends(get_redis),
):
    subject = quotas.subject_for(user, client_ip(request))
    return {"plan": subject.plan, "unlimited": subject.unlimited, "usage": await quotas.usage(redis, subject)}
