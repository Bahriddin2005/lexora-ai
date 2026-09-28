import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Language
from app.services.normalization import ALT_SCRIPTS

_TTL = 60.0
_cache: tuple[float, list["LanguageInfo"]] | None = None


@dataclass(frozen=True)
class LanguageInfo:
    code: str
    name: str
    native_name: str
    script: str
    direction: str
    flag: str | None
    tts_supported: bool


async def active_languages(session: AsyncSession) -> list[LanguageInfo]:
    global _cache
    if _cache and time.monotonic() - _cache[0] < _TTL:
        return _cache[1]
    rows = await session.scalars(
        select(Language).where(Language.is_active.is_(True)).order_by(Language.sort_order, Language.code)
    )
    langs = [
        LanguageInfo(
            lang.code, lang.name, lang.native_name, lang.script, lang.direction, lang.flag, lang.tts_supported
        )
        for lang in rows
    ]
    _cache = (time.monotonic(), langs)
    return langs


def invalidate() -> None:
    global _cache
    _cache = None


def candidates_for_script(langs: list[LanguageInfo], script: str) -> list[str]:
    """Languages whose words can be typed in `script` (e.g. Uzbek accepts Cyrillic input)."""
    return [
        lang.code for lang in langs if lang.script == script or script in ALT_SCRIPTS.get(lang.code, set())
    ]
