from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.languages import active_languages

router = APIRouter(tags=["languages"])


class LanguageOut(BaseModel):
    code: str
    name: str
    native_name: str
    script: str
    direction: str
    flag: str | None
    tts_supported: bool


@router.get("/languages", response_model=list[LanguageOut])
async def list_languages(session: AsyncSession = Depends(get_db)):
    return [LanguageOut(**lang.__dict__) for lang in await active_languages(session)]
