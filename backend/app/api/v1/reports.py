from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import client_ip, get_current_user_optional
from app.core.errors import bad_request, not_found
from app.core.redis import get_redis
from app.models import Report, User, Word, WordSense
from app.models.enums import ReportReason
from app.services import quotas

router = APIRouter(tags=["reports"])


class ReportIn(BaseModel):
    word_id: int
    sense_id: int | None = None
    reason: ReportReason
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/reports", status_code=201)
async def create_report(
    data: ReportIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    await quotas.rate_limit(redis, f"report:{client_ip(request)}", limit=20, window_seconds=3600)
    if not await session.get(Word, data.word_id):
        raise not_found("So‘z topilmadi")
    if data.sense_id is not None:
        owner = await session.scalar(select(WordSense.word_id).where(WordSense.id == data.sense_id))
        if owner != data.word_id:
            raise bad_request("Ma’no bu so‘zga tegishli emas")
    report = Report(
        user_id=user.id if user else None,
        word_id=data.word_id,
        sense_id=data.sense_id,
        reason=data.reason,
        comment=(data.comment or "").strip() or None,
    )
    session.add(report)
    await session.commit()
    return {"id": report.id, "status": report.status}
