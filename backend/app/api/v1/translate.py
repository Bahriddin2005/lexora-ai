from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import AIError, get_provider, require_provider
from app.core.db import get_db
from app.core.deps import client_ip, get_current_user_optional
from app.core.errors import ai_unavailable, bad_request
from app.core.redis import get_redis
from app.models import User
from app.services import quotas, translation, tts
from app.services.languages import active_languages

router = APIRouter(tags=["translate"])


class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    source: str = "auto"
    target: str = "uz"
    context: str | None = Field(default=None, max_length=1000)


@router.post("/translate", response_model=translation.TranslateOut)
async def translate_text(
    data: TranslateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    codes = {lang.code for lang in await active_languages(session)}
    if data.target not in codes or (data.source != "auto" and data.source not in codes):
        raise bad_request("Qo‘llab-quvvatlanmaydigan til")
    try:
        return await translation.translate(
            session,
            redis,
            get_provider(),
            text=data.text,
            source=data.source,
            target=data.target,
            context=data.context,
            subject=quotas.subject_for(user, client_ip(request)),
            user_id=user.id if user else None,
        )
    except AIError as exc:
        raise ai_unavailable() from exc


@router.get("/tts", summary="Pronunciation audio (WAV), cached in object storage")
async def text_to_speech(
    request: Request,
    text: str = Query(min_length=1, max_length=tts.MAX_TTS_CHARS),
    lang: str = Query(max_length=8),
    accent: str | None = Query(default=None, max_length=8),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    langs = {lang.code: lang for lang in await active_languages(session)}
    if lang not in langs or not langs[lang].tts_supported:
        raise bad_request("Bu til uchun talaffuz mavjud emas")
    provider = require_provider()
    try:
        audio = await tts.get_audio(
            session,
            redis,
            provider,
            text=text.strip(),
            lang=lang,
            accent=accent,
            subject=quotas.subject_for(user, client_ip(request)),
        )
    except AIError as exc:
        raise ai_unavailable() from exc
    return Response(
        audio, media_type="audio/wav", headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )
